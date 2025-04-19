"""
提示模板工具

用于加载和管理提示模板的模块
"""

import os
from pathlib import Path
from typing import Dict, Optional, Any

# 模板缓存
_template_cache: Dict[str, str] = {}

def get_template_path(template_name: str) -> Path:
    """
    获取模板文件路径
    
    Args:
        template_name: 模板名称，不带扩展名
        
    Returns:
        Path: 模板文件路径
    """
    # 当前模块目录
    current_dir = Path(__file__).parent
    
    # 模板目录
    template_dir = current_dir / "templates"
    
    # 模板文件路径
    template_path = template_dir / f"{template_name}.md"
    
    return template_path

def load_template(template_name: str) -> str:
    """
    加载模板文件内容
    
    Args:
        template_name: 模板名称，不带扩展名
        
    Returns:
        str: 模板内容
    
    Raises:
        FileNotFoundError: 模板文件不存在时抛出
    """
    # 检查缓存
    if template_name in _template_cache:
        return _template_cache[template_name]
    
    # 获取模板路径
    template_path = get_template_path(template_name)
    
    # 检查文件是否存在
    if not template_path.exists():
        raise FileNotFoundError(f"模板文件不存在: {template_path}")
    
    # 读取模板内容
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
    
    # 缓存模板
    _template_cache[template_name] = template_content
    
    return template_content

def render_template(template_name: str, **kwargs: Any) -> str:
    """
    渲染模板
    
    Args:
        template_name: 模板名称，不带扩展名
        **kwargs: 模板变量
        
    Returns:
        str: 渲染后的模板内容
    """
    # 加载模板
    template_content = load_template(template_name)
    
    # 使用简单的字符串替换渲染模板
    for key, value in kwargs.items():
        template_content = template_content.replace(f"{{{key}}}", str(value))
    
    return template_content

def load_system_prompt(template_name: str, **kwargs: Any) -> str:
    """
    加载系统提示
    
    Args:
        template_name: 模板名称，不带扩展名
        **kwargs: 模板变量
        
    Returns:
        str: 系统提示内容
    """
    try:
        # 尝试加载并渲染模板
        return render_template(template_name, **kwargs)
    except FileNotFoundError:
        # 如果模板文件不存在，返回默认系统提示
        return DEFAULT_SYSTEM_PROMPT

# 默认系统提示，当模板文件不存在时使用
DEFAULT_SYSTEM_PROMPT = """你是一个AR智能导游助手，负责帮助用户了解他们看到的景点、建筑和物品。
你应该:
1. 分析用户提供的图像，识别其中的景点、建筑或物品
2. 提供简洁、准确、信息丰富的回答
3. 当不确定时，坦诚承认而不是编造信息
4. 使用友好、专业的语气

当用户上传图像时，首先识别图像内容，然后回答相关问题。
如果用户只发送图像没有文本，你应该主动识别图像内容并提供相关信息。""" 