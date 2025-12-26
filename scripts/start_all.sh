#!/bin/bash
# MSearch完整启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 项目根目录
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 创建必要的目录
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/data"

# 激活虚拟环境（如果存在）
if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "激活虚拟环境..."
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# 设置环境变量
export PYTHONPATH="$PROJECT_ROOT"
export PYTHONWARNINGS=ignore
export KMP_DUPLICATE_LIB_OK=TRUE

# 使用stop_services.py停止已运行的服务
echo "检测并停止已运行的服务..."
python3 "$SCRIPT_DIR/stop_services.py" --service api

# 显示启动信息
echo "==============================================="
echo "          MSearch 服务启动脚本                "
echo "==============================================="
echo ""
echo "启动API服务..."
echo "API地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "查看日志: tail -f $PROJECT_ROOT/logs/msearch.log"
echo "停止服务: python3 $SCRIPT_DIR/stop_services.py --service api"
echo ""

# 启动API服务（后台运行）并保存PID
cd "$PROJECT_ROOT"
python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload > "$PROJECT_ROOT/logs/api.log" 2>&1 &
API_PID=$!

# 保存PID到文件（与stop_services.py兼容）
echo "$API_PID" > "$PROJECT_ROOT/data/api.pid"

echo "API服务已启动，进程ID: $API_PID"
echo "PID文件: $PROJECT_ROOT/data/api.pid"
echo "==============================================="
