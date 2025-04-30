"""
提示模板工具

用于加载和管理提示模板的模块
"""

from .thinker import THINKER_PROMPT

def load_thinker_prompt() -> str:
    """
    加载Thinker节点提示词
    
    Returns:
        str: Thinker节点提示词内容
    """
    return THINKER_PROMPT 