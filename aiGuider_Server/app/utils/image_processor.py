#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图像处理工具模块
提供图像预处理、压缩等功能
"""

import logging
import io
from PIL import Image
from fastapi import UploadFile, HTTPException
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# 全局配置参数
MAX_DIMENSION = 1260  # 图像最大尺寸
IMAGE_FORMAT = 'PNG'  # 处理后的图像格式

def resize_image(img: Image.Image) -> Tuple[Image.Image, bool]:
    """
    调整图像尺寸为28的倍数，且最大边长不超过1260像素
    TODO：后面需要改成由前端裁剪。
    
    参数:
        img: PIL图像对象
        
    返回:
        调整后的图像对象和是否进行了调整的标志
    """
    # 获取原始图片尺寸
    width, height = img.size
    
    # 保持原始比例进行缩放
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        # 确定哪个维度超出了限制
        if width >= height:
            # 如果宽度是较大的维度
            new_width = MAX_DIMENSION
            new_height = int(height * (MAX_DIMENSION / width))
        else:
            # 如果高度是较大的维度
            new_height = MAX_DIMENSION
            new_width = int(width * (MAX_DIMENSION / height))
    else:
        # 如果两个维度都没有超过最大值，保持原始尺寸
        new_width = width
        new_height = height
    
    # 调整为28的倍数
    new_width = new_width - (new_width % 28) if new_width % 28 != 0 else new_width
    new_height = new_height - (new_height % 28) if new_height % 28 != 0 else new_height
    
    # 检查调整后的尺寸是否小于28
    if new_width < 28 or new_height < 28:
        logger.warning(f"计算的调整尺寸({new_width}x{new_height})小于最小要求(28x28)，取消缩放")
        return img, False
    
    # 尺寸没有变化，无需调整
    if new_width == width and new_height == height:
        logger.info("图像正好是28的倍数，而且大小合适，无需resize调整，使用原始数据")
        return img, False
    
    # 调整图片大小
    resized_img = img.resize((new_width, new_height))
    logger.info(f"图像已调整尺寸: {width}x{height} -> {new_width}x{new_height}")
    
    return resized_img, True

async def preprocess_image(image: Optional[UploadFile] = None) -> Optional[bytes]:
    """
    图像预处理函数
    
    将上传的图像文件读取为字节数据，为后续处理做准备
    
    参数:
        image: 用户上传的图像文件
        
    返回:
        处理后的图像字节数据，如果没有图像则返回None
        
    异常:
        HTTPException: 图像处理失败时抛出
    """
    image_data = None
    if image:
        try:
            # 读取上传文件的内容为字节数据 - 这一步是必须的，FastAPI中处理上传文件必须先读取内容
            original_data = await image.read()
  
            # 图像压缩功能
            try:
                # 从字节数据创建图像对象
                img = Image.open(io.BytesIO(original_data))
                
                # 调整图像尺寸
                resized_img, was_resized = resize_image(img)
                
                if was_resized:
                    # 将调整后的图像转换为字节 - 这一步是必须的，需要将PIL图像对象转回字节
                    buffer = io.BytesIO()
                    # 使用固定的图像格式，提高效率和稳定性
                    resized_img.save(buffer, format=IMAGE_FORMAT)
                    image_data = buffer.getvalue()
                else:
                    # 使用原始图像数据
                    image_data = original_data
                    logger.info("图像无需resize调整，使用原始数据")
                
            except Exception as e:
                logger.error(f"图像压缩失败: {str(e)}")
                # 如果压缩失败，使用原始图像数据
                image_data = original_data
            
        except Exception as e:
            logger.error(f"读取上传图片失败: {str(e)}")
            raise HTTPException(status_code=400, detail=f"图片处理失败: {str(e)}")
    
    return image_data 