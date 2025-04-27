"""
图节点定义

定义LangGraph流程图中的节点函数
"""

from typing import Dict, Any, List, Optional
import logging
import copy

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import END
from ..tools.image_analyzer import ImageAnalyzer
from ..tools.knowledge_retriever import KnowledgeRetriever
from .state import AgentState

logger = logging.getLogger(__name__)

def analyze_image(
    state: Dict[str, Any],
    image_analyzer: ImageAnalyzer
) -> Dict[str, Any]:
    """
    分析图像节点
    
    从状态中提取图像，使用图像分析器进行分析
    
    Args:
        state: 当前状态
        image_analyzer: 图像分析器
        
    Returns:
        Dict: 更新后的状态
    """
    logger.info("开始分析图像")
    
    # 创建状态的副本，避免直接修改原始状态
    new_state = copy.deepcopy(state)
    
    # 从状态中获取消息
    messages = new_state.get("messages", [])
    
    # 检查是否有用户消息
    user_messages = [m for m in messages if isinstance(m, HumanMessage)]
    if not user_messages:
        logger.warning("没有找到用户消息")
        new_state["image_analysis_result"] = ""
        return new_state
    
    # 获取最后一条用户消息
    last_user_msg = user_messages[-1]
    
    # 检查消息内容是否包含图像
    if not isinstance(last_user_msg.content, list):
        logger.info("用户消息中没有图像内容")
        new_state["image_analysis_result"] = ""
        return new_state
    
    # 提取图像内容
    image_parts = [
        part for part in last_user_msg.content 
        if isinstance(part, dict) and part.get("type") == "image_url"
    ]
    
    if not image_parts:
        logger.info("用户消息中没有图像URL")
        new_state["image_analysis_result"] = ""
        return new_state
    
    # 获取第一个图像URL
    image_url = image_parts[0].get("image_url", {}).get("url", "")
    
    if not image_url:
        logger.warning("图像URL为空")
        new_state["image_analysis_result"] = ""
        return new_state
    
    # 分析图像
    try:
        analysis_result = image_analyzer.analyze(image_url)
        if analysis_result:
            logger.info(f"图像分析完成: {analysis_result[:100]}...")
            new_state["image_analysis_result"] = analysis_result
        else:
            logger.warning("图像分析结果为空")
            new_state["image_analysis_result"] = "无法获取图像分析结果"
    except Exception as e:
        logger.error(f"图像分析出错: {e}", exc_info=True)
        new_state["image_analysis_result"] = f"图像分析失败: {str(e)}"
    
    return new_state

def retrieve_knowledge(
    state: Dict[str, Any],
    knowledge_retriever: KnowledgeRetriever
) -> Dict[str, Any]:
    """
    检索知识节点
    
    基于图像分析结果和用户问题检索相关知识
    
    Args:
        state: 当前状态
        knowledge_retriever: 知识检索器
        
    Returns:
        Dict: 更新后的状态
    """
    logger.info("开始检索知识")
    
    # 创建状态的副本
    new_state = copy.deepcopy(state)
    
    # 获取图像分析结果
    image_analysis = new_state.get("image_analysis_result", "")
    
    # 从状态中获取消息
    messages = new_state.get("messages", [])
    
    # 提取用户问题
    user_question = ""
    user_messages = [m for m in messages if isinstance(m, HumanMessage)]
    if user_messages:
        # 获取最后一条用户消息中的文本
        last_user_msg = user_messages[-1]
        if isinstance(last_user_msg.content, str):
            user_question = last_user_msg.content
        elif isinstance(last_user_msg.content, list):
            # 提取文本部分
            text_parts = [
                part.get("text", "") 
                for part in last_user_msg.content 
                if isinstance(part, dict) and part.get("type") == "text"
            ]
            user_question = " ".join(text_parts)
    
    # 如果没有有效的分析结果或问题，跳过知识检索
    if not image_analysis and not user_question:
        logger.info("没有足够信息进行知识检索")
        new_state["knowledge"] = ""
        return new_state
    
    # 组合查询内容
    query = f"{image_analysis} {user_question}".strip()
    
    # 检索知识
    try:
        knowledge = knowledge_retriever.retrieve(query)
        if knowledge:
            logger.info(f"知识检索完成: {knowledge[:100]}...")
            new_state["knowledge"] = knowledge
        else:
            logger.info("知识检索未返回结果")
            new_state["knowledge"] = ""
    except Exception as e:
        logger.error(f"知识检索出错: {e}", exc_info=True)
        new_state["knowledge"] = ""
    
    return new_state

