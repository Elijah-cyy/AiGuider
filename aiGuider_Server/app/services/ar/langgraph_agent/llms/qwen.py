"""
通义千问 VL 模型接口 (基于 LangChain ChatTongyi)

封装通义千问多模态大模型的调用接口
"""

import os
import logging
import time
import random
from typing import Dict, Any, Optional, List, Union, Callable, Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage,
    AIMessage,
    HumanMessage,
    SystemMessage
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool

from ..config.model_config import ModelConfig
from ..config.error_codes import ErrorCodes, ModelError

logger = logging.getLogger(__name__)

# 尝试导入 Tongyi 相关包
try:
    from langchain_community.chat_models.tongyi import ChatTongyi
    TONGYI_AVAILABLE = True
except ImportError:
    logger.warning("未能导入通义千问的接口。请安装 `langchain_community` 并确保安装了 Tongyi 相关依赖。 pip install langchain_community dashscope", exc_info=True)
    TONGYI_AVAILABLE = False

# 重试设置
MAX_RETRIES = 3  # 最大重试次数
BASE_DELAY = 1   # 基础延迟时间（秒）
MAX_DELAY = 10   # 最大延迟时间（秒）

class QwenVLModel(BaseChatModel):
    """
    通义千问模型封装类 (基于 LangChain ChatTongyi)

    封装通义千问多模态大模型的调用接口
    """
    client: Optional[ChatTongyi] = None

    def __init__(self, config: ModelConfig):
        """
        按配置初始化指定版本的通义千问模型

        Args:
            config: 模型配置

        Raises:
            ModelError: 如果依赖缺失、API Key缺失或客户端初始化失败
        """
        super().__init__() # 调用父类的初始化方法

        # 1. 检查依赖
        if not TONGYI_AVAILABLE:
            error_message = "通义千问模型所需依赖 'langchain_community' 或 'dashscope' 未安装。"
            logger.error(f"{error_message} [错误码: {ErrorCodes.MODEL_DEPENDENCY_MISSING}]")
            raise ModelError(message=error_message, error_code=ErrorCodes.MODEL_DEPENDENCY_MISSING)

        # 2. 检查API密钥 (使用 DashScope 的标准)
        api_key = config.dashscope_api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            error_message = "通义千问模型API密钥未配置 (config.dashscope_api_key 或 DASHSCOPE_API_KEY 环境变量)。"
            logger.error(f"{error_message} [错误码: {ErrorCodes.MODEL_API_KEY_MISSING}]")
            raise ModelError(message=error_message, error_code=ErrorCodes.MODEL_API_KEY_MISSING)

        # 3. 初始化通义模型客户端
        try:
            # 使用 ChatTongyi 初始化
            self.client = ChatTongyi(
                model=config.model_name,  # 设置选定版本的通义模型
                dashscope_api_key=api_key,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                streaming=config.streaming,
                model_kwargs=config.model_kwargs or {},
            )
            # logger.info(f"通义千问模型 (ChatTongyi) 客户端初始化成功: {config}")
        except Exception as e:
            error_message = f"通义千问模型 (ChatTongyi) 客户端初始化失败: {e}"
            logger.error(f"{error_message} [错误码: {ErrorCodes.MODEL_INIT_FAILED}]", exc_info=True)
            # 将原始异常包装在ModelError中抛出
            raise ModelError(
                message=error_message,
                error_code=ErrorCodes.MODEL_INIT_FAILED
            ) from e

    def bind_tools(self, tools: Sequence[Union[BaseTool, Callable]]) -> "QwenVLModel":
        """
        将工具绑定到模型实例
        这个方法允许为大语言模型绑定LangChain工具，实现工具调用功能。

        Args:
            tools: LangChain工具列表，可以是BaseTool实例或被@tool装饰的函数

        Returns:
            QwenVLModel: 返回绑定了工具的模型实例（self）
        """
        if self.client is None:
            error_message = "模型客户端未初始化，无法绑定工具"
            logger.error(f"{error_message} [错误码: {ErrorCodes.MODEL_INIT_FAILED}]")
            raise ModelError(message=error_message, error_code=ErrorCodes.MODEL_INIT_FAILED)
        
        try:
            self.client = self.client.bind_tools(tools)
            return self
            
        except Exception as e:
            error_message = f"绑定工具失败: {e}"
            logger.error(f"{error_message} [错误码: {ErrorCodes.MODEL_TOOLS_BINDING_FAILED}]", exc_info=True)
            raise ModelError(
                message=error_message,
                error_code=ErrorCodes.MODEL_TOOLS_BINDING_FAILED
            ) from e

    def _exponential_backoff(self, retry_count: int) -> float:
        """
        计算指数退避延迟时间

        Args:
            retry_count: 当前重试次数

        Returns:
            float: 延迟时间（秒）
        """
        # 指数退避算法: 随机抖动 + 指数增长
        delay = min(MAX_DELAY, BASE_DELAY * (2 ** retry_count))
        # 添加随机抖动 (0.5 ~ 1.5 倍)
        jitter = 0.5 + random.random()
        return delay * jitter

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager = None,
        **kwargs
    ) -> ChatResult:
        """
        生成回复，包含重试机制

        Args:
            messages: 消息列表
            stop: 停止词
            run_manager: 运行管理器
            **kwargs: 其他参数

        Returns:
            ChatResult: 聊天结果

        Raises:
            ModelError: 如果模型API调用失败且超过最大重试次数
        """
        # __init__ 保证了 self.client 不为 None
        if self.client is None:
            # 理论上不应该执行到这里，但作为保险
            error_message = "Tongyi client (ChatTongyi) 未初始化，无法调用 _generate。"
            logger.error(f"{error_message} [错误码: {ErrorCodes.MODEL_INIT_FAILED}]")
            raise ModelError(message=error_message, error_code=ErrorCodes.MODEL_INIT_FAILED)

        # 初始化重试计数
        retry_count = 0
        last_exception = None

        # 实现重试机制（带指数退避）
        while retry_count <= MAX_RETRIES:
            try:
                # 调用 ChatTongyi 模型
                response_message = self.client.invoke(
                    messages,
                    stop=stop,
                    **kwargs
                )
                # 成功获取响应，构建 ChatResult 并返回
                generation = ChatGeneration(message=response_message)
                return ChatResult(generations=[generation])

            except Exception as e:
                last_exception = e
                retry_count += 1

                # 如果已达最大重试次数，抛出异常
                if retry_count > MAX_RETRIES:
                    error_message = f"通义千问模型 (ChatTongyi) API调用失败，已重试{MAX_RETRIES}次: {e}"
                    logger.error(f"{error_message} [错误码: {ErrorCodes.MODEL_INVOKE_FAILED}]", exc_info=True)
                    # 将原始异常包装在ModelError中抛出
                    raise ModelError(
                        message=error_message,
                        error_code=ErrorCodes.MODEL_INVOKE_FAILED
                    ) from e

                # 计算延迟时间并等待
                delay = self._exponential_backoff(retry_count - 1)
                logger.warning(f"通义千问模型调用失败，正在进行第{retry_count}次重试，等待{delay:.2f}秒: {e}")
                time.sleep(delay)

    @property
    def _llm_type(self) -> str:
        """返回LLM类型"""
        # 可以保持 qwen-vl 或改为更通用的 tongyi
        return "tongyi-chat"

def get_qwen_model(config: ModelConfig) -> QwenVLModel:
    """
    获取通义千问模型实例

    Args:
        config: 模型配置

    Returns:
        QwenVLModel: 模型实例
    """
    return QwenVLModel(config)
