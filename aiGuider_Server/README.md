# AR智能导游眼镜系统 - 后端服务

## 项目概述

这是一个AR智能导游眼镜系统的后端服务，负责处理来自AR眼镜客户端的请求，提供智能导游服务。

## 安装与启动

本项目使用 [uv](https://github.com/astral-sh/uv) 进行python包管理，提供了极速的依赖安装和可靠的环境管理。

### 1. 安装 uv 工具（首次执行）

在服务器上执行以下命令安装 uv。如果已安装，请跳过此步骤。

```bash
# 使用 pip 安装 uv，并配置国内镜像源
pip install uv -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
```

### 2. 同步依赖环境

进入项目目录，执行 `uv sync` 命令。uv 将自动完成所有环境配置。

```bash
# 进入后端服务目录
cd aiGuider_Server

# 使用国内镜像源一键同步依赖环境
uv sync --frozen --index-url http://mirrors.aliyun.com/pypi/simple/
```

> **提示**: `uv sync` 会自动下载所需的 Python 3.11 版本，并创建 `.venv` 虚拟环境，无需手动操作。`--frozen` 参数确保严格按照 `uv.lock` 文件安装，保证生产环境的一致性。

### 3. 启动服务

使用 `uv run` 命令启动服务，无需手动激活虚拟环境。

```bash
# 进入后端服务目录
cd aiGuider_Server

# 启动服务
uv run uvicorn app.main:app --host 0.0.0.0 --port 6160
```

## API接口文档

系统提供多种API端点用于AR眼镜客户端和Web后台交互。完整的API文档请参考：

- **Android客户端接口**: 查看 [API_for_Android.md](doc/API_for_Android.md)
- **Web后台接口**: 查看 [API_for_Web.md](doc/API_for_Web.md)

API文档包含各接口的详细说明、请求参数、响应格式和示例代码。
