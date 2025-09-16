#!/bin/bash

# 开发环境启动脚本
echo "🚀 启动 TestGPT 开发环境..."

# 检查是否安装了依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 安装前端依赖..."
    cd frontend && npm install && cd ..
fi

if [ ! -d "backend/venv" ]; then
    echo "🐍 安装后端依赖..."
    cd backend && python -m venv venv && source venv/bin/activate && pip install -e . && cd ..
fi

# 启动服务
echo "🌟 启动前后端服务..."
npm run dev 