def generate_response(
    state: Dict[str, Any],
    model: Any
) -> Dict[str, Any]:
    """
    生成回复节点
    
    基于图像分析结果、检索的知识和用户问题生成回复
    
    Args:
        state: 当前状态
        model: 语言模型
        
    Returns:
        Dict: 更新后的状态
    """
    logger.info("开始生成回复")
    
    # 创建状态的副本
    new_state = copy.deepcopy(state)
    
    # 获取状态数据
    messages = new_state.get("messages", [])
    image_analysis = new_state.get("image_analysis_result", "")
    knowledge = new_state.get("knowledge", "")
    
    # 如果没有消息，返回错误提示
    if not messages:
        logger.error("消息列表为空")
        new_state["response"] = "抱歉，我无法处理空的消息列表。"
        return new_state
    
    # 创建系统消息
    system_prompt = messages[0].content if messages and isinstance(messages[0], SystemMessage) else ""
    
    # 如果有图像分析结果和知识，添加到系统提示
    additional_context = ""
    if image_analysis:
        additional_context += f"\n\n图像分析结果: {image_analysis}"
    if knowledge:
        additional_context += f"\n\n相关知识: {knowledge}"
    
    # 如果有额外上下文，创建一个新的系统消息
    if additional_context and messages:
        enhanced_system_prompt = system_prompt + additional_context
        messages = [SystemMessage(content=enhanced_system_prompt)] + messages[1:]
    
    # 生成回复
    try:
        response = model.invoke(messages)
        if response and hasattr(response, 'content'):
            response_text = response.content
            logger.info(f"生成回复完成: {response_text[:100]}...")
            
            # 添加AI回复到消息历史
            messages.append(AIMessage(content=response_text))
            
            # 更新状态
            new_state["messages"] = messages
            new_state["response"] = response_text
        else:
            logger.warning("模型返回了无效的响应")
            new_state["response"] = "抱歉，我生成回复时遇到了问题。请稍后再试。"
    except Exception as e:
        logger.error(f"生成回复出错: {e}", exc_info=True)
        new_state["response"] = "抱歉，我在处理您的请求时遇到了问题。请稍后再试。"
    
    return new_state 

def image_analyzer_node(state: AgentState) -> Dict[str, Any]:
    """
    图像分析节点包装函数
    
    Args:
        state: 当前状态
        
    Returns:
        Dict: 更新后的状态
    """
    logger.info("执行图像分析节点")
    try:
        # 从状态上下文中获取图像分析器
        image_analyzer = state.get("_tools", {}).get("image_analyzer")
        if not image_analyzer:
            raise ValueError("图像分析器未在状态中找到")
            
        state_update = analyze_image(state, image_analyzer)
        return state_update
    except Exception as e:
        logger.error(f"图像分析节点执行出错: {e}", exc_info=True)
        return {
            **state,
            "error": f"图像分析失败: {str(e)}"
        }

def knowledge_retriever_node(state: AgentState) -> Dict[str, Any]:
    """
    知识检索节点包装函数
    
    Args:
        state: 当前状态
        
    Returns:
        Dict: 更新后的状态
    """
    logger.info("执行知识检索节点")
    try:
        # 从状态上下文中获取知识检索器
        knowledge_retriever = state.get("_tools", {}).get("knowledge_retriever")
        if not knowledge_retriever:
            raise ValueError("知识检索器未在状态中找到")
            
        state_update = retrieve_knowledge(state, knowledge_retriever)
        return state_update
    except Exception as e:
        logger.error(f"知识检索节点执行出错: {e}", exc_info=True)
        return {
            **state,
            "error": f"知识检索失败: {str(e)}"
        }

