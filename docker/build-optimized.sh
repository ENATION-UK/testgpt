#!/bin/bash

# ========================================
# 代理配置 - 修改这里的代理地址
# ========================================
PROXY_HOST="192.168.2.210"
PROXY_PORT="7012"
HTTP_PROXY="http://${PROXY_HOST}:${PROXY_PORT}"
HTTPS_PROXY="http://${PROXY_HOST}:${PROXY_PORT}"
ALL_PROXY="socks5://${PROXY_HOST}:${PROXY_PORT}"

# ========================================
# 构建配置
# ========================================
BUILD_BACKEND=true
BUILD_FRONTEND=true

# ========================================
# 函数定义
# ========================================

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -a, --all          构建所有镜像 (默认)"
    echo "  -b, --backend      仅构建后端镜像"
    echo "  -f, --frontend     仅构建前端镜像"
    echo "  -h, --help         显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                 # 构建所有镜像"
    echo "  $0 -b              # 仅构建后端"
    echo "  $0 -f              # 仅构建前端"
    echo "  $0 --backend       # 仅构建后端"
}

# 设置代理环境变量
setup_proxy() {
    echo "1. 设置代理环境变量..."
    export http_proxy=$HTTP_PROXY
    export https_proxy=$HTTPS_PROXY
    export all_proxy=$ALL_PROXY
    
    echo "   ✓ 代理配置:"
    echo "     http_proxy: $http_proxy"
    echo "     https_proxy: $https_proxy"
    echo "     all_proxy: $all_proxy"
    echo ""
}

# 检查Docker状态
check_docker() {
    echo "2. 检查Docker状态..."
    if ! docker version > /dev/null 2>&1; then
        echo "   ❌ Docker未运行，请先启动Docker Desktop"
        exit 1
    fi
    echo "   ✓ Docker正在运行"
    echo ""
}

# 停止旧容器
stop_containers() {
    echo "3. 停止正在运行的容器..."
    docker-compose -f docker/docker-compose.yml down > /dev/null 2>&1
    echo "   ✓ 已停止旧容器"
    echo ""
}

# 构建后端镜像
build_backend() {
    if [ "$BUILD_BACKEND" = true ]; then
        echo "4. 构建后端镜像..."
        echo "   基于基础镜像，构建速度会很快..."
        echo ""
        
        if docker build \
            --build-arg http_proxy=$HTTP_PROXY \
            --build-arg https_proxy=$HTTPS_PROXY \
            --build-arg all_proxy=$ALL_PROXY \
            -f docker/Dockerfile.backend -t docker-backend:latest backend; then
            echo "   ✅ 后端镜像构建成功！"
            echo ""
        else
            echo "   ❌ 后端镜像构建失败"
            exit 1
        fi
    fi
}

# 构建前端镜像
build_frontend() {
    if [ "$BUILD_FRONTEND" = true ]; then
        echo "5. 构建前端镜像..."
        echo ""
        
        if docker build \
            --build-arg http_proxy=$HTTP_PROXY \
            --build-arg https_proxy=$HTTPS_PROXY \
            --build-arg all_proxy=$ALL_PROXY \
            -f docker/Dockerfile.frontend -t docker-frontend:latest frontend; then
            echo "   ✅ 前端镜像构建成功！"
            echo ""
        else
            echo "   ❌ 前端镜像构建失败"
            exit 1
        fi
    fi
}

# 显示构建完成信息
show_completion_info() {
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
}

# ========================================
# 主程序
# ========================================

echo "=== 构建docker ==="
echo "时间: $(date)"
echo ""

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--all)
            BUILD_BACKEND=true
            BUILD_FRONTEND=true
            shift
            ;;
        -b|--backend)
            BUILD_BACKEND=true
            BUILD_FRONTEND=false
            shift
            ;;
        -f|--frontend)
            BUILD_BACKEND=false
            BUILD_FRONTEND=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 显示构建计划
echo "构建计划:"
if [ "$BUILD_BACKEND" = true ] && [ "$BUILD_FRONTEND" = true ]; then
    echo "  ✓ 后端镜像"
    echo "  ✓ 前端镜像"
elif [ "$BUILD_BACKEND" = true ]; then
    echo "  ✓ 后端镜像"
    echo "  ✗ 前端镜像 (跳过)"
elif [ "$BUILD_FRONTEND" = true ]; then
    echo "  ✗ 后端镜像 (跳过)"
    echo "  ✓ 前端镜像"
fi
echo ""

# 执行构建流程
setup_proxy
check_docker
stop_containers
build_backend
build_frontend
show_completion_info 