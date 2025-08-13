#!/bin/bash

# 获取环境变量
API_BASE_URL=${VITE_API_BASE_URL:-"/api"}

echo "Starting frontend with API_BASE_URL: $API_BASE_URL"

# 创建运行时配置文件
cat > /app/dist/config.js << EOF
window.__APP_CONFIG__ = {
  API_BASE_URL: '$API_BASE_URL'
};
EOF

# 启动服务
exec serve -s dist -l 3000
