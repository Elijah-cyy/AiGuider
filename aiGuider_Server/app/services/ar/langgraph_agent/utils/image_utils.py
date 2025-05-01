"""
图像工具函数

提供图像处理和验证的工具函数
"""

import base64
import re
from typing import Union, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def ensure_base64_format(image_data: Union[str, bytes]) -> str:
    """
    确保传入给多模态大模型的图像数据是base64格式
    
    Args:
        image_data: 图像数据，可以是bytes、data URI字符串或base64编码的字符串
        
    Returns:
        str: base64编码的字符串（不包含data URI前缀）
        
    Raises:
        ValueError: 当输入的图像数据格式不支持或无效时抛出
    """
    # 如果是字节数据，转换为base64编码
    if isinstance(image_data, bytes):
        image_b64 = base64.b64encode(image_data).decode("utf-8")
        return image_b64
    
    # 如果是data URI格式，提取base64部分
    elif isinstance(image_data, str) and image_data.startswith("data:image"):
        try:
            # 提取base64部分（去除"data:image/jpeg;base64,"前缀）
            image_b64 = image_data.split(",", 1)[1]
            logger.info("输入已经是data URI格式")
            return image_b64
        except IndexError:
            # 格式错误
            raise ValueError("无效的Data URI格式图像")
            
    # 如果是字符串，假设已经是base64编码
    elif isinstance(image_data, str):
        # 假设已经是base64字符串
        image_b64 = image_data
        logger.info("输入被假定为base64字符串格式")
        return image_b64
        
    # 不支持的类型
    else:
        raise ValueError(f"不支持的图像数据类型: {type(image_data)}")