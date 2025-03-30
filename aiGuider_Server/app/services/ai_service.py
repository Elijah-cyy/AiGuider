#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI服务模块 (暂用print替代实际实现)
"""

from typing import Dict, List, Any, Optional

async def process_ar_query(
    query_text: str,
    location: Dict[str, float],
    landmarks: List[Dict[str, Any]] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    处理AR查询请求
    
    参数:
        query_text: 用户查询文本
        location: 包含经纬度的位置信息
        landmarks: 识别到的地标列表
        user_id: 可选的用户ID
        
    返回:
        包含响应文本和相关信息的字典
    """
    # 暂时用print替代实际的LangGraph处理逻辑
    print(123)
    print(f"处理查询: {query_text}")
    print(f"用户位置: {location}")
    print(f"识别地标: {landmarks}")
    
    # 返回模拟响应
    return {
        "text": f"您好!我是AR导游。您询问的是'{query_text}'。我正在您所在的位置为您提供导游服务。",
        "landmarks": [],
        "suggestions": [
            "这个建筑有什么历史?",
            "附近有什么推荐景点?",
            "如何前往最近的餐厅?"
        ]
    } 