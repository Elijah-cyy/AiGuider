"""
模型配置

管理大模型配置的模块，包括模型选择、参数设置等
"""

import os
import json
import logging
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

# 引入新的错误码系统
from .error_codes import ConfigError, ErrorCodes

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """模型配置类"""

    # 模型名称
    model_name: str

    # 温度参数，控制输出的随机性
    temperature: float

    # 最大新生成的token数
    max_tokens: int

    # 控制采样范围的概率质量
    top_p: float = 0.8

    # 是否启用流式输出
    streaming: bool = False

    # API密钥
    dashscope_api_key: Optional[str] = None

    # 其他模型参数
    model_kwargs: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后的处理，如从环境变量加载配置"""
        # 从环境变量加载API密钥
        if not self.dashscope_api_key:
            self.dashscope_api_key = os.environ.get("DASHSCOPE_API_KEY")

def load_model_config(model_name: str) -> ModelConfig:
    """
    从配置文件加载模型配置

    Args:
        model_name: 模型名称，用于在配置文件中查找对应的配置

    Returns:
        ModelConfig: 模型配置对象

    Raises:
        ConfigError: 配置文件不存在或格式错误时抛出
    """
    # 获得模型配置文件路径
    config_path = Path(__file__).parent / "model_configs.json"

    # 生成错误调试指纹
    error_id = None

    try:
        # 检查配置文件是否存在
        if not config_path.exists():
            error_message = f"模型配置文件不存在: {config_path}"
            logger.error(f"{error_message} [错误码: {ErrorCodes.CONFIG_FILE_NOT_FOUND}]")
            # 这是一个严重错误，抛出异常
            raise ConfigError(
                message=error_message,
                error_code=ErrorCodes.CONFIG_FILE_NOT_FOUND
            )

        # 读取配置文件
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except json.JSONDecodeError:
            error_message = f"模型配置文件格式错误: {config_path}"
            logger.error(f"{error_message} [错误码: {ErrorCodes.CONFIG_PARSE_ERROR}]")
            raise ConfigError(
                message=error_message,
                error_code=ErrorCodes.CONFIG_PARSE_ERROR
            )

        # 查找模型配置
        model_config_data = config_data.get(model_name)
        if not model_config_data:
            error_message = f"未找到模型 {model_name} 的配置"
            logger.error(f"{error_message} [错误码: {ErrorCodes.MODEL_CONFIG_NOT_FOUND}]")
            raise ConfigError(
                message=error_message,
                error_code=ErrorCodes.MODEL_CONFIG_NOT_FOUND
            )

        # 创建配置对象
        config = ModelConfig(
            model_name=model_config_data["model_name"],
            temperature=model_config_data["temperature"],
            max_tokens=model_config_data["max_tokens"],
            top_p=model_config_data.get("top_p", 0.8),
            streaming=model_config_data.get("streaming", False),
            dashscope_api_key=model_config_data.get("dashscope_api_key"),
            model_kwargs=model_config_data.get("model_kwargs", {})
        )

        return config

    except ConfigError:
        # 重新抛出已经格式化好的配置错误
        raise
    except Exception as e:
        # 捕获其他未预期的异常
        error_message = f"加载模型配置时发生未预期错误: {str(e)}"
        logger.error(f"{error_message} [错误码: {ErrorCodes.CONFIG_INVALID}]", exc_info=True)
        # 转换为ConfigError并包含原始异常信息
        raise ConfigError(
            message=error_message,
            error_code=ErrorCodes.CONFIG_INVALID
        ) from e
