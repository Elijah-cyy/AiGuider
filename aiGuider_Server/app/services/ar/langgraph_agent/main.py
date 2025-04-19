"""
AR智能导游Agent主入口

这个模块是ARGuideAgent的主入口点，提供Agent初始化和查询处理功能。
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Union
import base64
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from .config.model_config import load_model_config
from .graph.builder import build_agent_graph
from .llms.qwen import get_qwen_model
from .tools.image_analyzer import ImageAnalyzer
from .tools.knowledge_retriever import KnowledgeRetriever
from .prompts.templates import load_system_prompt

# 添加检查点支持
try:
    from langgraph.checkpoint import LocalStateCheckpointManager
    CHECKPOINT_AVAILABLE = True
except ImportError:
    CHECKPOINT_AVAILABLE = False

logger = logging.getLogger(__name__)

class ARGuideAgent:
    """
    AR智能导游Agent类
    
    这个类封装了AR智能导游系统的多模态AI Agent，使用LangGraph构建流程图，
    集成Qwen2.5-VL模型处理图像和文本输入。
    """
    
    def __init__(self, model_config: Optional[Dict] = None, use_checkpoints: bool = True):
        """
        初始化AR智能导游Agent
        
        Args:
            model_config: 模型配置，如果为None则使用默认配置
            use_checkpoints: 是否使用检查点功能
        """
        # 加载模型配置
        self.config = model_config or load_model_config()
        
        # 初始化模型
        self.model = get_qwen_model(self.config)
        
        # 加载系统提示
        self.system_prompt = load_system_prompt("tour_guide")
        
        # 初始化工具
        self.image_analyzer = ImageAnalyzer(self.model)
        self.knowledge_retriever = KnowledgeRetriever()
        
        # 初始化检查点管理器
        self.checkpointer = None
        if use_checkpoints and CHECKPOINT_AVAILABLE:
            try:
                checkpoint_dir = os.environ.get("CHECKPOINT_DIR", "./checkpoints")
                self.checkpointer = LocalStateCheckpointManager(
                    cache_dir=checkpoint_dir
                )
                logger.info(f"检查点管理器初始化成功，路径: {checkpoint_dir}")
            except Exception as e:
                logger.warning(f"检查点管理器初始化失败: {e}")
        
        # 构建Agent图
        self.graph = build_agent_graph(
            model=self.model,
            image_analyzer=self.image_analyzer,
            knowledge_retriever=self.knowledge_retriever,
            system_prompt=self.system_prompt,
            checkpointer=self.checkpointer
        )
    
    async def process_query(self, 
                     text_query: str, 
                     image_data: Optional[Union[str, bytes]] = None,
                     session_id: Optional[str] = None) -> Dict:
        """
        处理多模态查询
        
        Args:
            text_query: 用户文本查询
            image_data: 可选的图像数据，可以是base64字符串或字节
            session_id: 会话ID，用于上下文保持
            
        Returns:
            包含回复文本的字典
        """
        # 准备输入
        messages = []
        
        # 添加系统消息
        messages.append(SystemMessage(content=self.system_prompt))
        
        # 创建用户消息内容
        content = []
        
        # 添加文本内容
        content.append({"type": "text", "text": text_query})
        
        # 如果有图像，添加图像内容
        if image_data:
            # 如果是字节数据，转换为base64
            if isinstance(image_data, bytes):
                image_data = base64.b64encode(image_data).decode('utf-8')
            
            # 确保image_data是base64字符串
            if not image_data.startswith('data:image'):
                image_data = f"data:image/jpeg;base64,{image_data}"
                
            content.append({"type": "image_url", "image_url": {"url": image_data}})
        
        # 添加人类消息
        messages.append(HumanMessage(content=content))
        
        # 准备状态
        state = {
            "messages": messages,
            "session_id": session_id,
            "response": ""
        }
        
        # 配置运行时参数
        config = {}
        if session_id and self.checkpointer:
            config["configurable"] = {"thread_id": session_id}
        
        # 异步执行图 - 使用流式处理获取结果
        try:
            final_result = {"response": "", "status": "success"}
            
            # 使用astream获取流式结果
            async for event in self.graph.astream(state, config):
                if "response" in event:
                    final_result["response"] = event["response"]
                    
            return final_result
        except Exception as e:
            logger.error(f"处理查询时出错: {e}", exc_info=True)
            return {"response": "很抱歉，我处理您的请求时遇到了问题。请稍后再试。", "status": "error"}


# 创建单例实例
_agent_instance = None

def get_agent_instance() -> ARGuideAgent:
    """获取ARGuideAgent单例实例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ARGuideAgent()
    return _agent_instance

async def process_multimodal_query(
    text_query: str,
    image_data: Optional[Union[str, bytes]] = None,
    session_id: Optional[str] = None
) -> Dict:
    """
    处理多模态查询的便捷函数
    
    Args:
        text_query: 用户文本查询
        image_data: 可选的图像数据，可以是base64字符串或字节
        session_id: 会话ID，用于上下文保持
        
    Returns:
        包含回复文本的字典
    """
    agent = get_agent_instance()
    return await agent.process_query(text_query, image_data, session_id) 