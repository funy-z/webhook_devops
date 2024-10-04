#!/bin/bash

if [ ! -d ".venv"]; then
  echo ".venv 不存在，正在创建虚拟环境..."
  python -m venv .venv
  echo ".venv 虚拟环境创建完成!"
fi

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install --no-cache-dir -r requirements.txt

nohup python app/main.py > output.log 2>&1 &

echo "FastAPI 服务已启动"
