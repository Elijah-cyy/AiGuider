"""
模型配置

管理大模型配置的模块，包括模型选择、参数设置等
"""

import os
import json
import logging
import uuid
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# 错误码定义
class ErrorCodes:
    CONFIG_FILE_NOT_FOUND = "CONFIG_001"
    CONFIG_PARSE_ERROR = "CONFIG_002"
    MODEL_CONFIG_NOT_FOUND = "CONFIG_003"

@dataclass
class ModelConfig:
    """模型配置类"""
    
    # 模型名称
    model_name: str
    
    # 温度参数，控制输出的随机性
    temperature: float
    
    # 最大新生成的token数
    max_tokens: int
    
    # API密钥和端点配置
    api_key: str
    api_base: str
    
    # 其他模型参数
    model_kwargs: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后的处理，如从环境变量加载配置"""
        # 从环境变量加载API密钥
        if not self.api_key:
            self.api_key = os.environ.get("QWEN_API_KEY")
        
        # 从环境变量加载API基础URL
        if not self.api_base:
            self.api_base = os.environ.get("QWEN_API_BASE")

class ConfigError(Exception):
    """配置错误异常类"""
    
    def __init__(self, message: str, error_code: str, error_id: str = None):
        """
        初始化配置错误
        
        Args:
            message: 错误信息
            error_code: 错误码
            error_id: 错误唯一标识，用于调试和跟踪
        """
        self.error_code = error_code
        self.error_id = error_id or str(uuid.uuid4())
        self.message = message
        super().__init__(f"[{error_code}] {message} (ID: {self.error_id})")

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
    error_id = str(uuid.uuid4())
    
    try:
        # 检查配置文件是否存在
        if not config_path.exists():
            error_message = f"模型配置文件不存在: {config_path}"
            logger.error(f"{error_message} [错误码: {ErrorCodes.CONFIG_FILE_NOT_FOUND}, ID: {error_id}]")
            # 这是一个严重错误，抛出异常
            raise ConfigError(
                message=error_message,
                error_code=ErrorCodes.CONFIG_FILE_NOT_FOUND,
                error_id=error_id
            )
        
        # 读取配置文件
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except json.JSONDecodeError:
            error_message = f"模型配置文件格式错误: {config_path}"
            logger.error(f"{error_message} [错误码: {ErrorCodes.CONFIG_PARSE_ERROR}, ID: {error_id}]")
            raise ConfigError(
                message=error_message,
                error_code=ErrorCodes.CONFIG_PARSE_ERROR,
                error_id=error_id
            )
        
        # 查找模型配置
        model_config_data = config_data.get(model_name)
        if not model_config_data:
            error_message = f"未找到模型 {model_name} 的配置"
            logger.error(f"{error_message} [错误码: {ErrorCodes.MODEL_CONFIG_NOT_FOUND}, ID: {error_id}]")
            raise ConfigError(
                message=error_message,
                error_code=ErrorCodes.MODEL_CONFIG_NOT_FOUND,
                error_id=error_id
            )
        
        # 创建配置对象
        config = ModelConfig(
            model_name=model_config_data["model_name"],
            temperature=model_config_data["temperature"],
            max_tokens=model_config_data["max_tokens"],
            api_key=model_config_data["api_key"],
            api_base=model_config_data["api_base"],
            model_kwargs=model_config_data.get("model_kwargs", {})
        )
        
        return config
        
    except ConfigError:
        # 重新抛出已经格式化好的配置错误
        raise
    except Exception as e:
        # 捕获其他未预期的异常
        error_message = f"加载模型配置时发生未预期错误: {str(e)}"
        logger.error(f"{error_message} [ID: {error_id}]", exc_info=True)
        # 转换为ConfigError并包含原始异常信息
        raise ConfigError(
            message=error_message,
            error_code="CONFIG_999",
            error_id=error_id
        ) from e 