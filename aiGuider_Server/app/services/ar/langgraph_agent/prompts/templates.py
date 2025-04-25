"""
提示模板工具

用于加载和管理提示模板的模块
"""

from .tour_guide import TOUR_GUIDE_PROMPT

def load_system_prompt() -> str:
    """
    加载系统提示
    
    Returns:
        str: 系统提示内容
    """
    # 直接返回导入的提示词内容
    return TOUR_GUIDE_PROMPT 