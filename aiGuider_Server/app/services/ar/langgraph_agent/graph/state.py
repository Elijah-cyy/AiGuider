"""
状态定义

定义LangGraph流程图中使用的状态类型。
"""

from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from pydantic import BaseModel, Field

class MultiModalInput(BaseModel):
    """多模态输入的定义，支持文本和图像"""
    
    text: str = Field(default="", description="用户文本输入")
    image_urls: List[str] = Field(default_factory=list, description="图像URL列表")

class AgentState(BaseModel):
    """
    Agent状态类, 包含多模态交互所需的所有状态
    
    遵循ReAct模式，存储消息历史、当前输入、工具输出和最终回答
    """
    # 消息历史
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="消息历史记录")
    
    # 当前输入 - 可能是文本或多模态内容
    current_input: Optional[MultiModalInput] = Field(default=None, description="当前处理的输入")
    
    # 工具使用
    action_name: Optional[str] = Field(default=None, description="待执行工具名称")
    action_input: Optional[Dict[str, Any]] = Field(default=None, description="工具输入参数")
    action_output: Optional[str] = Field(default=None, description="工具执行结果")
    
    # 安全检查
    safety_issues: List[str] = Field(default_factory=list, description="安全问题列表")
    
    # 最终输出
    final_answer: Optional[str] = Field(default=None, description="生成的最终回答")
    
    # 交互时间记录
    last_interaction_time: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True 