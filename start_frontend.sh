#!/bin/bash

# AR智能导游眼镜系统 - Web前端启动脚本

# 进入前端项目目录
cd aiGuider_Client/web


echo "使用Python启动Web服务器..."
echo "在浏览器中访问 `http://localhost:8080`即可启动web前端"
python -m http.server 8080

# 脚本结束时提示
echo "Web服务器已关闭" 