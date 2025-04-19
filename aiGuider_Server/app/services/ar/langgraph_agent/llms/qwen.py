"""
通义千问2.5 VL模型接口

封装通义千问2.5 VL模型的调用接口
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage, 
    AIMessage, 
    HumanMessage, 
    SystemMessage
)
from langchain_core.outputs import ChatGeneration, ChatResult

from ..config.model_config import ModelConfig

logger = logging.getLogger(__name__)

# 尝试导入Qwen相关包
try:
    from langchain_community.chat_models import QianfanChatEndpoint as QwenChat
    QWEN_AVAILABLE = True
except ImportError:
    logger.warning("未能导入通义千问的接口，将使用模拟模式。请安装langchain_community以使用通义千问。")
    QWEN_AVAILABLE = False

class QwenVLModel(BaseChatModel):
    """
    通义千问2.5 VL模型封装类
    
    封装通义千问2.5 VL多模态大模型的调用接口
    """
    
    def __init__(self, config: ModelConfig):
        """
        初始化通义千问2.5 VL模型
        
        Args:
            config: 模型配置
        """
        super().__init__()
        self.config = config
        
        # 检查必要配置
        if not config.api_key and not os.environ.get("QWEN_API_KEY"):
            logger.warning("未配置通义千问API密钥，将使用模拟模式")
        
        # 创建Qwen客户端
        if QWEN_AVAILABLE:
            try:
                self.client = QwenChat(
                    model=config.model_name,
                    qianfan_ak=config.api_key or os.environ.get("QWEN_API_KEY"),
                    qianfan_sk=os.environ.get("QWEN_API_SECRET"),
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    **config.model_kwargs
                )
                logger.info(f"通义千问2.5 VL模型初始化成功: {config.model_name}")
            except Exception as e:
                logger.error(f"通义千问2.5 VL模型初始化失败: {e}", exc_info=True)
                self.client = None
        else:
            self.client = None
    
    def _generate(
        self, 
        messages: List[BaseMessage], 
        stop: Optional[List[str]] = None,
        run_manager = None,
        **kwargs
    ) -> ChatResult:
        """
        生成回复
        
        Args:
            messages: 消息列表
            stop: 停止词
            run_manager: 运行管理器
            **kwargs: 其他参数
            
        Returns:
            ChatResult: 聊天结果
        """
        if not QWEN_AVAILABLE or self.client is None:
            # 使用模拟模式
            logger.warning("使用模拟模式生成回复")
            return self._mock_response(messages)
        
        try:
            # 调用通义千问模型
            response = self.client.invoke(
                messages, 
                stop=stop,
                **kwargs
            )
            return response
        except Exception as e:
            logger.error(f"通义千问模型调用失败: {e}", exc_info=True)
            # 失败时使用模拟模式
            return self._mock_response(messages)
    
    def _mock_response(self, messages: List[BaseMessage]) -> ChatResult:
        """
        生成模拟回复
        
        Args:
            messages: 消息列表
            
        Returns:
            ChatResult: 模拟的聊天结果
        """
        # 提取最后一条用户消息内容
        user_msg = "没有找到用户消息"
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                if isinstance(msg.content, str):
                    user_msg = msg.content
                elif isinstance(msg.content, list):
                    text_parts = []
                    has_image = False
                    for part in msg.content:
                        if isinstance(part, dict):
                            if part.get("type") == "text":
                                text_parts.append(part.get("text", ""))
                            elif part.get("type") == "image_url":
                                has_image = True
                    user_msg = " ".join(text_parts)
                    if has_image:
                        user_msg = f"[包含图像] {user_msg}"
                break
        
        # 生成模拟回复
        mock_response = (
            f"这是一个模拟回复，因为无法连接到通义千问模型。\n"
            f"您的问题是: '{user_msg}'\n"
            f"在实际部署时，这里将返回通义千问2.5 VL模型的回复。"
        )
        
        # 创建生成结果
        generation = ChatGeneration(
            message=AIMessage(content=mock_response)
        )
        
        return ChatResult(generations=[generation])
    
    @property
    def _llm_type(self) -> str:
        """返回LLM类型"""
        return "qwen-2.5-vl"

def get_qwen_model(config: ModelConfig) -> QwenVLModel:
    """
    获取通义千问2.5 VL模型实例
    
    Args:
        config: 模型配置
        
    Returns:
        QwenVLModel: 模型实例
    """
    return QwenVLModel(config) 