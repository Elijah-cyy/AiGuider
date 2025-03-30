#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AR智能导游眼镜系统 - 后端主入口
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.api import api_router
from app.core.config import settings
from app.core.errors import CustomException

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AR智能导游眼镜系统API",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 全局异常处理
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    """
    自定义异常处理器
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.error_code,
            "message": exc.message,
            "debug_id": exc.debug_id,
        },
    )

@app.get("/")
async def root():
    """
    根路径欢迎信息
    """
    return {"message": "欢迎使用AR智能导游眼镜系统API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 