def response_generator_node(state: AgentState) -> Dict[str, Any]:
    """
    回复生成节点包装函数
    
    Args:
        state: 当前状态
        
    Returns:
        Dict: 更新后的状态
    """
    logger.info("执行回复生成节点")
    try:
        # 从状态上下文中获取模型
        model = state.get("_tools", {}).get("model")
        if not model:
            raise ValueError("语言模型未在状态中找到")
            
        state_update = generate_response(state, model)
        return state_update
    except Exception as e:
        logger.error(f"回复生成节点执行出错: {e}", exc_info=True)
        return {
            **state,
            "error": f"生成回复失败: {str(e)}"
        }

def error_handler_node(state: AgentState) -> Dict[str, Any]:
    """
    错误处理节点
    
    处理流程中的错误，生成友好的错误消息
    
    Args:
        state: 当前状态
        
    Returns:
        Dict: 更新后的状态
    """
    logger.info("执行错误处理节点")
    
    # 创建状态的副本
    new_state = copy.deepcopy(state)
    
    # 获取错误信息
    error_msg = new_state.get("error", "未知错误")
    logger.error(f"处理错误: {error_msg}")
    
    # 获取消息历史
    messages = new_state.get("messages", [])
    
    # 创建错误响应
    friendly_error_msg = f"抱歉，我在处理您的请求时遇到了问题: {error_msg}。请重新尝试或换一种方式提问。"
    
    # 添加错误消息到历史
    messages.append(AIMessage(content=friendly_error_msg))
    new_state["messages"] = messages
    
    # 清除错误状态，防止无限循环
    new_state.pop("error", None)
    
    return new_state

