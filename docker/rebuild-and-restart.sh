#!/bin/bash

echo "停止现有容器..."
docker-compose down

echo "重新构建前端容器..."
docker-compose build --no-cache frontend

echo "启动所有服务..."
docker-compose up -d

echo "查看服务状态..."
docker-compose ps

echo "查看前端容器日志..."
docker-compose logs frontend 