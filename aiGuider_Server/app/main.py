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
from app.services import get_session_manager

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

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """
    应用启动事件处理函数
    - 初始化会话管理器
    - 初始化其他资源
    """
    logger.info("应用启动中...")
    # 初始化会话管理器 - 调用get_session_manager()会触发SessionManager的创建
    get_session_manager()
    logger.info("应用启动完成")

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭事件处理函数
    - 清理会话管理器资源
    - 清理其他资源
    """
    logger.info("应用关闭中...")
    # 清理会话管理器资源
    session_manager = get_session_manager()
    await session_manager.cleanup_all()
    logger.info("应用关闭完成")

# 日志中间件：全局HTTP中间件，会在每次HTTP请求到达时触发
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"---------------------------------------------------------------------------")
    logger.info(f"请求开始: {request.method} {request.url}")
    logger.debug(f"请求头: {dict(request.headers)}")

    try:
        response = await call_next(request)
        logger.info(f"请求完成: {request.method} {request.url} 状态码: {response.status_code}")
        print(f"---------------------------------------------------------------------------")
        return response
    except Exception as e:
        logger.error(f"请求异常: {request.method} {request.url} 错误: {str(e)}")
        print(f"---------------------------------------------------------------------------")
        raise

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
