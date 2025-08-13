#!/bin/bash

# 设置代理环境变量（如果需要）
# export https_proxy=http://127.0.0.1:7012
# export http_proxy=http://127.0.0.1:7012
# export all_proxy=socks5://127.0.0.1:7012

echo "🚀 启动AutoTest Backend服务..."

# 确保数据目录存在并有正确权限
mkdir -p ./data
chmod 755 ./data

# 显示数据目录信息
echo "📁 数据目录: $(pwd)/data"
echo "📁 数据目录权限: $(ls -ld ./data)"

# 构建并启动服务
echo "🔨 构建并启动服务..."
docker-compose up --build backend

echo "✅ 服务启动完成！"
echo "📖 API文档: http://localhost:8000/docs"
echo "🔍 查看日志: docker-compose logs -f backend" 