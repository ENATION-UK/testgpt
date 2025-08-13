#!/bin/bash

echo "测试环境变量加载..."
echo "================================"

# 加载环境变量文件
if [ -f "config.env" ]; then
    echo "发现config.env文件"
    export $(cat config.env | grep -v '^#' | xargs)
    echo "VITE_API_BASE_URL: $VITE_API_BASE_URL"
    echo "TZ: $TZ"
else
    echo "未发现config.env文件"
fi

echo ""
echo "测试docker-compose环境变量..."
echo "================================"

# 测试docker-compose是否能读取环境变量
docker-compose config | grep -A 10 -B 5 "VITE_API_BASE_URL"
