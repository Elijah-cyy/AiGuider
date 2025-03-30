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