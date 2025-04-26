"""
图构建器

构建LangGraph流程图的模块，仅负责图结构和流程的构建。
"""

from typing import Any, Optional, Dict, List, TypedDict
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage

from .nodes import (
    image_analyzer_node, 
    knowledge_retriever_node, 
    response_generator_node, 
    error_handler_node
)

logger = logging.getLogger(__name__)

# 定义状态类型
class AgentState(TypedDict):
    """Agent的状态定义"""
    messages: List[BaseMessage]  # 消息历史
    image_analysis_result: Optional[str]  # 图像分析结果
    knowledge: Optional[str]  # 检索到的知识
    current_step: str  # 当前处理步骤
    error: Optional[str]  # 错误信息

# 路由函数
def router(state: AgentState) -> str:
    """
    根据状态决定下一步操作
    
    Args:
        state: 当前状态
        
    Returns:
        str: 下一个节点的名称
    """
    current_step = state.get("current_step", "")
    has_error = "error" in state and state["error"]
    
    if has_error:
        return "error_handler"
    
    if current_step == "image_analysis_complete":
        return "knowledge_retriever"
    elif current_step == "knowledge_retrieval_complete":
        return "response_generator"
    elif current_step == "response_complete":
        return END
    else:
        # 如果状态不明确，默认执行图像分析
        return "image_analyzer"

def entry_point_router(state: AgentState) -> str:
    """
    入口路由决定初始节点
    
    Args:
        state: 当前状态
        
    Returns:
        str: 初始节点的名称
    """
    # 如果有错误状态，进入错误处理
    if "error" in state and state["error"]:
        return "error_handler"
    
    # 如果没有系统提示词，设置错误状态
    system_prompt = None
    if state.get("messages") and len(state.get("messages", [])) > 0:
        first_message = state["messages"][0]
        if isinstance(first_message, SystemMessage):
            system_prompt = first_message.content
            
    if not system_prompt and not (state.get("messages") and len(state.get("messages", [])) > 0):
        logger.error("系统提示词为空")
        # 修改state添加错误信息（注意：这里不会修改原始状态，需要在调用时处理）
        return "error_handler"
        
    # 如果已经有图像分析结果，则直接进入知识检索
    if state.get("image_analysis_result"):
        return "knowledge_retriever"
    # 如果已经有知识检索结果，则直接进入回复生成
    elif state.get("knowledge") and state.get("image_analysis_result"):
        return "response_generator"
    # 默认从图像分析开始
    else:
        return "image_analyzer"

def build_agent_graph(
    model: Any,
    image_analyzer: Any,
    knowledge_retriever: Any,
    system_prompt: Optional[str],
    checkpointer: Optional[BaseCheckpointSaver]
) -> StateGraph:
    """
    构建Agent处理流程图
    
    使用LangGraph构建带有条件路由的AR导游助手Agent
    
    Args:
        model: 语言模型
        image_analyzer: 图像分析器
        knowledge_retriever: 知识检索器
        system_prompt: 系统提示
        checkpointer: 检查点存储器
        
    Returns:
        StateGraph: 构建好的状态图
    """
    # 创建工作流图
    workflow = StateGraph(AgentState)
    
    # 设置工具到状态中
    def add_tools_to_state(state):
        tools = state.get("_tools", {})
        tools["model"] = model
        tools["image_analyzer"] = image_analyzer
        tools["knowledge_retriever"] = knowledge_retriever
        state["_tools"] = tools
        return state
    
    # 添加节点
    workflow.add_node("image_analyzer", image_analyzer_node)
    workflow.add_node("knowledge_retriever", knowledge_retriever_node)
    workflow.add_node("response_generator", response_generator_node)
    workflow.add_node("error_handler", error_handler_node)
    
    # 添加条件边
    workflow.add_conditional_edges("image_analyzer", router)
    workflow.add_conditional_edges("knowledge_retriever", router)
    workflow.add_conditional_edges("response_generator", router)
    workflow.add_conditional_edges("error_handler", lambda _: END)
    
    # 设置条件入口点
    workflow.set_conditional_entry_point(entry_point_router)
    
    # 设置状态转换器，添加工具到状态中
    workflow.set_state_transformer(add_tools_to_state)
    
    # 编译图
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    else:
        return workflow.compile() 