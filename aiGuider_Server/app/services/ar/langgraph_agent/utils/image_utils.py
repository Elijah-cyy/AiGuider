"""
图像工具函数

提供图像处理和验证的工具函数
"""

import base64
import re
from typing import Union, Optional, Tuple

def is_valid_base64(s: str) -> bool:
    """
    检查字符串是否是有效的base64编码
    
    Args:
        s: 要检查的字符串
        
    Returns:
        bool: 是否是有效的base64编码
    """
    try:
        # 去除可能的填充等号
        s = s.strip()
        # 修正填充
        if len(s) % 4:
            s += '=' * (4 - len(s) % 4)
        
        # 检查是否匹配base64模式
        pattern = r'^[A-Za-z0-9+/]+={0,2}$'
        if not re.match(pattern, s):
            return False
        
        # 尝试解码
        base64.b64decode(s)
        return True
    except Exception:
        return False

def is_valid_data_url(url: str) -> bool:
    """
    检查字符串是否是有效的数据URL
    
    Args:
        url: 要检查的URL
        
    Returns:
        bool: 是否是有效的数据URL
    """
    pattern = r'^data:image/[a-zA-Z]+;base64,[A-Za-z0-9+/]+=*$'
    return bool(re.match(pattern, url))

def extract_base64_from_data_url(data_url: str) -> Optional[str]:
    """
    从数据URL中提取base64编码的部分
    
    Args:
        data_url: 数据URL
        
    Returns:
        Optional[str]: base64编码的部分，如果无效则返回None
    """
    if not is_valid_data_url(data_url):
        return None
    
    # 提取base64部分
    _, base64_part = data_url.split(',', 1)
    return base64_part if is_valid_base64(base64_part) else None

def ensure_data_url_format(image_data: str) -> str:
    """
    确保图像数据是数据URL格式
    
    如果是base64编码，则转换为数据URL格式
    
    Args:
        image_data: 图像数据
        
    Returns:
        str: 数据URL格式的图像数据
    """
    # 已经是数据URL
    if is_valid_data_url(image_data):
        return image_data
    
    # 是base64编码
    if is_valid_base64(image_data):
        return f"data:image/jpeg;base64,{image_data}"
    
    # 无效数据
    raise ValueError("无效的图像数据格式，需要base64字符串或数据URL") 