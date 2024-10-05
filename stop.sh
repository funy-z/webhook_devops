#!/bin/bash

# 查找并停止已经运行的 FastAPI 服务及其子进程
PIDS=$(pgrep -f 'python app/main.py')

if [ -n "$PIDS" ]; then
    echo "正在停止 FastAPI 服务及其子进程 (PIDs: $PIDS)..."
    pkill -TERM -P $PIDS
    kill -9 $PIDS
    echo "FastAPI 服务及其子进程已停止"
else
    echo "没有找到正在运行的 FastAPI 服务"
fi
