# -*- coding: utf-8 -*-
"""
服务层模块 - 提供AR导游系统的各种服务功能
"""

# 导出会话管理服务
from .session.session_manager import get_session_manager

# 导出AR查询服务
from .ar.ar_query_service import process_ar_query 