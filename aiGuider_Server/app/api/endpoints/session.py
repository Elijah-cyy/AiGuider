#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
会话管理API端点
"""

from fastapi import APIRouter, HTTPException, Cookie
from typing import Dict, Optional

from app.services.session_service import get_session_manager
from app.schemas.responses import SessionResponse

router = APIRouter()

@router.post("/create", response_model=SessionResponse)
async def create_session():
    """
    创建新的会话
    
    每次创建新会话都会生成一个唯一的会话ID
    """
    session_id = get_session_manager().create_session()
    return SessionResponse(
        session_id=session_id,
        message="会话创建成功"
    )

@router.get("/status", response_model=Dict)
async def session_status(session_id: Optional[str] = Cookie(None)):
    """
    获取会话状态
    
    如果会话存在，返回会话信息；否则返回错误
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="未提供会话ID")
    
    session = get_session_manager().get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")
    
    return {
        "session_id": session_id,
        "active": True,
        "created_at": session.created_at.isoformat(),
        "last_active": session.last_active.isoformat()
    } 