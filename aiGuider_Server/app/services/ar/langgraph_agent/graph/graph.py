"""
图构建器

构建LangGraph流程图的模块，实现ReAct模式的多模态Agent。
"""

from typing import Dict, Any, Optional, List
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from .state import AgentState
from .nodes import (
    thinker_node,
    router_node,
    action_executor_node,
    error_handler_node
)

logger = logging.getLogger(__name__)

def create_agent(
    multimodal_model: Any, 
    knowledge_searcher: Any,
    checkpointer: Optional[BaseCheckpointSaver] = None
) -> StateGraph:
    """
    创建一个完整配置的多模态Agent
    
    使用ReAct模式构建LangGraph循环流程
    
    Args:
        multimodal_model: 多模态语言模型，能够直接分析图像内容
        knowledge_searcher: 知识搜索工具，整合知识图谱和向量检索
        checkpointer: 检查点存储器，用于状态持久化
        
    Returns:
        StateGraph: 构建好的Agent图
    """
    # 创建工作流图
    workflow = StateGraph(AgentState)
    
    # 构建工具字典
    tools = {
        "knowledge_search": knowledge_searcher
    }
    
    # 添加所有节点
    workflow.add_node("thinker", lambda state: thinker_node(state, multimodal_model))  # 核心思考节点
    workflow.add_node("action_executor", lambda state: action_executor_node(state, tools))  # 工具执行节点
    workflow.add_node("error_handler", error_handler_node)  # 错误处理节点
    
    # 设置入口点为思考节点
    workflow.set_entry_point("thinker")
    
    # 思考节点 -> 条件路由
    workflow.add_conditional_edges(
        "thinker",
        router_node,
        {
            "action_executor": "action_executor",  # 如果需要执行工具
            "end": END,  # 如果可以直接生成回答或忽略
            "error_handler": "error_handler"  # 如果发生错误
        }
    )
    
    # 工具执行节点 -> 思考节点（形成循环）
    workflow.add_edge("action_executor", "thinker")
    
    # 错误处理节点 -> 结束
    workflow.add_edge("error_handler", END)
    
    # 编译图
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    else:
        return workflow.compile() 