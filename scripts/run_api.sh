#!/bin/bash
# msearch API 服务器启动/停止脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# PID文件
PID_FILE="$PROJECT_ROOT/data/pids/msearch-api.pid"
LOG_FILE="$PROJECT_ROOT/logs/api.log"

print_msg() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 检查是否运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# 停止服务
stop() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_msg "$YELLOW" "正在停止 API 服务 (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            
            # 等待进程结束
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                ((count++))
            done
            
            # 强制杀死
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
        rm -f "$PID_FILE"
        print_msg "$GREEN" "✓ API 服务已停止"
    else
        print_msg "$YELLOW" "API 服务未运行"
    fi
    
    # 清理残留进程
    pkill -f "api_server.py" 2>/dev/null || true
}

# 启动服务
start() {
    if is_running; then
        print_msg "$YELLOW" "API 服务已在运行"
        return 0
    fi
    
    echo "========================================"
    echo "启动 msearch API 服务器"
    echo "========================================"
    echo ""
    
    # 激活虚拟环境
    echo "[1/3] 激活虚拟环境..."
    VENV_PATH="$PROJECT_ROOT/venv"
    if [ ! -d "$VENV_PATH" ]; then
        echo "错误: 虚拟环境不存在，请先运行 install.sh"
        exit 1
    fi
    source "$VENV_PATH/bin/activate"
    echo "✓ 虚拟环境已激活"
    echo ""
    
    # 设置环境变量
    echo "[2/3] 配置环境变量..."
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    export MSEARCH_CONFIG="$PROJECT_ROOT/config/config.yml"
    export MSEARCH_DATA_DIR="$PROJECT_ROOT/data"
    export MSEARCH_LOG_LEVEL="INFO"
    
    echo "✓ 环境变量配置完成"
    echo "  - PYTHONPATH: $PYTHONPATH"
    echo "  - MSEARCH_CONFIG: $MSEARCH_CONFIG"
    echo "  - MSEARCH_DATA_DIR: $MSEARCH_DATA_DIR"
    echo ""
    
    # 创建日志目录
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/data/pids"
    
    # 启动 API 服务器
    echo "[3/3] 启动 API 服务器..."
    echo ""
    cd "$PROJECT_ROOT"
    
    nohup python src/api_server.py \
        --config "$MSEARCH_CONFIG" \
        > "$LOG_FILE" 2>&1 &
    
    local pid=$!
    echo "$pid" > "$PID_FILE"
    
    sleep 2
    
    if kill -0 "$pid" 2>/dev/null; then
        echo ""
        print_msg "$GREEN" "✓ API 服务已启动 (PID: $pid)"
        print_msg "$BLUE" "  API 地址: http://localhost:8000"
        print_msg "$BLUE" "  WebUI:   http://localhost:8000/webui/index.html"
        print_msg "$BLUE" "  日志:    $LOG_FILE"
    else
        echo ""
        print_msg "$RED" "✗ API 服务启动失败"
        print_msg "$YELLOW" "查看日志: tail -f $LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# 主逻辑
case "${1:-start}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 2
        start
        ;;
    status)
        if is_running; then
            print_msg "$GREEN" "✓ API 服务运行中 (PID: $(cat $PID_FILE))"
        else
            print_msg "$YELLOW" "✗ API 服务未运行"
        fi
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
