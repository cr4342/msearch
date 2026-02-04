#!/bin/bash
# msearch WebUI 启动/停止脚本 - 同时启动后端API和WebUI

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
BACKEND_PID_FILE="$PROJECT_ROOT/data/pids/msearch-backend.pid"
WEBUI_PID_FILE="$PROJECT_ROOT/data/pids/msearch-webui.pid"
LOG_DIR="$PROJECT_ROOT/logs"
BACKEND_LOG_FILE="$LOG_DIR/backend.log"
WEBUI_LOG_FILE="$LOG_DIR/webui.log"

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

# 检查后端是否运行
is_backend_running() {
    if [ -f "$BACKEND_PID_FILE" ]; then
        local pid=$(cat "$BACKEND_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# 检查WebUI是否运行
is_webui_running() {
    if [ -f "$WEBUI_PID_FILE" ]; then
        local pid=$(cat "$WEBUI_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# 检查所有服务是否运行
is_all_running() {
    if is_backend_running && is_webui_running; then
        return 0
    fi
    return 1
}

# 停止服务
stop() {
    print_header "停止 msearch 服务"

    # 停止WebUI
    if [ -f "$WEBUI_PID_FILE" ]; then
        local pid=$(cat "$WEBUI_PID_FILE")
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
                print_msg "$YELLOW" "强制杀死 WebUI 进程..."
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
        rm -f "$WEBUI_PID_FILE"
        print_msg "$GREEN" "✓ WebUI 服务已停止"
    else
        print_msg "$YELLOW" "WebUI 服务未运行"
    fi

    # 停止后端API
    if [ -f "$BACKEND_PID_FILE" ]; then
        local pid=$(cat "$BACKEND_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_msg "$YELLOW" "正在停止 后端API 服务 (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            
            # 等待进程结束
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                ((count++))
            done
            
            # 强制杀死
            if kill -0 "$pid" 2>/dev/null; then
                print_msg "$YELLOW" "强制杀死后端API进程..."
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
        rm -f "$BACKEND_PID_FILE"
        print_msg "$GREEN" "✓ 后端API服务已停止"
    else
        print_msg "$YELLOW" "后端API服务未运行"
    fi
    
    # 清理残留进程
    print_msg "$BLUE" "清理残留进程..."
    pkill -f "src/webui/app.py" 2>/dev/null || true
    pkill -f "src/api_server.py" 2>/dev/null || true
    pkill -f "src/main.py" 2>/dev/null || true
    print_msg "$GREEN" "✓ 残留进程已清理"
}

# 启动服务
start() {
    print_header "启动 msearch 完整服务"

    # 检查是否已在运行
    if is_all_running; then
        print_msg "$YELLOW" "所有服务已在运行"
        status
        return 0
    fi
    
    # 激活虚拟环境
    print_msg "$BLUE" "[1/5] 激活虚拟环境..."
    VENV_PATH="$PROJECT_ROOT/venv"
    if [ ! -d "$VENV_PATH" ]; then
        print_msg "$RED" "错误: 虚拟环境不存在"
        print_msg "$YELLOW" "请先运行: bash scripts/install.sh"
        exit 1
    fi
    source "$VENV_PATH/bin/activate"
    print_msg "$GREEN" "✓ 虚拟环境已激活"
    
    # 检查依赖
    print_msg "$BLUE" "[2/5] 检查依赖..."
    if ! python -c "import gradio" 2>/dev/null; then
        print_msg "$YELLOW" "缺少 gradio 依赖，正在安装..."
        pip install gradio
        print_msg "$GREEN" "✓ gradio 安装完成"
    fi
    
    if ! python -c "import fastapi" 2>/dev/null; then
        print_msg "$YELLOW" "缺少 fastapi 依赖，正在安装..."
        pip install fastapi uvicorn
        print_msg "$GREEN" "✓ fastapi 安装完成"
    fi
    
    print_msg "$GREEN" "✓ 依赖检查通过"
    
    # 设置环境变量
    print_msg "$BLUE" "[3/5] 配置环境变量..."
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
    print_msg "$BLUE" "[4/5] 准备启动环境..."
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/data/pids"
    mkdir -p "$PROJECT_ROOT/data/models"
    mkdir -p "$PROJECT_ROOT/testdata"
    
    # 启动后端API服务
    if ! is_backend_running; then
        print_msg "$BLUE" "[5/5] 启动后端API服务..."
        cd "$PROJECT_ROOT"
        
        nohup python src/api_server.py > "$BACKEND_LOG_FILE" 2>&1 &
        
        local backend_pid=$!
        echo "$backend_pid" > "$BACKEND_PID_FILE"
        
        print_msg "$BLUE" "等待后端API服务启动..."
        sleep 8  # 等待后端服务充分启动
        
        if kill -0 "$backend_pid" 2>/dev/null; then
            print_msg "$GREEN" "✓ 后端API服务启动成功 (PID: $backend_pid)"
            print_msg "$GREEN" "✓ API地址: http://localhost:8000"
        else
            print_msg "$RED" "✗ 后端API服务启动失败"
            print_msg "$YELLOW" "查看日志: tail -f $BACKEND_LOG_FILE"
            rm -f "$BACKEND_PID_FILE"
            exit 1
        fi
    else
        local pid=$(cat "$BACKEND_PID_FILE")
        print_msg "$YELLOW" "后端API服务已在运行 (PID: $pid)"
    fi
    
    # 等待后端服务稳定
    sleep 2
    
    # 启动WebUI服务
    if ! is_webui_running; then
        print_msg "$BLUE" "启动 WebUI 服务..."
        cd "$PROJECT_ROOT"
        
        # 使用端口 7860 避免冲突
        export GRADIO_SERVER_PORT=7860
        
        nohup python src/webui/app.py > "$WEBUI_LOG_FILE" 2>&1 &
        
        local webui_pid=$!
        echo "$webui_pid" > "$WEBUI_PID_FILE"
        
        print_msg "$BLUE" "等待 WebUI 服务启动..."
        sleep 5
        
        if kill -0 "$webui_pid" 2>/dev/null; then
            print_msg "$GREEN" "✓ WebUI 服务启动成功 (PID: $webui_pid)"
            print_msg "$GREEN" "✓ WebUI 地址: http://localhost:7860"
            print_msg "$GREEN" "✓ 日志文件: $WEBUI_LOG_FILE"
        else
            print_msg "$RED" "✗ WebUI 服务启动失败"
            print_msg "$YELLOW" "查看日志: tail -f $WEBUI_LOG_FILE"
            rm -f "$WEBUI_PID_FILE"
            exit 1
        fi
    else
        local pid=$(cat "$WEBUI_PID_FILE")
        print_msg "$YELLOW" "WebUI 服务已在运行 (PID: $pid)"
    fi
    
    print_msg "$GREEN" ""
    print_msg "$GREEN" "✓ msearch 完整服务启动成功！"
    
    # 显示使用提示
    print_msg "$YELLOW" ""
    print_msg "$YELLOW" "使用提示:"
    print_msg "$YELLOW" "  1. WebUI界面: http://localhost:7860"
    print_msg "$YELLOW" "  2. API接口: http://localhost:8000/docs"
    print_msg "$YELLOW" "  3. 文件监控: 自动监控 testdata 目录"
    print_msg "$YELLOW" "  4. 任务管理: 通过WebUI查看索引任务"
    print_msg "$YELLOW" ""
    print_msg "$YELLOW" "注意: 系统会自动监控 testdata 目录中的文件变化并创建索引任务"
}

# 显示状态
status() {
    print_header "msearch 服务状态"
    
    print_msg "$BLUE" "后端API服务状态:"
    if is_backend_running; then
        local pid=$(cat "$BACKEND_PID_FILE")
        print_msg "$GREEN" "  ✓ 运行中 (PID: $pid)"
        print_msg "$BLUE" "    - 地址: http://localhost:8000"
        print_msg "$BLUE" "    - 日志: $BACKEND_LOG_FILE"
    else
        print_msg "$YELLOW" "  ✗ 未运行"
        print_msg "$BLUE" "    - 启动命令: bash $0 start"
    fi
    
    print_msg "$BLUE" "WebUI服务状态:"
    if is_webui_running; then
        local pid=$(cat "$WEBUI_PID_FILE")
        print_msg "$GREEN" "  ✓ 运行中 (PID: $pid)"
        print_msg "$BLUE" "    - 地址: http://localhost:7860"
        print_msg "$BLUE" "    - 日志: $WEBUI_LOG_FILE"
    else
        print_msg "$YELLOW" "  ✗ 未运行"
        print_msg "$BLUE" "    - 启动命令: bash $0 start"
    fi
    
    if is_all_running; then
        print_msg "$GREEN" ""
        print_msg "$GREEN" "✓ 所有服务正常运行"
        print_msg "$GREEN" "✓ WebUI和API服务都在运行"
    else
        print_msg "$YELLOW" ""
        print_msg "$YELLOW" "✗ 部分或全部服务未运行"
        print_msg "$YELLOW" "  启动服务: bash $0 start"
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
        sleep 3
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
        print_msg "$BLUE" "  start    - 启动完整服务 (后端API + WebUI)"
        print_msg "$BLUE" "  stop     - 停止所有服务"
        print_msg "$BLUE" "  restart  - 重启所有服务"
        print_msg "$BLUE" "  status   - 查看服务状态"
        print_msg "$BLUE" ""
        print_msg "$BLUE" "示例:"
        print_msg "$BLUE" "  $0 start     # 启动完整服务"
        print_msg "$BLUE" "  $0 stop      # 停止所有服务"
        print_msg "$BLUE" "  $0 status    # 查看状态"
        exit 1
        ;;
esac
