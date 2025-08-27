#!/bin/bash

echo "🧹 清理代理环境变量..."

# 清理所有代理相关的环境变量
export http_proxy=
export https_proxy=
export all_proxy=
export HTTP_PROXY=
export HTTPS_PROXY=
export ALL_PROXY=
export no_proxy=
export NO_PROXY=

# 彻底删除环境变量
unset http_proxy
unset https_proxy
unset all_proxy
unset HTTP_PROXY
unset HTTPS_PROXY
unset ALL_PROXY
unset no_proxy
unset NO_PROXY

# 从/etc/environment文件中移除代理配置（如果存在）
if [ -f /etc/environment ]; then
    sed -i '/^http_proxy=/d' /etc/environment
    sed -i '/^https_proxy=/d' /etc/environment
    sed -i '/^all_proxy=/d' /etc/environment
    sed -i '/^HTTP_PROXY=/d' /etc/environment
    sed -i '/^HTTPS_PROXY=/d' /etc/environment
    sed -i '/^ALL_PROXY=/d' /etc/environment
    sed -i '/^no_proxy=/d' /etc/environment
    sed -i '/^NO_PROXY=/d' /etc/environment
fi

# 从/etc/profile中移除代理配置（如果存在）
if [ -f /etc/profile ]; then
    sed -i '/export.*_proxy/d' /etc/profile
    sed -i '/export.*_PROXY/d' /etc/profile
fi

# 创建一个环境变量清理脚本，供新的shell会话使用
cat > /etc/profile.d/clear_proxy.sh << 'EOF'
#!/bin/bash
# 清理代理环境变量
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY no_proxy NO_PROXY
EOF
chmod +x /etc/profile.d/clear_proxy.sh

echo "✅ 代理环境变量清理完成"

# 验证清理结果
echo "🔍 验证清理结果:"
proxy_vars=(http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY no_proxy NO_PROXY)
has_proxy=false
for var in "${proxy_vars[@]}"; do
    if [ ! -z "${!var}" ]; then
        echo "   ⚠️  $var: ${!var}"
        has_proxy=true
    fi
done

if [ "$has_proxy" = false ]; then
    echo "   ✅ 所有代理环境变量已清理"
fi

echo "✨ 设置环境变量..."

# 禁用browser-use默认扩展下载（中国大陆网络环境优化）
export BROWSER_USE_DISABLE_EXTENSIONS=true
export BROWSER_USE_SKIP_EXTENSION_DOWNLOAD=true

# 禁用遥测功能
export BROWSER_USE_DISABLE_TELEMETRY=true
export POSTHOG_DISABLED=true
export DO_NOT_TRACK=1
export POSTHOG_HOST=
export POSTHOG_PROJECT_API_KEY=
export DISABLE_TELEMETRY=true
export TELEMETRY_DISABLED=true

echo "🚫 默认扩展和遥测功能已禁用"
echo ""

echo "🚀 启动 Xvfb 虚拟显示器..."
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &

echo "⏳ 等待 Xvfb 启动..."
sleep 2

echo "🎯 启动 AutoTest API 服务..."
python run.py