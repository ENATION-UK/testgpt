#!/bin/bash

echo "停止现有容器..."
docker-compose down

echo "重建后端镜像..."
docker-compose build backend

echo "启动服务..."
docker-compose up -d

echo "查看日志..."
docker-compose logs -f backend 