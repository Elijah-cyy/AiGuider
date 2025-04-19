#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
会话管理服务 - 管理用户会话
"""

import asyncio
from typing import Dict, List, Optional
import uuid
import logging
from datetime import datetime

from .session_model import AIApplication

logger = logging.getLogger(__name__)

class SessionManager:
    """会话管理服务"""
    
    def __init__(self):
        self.sessions: Dict[str, AIApplication] = {}
        self.cleanup_interval = 3600  # 清理过期会话的间隔(秒)

        # 创建一个协程，用于启动定期清理任务并保存引用，便于后续取消
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

    async def _cleanup_expired_sessions(self):
        """定期清理过期会话"""
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                current_time = datetime.now()
                expired_sessions = []

                for session_id, app in self.sessions.items():
                    # 超过4小时未活动的会话视为过期
                    if (current_time - app.last_active).total_seconds() > 14400:
                        expired_sessions.append(session_id)

                # 删除过期会话
                for session_id in expired_sessions:
                    await self.cleanup_session(session_id)
        except asyncio.CancelledError:
            logger.info("[SESSION] 会话管理器的清理协程已停止")
        except Exception as e:
            logger.error(f"[SESSION] 会话管理器的清理协程出错: {str(e)}")

    async def cleanup_all(self):
        """
        清理所有会话资源和管理器自身资源，用于应用关闭时调用
        """
        # 取消清理协程
        if hasattr(self, '_cleanup_task') and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                # 等待协程正常结束
                await asyncio.wait_for(self._cleanup_task, timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                logger.warning("[SESSION] 等待清理协程取消超时")

        # 清理所有会话
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self.cleanup_session(session_id)

        logger.info("[SESSION] 所有会话和管理器资源已清理完成")

    async def cleanup_session(self, session_id: str):
        """
        清理会话并释放资源

        目前实现为直接删除会话，将来可修改为持久化到数据库

        Args:
            session_id: 要清理的会话ID
        """
        if session_id in self.sessions:
            # 先清理资源，主要是回收协程
            self.sessions[session_id].cleanup()
            # TODO:这里将来可以添加持久化到数据库的代码
            # 如: await self._persist_session_to_db(session_id, self.sessions[session_id])
            # 然后删除会话
            del self.sessions[session_id]
            logger.info(f"[SESSION] 会话 {session_id} 已清理")
        else:
            # 这里应该是不会被触发的
            logger.warning(f"[SESSION] 尝试清理不存在的会话 {session_id}")

    def create_session(self) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = AIApplication(session_id)
        logger.info(f"[SESSION] 创建新会话 {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[AIApplication]:
        """获取会话实例"""
        return self.sessions.get(session_id)

    def process_query(self, session_id: str, query_text: str, image=None) -> Dict:
        """处理查询"""
        # 获取或创建会话
        app = self.get_session(session_id)
        if not app:
            session_id = self.create_session()
            app = self.get_session(session_id)
            logger.info(f"[SESSION] 创建新会话处理查询 {session_id} 内容: {query_text[:50]}")

        # 处理查询
        return app.process_query(query_text, image)

    def get_pending_messages(self, session_id: str) -> List[Dict]:
        """获取待发送的主动消息"""
        app = self.get_session(session_id)
        if not app:
            logger.warning(f"[SESSION] 无效会话ID {session_id} 请求消息")
            return []

        messages = app.get_pending_messages()
        logger.debug(f"[SESSION] 返回会话 {session_id} 待处理消息 {len(messages)}条")
        return messages

# 全局会话管理器实例
_session_manager = None

def get_session_manager() -> SessionManager:
    """
    获取会话管理器实例

    此函数确保会话管理器是一个全局单例
    在FastAPI应用启动时调用初始化，关闭时调用清理
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager 