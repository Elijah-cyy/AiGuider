#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
辅助函数模块
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, TypeVar

T = TypeVar('T')

logger = logging.getLogger(__name__)

def retry_with_backoff(
    retries: int = 3,
    backoff_in_seconds: int = 1,
    max_backoff_in_seconds: int = 30,
    backoff_factor: int = 2,
    exceptions_to_retry: tuple = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    带指数退避的重试装饰器
    
    参数:
        retries: 最大重试次数
        backoff_in_seconds: 初始等待时间（秒）
        max_backoff_in_seconds: 最大等待时间（秒）
        backoff_factor: 退避因子
        exceptions_to_retry: 需要重试的异常类型
        
    返回:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            retry_backoff = backoff_in_seconds
            last_exception = None
            
            for retry_number in range(retries + 1):
                try:
                    if retry_number > 0:
                        logger.info(
                            f"重试 {func.__name__} 第 {retry_number}/{retries} 次 "
                            f"等待 {retry_backoff} 秒..."
                        )
                        time.sleep(retry_backoff)
                        # 计算下一次的退避时间
                        retry_backoff = min(
                            retry_backoff * backoff_factor,
                            max_backoff_in_seconds
                        )
                    
                    # 调用原始函数
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                
                except exceptions_to_retry as e:
                    last_exception = e
                    logger.warning(
                        f"函数 {func.__name__} 执行失败: {str(e)}. "
                        f"重试 {retry_number + 1}/{retries}"
                    )
            
            # 所有重试都失败了，抛出最后捕获的异常
            if last_exception:
                logger.error(
                    f"函数 {func.__name__} 在 {retries} 次重试后仍然失败: {str(last_exception)}"
                )
                raise last_exception
            
            # 这里不应该到达，但为了类型检查添加
            raise RuntimeError("重试逻辑错误")
            
        return wrapper
    
    return decorator

def format_location(location: Dict[str, float]) -> str:
    """
    格式化位置信息为可读字符串
    
    参数:
        location: 包含纬度和经度的字典
        
    返回:
        格式化的位置字符串
    """
    lat = location.get("latitude", 0)
    lng = location.get("longitude", 0)
    return f"{lat:.6f}, {lng:.6f}" 