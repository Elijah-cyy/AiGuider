#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库基础配置
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 创建异步数据库引擎
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=False,
    future=True,
)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖函数
    
    使用异步上下文管理器确保会话正确关闭
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 