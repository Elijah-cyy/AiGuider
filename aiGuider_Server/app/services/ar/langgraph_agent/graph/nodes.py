"""
节点实现

定义LangGraph Agent流程图的所有节点函数
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import uuid  # 新增导入UUID库

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from .state import AgentState, ToolState
from ..prompts.templates import load_thinker_prompt

logger = logging.getLogger(__name__)

def thinker_node(state: AgentState, multimodal_model: Any) -> Dict[str, Any]:
    """
    核心思考节点
    
    分析多模态输入，决定是否需要响应，判断是直接回答还是调用工具
    
    Args:
        state: 当前状态
        multimodal_model: 多模态语言模型
        
    Returns:
        更新后的状态，包含思考结果
    """
    # 从状态中获取消息
    messages = state["messages"]
    
    if not messages:
        logger.warning("不应被触发：对话的历史消息为空，无法执行思考节点")
        return {
            "safety_issues": ["对话的历史消息为空，无法执行思考节点"],
            "final_answer": "无法处理空消息"
        }
    
    # 获取当前输入
    input_data = state.get("current_input")
    # logger.info(f"当前输入: {input_data}")
    
    # 直接使用传入的多模态模型
    if not multimodal_model:
        logger.error("未找到多模态模型")
        return {"safety_issues": ["未找到多模态模型"]}
    
    # 构建提示词
    prompt = []
    thinker_prompt = load_thinker_prompt()
    prompt.append(SystemMessage(content=thinker_prompt))
    
    # 添加历史消息
    prompt.extend(messages)
    # # 打印提示词列表的每个成员
    # logger.info("提示词列表内容:")
    # for i, msg in enumerate(prompt):
    #     logger.info(f"消息 {i}: 类型={type(msg).__name__}, 内容={msg.content}")
    
    # 调用模型进行思考
    try:
        response = multimodal_model.invoke(prompt)
        logger.info(f"模型响应: {response}")
        
        # 处理多模态模型返回的内容格式，确保提取纯文本
        if hasattr(response, "content"):
            content_data = response.content
            # 处理不同格式的响应内容
            if isinstance(content_data, list):
                # 多模态模型返回的列表格式，提取文本内容
                extracted_texts = []
                for item in content_data:
                    if isinstance(item, dict) and 'text' in item:
                        extracted_texts.append(item['text'])
                content = "\n".join(extracted_texts)
                logger.info(f"从多模态响应中提取纯文本内容: {content}")
            elif isinstance(content_data, str):
                # 纯文本内容
                content = content_data
            else:
                # 其他类型，转为字符串
                content = str(content_data)
        else:
            content = str(response)
        
        # 检查是否需要忽略
        if "IGNORE_SIGNAL" in content:
            logger.info("思考节点决定忽略当前输入")
            return {"final_answer": ""}
        
        # 检查是否有工具调用
        if hasattr(response, "additional_kwargs") and \
           isinstance(response.additional_kwargs, dict) and \
           "tool_calls" in response.additional_kwargs and \
           response.additional_kwargs["tool_calls"]:
            
            logger.info("检测到模型响应的additional_kwargs中包含tool_calls")
            tool_calls_list = response.additional_kwargs["tool_calls"]
            logger.debug(f"additional_kwargs中的tool_calls内容: {tool_calls_list}")
            
            tool_call = tool_calls_list[0]  # 取第一个工具调用
            
            # 根据实际响应结构获取工具信息
            tool_name = None # 初始化
            tool_args = {} # 初始化

            if hasattr(tool_call, "name") and hasattr(tool_call, "args"):
                # 直接访问属性的情况
                tool_name = tool_call.name
                tool_args = tool_call.args
            elif isinstance(tool_call, dict):
                # 字典结构的情况
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
            elif hasattr(tool_call, "function"):
                # 可能是嵌套在function字段中的情况
                function = tool_call.function
                tool_name = getattr(function, "name", None)
                arguments = getattr(function, "arguments", "{}")
                import json
                try:
                    if isinstance(arguments, str):
                        tool_args = json.loads(arguments)
                    else:
                        tool_args = arguments
                except:
                    tool_args = {"query": str(arguments)}
            else:
                # 其他情况，尝试使用字符串表示并记录日志
                logger.warning(f"无法识别的tool_call格式 (来自additional_kwargs): {tool_call}")
                # 不再设置tool_name = str(tool_call) 来强制执行，而是让其保持为None
            
            if tool_name: # 仅当tool_name被成功解析时才继续
                # 创建工具状态
                tool_state = ToolState(
                    name=tool_name,
                    input=tool_args,
                    status="pending"
                )
                logger.info(f"准备调用工具 (来自additional_kwargs): {tool_name}，参数: {tool_args}")
                return {
                    "messages": [AIMessage(content=content)], # 'content' is the full model text response
                    "tool": tool_state
                }
            else:
                logger.info("在additional_kwargs中发现tool_calls，但未能成功解析出有效的tool_name。将不执行工具调用。")

        # 保留原有的文本解析逻辑作为备选方案
        elif "TOOL_CALL:" in content:
            logger.info("通过文本解析检测到工具调用指令 (未在additional_kwargs成功解析或additional_kwargs无tool_calls)")
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
                    "messages": [AIMessage(content=content)],
                    "tool": tool_state
                }
        
        # 直接生成最终答案
        if "FINAL_ANSWER:" in content:
            answer = content.split("FINAL_ANSWER:")[1].strip()
            logger.info("思考节点生成了最终答案")
            
            # 使用add_messages Reducer，直接返回新消息
            return {
                "messages": [AIMessage(content=answer)],
                "final_answer": answer
            }
        
        # 未找到明确的行动指令，将全部内容作为回答
        logger.info("思考节点生成了不带标记的答案")
        return {
            "messages": [AIMessage(content=content)],
            "final_answer": content
        }
        
    except Exception as e:
        error_msg = f"思考节点执行失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"safety_issues": [error_msg]}

def router_node(state: AgentState) -> str:
    """
    路由节点
    
    根据Agent状态决定下一步行动
    
    Args:
        state: 当前状态
        
    Returns:
        下一个节点名称
    """
    # 检查是否有安全问题
    safety_issues = state.get("safety_issues", [])
    if safety_issues:
        logger.info("检测到安全问题，转到错误处理节点")
        return "error_handler"
    
    # 检查是否已有最终回答
    final_answer = state.get("final_answer")
    if final_answer is not None:
        logger.info("已有最终回答，结束流程")
        return "end"
    
    # 检查是否需要执行工具
    tool = state.get("tool")
    if tool:
        # 打印当前消息列表
        messages = state.get("messages", [])
        logger.info(f"当前消息列表: {messages[-1]}")
        logger.info(f"需要执行工具: {tool.name if hasattr(tool, 'name') else 'unknown'}")
        return "action_executor"
    
    # 默认结束流程
    logger.info("没有明确后续流程，结束执行")
    return "end"

def action_executor_node(state: AgentState, tools: Dict[str, Any]) -> Dict[str, Any]:
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
    
    # 获取工具信息
    tool = state["tool"]
    
    if not tool or not hasattr(tool, "name") or not hasattr(tool, "input"):
        logger.warning("没有工具调用需要执行")
        return {"safety_issues": ["工具调用信息不完整"]}
    
    # 获取工具名称和参数
    tool_name = tool.name
    tool_args = tool.input
    
    # 检查工具是否存在
    if not tools or tool_name not in tools:
        error_msg = f"未找到工具: {tool_name}"
        logger.error(error_msg)
        
        # 修改: 不直接报错，而是返回友好的错误信息作为工具结果
        result = f"系统当前不支持 {tool_name} 工具。我会尝试直接回答您的问题。"
        
        # 创建工具消息，使用已有参数
        tool_message = ToolMessage(
            content=result,
            name=tool_name,
            tool_call_id=str(uuid.uuid4())  # 添加唯一的工具调用ID
        )
        
        # 更新工具状态为不支持但可继续
        updated_tool = ToolState(
            name=tool_name,
            input=tool_args,
            output=result,
            status="unsupported"
        )
        
        # 使用add_messages Reducer，返回新消息和错误信息，但不中断流程
        return_val = {
            "messages": [tool_message],
            "tool": updated_tool
        }
        
        # 打印工具输出内容
        logger.info(f"工具节点输出 (工具不存在): {result}")
        
        return return_val
    
    # 执行工具调用
    try:
        tool_func = tools[tool_name]
        # 直接调用函数，而不是调用search方法
        result = tool_func(**tool_args)
        
        # 生成唯一的工具调用ID
        tool_call_id = str(uuid.uuid4())
        
        # 创建工具消息
        tool_message = ToolMessage(
            content=result,
            name=tool_name,
            tool_call_id=tool_call_id  # 添加工具调用ID
        )
        
        # 更新工具状态
        updated_tool = ToolState(
            name=tool_name,
            input=tool_args,
            output=result,
            status="success"
        )
        
        # 使用add_messages Reducer，直接返回新消息
        action_result = {
            "messages": [tool_message],
            "tool": updated_tool
        }
        
        logger.info(f"工具 {tool_name} 执行完成")
        # 打印工具输出内容
        logger.info(f"工具节点输出: {result}")
        
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
        
        # 也需要为错误情况添加工具调用ID
        tool_call_id = str(uuid.uuid4())
        error_content = f"执行出错: {str(e)}"
        tool_message = ToolMessage(
            content=error_content,
            name=tool_name,
            tool_call_id=tool_call_id
        )
        
        # 打印工具错误输出
        logger.info(f"工具节点错误输出: {error_content}")
        
        return {
            "messages": [tool_message],
            "safety_issues": [error_msg],
            "tool": updated_tool
        }

def error_handler_node(state: AgentState) -> Dict[str, Any]:
    """
    错误处理节点
    
    处理流程中发生的错误，生成用户友好的错误消息
    
    触发时机:
    1. 当state中存在safety_issues时，由router_node路由到此节点
    2. safety_issues在以下情况下会被设置:
       - 思考节点(thinker_node)中:
         - 未找到多模态模型时
         - 模型调用过程中出现异常时
       - 工具执行节点(action_executor_node)中:
         - 工具调用信息不完整时(没有工具对象、工具名称或输入参数)
         - 请求的工具不存在于可用工具字典中
         - 工具执行过程中出现异常时
    
    Args:
        state: 当前状态
        
    Returns:
        包含错误处理结果的状态
    """
    logger.info("错误处理节点执行")
    
    # 获取安全问题
    safety_issues = state["safety_issues"]
    
    # 汇总错误原因
    error_reasons = " ".join(safety_issues) if safety_issues else "未知错误"
    
    # 构建用户友好的错误消息
    error_message = f"很抱歉，我在处理您的请求时遇到了问题。{error_reasons}"
    
    # 创建回复消息
    error_response = AIMessage(content=error_message)
    
    # 返回包含错误消息的状态
    return {
        "messages": [error_response],
        "final_answer": error_message
    } 