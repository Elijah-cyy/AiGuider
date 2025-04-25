"""
图构建器

构建LangGraph流程图的模块，基于LangGraph官方最佳实践实现AR导游助手Agent。
"""

from typing import Dict, Any, Optional, List, TypedDict
import logging
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, SystemMessage, BaseMessage

# 添加检查点支持
from langgraph.checkpoint.base import BaseCheckpointSaver

from .nodes import analyze_image, retrieve_knowledge, generate_response
from ..tools.image_analyzer import ImageAnalyzer
from ..tools.knowledge_retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)

# 定义状态类型
class AgentState(TypedDict):
    """Agent的状态定义"""
    messages: List[BaseMessage]  # 消息历史
    image_analysis_result: Optional[str]  # 图像分析结果
    knowledge: Optional[str]  # 检索到的知识
    current_step: str  # 当前处理步骤
    error: Optional[str]  # 错误信息

# 定义工具占位函数
def print_tool(input_text: str) -> str:
    """工具调用的占位实现，仅打印输入并返回"""
    print(f"[工具调用] 输入: {input_text}")
    return f"[工具调用结果] 处理了: {input_text}"

def build_agent_graph(
    model: Any,
    image_analyzer: ImageAnalyzer,
    knowledge_retriever: KnowledgeRetriever,
    system_prompt: Optional[str],
    checkpointer: Optional[BaseCheckpointSaver]
) -> StateGraph:
    """
    构建Agent处理流程图
    
    使用LangGraph构建一个带有条件路由和工具使用的AR导游助手Agent
    
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
    
    # 定义图像分析节点
    def image_analyzer_node(state: AgentState) -> Dict[str, Any]:
        """图像分析节点"""
        logger.info("执行图像分析节点")
        try:
            state_update = analyze_image(state, image_analyzer)
            state_update["current_step"] = "image_analysis_complete"
            return state_update
        except Exception as e:
            logger.error(f"图像分析失败: {str(e)}")
            return {
                "error": f"图像分析错误: {str(e)}",
                "current_step": "error"
            }
    
    # 定义知识检索节点
    def knowledge_retriever_node(state: AgentState) -> Dict[str, Any]:
        """知识检索节点"""
        logger.info("执行知识检索节点")
        try:
            state_update = retrieve_knowledge(state, knowledge_retriever)
            state_update["current_step"] = "knowledge_retrieval_complete"
            return state_update
        except Exception as e:
            logger.error(f"知识检索失败: {str(e)}")
            return {
                "error": f"知识检索错误: {str(e)}",
                "current_step": "error"
            }
    
    # 定义回复生成节点
    def response_generator_node(state: AgentState) -> Dict[str, Any]:
        """回复生成节点"""
        logger.info("执行回复生成节点")
        try:
            state_update = generate_response(state, model)
            state_update["current_step"] = "response_complete"
            return state_update
        except Exception as e:
            logger.error(f"生成回复失败: {str(e)}")
            return {
                "error": f"生成回复错误: {str(e)}",
                "current_step": "error"
            }
    
    # 定义错误处理节点
    def error_handler_node(state: AgentState) -> Dict[str, Any]:
        """错误处理节点"""
        logger.error(f"执行错误处理: {state.get('error', '未知错误')}")
        
        error_message = state.get("error", "处理请求时发生未知错误")
        
        # 创建一个错误响应
        messages = state.get("messages", [])
        messages.append(AIMessage(content=f"抱歉，我在处理您的请求时遇到了问题: {error_message}"))
        
        return {
            "messages": messages,
            "current_step": "complete"
        }
    
    # 定义条件路由
    def router(state: AgentState) -> str:
        """根据状态决定下一步操作"""
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
    
    # 设置入口点
    # 根据是否有图像分析结果，可以跳过图像分析步骤
    def entry_point_router(state: AgentState) -> str:
        """入口路由决定初始节点"""
        # 如果有错误状态，进入错误处理
        if "error" in state and state["error"]:
            return "error_handler"
        
        # 如果没有系统提示词，设置错误状态
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
    
    workflow.set_conditional_entry_point(entry_point_router)
    
    # 初始化状态
    def get_initial_state() -> AgentState:
        """获取初始状态"""
        # 检查system_prompt是否为空
        if not system_prompt:
            logger.error("系统提示词为空")
            # 返回带有错误状态的初始状态
            return {
                "messages": [],
                "image_analysis_result": "",
                "knowledge": "",
                "current_step": "error",
                "error": "系统提示词缺失，无法初始化agent"
            }
        
        # 正常初始化状态
        return {
            "messages": [SystemMessage(content=system_prompt)],
            "image_analysis_result": "",
            "knowledge": "",
            "current_step": "start",
            "error": None
        }
    
    # 编译图（添加检查点支持）
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    else:
        return workflow.compile() 