"""
模型配置

管理大模型配置的模块，包括模型选择、参数设置等
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ModelConfig:
    """模型配置类"""
    
    # 模型名称，默认使用Qwen2.5-VL
    model_name: str = "Qwen/Qwen2.5-VL"
    
    # 温度参数，控制输出的随机性
    temperature: float = 0.7
    
    # 最大新生成的token数
    max_tokens: int = 1024
    
    # API密钥和端点配置
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    
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

def load_model_config() -> ModelConfig:
    """
    加载模型配置
    
    从环境变量或配置文件加载模型配置信息
    
    Returns:
        ModelConfig: 模型配置对象
    """
    # 这里可以添加从配置文件加载的逻辑
    return ModelConfig() 