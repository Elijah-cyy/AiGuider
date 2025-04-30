#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
会话数据模型 - 定义会话相关的数据结构
"""

import time
import random
import asyncio
from typing import Dict, List, Optional
import uuid
import logging
from datetime import datetime

# 导入LangGraph Agent
from ..ar.langgraph_agent import process_multimodal_query

logger = logging.getLogger(__name__)

class AIApplication:
    """AI应用实例模型"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.conversation_history = []
        self.pending_messages = []  # 存储待发送的主动消息
        self.message_interval = random.randint(5, 10)  # 主动发消息的间隔(秒)
        self.last_proactive_time = time.time()
        self.MAX_PENDING_MESSAGES = 2  # 最多允许2条待处理的主动消息

        # 初始化一个协程，用于主动消息任务
        self._task = asyncio.create_task(self._generate_proactive_messages())

    def cleanup(self):
        """清理资源，取消后台任务"""
        if hasattr(self, '_task') and not self._task.done():
            self._task.cancel()
            logger.info(f"[SESSION] 会话 {self.session_id} 的消息生成协程已取消")

    async def _generate_proactive_messages(self):
        """生成主动消息的协程"""
        try:
            while True:
                await asyncio.sleep(self.message_interval)
                current_time = time.time()

                # 检查是否应该生成新消息，并确保待处理消息不超过最大限制
                if (current_time - self.last_proactive_time >= self.message_interval and
                        len(self.pending_messages) < self.MAX_PENDING_MESSAGES):
                    proactive_message = self._create_proactive_message()
                    if proactive_message:
                        self.pending_messages.append({
                            "id": str(uuid.uuid4()),
                            "content": proactive_message,
                            "timestamp": datetime.now().isoformat()
                        })
                        self.last_proactive_time = current_time
                        logger.debug(f"[SESSION] 会话 {self.session_id} 生成新的主动消息，当前共有 {len(self.pending_messages)} 条待处理消息")
        except asyncio.CancelledError:
            logger.info(f"[SESSION] 会话 {self.session_id} 的消息生成协程已停止")
        except Exception as e:
            logger.error(f"[SESSION] 会话 {self.session_id} 的消息生成协程出错: {str(e)}")

    def _create_proactive_message(self) -> Optional[str]:
        """创建一条主动消息"""
        proactive_messages = [
            "我注意到您正经过一处历史建筑，需要了解相关信息吗？",
            "前方500米有一家评分很高的餐厅，要听听详细介绍吗？",
            "这个地区有几个值得参观的景点，需要我推荐一下吗？",
            "根据您的兴趣偏好，我觉得您可能会喜欢附近的这个展览。",
            "现在正好是这里的文化节，有几项活动可能符合您的喜好。",
            "您已经走了3公里了，要不要休息一下？附近有几个适合放松的地方。",
            "这个位置拍照效果很好，建议您可以在此驻足拍摄。",
            "我发现您对历史建筑很感兴趣，这个区域有一个不太知名但很有价值的历史遗迹。"
        ]
        return random.choice(proactive_messages)

    async def process_query(self, query_text: str, image=None) -> Dict:
        """处理用户查询"""
        self.last_active = datetime.now()

        # 记录对话历史，处理纯图像的情况
        content_description = query_text if query_text else "【图像输入】"
        self.conversation_history.append({
            "role": "user",
            "content": content_description,
            "timestamp": datetime.now().isoformat()
        })

        response = await self._generate_response(query_text, image)

        # 记录系统回复
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })

        return {
            "reply": response,
            "session_id": self.session_id
        }

    async def _generate_response(self, query_text: str, image=None) -> str:
        """生成回复内容"""
        # 控制是否使用原始逻辑的标志，可以后续修改为配置项
        use_original_logic = False
        
        if use_original_logic:
            # 原有的模拟回复逻辑
            if image:
                image_responses = [
                    f"我看到您上传了一张图片。这似乎是一个地标建筑，建于约1920年代。",
                    f"从您分享的照片来看，这是当地著名的景点之一，每年吸引约50万游客。",
                    f"您的图片中显示的是一处历史遗迹，有着丰富的文化背景。",
                    f"这张照片展示的是一座具有典型地方特色的建筑，设计融合了现代与传统元素。"
                ]
                return random.choice(image_responses)

            # 关键词响应
            if query_text and ("历史" in query_text or "文化" in query_text):
                return f"关于{query_text}，这个地区的历史可以追溯到明清时期，有着丰富的文化遗产和历史故事。"
            elif query_text and ("美食" in query_text or "餐厅" in query_text or "吃" in query_text):
                return f"当地有多种特色美食，最有名的是手工面点和农家菜。附近的'老街坊'餐厅评分很高，距离您约300米。"
            elif query_text and ("景点" in query_text or "参观" in query_text or "游览" in query_text):
                return f"附近有几个值得参观的景点，包括历史博物馆、古城墙和艺术区。我可以为您规划一条最优游览路线。"
            elif query_text and ("交通" in query_text or "路线" in query_text):
                return f"从当前位置到目的地，您可以乘坐公交102路，约15分钟到达。或者步行约25分钟，沿途可以欣赏城市风光。"

            # 默认回复
            if query_text:
                general_responses = [
                    f"您询问的是关于'{query_text}'的信息。根据当前位置和上下文，我推荐您可以...",
                    f"关于'{query_text}'，我找到了一些相关信息。这个地区以...而闻名。",
                    f"我理解您对'{query_text}'很感兴趣。这里有一些您可能会喜欢的相关信息...",
                    f"关于'{query_text}'的问题很有见地。从历史角度来看，这个地方...",
                ]
                return random.choice(general_responses)
            else:
                # 纯图像输入的默认回复
                return "我看到了您分享的图片，这似乎是一个有趣的地方。"
        else:
            # 使用LangGraph Agent处理请求
            try:
                # 记录请求类型
                if image and not query_text:
                    logger.info(f"[SESSION] 使用LangGraph Agent处理纯图像请求")
                elif image and query_text:
                    logger.info(f"[SESSION] 使用LangGraph Agent处理图像+文字请求: {query_text}")
                else:
                    logger.info(f"[SESSION] 使用LangGraph Agent处理纯文本请求: {query_text}")
                
                # 直接调用异步函数处理查询
                result = await process_multimodal_query(
                    text_query=query_text,
                    image_data=image,
                    session_id=self.session_id
                )

                # 从结果中提取响应
                if result and "response" in result:
                    response = result["response"]
                    # 处理多模态模型可能返回的复杂响应格式
                    if isinstance(response, list):
                        extracted_texts = []
                        for item in response:
                            if isinstance(item, dict) and 'text' in item:
                                extracted_texts.append(item['text'])
                        response = "\n".join(extracted_texts)
                        logger.info(f"从多模态响应中提取纯文本内容: {response}")
                    return response
                else:
                    logger.warning(f"LangGraph Agent返回了无效结果: {result}")
                    raise ValueError("无效的响应结果")
                    
            except Exception as e:
                # 发生错误时记录并降级回简单响应
                logger.error(f"使用LangGraph Agent生成回复时出错: {str(e)}", exc_info=True)
                
                # 根据输入类型提供不同的错误响应
                if image and not query_text:
                    return "抱歉，我在处理您的图片时遇到了问题。请稍后再试。"
                elif query_text:
                    return f"抱歉，我在处理您的关于'{query_text}'的请求时遇到了问题。请稍后再试。"
                else:
                    return "抱歉，系统处理您的请求时遇到了问题。请稍后再试。"

    def get_pending_messages(self) -> List[Dict]:
        """获取并清空待发送的主动消息"""
        messages = self.pending_messages.copy()
        self.pending_messages = []
        return messages 