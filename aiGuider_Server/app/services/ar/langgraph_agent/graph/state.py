"""
状态定义

定义LangGraph流程图中使用的状态类型。
"""

from typing import List, Dict, Any, Optional, Tuple, Union
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import MessagesState

class ToolState(BaseModel):
    """工具状态子结构，包含工具调用的所有相关信息"""
    
    name: Optional[str] = Field(default=None, description="工具名称")
    input: Optional[Dict[str, Any]] = Field(default=None, description="工具输入参数")
    output: Optional[str] = Field(default=None, description="工具执行结果")
    status: Optional[str] = Field(default=None, description="工具执行状态，如'pending'/'success'/'error'等")

class AgentState(MessagesState):
    """
    Agent状态类, 包含多模态交互所需的所有状态
    
    遵循ReAct模式，存储消息历史、当前输入、工具输出和最终回答
    MessagesState基类已经内置了messages字段和add_messages Reducer
    """
    # 当前输入 - 使用LangChain的HumanMessage支持多模态输入
    current_input: Optional[HumanMessage] = Field(default=None, description="当前处理的多模态输入")
    
    # 工具使用 - 使用ToolState子结构封装工具相关信息
    tool: Optional[ToolState] = Field(default=None, description="工具调用状态")
    
    # 安全检查
    safety_issues: List[str] = Field(default_factory=list, description="安全问题列表")
    
    # 最终输出
    final_answer: Optional[str] = Field(default=None, description="生成的最终回答")
    
    class Config:
        arbitrary_types_allowed = True 