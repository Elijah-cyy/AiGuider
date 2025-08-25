# AR智能导游眼镜系统 - 后端服务

## 项目概述

这是一个AR智能导游眼镜系统的后端服务，负责处理来自AR眼镜客户端的请求，提供智能导游服务。

## 快速启动

### 前置条件

确保已安装 [uv](https://github.com/astral-sh/uv) 包管理工具：

```bash
# 安装 uv（仅首次需要）
pip install uv -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
```

### 一键启动服务

```bash
# 进入后端服务目录
cd aiGuider_Server

# 🚀 一键启动（自动安装依赖 + 启动服务）
uv run start_server.py
```

> **提示**: `uv run` 会自动使用国内镜像源去创建Python 3.11虚拟环境、安装所有依赖包，然后启动服务。无需手动执行 `uv sync`步骤！

### 启动选项

```bash
# 开发模式（默认，支持热重载）
uv run start_server.py

# 生产模式启动
uv run start_server.py --prod

# 指定端口启动
uv run start_server.py --port 8080

# 查看所有启动参数
uv run start_server.py --help
```

## API接口文档

系统提供多种API端点用于AR眼镜客户端和Web后台交互。完整的API文档请参考：

- **Android客户端接口**: 查看 [API_for_Android.md](doc/API_for_Android.md)
- **Web后台接口**: 查看 [API_for_Web.md](doc/API_for_Web.md)

API文档包含各接口的详细说明、请求参数、响应格式和示例代码。
