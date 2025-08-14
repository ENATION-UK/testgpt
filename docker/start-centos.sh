#!/bin/bash

# CentOS环境专用启动脚本
echo "🚀 在CentOS环境中启动AutoTest Backend服务..."

# 设置代理环境变量（如果需要）
# export https_proxy=http://127.0.0.1:7012
# export http_proxy=http://127.0.0.1:7012
# export all_proxy=socks5://127.0.0.1:7012

# 确保数据目录存在
mkdir -p ./data

# 设置正确的权限（CentOS可能需要）
chmod 755 ./data
chown -R $USER:$USER ./data

# 显示目录信息
echo "📁 数据目录: $(pwd)/data"
echo "📁 数据目录权限: $(ls -ld ./data)"
echo "👤 当前用户: $(whoami)"
echo "🔑 用户ID: $(id)"

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose down

# 清理现有容器和镜像（可选）
# echo "🧹 清理现有容器和镜像..."
# docker-compose down --rmi all --volumes --remove-orphans

# 重新构建并启动
echo "🔨 重新构建镜像..."
docker-compose build --no-cache backend

echo "🚀 启动服务..."
docker-compose up backend

echo "✅ 服务启动完成！"
echo "📖 API文档: http://localhost:8000/docs"
echo "🔍 查看日志: docker-compose logs -f backend"
echo "📁 数据文件位置: $(pwd)/data/autotest.db"
