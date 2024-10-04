#!/bin/bash

# 查找并停止已经运行的 FastAPI 服务
PID=$(ps aux | grep 'python app/main.py' | grep -v grep | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "正在停止 FastAPI 服务 (PID: $PID)..."
    kill -9 $PID
    echo "FastAPI 服务已停止"
else
    echo "没有找到正在运行的 FastAPI 服务"
fi
