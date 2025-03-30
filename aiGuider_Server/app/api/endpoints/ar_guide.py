#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AR导游API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any
from pydantic import BaseModel

from app.services.ai_service import process_ar_query
from app.schemas.responses import ARGuideResponse

router = APIRouter()

class ARQuery(BaseModel):
    """AR查询请求模型"""
    query_text: str
    location: Dict[str, float]  # 包含经纬度的位置信息
    landmarks: list = []  # 识别到的地标列表
    user_id: str = None  # 可选的用户ID

@router.post("/query", response_model=ARGuideResponse)
async def ar_guide_query(query: ARQuery = Body(...)):
    """
    AR导游查询接口
    
    接收用户查询和上下文信息，返回智能导游响应
    """
    try:
        # 调用AI服务处理查询 (当前用print替代实际实现)
        result = await process_ar_query(
            query_text=query.query_text,
            location=query.location,
            landmarks=query.landmarks,
            user_id=query.user_id
        )
        
        return ARGuideResponse(
            response_text=result.get("text", ""),
            landmarks=result.get("landmarks", []),
            suggestions=result.get("suggestions", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 