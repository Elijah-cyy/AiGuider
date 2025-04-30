"""
状态定义

定义LangGraph流程图中使用的状态类型。
"""

from typing import List, Dict, Any, Optional, Tuple, Union, Annotated
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class ToolState(BaseModel):
    """工具状态子结构，包含工具调用的所有相关信息"""
    
    name: Optional[str] = Field(default=None, description="工具名称")
    input: Optional[Dict[str, Any]] = Field(default=None, description="工具输入参数")
    output: Optional[str] = Field(default=None, description="工具执行结果")
    status: Optional[str] = Field(default=None, description="工具执行状态，如'pending'/'success'/'error'等")

class AgentState(TypedDict):
    """
    Agent状态类, 包含多模态交互所需的所有状态
    
    遵循ReAct模式，存储消息历史、当前输入、工具输出和最终回答
    使用add_messages作为messages字段的Reducer，支持消息添加和更新
    """
    # 消息历史 - 使用add_messages作为Reducer确保消息正确添加和更新
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 当前大模型的输入 - 使用LangChain的HumanMessage支持多模态输入
    current_input: Optional[HumanMessage]
    
    # 工具使用 - 使用ToolState子结构封装工具相关信息
    tool: Optional[ToolState]
    
    # 安全检查
    safety_issues: List[str]
    
    # 最终输出
    final_answer: Optional[str] 