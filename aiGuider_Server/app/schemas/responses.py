#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API响应模型
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="系统状态")
    api_status: bool = Field(..., description="API服务状态")
    db_status: bool = Field(..., description="数据库连接状态")
    version: str = Field(..., description="API版本")

class Landmark(BaseModel):
    """地标信息模型"""
    id: str
    name: str
    description: str
    location: Dict[str, float]
    image_url: Optional[str] = None

class ARGuideResponse(BaseModel):
    """AR导游响应模型"""
    response_text: str = Field(..., description="导游文本响应")
    landmarks: List[Landmark] = Field(default_factory=list, description="相关地标信息")
    suggestions: List[str] = Field(default_factory=list, description="推荐查询建议")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")

# 从chat.py迁移的响应模型
class ChatResponse(BaseModel):
    """聊天响应模型"""
    reply: str = Field(..., description="AI回复内容")
    session_id: str = Field(..., description="会话ID")

class Message(BaseModel):
    """消息模型"""
    id: str = Field(..., description="消息唯一标识")
    content: str = Field(..., description="消息内容")
    timestamp: str = Field(..., description="消息时间戳")

class MessagesResponse(BaseModel):
    """消息列表响应模型"""
    messages: List[Message] = Field(..., description="消息列表")
    has_more: bool = Field(False, description="是否有更多消息")

# 从session.py迁移的响应模型
class SessionResponse(BaseModel):
    """会话响应模型"""
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="操作结果信息") 