#!/bin/bash

# 启动Xvfb虚拟显示
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
export DISPLAY=:99

# 等待Xvfb启动
sleep 2

# 启动后端服务
cd /app
python run.py 