#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API路由注册模块
"""

from fastapi import APIRouter

from app.api.endpoints import health, ar_guide, session, chat

# 创建API路由器
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(health.router, prefix="/health", tags=["健康检查"])
api_router.include_router(ar_guide.router, prefix="/guide", tags=["AR导游"])
api_router.include_router(session.router, prefix="/session", tags=["会话管理"])
api_router.include_router(chat.router, tags=["聊天"]) 