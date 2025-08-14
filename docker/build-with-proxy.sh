#!/bin/bash

# Docker构建脚本（带代理配置）
# 用于在中国大陆环境下构建Docker镜像

echo "=== Docker 代理构建脚本 ==="
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
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker version > /dev/null 2>&1; then
        echo "   ✓ Docker daemon正在运行"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "   ⏳ 等待Docker启动... (尝试 $RETRY_COUNT/$MAX_RETRIES)"
        
        if [ $RETRY_COUNT -eq 1 ]; then
            echo "   启动Docker Desktop..."
            open -a Docker
        fi
        
        sleep 5
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "   ❌ Docker启动失败，请手动启动Docker Desktop"
    exit 1
fi

# 显示Docker信息
echo ""
echo "3. Docker信息:"
docker version --format '   Docker版本: {{.Client.Version}}'
echo ""

# 测试网络连接
echo "4. 测试网络连接..."
if timeout 30 docker pull hello-world > /dev/null 2>&1; then
    echo "   ✓ 网络连接正常，可以拉取镜像"
else
    echo "   ⚠️  网络连接可能有问题，但继续尝试构建"
fi
echo ""

# 清理旧镜像
echo "5. 清理旧镜像..."
docker-compose -f docker/docker-compose.yml down > /dev/null 2>&1
echo "   ✓ 已停止旧容器"
echo ""

# 构建镜像
echo "6. 开始构建镜像..."
echo "   这可能需要几分钟时间，请耐心等待..."
echo ""

if docker-compose -f docker/docker-compose.yml build --no-cache; then
    echo ""
    echo "✅ 镜像构建成功！"
    echo ""
    
    # 启动服务
    echo "7. 启动服务..."
    if docker-compose -f docker/docker-compose.yml up -d; then
        echo "✅ 服务启动成功！"
        echo ""
        echo "访问地址："
        echo "  前端: http://localhost:3000"
        echo "  后端: http://localhost:8000"
        echo ""
        echo "查看服务状态:"
        docker-compose -f docker/docker-compose.yml ps
    else
        echo "❌ 服务启动失败"
        exit 1
    fi
else
    echo ""
    echo "❌ 镜像构建失败"
    echo ""
    echo "故障排除建议："
    echo "1. 检查代理服务器 192.168.2.210:7012 是否可访问"
    echo "2. 确认网络连接正常"
    echo "3. 重启Docker Desktop"
    echo "4. 查看详细错误信息"
    exit 1
fi

echo ""
echo "=== 构建完成 ==="