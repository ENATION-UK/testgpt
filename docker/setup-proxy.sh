#!/bin/bash

# Docker代理配置脚本
# 用于在中国大陆环境下配置Docker代理

echo "正在配置Docker代理..."

# 设置代理环境变量
export https_proxy=http://192.168.2.99:7012
export http_proxy=http://192.168.2.99:7012
export all_proxy=socks5://192.168.2.99:7012

echo "代理环境变量已设置:"
echo "  http_proxy: $http_proxy"
echo "  https_proxy: $https_proxy"
echo "  all_proxy: $all_proxy"

# 创建Docker daemon配置目录（如果不存在）
DOCKER_CONFIG_DIR="$HOME/.docker"
mkdir -p "$DOCKER_CONFIG_DIR"

# 创建Docker daemon配置文件
cat > "$DOCKER_CONFIG_DIR/config.json" << EOF
{
  "proxies": {
    "default": {
      "httpProxy": "http://192.168.2.99:7012",
      "httpsProxy": "http://192.168.2.99:7012",
      "noProxy": "localhost,127.0.0.1,::1"
    }
  }
}
EOF

echo "Docker daemon配置已更新: $DOCKER_CONFIG_DIR/config.json"

# 重启Docker服务的提示
echo ""
echo "请注意:"
echo "1. 需要重启Docker Desktop应用以使代理配置生效"
echo "2. 或者您可以尝试以下命令重启Docker daemon:"
echo "   sudo systemctl restart docker  # Linux系统"
echo "   brew services restart docker  # macOS with Homebrew"
echo ""
echo "3. 重启后，您可以运行以下命令验证代理是否生效:"
echo "   docker pull hello-world"
echo ""
echo "4. 然后重新构建项目镜像:"
echo "   docker-compose -f docker/docker-compose.yml build --no-cache"