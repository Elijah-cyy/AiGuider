"""
AR智能导游Agent主入口

这个模块是ARGuideAgent的主入口点，提供Agent初始化和查询处理功能。
"""

import asyncio
import logging
import os
from typing import Dict, Optional, Union
import base64
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver

from .config.model_config import load_model_config, ConfigError
from .graph.graph import create_agent
from .llms.qwen import get_qwen_model
from .tools.knowledge_searcher import KnowledgeSearcher
from .prompts.templates import load_system_prompt
from .graph.state import MultiModalInput

logger = logging.getLogger(__name__)

class ARGuideAgent:
    """
    AR智能导游Agent类
    
    这个类封装了AR智能导游系统的多模态AI Agent，使用LangGraph构建流程图，
    集成多模态模型处理图像和文本输入。
    """
    
    def __init__(self, model_name: str):
        """
        初始化AR智能导游Agent
        
        Args:
            model_name: 要使用的模型名称，对应配置文件中的模型标识
            
        Raises:
            ConfigError: 当配置加载失败时抛出
            RuntimeError: 当模型初始化失败时抛出
        """
        try:
            # 从配置文件加载模型配置，用于初始化模型
            self.config = load_model_config(model_name)
            
            # 初始化多模态模型
            self.model = self._initialize_model(model_name)
            
            # 初始化知识搜索工具
            self.knowledge_searcher = KnowledgeSearcher()
            
            # 初始化检查点管理器
            self.checkpointer = MemorySaver()
            
            # 构建Agent图
            logger.info("创建多模态Agent图...")
            self.graph = create_agent(
                multimodal_model=self.model,
                knowledge_searcher=self.knowledge_searcher,
                checkpointer=self.checkpointer
            )
            logger.info("多模态Agent图创建完成")
            
        except ConfigError as e:
            # 配置错误是严重错误，记录并重新抛出
            logger.critical(f"初始化ARGuideAgent失败: {e}")
            raise
        except Exception as e:
            # 其他初始化错误，包装为RuntimeError并抛出
            error_message = f"初始化ARGuideAgent时发生未预期错误: {str(e)}"
            logger.critical(error_message, exc_info=True)
            raise RuntimeError(error_message) from e
    
    def _initialize_model(self, model_name: str):
        """
        根据模型名称初始化对应的模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            初始化好的模型实例
            
        Raises:
            RuntimeError: 当模型初始化失败时抛出
        """
        try:
            # 根据模型名称前缀选择对应的初始化函数
            if model_name.startswith("qwen"):
                return get_qwen_model(self.config)
            # 这里可以添加更多模型类型的支持
            # elif model_name.startswith("gpt"):
            #     return get_gpt_model(self.config)
            # elif model_name.startswith("gemini"):
            #     return get_gemini_model(self.config)
            else:
                logger.warning(f"未知的模型类型: {model_name}，使用默认的Qwen模型")
                return get_qwen_model(self.config)
        except Exception as e:
            error_message = f"初始化模型 {model_name} 失败: {str(e)}"
            logger.error(error_message, exc_info=True)
            raise RuntimeError(error_message) from e
    
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
        # 准备系统消息
        system_message = SystemMessage(content=load_system_prompt())
        
        # 处理图像数据
        image_url = None
        if image_data:
            # 如果是字节数据，转换为base64
            if isinstance(image_data, bytes):
                image_data = base64.b64encode(image_data).decode('utf-8')
            
            # 确保image_data是base64字符串
            if not image_data.startswith('data:image'):
                image_data = f"data:image/jpeg;base64,{image_data}"
            
            image_url = image_data
        
        # 创建用户消息内容
        content = []
        
        # 添加文本内容
        if text_query:
            content.append({"type": "text", "text": text_query})
        
        # 如果有图像，添加图像内容
        if image_url:
            content.append({"type": "image_url", "image_url": {"url": image_url}})
        
        # 添加人类消息
        user_message = HumanMessage(content=content)
        
        # 准备状态
        state = {
            "messages": [system_message, user_message],
            "input": MultiModalInput(
                image_url=image_url,
                text=text_query,
                context="",
                timestamp=datetime.now()
            ),
            "should_respond": True
        }
        
        # 配置运行时参数
        config = {}
        if session_id and self.checkpointer:
            config["configurable"] = {"thread_id": session_id}
        
        # 异步执行图
        try:
            final_result = {"response": "", "status": "success"}
            
            # 使用astream获取流式结果
            async for event in self.graph.astream(state, config):
                if "response" in event:
                    final_result["response"] = event["response"]
                elif "error" in event:
                    final_result["status"] = "error"
                    final_result["error"] = event["error"]
                elif "safety_issues" in event and event["safety_issues"]:
                    final_result["status"] = "safety_filtered"
                    final_result["safety_issues"] = event["safety_issues"]
                    
            # 如果Agent决定不响应，返回空响应
            if "should_respond" in event and not event["should_respond"]:
                final_result["status"] = "no_response_needed"
                
            return final_result
        except Exception as e:
            # 记录详细错误信息
            error_id = f"err_{hash(e)%10000:04d}"
            logger.error(f"处理查询时出错 [ID: {error_id}]: {e}", exc_info=True)
            
            return {
                "response": "很抱歉，我处理您的请求时遇到了问题。请稍后再试。", 
                "status": "error",
                "error_id": error_id
            }


# 创建单例实例
_agent_instance = None
_agent_model_name = None

def get_agent_instance(model_name: str = "qwen2.5-vl") -> ARGuideAgent:
    """
    获取ARGuideAgent单例实例
    
    Args:
        model_name: 要使用的模型名称
        
    Returns:
        ARGuideAgent实例
        
    Raises:
        ConfigError: 配置加载失败时抛出
        RuntimeError: 其他初始化错误时抛出
    """
    global _agent_instance, _agent_model_name

    # 如果没有实例或模型名称变更，创建新实例
    if _agent_instance is None or _agent_model_name != model_name:
        logger.info(f"没有实例或模型名称变更,创建ARGuideAgent单例实例: {model_name}")
        try:
            _agent_instance = ARGuideAgent(model_name)
            _agent_model_name = model_name
        except Exception as e:
            # 单例初始化失败是严重错误，记录并重新抛出
            logger.critical(f"创建ARGuideAgent单例实例失败: {e}")
            raise
        
    return _agent_instance

async def process_multimodal_query(
    text_query: str,
    image_data: Optional[Union[str, bytes]] = None,
    session_id: Optional[str] = None
) -> Dict:
    """
    处理多模态查询的便捷函数，也是调用AR agent的函数入口
    
    Args:
        text_query: 用户文本查询
        image_data: 可选的图像数据，可以是base64字符串或字节
        session_id: 会话ID，用于上下文保持
        
    Returns:
        包含回复文本的字典
    """
    try:
        agent = get_agent_instance("qwen2.5-vl")
        return await agent.process_query(text_query, image_data, session_id)
    except Exception as e:
        # 捕获并处理所有异常，确保API始终返回响应
        error_id = f"api_{hash(e)%10000:04d}"
        logger.critical(f"处理多模态查询失败 [ID: {error_id}]: {e}", exc_info=True)
        
        return {
            "response": "系统发生严重错误，无法处理您的请求。请联系管理员检查系统日志。", 
            "status": "fatal_error",
            "error_id": error_id
        } 