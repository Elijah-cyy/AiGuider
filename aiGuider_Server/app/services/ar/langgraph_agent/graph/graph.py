"""
图构建器

构建LangGraph流程图的模块，仅负责图结构和流程的构建。
"""

from typing import Any, Optional, Dict
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage

from .state import AgentState # Import from new state module
from .nodes import (
    agent_node,
    tools_node,
    error_handler_node
)

logger = logging.getLogger(__name__)

# ReAct模式路由函数
def should_continue(state: AgentState) -> str:
    """
    检查是否需要继续工具调用循环
    
    Args:
        state: 当前状态
        
    Returns:
        str: 下一个节点的名称 ("continue", "end" 或 "error")
    """
    # 检查是否有错误
    if "error" in state and state["error"]:
        return "error"
    
    # 获取消息列表
    messages = state.get("messages", [])
    
    # 如果没有消息，无法继续
    if not messages:
        return "end"
    
    # 获取最后一条消息
    last_message = messages[-1]
    
    # 检查是否是AI消息且包含工具调用
    if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "continue"
    else:
        return "end"

def init_tools_node(state: AgentState, model: Any, image_analyzer: Any, knowledge_retriever: Any) -> Dict[str, Any]:
    """
    初始化工具节点
    
    将模型和工具添加到状态中
    
    Args:
        state: 当前状态
        model: 语言模型
        image_analyzer: 图像分析器
        knowledge_retriever: 知识检索器
        
    Returns:
        Dict: 更新后的状态
    """
    logger.info("初始化工具")
    
    # 创建状态的副本
    new_state = state.copy()
    
    # 添加工具到状态
    tools = new_state.get("_tools", {})
    tools["model"] = model
    tools["image_analyzer"] = image_analyzer
    tools["knowledge_retriever"] = knowledge_retriever
    new_state["_tools"] = tools
    
    return new_state

def build_agent_graph(
    model: Any,
    image_analyzer: Any,
    knowledge_retriever: Any,
    system_prompt: Optional[str],
    checkpointer: Optional[BaseCheckpointSaver]
) -> StateGraph:
    """
    构建Agent处理流程图
    
    使用ReAct模式构建LangGraph循环流程，实现Agent的思考-行动循环
    
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
    
    # 创建工具初始化函数，绑定所需参数
    def init_tools(state: AgentState) -> Dict[str, Any]:
        return init_tools_node(state, model, image_analyzer, knowledge_retriever)
    
    # 添加节点
    workflow.add_node("init", init_tools)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("error_handler", error_handler_node)
    
    # 设置入口点为初始化节点
    workflow.set_entry_point("init")
    
    # 初始化完成后进入agent节点
    workflow.add_edge("init", "agent")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools", 
            "end": END,
            "error": "error_handler"
        }
    )
    
    # 工具节点执行后回到agent节点，形成循环
    workflow.add_edge("tools", "agent")
    
    # 错误处理后结束
    workflow.add_edge("error_handler", END)
    
    # 编译图
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    else:
        return workflow.compile() 