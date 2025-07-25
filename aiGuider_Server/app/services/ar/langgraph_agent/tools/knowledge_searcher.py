"""
知识搜索工具

统一的知识搜索工具，整合知识图谱和知识库检索功能，提供统一的接口。
"""

import logging
from typing import List, Dict, Any, Optional, Union
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# 存储模拟数据的全局变量
_kg_examples = {
    "长城": [
        {
            "source": "kg", 
            "title": "长城基本信息",
            "content": "长城是中国古代的伟大防御工程，也是世界文化遗产。始建于春秋战国时期，绵延万里。",
            "confidence": 0.95
        },
        {
            "source": "kg",
            "title": "长城历史",
            "content": "长城修建历经多个朝代，现存大部分为明长城。秦始皇时期大规模修建，明朝时期达到鼎盛。",
            "confidence": 0.92
        }
    ],
    "故宫": [
        {
            "source": "kg",
            "title": "故宫基本信息",
            "content": "故宫，又称紫禁城，位于北京中轴线上，是明清两代的皇家宫殿，世界上现存规模最大、保存最完整的木质结构古建筑群。",
            "confidence": 0.96
        }
    ]
}

_vector_examples = {
    "天坛": [
        {
            "source": "vector", 
            "title": "天坛公园",
            "content": "天坛公园位于北京市区南部，是明清两代帝王祭天的场所，是中国现存规模最大、祭祀体系最完整的古代祭祀建筑群。",
            "confidence": 0.89
        }
    ],
    "颐和园": [
        {
            "source": "vector",
            "title": "颐和园简介",
            "content": "颐和园位于北京西郊，是中国古典园林的杰出代表，以昆明湖、万寿山为基址，以杭州西湖为蓝本，汲取江南园林的设计手法而建成的一座大型山水园林。",
            "confidence": 0.91
        }
    ]
}

def _search_knowledge_graph(query: str, limit: int) -> List[Dict[str, Any]]:
    """
    从知识图谱中搜索
    
    Args:
        query: 搜索查询
        limit: 结果数量限制
        
    Returns:
        List[Dict]: 知识图谱搜索结果
    """
    # 示例知识图谱结果
    results = []
    for key, entries in _kg_examples.items():
        if key in query:
            results.extend(entries)
            if len(results) >= limit:
                break
    
    return results[:limit]

def _search_vector_db(query: str, limit: int) -> List[Dict[str, Any]]:
    """
    从向量数据库中搜索
    
    Args:
        query: 搜索查询
        limit: 结果数量限制
        
    Returns:
        List[Dict]: 向量数据库搜索结果
    """
    # 示例向量检索结果
    results = []
    for key, entries in _vector_examples.items():
        if key in query:
            results.extend(entries)
            if len(results) >= limit:
                break
    
    return results[:limit]

def _merge_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    合并、去重和排序结果
    
    Args:
        results: 搜索结果列表
        
    Returns:
        List[Dict]: 处理后的结果
    """
    # 去重 (基于title)
    title_seen = set()
    unique_results = []
    
    for result in results:
        if result["title"] not in title_seen:
            title_seen.add(result["title"])
            unique_results.append(result)
    
    # 按置信度排序
    sorted_results = sorted(unique_results, key=lambda x: x.get("confidence", 0), reverse=True)
    
    return sorted_results

def _format_results(results: List[Dict[str, Any]]) -> str:
    """
    格式化搜索结果为易读字符串
    
    Args:
        results: 搜索结果列表
        
    Returns:
        str: 格式化后的结果
    """
    formatted = "找到以下相关信息：\n\n"
    
    for i, result in enumerate(results):
        formatted += f"{i+1}. {result['title']}\n"
        formatted += f"{result['content']}\n"
        formatted += f"(来源: {'知识图谱' if result['source'] == 'kg' else '知识库'})\n\n"
    
    return formatted

@tool
def knowledge_search(query: str, mode: str = "auto", limit: int = 5) -> str:
    """
    搜索相关知识
    
    根据查询内容搜索相关知识，可指定搜索模式
    
    Args:
        query: 搜索查询
        mode: 搜索模式，可选 "kg"(知识图谱), "vector"(向量检索), "auto"(自动)
        limit: 返回结果数量限制
        
    Returns:
        str: 合并后的检索结果
    """
    logger.info(f"搜索知识: {query}, 模式: {mode}, 限制: {limit}")
    
    results = []
    
    try:
        if mode in ["kg", "auto"]:
            # 从知识图谱检索
            kg_results = _search_knowledge_graph(query, limit)
            results.extend(kg_results)
            
        if mode in ["vector", "auto"]:
            # 从向量数据库检索
            vector_results = _search_vector_db(query, limit)
            results.extend(vector_results)
            
        # 合并、去重和排序结果
        unique_results = _merge_results(results)
        
        # 格式化输出
        if unique_results:
            formatted_results = _format_results(unique_results[:limit])
            return formatted_results
        else:
            # 返回一个随便的字符串，保证流程拉通
            return f"【模拟知识检索】你查询了：{query}，目前为测试环境，后续将接入真实知识库。"
            
    except Exception as e:
        logger.error(f"知识搜索出错: {e}", exc_info=True)
        # 这里也返回一个随便的字符串
        return f"【模拟知识检索-异常】你查询了：{query}，目前为测试环境，后续将接入真实知识库。" 