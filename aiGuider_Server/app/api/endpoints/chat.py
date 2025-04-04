#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
聊天API端点
"""

import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Cookie, Header
from typing import Dict, List, Optional
from pydantic import BaseModel
import json

from app.services.session_service import session_manager

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatResponse(BaseModel):
    """聊天响应模型"""
    reply: str
    session_id: str

class Message(BaseModel):
    """消息模型"""
    id: str
    content: str
    timestamp: str

class MessagesResponse(BaseModel):
    """消息列表响应模型"""
    messages: List[Message]
    has_more: bool = False

@router.post("/chat", response_model=ChatResponse)
async def chat(
    message: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    conversation_history: str = Form("[]"),
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None)
):
    """
    聊天接口
    
    接收用户消息和可选的图片，返回AI回复
    如果没有提供会话ID，将创建新会话
    """
    # 优先使用Header中的会话ID，其次使用Cookie
    effective_session_id = x_session_id or session_id
    
    # 如果没有会话ID，创建新会话
    if not effective_session_id:
        effective_session_id = session_manager.create_session()
    
    # 解析对话历史
    history = []
    if conversation_history:
        try:
            history = json.loads(conversation_history)
        except json.JSONDecodeError:
            pass
    
    # 验证消息内容
    if not message and not image:
        raise HTTPException(status_code=400, detail="请提供文本消息或图片")
    
    # 处理消息
    query_text = message or "查询图片信息"
    response = session_manager.process_query(
        effective_session_id, 
        query_text,
        image
    )
    
    return ChatResponse(
        reply=response["reply"],
        session_id=effective_session_id
    )

@router.get("/messages", response_model=MessagesResponse)
async def get_messages(
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None)
):
    """
    获取后端主动推送的消息
    
    返回指定会话中的待发送消息
    如果没有提供会话ID，将返回空列表
    """
    # 优先使用Header中的会话ID(X-Session-ID)，其次使用Cookie中的session_id
    # 这种设计允许前端通过Header或Cookie两种方式传递会话ID
    effective_session_id = x_session_id or session_id
    
    # 如果没有有效的会话ID，直接返回空列表
    # 这种情况通常发生在用户首次访问或会话过期时
    if not effective_session_id:
        logger.warning("[MESSAGE] 无效会话ID请求消息")
        return MessagesResponse(messages=[])
    
    # 从session_manager获取该会话的待发送消息
    # 这些消息可能是后端主动推送的通知或异步处理结果
    pending_messages = session_manager.get_pending_messages(effective_session_id)
    logger.info(f"[MESSAGE] 获取会话 {effective_session_id} 的待发消息，数量：{len(pending_messages)}")
    
    # 将原始消息字典列表转换为Message模型列表
    # 这里进行数据格式转换，确保返回数据符合API规范
    messages = [
        Message(
            id=msg["id"],  # 消息唯一标识
            content=msg["content"],  # 消息内容
            timestamp=msg["timestamp"]  # 消息时间戳
        )
        for msg in pending_messages
    ]
    
    # 返回格式化后的消息列表
    # has_more字段暂时固定为False，未来可分页实现
    logger.debug(f"[MESSAGE] 返回消息列表：{messages}")
    return MessagesResponse(
        messages=messages,
        has_more=False
    )