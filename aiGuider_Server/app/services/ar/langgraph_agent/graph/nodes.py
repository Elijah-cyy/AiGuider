"""
节点实现

定义LangGraph Agent流程图的所有节点函数
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from .state import AgentState, ToolState
from ..prompts.templates import load_thinker_prompt

logger = logging.getLogger(__name__)

def thinker_node(state: Dict[str, Any], multimodal_model: Any) -> Dict[str, Any]:
    """
    核心思考节点
    
    分析多模态输入，决定是否需要响应，判断是直接回答还是调用工具
    
    Args:
        state: 当前状态
        multimodal_model: 多模态语言模型
        
    Returns:
        更新后的状态，包含思考结果
    """
    logger.info("思考节点执行")
    
    # 由于使用add_messages Reducer，不再需要初始化处理时间
    
    # 检查state是字典还是AgentState对象
    if isinstance(state, dict):
        messages = state.get("messages", [])
        state_dump = state
    else:
        messages = state.messages if hasattr(state, "messages") else []
        state_dump = state.model_dump()
    
    if not messages:
        logger.warning("消息为空，无法执行思考节点")
        return {**state_dump, "final_answer": "无法处理空消息"}
    
    # 获取最新的用户消息和多模态输入
    last_message = messages[-1]
    
    # 检查state是字典还是AgentState对象
    if isinstance(state, dict):
        input_data = state.get("current_input")
    else:
        input_data = state.current_input
    
    # 检查多模态内容
    has_image = False
    if input_data and isinstance(input_data.content, list):
        for item in input_data.content:
            if isinstance(item, dict) and (item.get("type") == "image_url" or item.get("type") == "image"):
                has_image = True
                break
    
    # 记录输入类型
    if has_image:
        logger.info("收到包含图像的多模态输入")
    
    # 直接使用传入的多模态模型，不从状态中获取
    if not multimodal_model:
        logger.error("未找到多模态模型")
        return {**state_dump, "safety_issues": ["未找到多模态模型"]}
    
    # 构建提示
    prompt = []
    
    # 添加系统消息
    thinker_prompt = load_thinker_prompt()
    prompt.append(SystemMessage(content=thinker_prompt))
    
    # 添加历史消息
    prompt.extend(messages)
    
    # 调用模型进行思考
    try:
        response = multimodal_model.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        
        # 检查是否需要忽略
        if "IGNORE_SIGNAL" in content:
            logger.info("思考节点决定忽略当前输入")
            return {**state_dump, "final_answer": ""}
        
        # 检查是否有工具调用
        if "TOOL_CALL:" in content:
            logger.info("思考节点决定调用工具")
            # 解析工具调用
            tool_parts = content.split("TOOL_CALL:")[1].strip().split("\n")
            tool_name = None
            tool_query = None
            
            for part in tool_parts:
                if part.startswith("工具:"):
                    tool_name = part.replace("工具:", "").strip()
                elif part.startswith("查询:"):
                    tool_query = part.replace("查询:", "").strip()
            
            if tool_name and tool_query:
                # 创建工具状态
                tool_state = ToolState(
                    name=tool_name,
                    input={"query": tool_query},
                    status="pending"
                )
                
                # 使用add_messages Reducer，直接返回新消息
                return {
                    **state_dump,
                    "messages": [AIMessage(content=content)],
                    "tool": tool_state
                }
        
        # 直接生成最终答案
        if "FINAL_ANSWER:" in content:
            answer = content.split("FINAL_ANSWER:")[1].strip()
            logger.info("思考节点生成了最终答案")
            
            # 使用add_messages Reducer，直接返回新消息
            return {
                **state_dump,
                "messages": [AIMessage(content=answer)],
                "final_answer": answer
            }
        
        # 未找到明确的行动指令，将全部内容作为回答
        logger.info("思考节点生成了不带标记的答案")
        return {
            **state_dump,
            "messages": [AIMessage(content=content)],
            "final_answer": content
        }
    
    except Exception as e:
        logger.error(f"思考节点执行出错: {e}", exc_info=True)
        return {**state_dump, "safety_issues": [f"思考过程发生错误: {str(e)}"]}

def router_node(state: Dict[str, Any]) -> str:
    """
    路由节点
    
    根据思考节点的输出决定下一步流程
    
    Args:
        state: 当前状态
        
    Returns:
        下一个节点的名称
    """
    logger.info("路由节点执行")
    
    # 检查state是字典还是AgentState对象
    if isinstance(state, dict):
        safety_issues = state.get("safety_issues", [])
        final_answer = state.get("final_answer")
        tool = state.get("tool")
    else:
        safety_issues = state.safety_issues
        final_answer = state.final_answer
        tool = state.tool
    
    # 检查安全问题
    if safety_issues:
        logger.warning(f"检测到安全问题: {safety_issues}")
        return "error_handler"
    
    # 检查是否有最终答案
    if final_answer is not None:
        logger.info(f"已生成最终答案：{final_answer}")
        logger.info("已生成最终答案，流程结束")
        return "end"
    
    # 检查是否有工具调用
    if tool and tool.name and tool.input:
        logger.info(f"检测到工具调用: {tool.name}，进入工具节点")
        return "action_executor"
    
    # 默认返回错误处理节点
    logger.warning("节点输出不明确，进入错误处理")
    return "error_handler"

def action_executor_node(state: Dict[str, Any], tools: Dict[str, Any]) -> Dict[str, Any]:
    """
    工具执行节点
    
    执行思考节点决定的工具调用
    
    Args:
        state: 当前状态
        tools: 可用工具字典
        
    Returns:
        更新后的状态，包含工具执行结果
    """
    logger.info("工具执行节点执行")
    
    # 检查state是字典还是AgentState对象
    if isinstance(state, dict):
        tool = state.get("tool")
        state_dump = state
    else:
        tool = state.tool
        state_dump = state.model_dump()
    
    if not tool or not tool.name or not tool.input:
        logger.warning("没有工具调用需要执行")
        return {**state_dump, "safety_issues": ["工具调用信息不完整"]}
    
    # 获取工具名称和参数
    tool_name = tool.name
    tool_args = tool.input
    
    # 检查工具是否存在
    if not tools or tool_name not in tools:
        error_msg = f"未找到工具: {tool_name}"
        logger.error(error_msg)
        return {**state_dump, "safety_issues": [error_msg]}
    
    # 执行工具调用
    try:
        tool = tools[tool_name]
        if tool_name == "knowledge_search":
            result = tool.search(**tool_args)
        else:
            logger.warning(f"未知的工具类型: {tool_name}")
            result = f"不支持的工具: {tool_name}"
        
        # 创建工具消息
        tool_message = ToolMessage(
            content=result,
            name=tool_name
        )
        
        # 更新工具状态
        updated_tool = ToolState(
            name=tool_name,
            input=tool_args,
            output=result,
            status="success"
        )
        
        # 记录工具执行结果
        # 使用add_messages Reducer，直接返回新消息
        action_result = {
            **state_dump,
            "messages": [tool_message],
            "tool": updated_tool
        }
        
        logger.info(f"工具 {tool_name} 执行完成")
        return action_result
    
    except Exception as e:
        error_msg = f"工具 {tool_name} 执行出错: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 更新工具状态为错误
        updated_tool = ToolState(
            name=tool_name,
            input=tool_args,
            output=str(e),
            status="error"
        )
        
        return {
            **state_dump, 
            "safety_issues": [error_msg],
            "tool": updated_tool
        }

def error_handler_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    错误处理节点
    
    处理流程中发生的错误，生成用户友好的错误消息
    
    Args:
        state: 当前状态
        
    Returns:
        包含错误处理结果的状态
    """
    logger.info("错误处理节点执行")
    
    # 检查state是字典还是AgentState对象
    if isinstance(state, dict):
        safety_issues = state.get("safety_issues", [])
        state_dump = state
    else:
        safety_issues = state.safety_issues
        state_dump = state.model_dump()
    
    # 汇总错误原因
    error_reasons = " ".join(safety_issues) if safety_issues else "未知错误"
    
    # 构建用户友好的错误消息
    error_message = f"很抱歉，我在处理您的请求时遇到了问题。{error_reasons}"
    
    # 创建回复消息
    error_response = AIMessage(content=error_message)
    
    # 返回包含错误消息的状态
    return {
        **state_dump,
        "messages": [error_response],
        "final_answer": error_message
    } 