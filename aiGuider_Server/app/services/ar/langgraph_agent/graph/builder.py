"""
图构建器

构建LangGraph流程图的模块
"""

from typing import Dict, Any, Optional, Callable
from langgraph.graph import StateGraph, END

# 添加检查点支持
from langgraph.checkpoint.base import BaseCheckpointSaver

from .nodes import analyze_image, retrieve_knowledge, generate_response
from ..tools.image_analyzer import ImageAnalyzer
from ..tools.knowledge_retriever import KnowledgeRetriever

def build_agent_graph(
    model: Any,
    image_analyzer: ImageAnalyzer,
    knowledge_retriever: KnowledgeRetriever,
    system_prompt: Optional[str] = None,
    checkpointer: Optional[BaseCheckpointSaver] = None
) -> StateGraph:
    """
    构建Agent处理流程图
    
    Args:
        model: 语言模型
        image_analyzer: 图像分析器
        knowledge_retriever: 知识检索器
        system_prompt: 系统提示
        checkpointer: 可选的检查点存储器
        
    Returns:
        StateGraph: 构建好的状态图
    """
    # 创建工作流图
    workflow = StateGraph(name="AR导游助手")
    
    # 定义节点
    workflow.add_node("分析图像", lambda state: analyze_image(state, image_analyzer))
    workflow.add_node("检索知识", lambda state: retrieve_knowledge(state, knowledge_retriever))
    workflow.add_node("生成回复", lambda state: generate_response(state, model))
    
    # 定义边
    workflow.add_edge("分析图像", "检索知识")
    workflow.add_edge("检索知识", "生成回复")
    workflow.add_edge("生成回复", END)
    
    # 设置入口
    workflow.set_entry_point("分析图像")
    
    # 编译图（添加检查点支持）
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    else:
        return workflow.compile() 