#!/bin/bash

# AR智能导游眼镜系统 - Web前端启动脚本

# 进入前端项目目录
cd aiGuider_Client/web

# 检查是否有Python可用，用于启动简单的HTTP服务器
if command -v python3 &>/dev/null; then
    echo "使用Python3启动Web服务器..."
    python3 -m http.server 8080
elif command -v python &>/dev/null; then
    echo "使用Python启动Web服务器..."
    python -m http.server 8080
else
    echo "错误: 未找到Python，无法启动Web服务器"
    echo "请安装Python或使用其他HTTP服务器"
    exit 1
fi

# 脚本结束时提示
echo "Web服务器已关闭" 