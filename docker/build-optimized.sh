#!/bin/bash

# 优化的Docker构建脚本
# 先构建基础镜像（包含系统依赖和Playwright），再构建应用镜像

echo "=== 优化的Docker构建脚本 ==="
echo "时间: $(date)"
echo ""

# 设置代理环境变量
echo "1. 设置代理环境变量..."
export https_proxy=http://192.168.2.210:7012
export http_proxy=http://192.168.2.210:7012
export all_proxy=socks5://192.168.2.210:7012

echo "   ✓ 代理配置:"
echo "     http_proxy: $http_proxy"
echo "     https_proxy: $https_proxy"
echo "     all_proxy: $all_proxy"
echo ""

# 检查Docker状态
echo "2. 检查Docker状态..."
if ! docker version > /dev/null 2>&1; then
    echo "   ❌ Docker未运行，请先启动Docker Desktop"
    exit 1
fi
echo "   ✓ Docker正在运行"
echo ""

echo "5. 停止正在运行的容器..."
docker-compose -f docker/docker-compose.yml down > /dev/null 2>&1
echo "   ✓ 已停止旧容器"
echo ""

# 构建基础镜像
echo "3. 构建基础镜像 (autotest-base)..."
echo "   这可能需要几分钟时间，但只需要构建一次..."
echo ""

if docker build  \
  --build-arg http_proxy=http://192.168.2.210:7012 \
  --build-arg https_proxy=http://192.168.2.210:7012 \
  --build-arg all_proxy=socks5://192.168.2.210:7012 \
  -f docker/Dockerfile.base -t autotest-base:latest .; then
    echo "   ✅ 基础镜像构建成功！"
    echo ""
else
    echo "   ❌ 基础镜像构建失败"
    exit 1
fi

# 构建后端镜像
echo "4. 构建后端镜像..."
echo "   基于基础镜像，构建速度会很快..."
echo ""

if docker build  \
  --build-arg http_proxy=http://192.168.2.210:7012 \
  --build-arg https_proxy=http://192.168.2.210:7012 \
  --build-arg all_proxy=socks5://192.168.2.210:7012 \
  -f docker/Dockerfile.backend -t docker-backend:latest backend; then
    echo "   ✅ 后端镜像构建成功！"
    echo ""
else
    echo "   ❌ 后端镜像构建失败"
    exit 1
fi

# 构建前端镜像
echo "5. 构建前端镜像..."
echo ""

if docker build  \
  --build-arg http_proxy=http://192.168.2.210:7012 \
  --build-arg https_proxy=http://192.168.2.210:7012 \
  --build-arg all_proxy=socks5://192.168.2.210:7012 \
  -f docker/Dockerfile.frontend -t docker-frontend:latest frontend; then
    echo "   ✅ 前端镜像构建成功！"
    echo ""
else
    echo "   ❌ 前端镜像构建失败"
    exit 1
fi

# 启动服务
# echo "6. 启动服务..."
# if docker-compose -f docker/docker-compose.yml up -d; then
#     echo "   ✅ 服务启动成功！"
#     echo ""
#     echo "访问地址："
#     echo "  前端: http://localhost:3000"
#     echo "  后端: http://localhost:8000"
#     echo ""
#     echo "查看服务状态:"
#     docker-compose -f docker/docker-compose.yml ps
# else
#     echo "   ❌ 服务启动失败"
#     exit 1
# fi

echo ""
echo "=== 构建完成 ==="
echo ""
echo "优势："
echo "  - 基础镜像只需构建一次，后续构建速度大大提升"
echo "  - 系统依赖和Playwright浏览器已预装"
echo "  - 开发调试时只需重新构建应用层"
echo ""
echo "常用命令："
echo "  重新构建基础镜像: docker build -f docker/Dockerfile.base -t autotest-base:latest ."
echo "  重新构建后端: docker build -f docker/Dockerfile.backend -t docker-backend:latest ../backend"
echo "  重新构建前端: docker build -f docker/Dockerfile.frontend -t docker-frontend:latest ../frontend"
echo "  查看镜像: docker images | grep autotest" 