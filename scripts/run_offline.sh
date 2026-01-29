#!/bin/bash
# msearch 离线模式启动脚本

# 设置离线环境变量
export HF_HOME="$(dirname "$0")/../data/models"
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HUB_OFFLINE=1
export INFINITY_LOCAL_MODE=1

# 激活虚拟环境
source "$(dirname "$0")/../venv/bin/activate"

# 启动主程序
python "$(dirname "$0")/../src/main.py"
