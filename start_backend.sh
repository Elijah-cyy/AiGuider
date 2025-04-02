#!/bin/bash

# AR智能导游眼镜系统 - 后端服务启动脚本

# 进入后端项目目录
cd aiGuider_Server

# 检查是否存在虚拟环境，如果不存在则创建
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境
if [ -d "venv/bin" ]; then
    # Linux/Mac
    source venv/bin/activate
elif [ -d "venv/Scripts" ]; then
    # Windows
    . venv/Scripts/activate
else
    echo "无法激活虚拟环境，请检查目录结构"
    exit 1
fi

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "警告: .env文件不存在，将使用默认配置"
fi

# 启动后端服务
echo "启动后端服务..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 脚本结束时提示
echo "后端服务已关闭" 