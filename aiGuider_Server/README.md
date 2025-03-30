# AR智能导游眼镜系统 - 后端服务

## 项目概述

这是一个基于FastAPI的AR智能导游眼镜系统后端服务，整合多模态感知、大语言模型（LLM）和知识图谱技术，实现低延迟的实时交互。本项目是整个AR智能导游眼镜系统的服务器端部分，负责处理来自AR眼镜客户端的请求，提供智能导游服务。

### 技术栈

- **Web框架**: FastAPI (>=0.95)
- **数据库**: PostgreSQL + SQLAlchemy异步驱动
- **通信协议**: gRPC-Web + Protocol Buffers
- **部署**: Gunicorn+Uvicorn组合

采用FastAPI框架，支持异步处理
使用PostgreSQL+SQLAlchemy作为数据库层
实现了三级错误处理机制
提供健康检查和AR导游查询API

## 项目结构详解

```
aiGuider_Server/
├── app/                      # 应用主目录
│   ├── __init__.py          # 应用初始化
│   ├── main.py              # FastAPI应用入口，包含应用创建和中间件配置
│   │
│   ├── core/                # 核心配置目录
│   │   ├── __init__.py
│   │   ├── config.py        # 系统配置管理，包含数据库、API等配置
│   │   ├── security.py      # 安全相关配置，如认证、加密等
│   │   └── errors.py        # 全局错误处理机制
│   │
│   ├── api/                 # API接口层
│   │   ├── __init__.py
│   │   ├── endpoints/       # API端点实现
│   │   │   ├── __init__.py
│   │   │   ├── health.py    # 健康检查接口
│   │   │   └── ar_guide.py  # AR导游功能接口
│   │   └── api.py           # API路由注册和版本控制
│   │
│   ├── schemas/             # 数据模型定义
│   │   ├── __init__.py
│   │   ├── base.py          # 基础数据模型
│   │   └── responses.py     # API响应模型
│   │
│   ├── services/            # 业务逻辑层（核心代码）
│   │   ├── __init__.py
│   │   ├── ai_service.py    # AI服务实现（LangGraph核心逻辑）
│   │   ├── llm_service.py   # LLM调用服务
│   │   ├── knowledge_service.py  # 知识图谱服务
│   │   └── perception_service.py  # 多模态感知服务
│   │
│   ├── db/                  # 数据库层
│   │   ├── __init__.py
│   │   ├── base.py          # 数据库连接和会话管理
│   │   └── models.py        # 数据库模型定义
│   │
│   └── utils/               # 工具函数
│       ├── __init__.py
│       └── helpers.py       # 通用辅助函数
│
├── tests/                   # 测试目录
├── proto/                   # Protocol Buffers定义文件
├── .env                     # 环境变量配置
└── requirements.txt         # 项目依赖
```

## 代码维护重点与学习指南

### 需要重点学习和维护的代码

1. **核心AI应用层 (`app/services/`)**
   - `ai_service.py`: 最核心的AI逻辑实现，包含LangGraph工作流程
   - 其他服务模块：如`knowledge_service.py`, `perception_service.py`
   - 这部分代码会随产品功能演进频繁变化

2. **API接口层 (`app/api/endpoints/`)**
   - `ar_guide.py`: 与客户端交互的接口定义
   - 需要根据功能扩展添加或修改端点

3. **数据模型 (`app/schemas/`)**
   - `responses.py`: API响应格式定义
   - 需要随功能需求调整响应模型

4. **配置管理 (`app/core/config.py`)**
   - 系统关键配置，如数据库连接、密钥等
   - 部署到不同环境时需要调整

### 可以相对固化的代码

1. **框架基础设施**
   - `app/main.py`: FastAPI应用入口
   - `app/core/errors.py`: 错误处理机制
   - `app/api/api.py`: 路由注册

2. **数据库基础层 (`app/db/`)**
   - `base.py`: 数据库连接配置
   - `models.py`: 数据库模型

3. **工具函数 (`app/utils/`)**
   - `helpers.py`: 通用工具函数

### 学习路径建议

1. **首先掌握**: 
   - `ai_service.py` - 理解LangGraph工作流程
   - `ar_guide.py` - 了解API交互方式

2. **其次了解**:
   - Pydantic模型 (`app/schemas/`)
   - 基本配置 (`app/core/config.py`)

3. **最后熟悉**:
   - FastAPI基础知识
   - 异步编程模式

### 维护建议

- **重点测试**: AI服务层和API接口
- **版本控制**: 关注`services`目录变更
- **文档更新**: 修改AI服务逻辑时更新文档
- **定期审查**: 检查依赖项更新后的兼容性

## 功能特点

- **错误处理机制**: 实现分级错误处理
- **异步处理**: 支持高并发
- **健康检查**: 提供服务和数据库状态监控
- **AR导游查询**: 处理AR眼镜查询请求

## 安装说明

1. 克隆代码库
```bash
git clone <代码库URL>
cd aiGuider_Server
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Windows下使用: venv\Scripts\activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 创建并配置`.env`
```bash
cp .env.example .env
# 编辑.env文件，填入必要的配置信息
```

5. 启动服务
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 开发指南

1. **代码规范**
   - 遵循PEP 8规范
   - 使用类型注解
   - 编写详细的文档字符串

2. **测试要求**
   - 编写单元测试
   - 进行集成测试
   - 确保测试覆盖率

3. **部署流程**
   - 使用Docker容器化
   - 配置CI/CD流程
   - 实现自动化部署

## 常见问题

1. **数据库连接问题**
   - 检查`.env`配置
   - 确认数据库服务状态
   - 验证连接字符串

2. **API响应错误**
   - 查看错误日志
   - 检查请求参数
   - 验证服务状态

3. **性能优化**
   - 使用缓存机制
   - 优化数据库查询
   - 实现异步处理