def agent_node(state: AgentState) -> Dict[str, Any]:
    """
    ReAct模式的Agent节点
    
    作为决策中心，处理用户输入，决定接下来的行动
    - 分析图像
    - 检索知识
    - 生成回复
    
    Args:
        state: 当前状态
        
    Returns:
        Dict: 带有下一步行动的状态更新
    """
    logger.info("执行Agent决策节点")
    
    # 创建状态的副本
    new_state = copy.deepcopy(state)
    
    # 获取状态数据
    messages = new_state.get("messages", [])
    tools = new_state.get("_tools", {})
    model = tools.get("model")
    
    if not model:
        logger.error("语言模型未在状态中找到")
        new_state["error"] = "缺少必要的语言模型"
        return new_state
    
    # 创建工具定义列表
    tool_definitions = [
        {
            "type": "function",
            "function": {
                "name": "analyze_image",
                "description": "分析用户提供的图像，识别其中的内容，特别是地标、景点等",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "retrieve_knowledge",
                "description": "根据图像分析结果和用户问题，检索相关的知识和信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询，可以是图像分析结果或用户问题"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    
    # 如果已有图像分析结果，添加到系统消息中
    if new_state.get("image_analysis_result"):
        # 查找系统消息或创建新的
        has_system_msg = False
        for i, msg in enumerate(messages):
            if isinstance(msg, SystemMessage):
                has_system_msg = True
                # 更新系统消息，添加图像分析信息
                original_content = msg.content
                if "图像分析结果:" not in original_content:
                    messages[i] = SystemMessage(content=f"{original_content}\n\n图像分析结果: {new_state['image_analysis_result']}")
                break
        
        # 如果没有系统消息，创建一个
        if not has_system_msg and messages:
            messages.insert(0, SystemMessage(content=f"图像分析结果: {new_state['image_analysis_result']}"))
    
    # 如果已有知识检索结果，添加到系统消息中
    if new_state.get("knowledge"):
        # 查找系统消息或创建新的
        has_system_msg = False
        for i, msg in enumerate(messages):
            if isinstance(msg, SystemMessage):
                has_system_msg = True
                # 更新系统消息，添加知识信息
                original_content = msg.content
                if "相关知识:" not in original_content:
                    messages[i] = SystemMessage(content=f"{original_content}\n\n相关知识: {new_state['knowledge']}")
                break
        
        # 如果没有系统消息，创建一个
        if not has_system_msg and messages:
            messages.insert(0, SystemMessage(content=f"相关知识: {new_state['knowledge']}"))
    
    try:
        # 配置模型使用工具
        model_with_tools = model.bind_tools(tool_definitions)
        
        # 调用模型进行决策
        response = model_with_tools.invoke(messages)
        
        # 将模型响应添加到消息历史
        messages.append(response)
        new_state["messages"] = messages
        
        return new_state
    except Exception as e:
        logger.error(f"Agent决策出错: {e}", exc_info=True)
        new_state["error"] = f"决策过程出错: {str(e)}"
        return new_state

def tools_node(state: AgentState) -> Dict[str, Any]:
    """
    工具执行节点
    
    执行Agent决定调用的工具
    
    Args:
        state: 当前状态
        
    Returns:
        Dict: 工具执行结果的状态更新
    """
    logger.info("执行工具节点")
    
    # 创建状态的副本
    new_state = copy.deepcopy(state)
    
    # 获取消息
    messages = new_state.get("messages", [])
    if not messages:
        logger.error("消息列表为空")
        new_state["error"] = "消息列表为空"
        return new_state
    
    # 获取最后一条AI消息
    ai_messages = [m for m in messages if isinstance(m, AIMessage)]
    if not ai_messages:
        logger.error("没有找到AI消息")
        new_state["error"] = "没有找到AI消息"
        return new_state
    
    last_ai_msg = ai_messages[-1]
    
    # 检查是否有工具调用
    if not hasattr(last_ai_msg, 'tool_calls') or not last_ai_msg.tool_calls:
        logger.info("AI消息中没有工具调用")
        return new_state
    
    # 获取工具
    tools = new_state.get("_tools", {})
    image_analyzer = tools.get("image_analyzer")
    knowledge_retriever = tools.get("knowledge_retriever")
    
    # 处理每个工具调用
    for tool_call in last_ai_msg.tool_calls:
        tool_name = tool_call.get("name", "")
        
        if tool_name == "analyze_image" and image_analyzer:
            try:
                result = analyze_image(new_state, image_analyzer)
                new_state["image_analysis_result"] = result.get("image_analysis_result", "")
            except Exception as e:
                logger.error(f"图像分析工具执行出错: {e}", exc_info=True)
                new_state["error"] = f"图像分析工具执行出错: {str(e)}"
        
        elif tool_name == "retrieve_knowledge" and knowledge_retriever:
            args = tool_call.get("args", {})
            query = args.get("query", "")
            
            # 如果没有提供查询，使用图像分析结果
            if not query and new_state.get("image_analysis_result"):
                query = new_state["image_analysis_result"]
            
            if query:
                try:
                    result = retrieve_knowledge({"messages": messages, "image_analysis_result": new_state.get("image_analysis_result", "")}, knowledge_retriever)
                    new_state["knowledge"] = result.get("knowledge", "")
                except Exception as e:
                    logger.error(f"知识检索工具执行出错: {e}", exc_info=True)
                    new_state["error"] = f"知识检索工具执行出错: {str(e)}"
    
    # 添加工具结果消息
    if new_state.get("image_analysis_result") or new_state.get("knowledge"):
        tool_result = ""
        if new_state.get("image_analysis_result"):
            tool_result += f"图像分析结果: {new_state['image_analysis_result']}\n\n"
        if new_state.get("knowledge"):
            tool_result += f"知识检索结果: {new_state['knowledge']}"
        
        # 添加工具消息到历史
        # 注意：这里不是LangChain的标准ToolMessage，我们用AIMessage来模拟工具结果
        # 更完善的实现应该使用专门的工具消息类型
        messages.append(AIMessage(content=tool_result))
        new_state["messages"] = messages
    
    return new_state 