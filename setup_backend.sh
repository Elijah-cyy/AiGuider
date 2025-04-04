#!/bin/bash

# AR智能导游眼镜系统 - 后端环境安装脚本

# 进入后端项目目录
cd aiGuider_Server

# 安装后端依赖
echo "安装项目所需依赖..."
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt

# 提示完成
echo "环境依赖安装完成"
