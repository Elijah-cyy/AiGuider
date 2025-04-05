#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API请求模型
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class ARQuery(BaseModel):
    """AR查询请求模型"""
    query_text: str
    location: Dict[str, float] = Field(..., description="包含经纬度的位置信息")
    landmarks: list = Field(default_factory=list, description="识别到的地标列表")
    user_id: Optional[str] = Field(None, description="可选的用户ID") 