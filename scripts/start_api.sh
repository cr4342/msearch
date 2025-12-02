#!/bin/bash
# 启动MSearch API服务

# 获取脚本所在目录
SCRIPT_DIR="/data/project/msearch/scripts"

# 尝试检测项目根目录
if [ -d "/data/project/msearch/scripts/../src" ] || [ -d "/data/project/msearch/scripts/../tests" ]; then
    PROJECT_ROOT="/data/project/msearch"
else
    PROJECT_ROOT="/data/project/msearch/scripts"
fi

# 激活虚拟环境（如果存在）
if [ -d "/data/project/msearch/venv" ]; then
    echo "激活虚拟环境..."
    source "/data/project/msearch/venv/bin/activate"
fi

# 设置环境变量
export PYTHONPATH="/data/project/msearch"
export PYTHONWARNINGS=ignore
export KMP_DUPLICATE_LIB_OK=TRUE

# 检查是否有正在运行的服务
if pgrep -f "uvicorn src.api.app:app" > /dev/null; then
    echo "检测到已运行的API服务，正在停止..."
    pkill -f "uvicorn src.api.app:app"
    sleep 2
fi

echo "启动MSearch API服务..."
echo "API地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "查看日志: tail -f /data/project/msearch/logs/msearch.log"
echo "按 Ctrl+C 停止服务"
echo ""

# 启动API服务
cd "/data/project/msearch"
python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
