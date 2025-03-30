#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库模型
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    sessions = relationship("UserSession", back_populates="user")

class UserSession(Base):
    """用户会话模型"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="sessions")
    queries = relationship("Query", back_populates="session")

class Landmark(Base):
    """地标模型"""
    __tablename__ = "landmarks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    description = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float, nullable=True)
    image_url = Column(String, nullable=True)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Query(Base):
    """查询记录模型"""
    __tablename__ = "queries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"))
    query_text = Column(Text)
    location = Column(JSONB)  # 存储位置信息JSON
    response_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    session = relationship("UserSession", back_populates="queries") 