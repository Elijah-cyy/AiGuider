# AR智能导游眼镜系统 - 后端服务

## 项目概述

这是一个基于FastAPI的AR智能导游眼镜系统后端服务，整合多模态感知、大语言模型（LLM）和知识图谱技术，实现低延迟的实时交互。本项目是整个AR智能导游眼镜系统的服务器端部分，负责处理来自AR眼镜客户端的请求，提供智能导游服务。

### 技术栈

- **Web框架**: FastAPI (>=0.95)
- **LLM编排**: LangGraph
- **数据库**: PostgreSQL + SQLAlchemy异步驱动
- **消息队列**: Kafka + aiokafka
- **通信协议**: gRPC-Web + Protocol Buffers
- **部署**: Gunicorn+Uvicorn组合

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
│   │   │   ├── session.py   # 会话管理接口
│   │   │   ├── chat.py      # 聊天功能接口
│   │   │   └── ar_guide.py  # AR导游功能接口
│   │   └── api.py           # API路由注册和版本控制
│   │
│   ├── schemas/             # 数据模型定义
│   │   ├── __init__.py
│   │   ├── requests.py      # API请求模型
│   │   └── responses.py     # API响应模型
│   │
│   ├── services/            # 业务逻辑层（核心代码）
│   │   ├── __init__.py      # 服务层入口
│   │   ├── session/         # 会话管理服务模块
│   │   │   ├── __init__.py
│   │   │   ├── session_model.py    # 会话数据模型
│   │   │   └── session_manager.py  # 会话管理器
│   │   └── ar/              # AR服务模块
│   │       ├── __init__.py
│   │       └── ar_query_service.py # AR查询服务
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
├── doc/                     # 文档目录
│   ├── API_for_Android.md   # Android客户端API文档
│   ├── API_for_Web.md       # Web客户端API文档
│   └── 后端会话管理技术文档.md  # 会话管理技术文档
├── .env                     # 环境变量配置
└── requirements.txt         # 项目依赖
```


## 错误处理机制

系统实现了分级错误处理机制，确保在各种场景下都能提供适当的错误响应和降级服务：

### 三级错误处理

1. **客户端错误 (400-499)**
   - 立即返回错误信息给客户端
   - 包含错误码、错误消息和调试ID
   - 常见错误: 请求参数无效、认证失败、资源不存在

2. **服务端错误 (500-599)**
   - 在3秒内返回降级响应
   - 记录完整错误堆栈并生成调试ID
   - 支持指数退避算法自动重试

3. **LLM错误 (特定错误码)**
   - 在AI模型不可用时返回预设知识库内容
   - 支持异步重试机制
   - 提供友好的降级响应

所有错误响应都包含以下信息:
- `error_code`: 错误标识码
- `message`: 用户友好的错误描述
- `debug_id`: 用于追踪和调试的唯一ID
- `details`: 可选的详细错误信息

## 功能特点

- **错误处理机制**: 实现分级错误处理
- **异步处理**: 支持高并发
- **健康检查**: 提供服务和数据库状态监控
- **AR导游查询**: 处理AR眼镜查询请求
- **会话管理**: 支持多用户会话和状态维护

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

3.1. **配置通义千问 API Key (重要)**

   后端服务依赖通义千问模型。请配置 API Key：
   *   **推荐方式：** 设置环境变量 `DASHSCOPE_API_KEY` 为您的 Key。
     ```bash
     # Linux/macOS
     export DASHSCOPE_API_KEY="你的通义千问API Key"
     # Windows (PowerShell)
     # $env:DASHSCOPE_API_KEY="你的通义千问API Key"
     ```
   *   **备选方式：** 修改配置文件 `aiGuider_Server/app/services/ar/langgraph_agent/config/model_configs.json` 中的 `api_key` 字段。

   请将 `"你的通义千问API Key"` 替换为您的真实 Key。

4. 启动服务
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```


## API接口文档

系统提供多种API端点用于AR眼镜客户端和Web后台交互。完整的API文档请参考：

- **Android客户端接口**: 查看 [API_for_Android.md](doc/API_for_Android.md)
- **Web后台接口**: 查看 [API_for_Web.md](doc/API_for_Web.md)

API文档包含各接口的详细说明、请求参数、响应格式和示例代码。
