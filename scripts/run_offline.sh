#!/bin/bash
# msearch 离线模式启动脚本（多进程架构）

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 设置离线环境变量
export HF_HOME="$PROJECT_ROOT/data/models"
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HUB_OFFLINE=1
export INFINITY_LOCAL_MODE=1
export NO_PROXY='*'
export no_proxy='*'

# 激活虚拟环境
source venv/bin/activate

# 启动多进程主程序
python src/main_multiprocess.py
