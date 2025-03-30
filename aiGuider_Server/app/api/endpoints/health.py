#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
健康检查API
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.responses import HealthResponse

router = APIRouter()

@router.get("/", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    系统健康检查接口
    
    检查API服务和数据库连接状态
    """
    # 检查数据库连接
    db_status = True
    try:
        # 执行简单查询以验证数据库连接
        await db.execute("SELECT 1")
    except Exception:
        db_status = False
    
    return HealthResponse(
        status="healthy",
        api_status=True,
        db_status=db_status,
        version="0.1.0"
    ) 