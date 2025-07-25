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

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from .config.model_config import load_model_config, ConfigError
from .graph.graph import create_agent
from .llms.qwen import get_qwen_model
from .graph.state import AgentState
from .utils.image_utils import ensure_base64_format
from .utils.image_token_utils import estimate_image_tokens

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
            
            # 初始化检查点管理器
            self.checkpointer = MemorySaver()
            
            # 构建Agent图
            logger.info("创建多模态Agent图...")
            self.graph = create_agent(
                multimodal_model=self.model,
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
        初始化要使用的多模态模型
        
        Args:
            model_name: 模型标识符
            
        Returns:
            初始化的模型实例
        """
        logger.info(f"初始化多模态模型: {model_name}")
        
        # 当前只支持通义千问模型
        if "qwen" in model_name.lower():
            return get_qwen_model(self.config)
        else:
            raise ValueError(f"不支持的模型类型: {model_name}")
    
    async def process_query(self, 
                     text_query: Optional[str] = "", 
                     image_data: Optional[Union[str, bytes]] = None,
                     session_id: Optional[str] = None) -> Dict:
        """
        处理多模态查询，执行Agent响应生成
        
        Args:
            text_query: 用户文本查询内容
            image_data: 可选的图像数据，可以是base64字符串或原始字节
            session_id: 会话ID，用于状态追踪
            
        Returns:
            Dict: 包含Agent响应的字典
        """
        try:
            # 准备多模态输入
            
            # 构建用户消息（支持多模态）
            # 判断输入类型：纯图像、图像+文字或纯文字（仅调试）
            
            # 如果有图像数据，确保图像转为base64格式
            if image_data:
                # 转换图像数据为base64格式
                try:
                    image_b64 = ensure_base64_format(image_data)
                    
                    # 估算图像token数量
                    try:
                        token_count, h_bar, w_bar = estimate_image_tokens(image_b64)
                        logger.info(f"图像token估算: {token_count} tokens (调整后尺寸: {w_bar}x{h_bar}像素 宽x高)")
                    except Exception as e:
                        logger.warning(f"图像token估算失败: {str(e)}")
                except ValueError as e:
                    logger.error(f"图像处理失败: {str(e)}")
                    raise
                
                # 构建多模态内容
                if text_query:
                    # 图像+文字情况
                    multimodal_content = [
                        {"text": text_query},
                        {"image": f"data:image/jpeg;base64,{image_b64}"}
                    ]
                else:
                    # 纯图像情况，提供一个默认的提示以便模型分析图像
                    multimodal_content = [
                        {"text": "现在我们看到的是这个画面"},
                        {"image": f"data:image/jpeg;base64,{image_b64}"}
                    ]
                
                user_message = HumanMessage(content=multimodal_content)
            else:
                # 纯文本输入 (仅用于调试)
                if not text_query:
                    # 既没有图像也没有文本，这是一个错误的输入
                    raise ValueError("必须提供图像或文本输入")
                
                logger.info("纯文本输入 (仅用于调试)")
                user_message = HumanMessage(content=text_query)
            
            # 准备状态，使用字典初始化，而非构造函数
            state = {
                "messages": [user_message],
                "current_input": user_message,
                "tool": None,
                "safety_issues": [],
                "final_answer": None
            }
            
            # 配置运行时参数，thread_id是会话ID
            config = {}
            if session_id and self.checkpointer:
                config["configurable"] = {"thread_id": session_id}
            
            # 调用Agent图执行推理
            logger.info("调用LangGraph执行推理")
            result = await asyncio.to_thread(self.graph.invoke, state, config)
            
            # 解析结果，获取最终回答
            final_answer = result.get("final_answer", "")
            
            # 处理可能的复杂响应格式（多模态模型返回的列表格式）
            if isinstance(final_answer, list):
                extracted_texts = []
                for item in final_answer:
                    if isinstance(item, dict) and 'text' in item:
                        extracted_texts.append(item['text'])
                final_answer = "\n".join(extracted_texts)
                logger.info(f"从最终答案中提取纯文本内容: {final_answer}")
            
            # 返回响应
            return {
                "response": final_answer,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_message = f"处理查询时发生错误: {str(e)}"
            logger.error(error_message, exc_info=True)
            return {
                "response": f"很抱歉，处理您的请求时发生了错误: {str(e)}",
                "success": False,
                "timestamp": datetime.now().isoformat()
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
    text_query: Optional[str] = "",
    image_data: Optional[Union[str, bytes]] = None,
    session_id: Optional[str] = None
) -> Dict:
    """
    处理多模态查询的便捷函数，也是调用AR agent的函数入口
    
    Args:
        text_query: 用户文本查询，可以为空字符串或None
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