"""
状态定义模块
"""
from typing import List, Optional, TypedDict
from langchain_core.messages import BaseMessage

# 定义状态类型
class AgentState(TypedDict):
    """Agent的状态定义"""
    messages: List[BaseMessage]  # 消息历史
    image_analysis_result: Optional[str]  # 图像分析结果
    knowledge: Optional[str]  # 检索到的知识
    error: Optional[str]  # 错误信息
    _tools: Optional[dict] # 用于传递工具实例 (新增) 