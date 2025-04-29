"""
提示模板工具

用于加载和管理提示模板的模块
"""

from .thinker import THINKER_PROMPT
from .system import SYSTEM_PROMPT

def load_system_prompt() -> str:
    """
    加载系统提示
    
    Returns:
        str: 系统提示内容
    """
    # 使用系统整体提示词
    return SYSTEM_PROMPT

def load_thinker_prompt() -> str:
    """
    加载Thinker节点提示词
    
    Returns:
        str: Thinker节点提示词内容
    """
    return THINKER_PROMPT 