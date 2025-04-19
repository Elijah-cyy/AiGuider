"""
图节点定义

定义LangGraph流程图中的节点函数
"""

from typing import Dict, Any, List, Optional
import logging
import copy

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from ..tools.image_analyzer import ImageAnalyzer
from ..tools.knowledge_retriever import KnowledgeRetriever

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