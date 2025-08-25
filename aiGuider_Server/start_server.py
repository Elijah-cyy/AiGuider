#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AR智能导游眼镜系统 - 一键启动脚本
快速启动FastAPI后端服务

使用方法:
    uv run start_server.py               # 开发模式启动（热重载）
    uv run start_server.py --prod        # 生产模式启动
    uv run start_server.py --port 8080   # 指定端口启动
"""

import argparse
import sys
import uvicorn
from pathlib import Path

def main():
    """主启动函数"""
    parser = argparse.ArgumentParser(description="AR智能导游眼镜系统后端服务启动器")
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="服务器绑定地址 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=6160, 
        help="服务器端口号 (默认: 6160)"
    )
    parser.add_argument(
        "--prod", 
        action="store_true", 
        help="生产模式启动（关闭热重载和调试）"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1, 
        help="工作进程数量（仅生产模式有效，默认: 1）"
    )
    
    args = parser.parse_args()
    
    # 确保在正确的目录中运行
    script_dir = Path(__file__).parent
    if script_dir.name != "aiGuider_Server":
        print("错误: 请在aiGuider_Server目录中运行此脚本")
        sys.exit(1)
    
    print("🚀 AR智能导游眼镜系统后端服务启动中...")
    print(f"📍 服务地址: http://{args.host}:{args.port}")
    print(f"📖 API文档: http://{args.host}:{args.port}/docs")
    print(f"📚 ReDoc文档: http://{args.host}:{args.port}/redoc")
    
    if args.prod:
        print("🌐 生产模式启动")
        # 生产模式配置
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            workers=args.workers,
            loop="uvloop",  # 使用高性能事件循环
            http="httptools",  # 使用高性能HTTP解析器
            access_log=True,
            log_level="info"
        )
    else:
        print("🔧 开发模式启动（支持热重载）")
        # 开发模式配置
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=True,  # 开启热重载
            log_level="debug"
        )

if __name__ == "__main__":
    main()
