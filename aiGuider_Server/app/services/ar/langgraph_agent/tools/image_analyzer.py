"""
图像分析工具

使用大语言模型分析图像内容
"""

import logging
import base64
from typing import Any, Optional, Dict, List, Union
import re

from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

class ImageAnalyzer:
    """
    图像分析工具
    
    使用多模态大语言模型分析图像内容
    """
    
    def __init__(self, model: Any):
        """
        初始化图像分析器
        
        Args:
            model: 多模态大语言模型
        """
        self.model = model
    
    def analyze(self, image_data: str) -> str:
        """
        分析图像并返回描述
        
        Args:
            image_data: 图像数据，可以是base64字符串或数据URL
            
        Returns:
            str: 图像分析结果
        """
        logger.info("开始分析图像")
        
        try:
            # 确保image_data是数据URL格式
            if not image_data.startswith('data:image'):
                # 尝试检测是否已经是base64编码
                if self._is_base64(image_data):
                    image_data = f"data:image/jpeg;base64,{image_data}"
                else:
                    raise ValueError("图像数据格式不正确，需要base64字符串或数据URL")
            
            # 创建分析提示
            system_prompt = """
            你是一个专业的图像分析助手。请详细分析以下图像，并提供以下信息：
            1. 图像中主要内容的详细描述
            2. 识别出的景点、建筑或物品名称
            3. 图像中的文字内容（如果有）
            4. 图像的风格和氛围
            
            请以结构化的方式回答，但不要使用标题和小标题，直接描述即可。
            描述要详尽且准确，尽可能多地提供有用信息。
            """
            
            # 创建消息内容
            content = [
                {"type": "text", "text": "请分析这张图片，提供详细描述。"},
                {"type": "image_url", "image_url": {"url": image_data}}
            ]
            
            # 创建消息
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=content)
            ]
            
            # 调用模型
            response = self.model.invoke(messages)
            
            # 处理响应
            analysis = response.content
            logger.info(f"图像分析完成: {analysis[:100]}...")
            
            return analysis
        
        except Exception as e:
            logger.error(f"图像分析失败: {e}", exc_info=True)
            return f"图像分析失败: {str(e)}"
    
    def _is_base64(self, s: str) -> bool:
        """
        检查字符串是否是有效的base64编码
        
        Args:
            s: 要检查的字符串
            
        Returns:
            bool: 是否是有效的base64编码
        """
        # 检查是否匹配base64模式
        pattern = r'^[A-Za-z0-9+/]+={0,2}$'
        return bool(re.match(pattern, s)) and len(s) % 4 == 0 