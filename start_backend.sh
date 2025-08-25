#!/bin/bash

# AR智能导游眼镜系统 - 后端服务启动脚本

# 进入后端项目目录
cd aiGuider_Server

# 启动后端服务
echo "启动后端服务..."
uvicorn app.main:app --host 0.0.0.0 --port 6160 --reload

# 脚本结束时提示
echo "后端服务已关闭" 