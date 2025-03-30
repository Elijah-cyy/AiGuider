#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
错误处理模块
"""

import uuid
from typing import Any, Dict, Optional

class ErrorCode:
    """错误码定义"""
    SYSTEM_ERROR = 10000  # 系统错误
    INVALID_REQUEST = 10001  # 无效请求
    UNAUTHORIZED = 10002  # 未授权
    FORBIDDEN = 10003  # 禁止访问
    NOT_FOUND = 10004  # 资源不存在
    SERVICE_UNAVAILABLE = 10005  # 服务不可用

class CustomException(Exception):
    """
    自定义异常基类
    
    支持三级错误处理:
    1. 客户端错误 (400-499)
    2. 服务端错误 (500-599)
    3. LLM错误 (特定错误码)
    """
    
    def __init__(
        self,
        status_code: int = 500,
        error_code: int = ErrorCode.SYSTEM_ERROR,
        message: str = "服务器内部错误",
        debug_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.debug_id = debug_id or str(uuid.uuid4())
        self.details = details
        super().__init__(self.message)

class ClientError(CustomException):
    """客户端错误"""
    
    def __init__(
        self,
        status_code: int = 400,
        error_code: int = ErrorCode.INVALID_REQUEST,
        message: str = "客户端请求错误",
        debug_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code, error_code, message, debug_id, details)

class ServerError(CustomException):
    """服务端错误"""
    
    def __init__(
        self,
        status_code: int = 500,
        error_code: int = ErrorCode.SYSTEM_ERROR,
        message: str = "服务器内部错误",
        debug_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code, error_code, message, debug_id, details)

class LLMError(CustomException):
    """LLM处理错误"""
    
    def __init__(
        self,
        status_code: int = 503,
        error_code: int = ErrorCode.SERVICE_UNAVAILABLE,
        message: str = "AI服务暂时不可用",
        debug_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code, error_code, message, debug_id, details) 