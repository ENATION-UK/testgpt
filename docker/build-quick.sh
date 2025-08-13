#!/bin/bash

# 快速构建脚本 - 用于日常开发调试
# 假设基础镜像已经构建好了

echo "=== 快速构建脚本 (开发调试) ==="
echo "时间: $(date)"
echo ""

# 设置代理环境变量
export https_proxy=http://192.168.2.210:7012
export http_proxy=http://192.168.2.210:7012
export all_proxy=socks5://192.168.2.210:7012

# 检查基础镜像是否存在
echo "1. 检查基础镜像..."
if ! docker images | grep -q "autotest-base"; then
    echo "   ❌ 基础镜像不存在，请先运行 ./docker/build-optimized.sh"
    exit 1
fi
echo "   ✓ 基础镜像存在"
echo ""

# 选择构建目标
echo "2. 选择构建目标:"
echo "   1) 只构建后端"
echo "   2) 只构建前端"
echo "   3) 构建后端和前端"
echo "   4) 构建所有并启动服务"
read -p "   请选择 (1-4): " choice

case $choice in
    1)
        echo "   构建后端镜像..."
        docker build -f docker/Dockerfile.backend -t docker-backend:latest backend
        ;;
    2)
        echo "   构建前端镜像..."
        docker build -f docker/Dockerfile.frontend -t docker-frontend:latest \
            --build-arg VITE_API_BASE_URL=http://localhost:8000 frontend
        ;;
    3)
        echo "   构建后端镜像..."
        docker build -f docker/Dockerfile.backend -t docker-backend:latest backend
        echo "   构建前端镜像..."
        docker build -f docker/Dockerfile.frontend -t docker-frontend:latest \
            --build-arg VITE_API_BASE_URL=http://localhost:8000 frontend
        ;;
    4)
        echo "   构建后端镜像..."
        docker build -f docker/Dockerfile.backend -t docker-backend:latest backend
        echo "   构建前端镜像..."
        docker build -f docker/Dockerfile.frontend -t docker-frontend:latest \
            --build-arg VITE_API_BASE_URL=http://localhost:8000 frontend
        echo "   启动服务..."
        docker-compose -f docker/docker-compose.yml up -d
        echo "   ✅ 服务启动成功！"
        echo "   访问地址："
        echo "     前端: http://localhost:3000"
        echo "     后端: http://localhost:8000"
        ;;
    *)
        echo "   无效选择"
        exit 1
        ;;
esac

echo ""
echo "=== 构建完成 ===" 