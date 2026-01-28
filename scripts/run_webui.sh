#!/bin/bash
# msearch WebUI 启动/停止脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# PID文件
PID_FILE="$PROJECT_ROOT/data/pids/msearch-webui.pid"
LOG_FILE="$PROJECT_ROOT/logs/webui.log"

print_msg() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo -e "\n${CYAN}=====================================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}=====================================================${NC}"
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
    print_header "停止 WebUI 服务"
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_msg "$YELLOW" "正在停止 WebUI 服务 (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            
            # 等待进程结束
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                ((count++))
            done
            
            # 强制杀死
            if kill -0 "$pid" 2>/dev/null; then
                print_msg "$YELLOW" "强制杀死进程..."
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
        rm -f "$PID_FILE"
        print_msg "$GREEN" "✓ WebUI 服务已停止"
    else
        print_msg "$YELLOW" "WebUI 服务未运行"
    fi
    
    # 清理残留进程
    print_msg "$BLUE" "清理残留进程..."
    pkill -f "src/webui/app.py" 2>/dev/null || true
    print_msg "$GREEN" "✓ 残留进程已清理"
}

# 启动服务
start() {
    print_header "启动 msearch WebUI"
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_msg "$YELLOW" "WebUI 服务已在运行 (PID: $pid)"
        print_msg "$BLUE" "WebUI 地址: http://localhost:7860"
        return 0
    fi
    
    # 激活虚拟环境
    print_msg "$BLUE" "[1/4] 激活虚拟环境..."
    VENV_PATH="$PROJECT_ROOT/venv"
    if [ ! -d "$VENV_PATH" ]; then
        print_msg "$RED" "错误: 虚拟环境不存在"
        print_msg "$YELLOW" "请先运行: bash scripts/install.sh"
        exit 1
    fi
    source "$VENV_PATH/bin/activate"
    print_msg "$GREEN" "✓ 虚拟环境已激活"
    
    # 检查依赖
    print_msg "$BLUE" "[2/4] 检查依赖..."
    if ! python -c "import gradio" 2>/dev/null; then
        print_msg "$YELLOW" "缺少 gradio 依赖，正在安装..."
        pip install gradio
        print_msg "$GREEN" "✓ gradio 安装完成"
    else
        print_msg "$GREEN" "✓ 依赖检查通过"
    fi
    
    # 设置环境变量
    print_msg "$BLUE" "[3/4] 配置环境变量..."
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    export MSEARCH_CONFIG="$PROJECT_ROOT/config/config.yml"
    export MSEARCH_DATA_DIR="$PROJECT_ROOT/data"
    export MSEARCH_LOG_LEVEL="INFO"
    
    # 离线模式配置
    export HF_HOME="$PROJECT_ROOT/data/models"
    export TRANSFORMERS_OFFLINE=1
    export HF_DATASETS_OFFLINE=1
    export HF_HUB_OFFLINE=1
    export HF_HUB_DISABLE_IMPORT_ERROR=1
    
    print_msg "$GREEN" "✓ 环境变量配置完成"
    print_msg "$BLUE" "  - PYTHONPATH: $PYTHONPATH"
    print_msg "$BLUE" "  - MSEARCH_CONFIG: $MSEARCH_CONFIG"
    print_msg "$BLUE" "  - 离线模式: 已启用"
    
    # 创建日志目录
    print_msg "$BLUE" "[4/4] 准备启动环境..."
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/data/pids"
    mkdir -p "$PROJECT_ROOT/data/models"
    mkdir -p "$PROJECT_ROOT/testdata"
    
    # 启动 WebUI
    print_msg "$BLUE" "启动 WebUI 服务..."
    cd "$PROJECT_ROOT"
    
    # 使用端口 7860 避免冲突
    export GRADIO_SERVER_PORT=7860
    
    nohup python src/webui/app.py > "$LOG_FILE" 2>&1 &
    
    local pid=$!
    echo "$pid" > "$PID_FILE"
    
    print_msg "$BLUE" "等待 WebUI 服务启动..."
    sleep 5
    
    if kill -0 "$pid" 2>/dev/null; then
        print_msg "$GREEN" "✓ WebUI 服务启动成功 (PID: $pid)"
        print_msg "$GREEN" "✓ WebUI 地址: http://localhost:7860"
        print_msg "$GREEN" "✓ 日志文件: $LOG_FILE"
        
        # 显示使用提示
        print_msg "$YELLOW" ""
        print_msg "$YELLOW" "使用提示:"
        print_msg "$YELLOW" "  1. 在浏览器中打开 WebUI 地址: http://localhost:7860"
        print_msg "$YELLOW" "  2. 输入关键词进行搜索测试"
        print_msg "$YELLOW" "  3. 上传图片/音频/视频进行多模态搜索"
        print_msg "$YELLOW" "  4. 查看搜索结果和性能"
    else
        print_msg "$RED" "✗ WebUI 服务启动失败"
        print_msg "$YELLOW" "查看日志: tail -f $LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# 显示状态
status() {
    print_header "WebUI 服务状态"
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_msg "$GREEN" "✓ WebUI 服务运行中"
        print_msg "$BLUE" "  - PID: $pid"
        print_msg "$BLUE" "  - 地址: http://localhost:7860"
        print_msg "$BLUE" "  - 日志: $LOG_FILE"
    else
        print_msg "$YELLOW" "✗ WebUI 服务未运行"
        print_msg "$YELLOW" "  启动服务: bash scripts/run_webui.sh start"
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
        status
        ;;
    *)
        print_header "使用帮助"
        print_msg "$BLUE" "用法: $0 {start|stop|restart|status}"
        print_msg "$BLUE" ""
        print_msg "$BLUE" "选项:"
        print_msg "$BLUE" "  start    - 启动 WebUI 服务"
        print_msg "$BLUE" "  stop     - 停止 WebUI 服务"
        print_msg "$BLUE" "  restart  - 重启 WebUI 服务"
        print_msg "$BLUE" "  status   - 查看 WebUI 服务状态"
        print_msg "$BLUE" ""
        print_msg "$BLUE" "示例:"
        print_msg "$BLUE" "  $0 start     # 启动服务"
        print_msg "$BLUE" "  $0 stop      # 停止服务"
        print_msg "$BLUE" "  $0 status    # 查看状态"
        exit 1
        ;;
esac
