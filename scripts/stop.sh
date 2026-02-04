#!/bin/bash
###############################################################################
# msearch 停止脚本
# 一键停止所有msearch服务（主程序、API服务、WebUI）
###############################################################################

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# PID文件路径
MAIN_PID_FILE="$PROJECT_ROOT/data/pids/msearch-main.pid"
API_PID_FILE="$PROJECT_ROOT/data/pids/msearch-api.pid"
WEBUI_PID_FILE="$PROJECT_ROOT/data/pids/msearch-webui.pid"

# 创建PID目录
mkdir -p "$PROJECT_ROOT/data/pids"

print_info "========================================"
print_info "  msearch 多模态搜索系统 - 停止"
print_info "========================================"
print_info ""

# 停止主程序
stop_main() {
    print_info "检查主程序..."
    
    # 从PID文件读取
    if [ -f "$MAIN_PID_FILE" ]; then
        local pid=$(cat "$MAIN_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_info "停止主程序 (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            
            # 等待进程结束
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                ((count++))
                echo -n "."
            done
            echo ""
            
            # 强制杀死
            if kill -0 "$pid" 2>/dev/null; then
                print_warning "主程序未响应，强制停止..."
                kill -9 "$pid" 2>/dev/null || true
            fi
            
            print_success "主程序已停止"
        else
            print_warning "主程序PID文件存在但进程未运行"
        fi
        rm -f "$MAIN_PID_FILE"
    else
        # 通过进程名查找
        local pids=$(pgrep -f "python src/main.py" || true)
        if [ -n "$pids" ]; then
            print_info "停止主程序进程: $pids"
            echo "$pids" | xargs kill 2>/dev/null || true
            sleep 2
            
            # 强制杀死
            pids=$(pgrep -f "python src/main.py" || true)
            if [ -n "$pids" ]; then
                print_warning "主程序未响应，强制停止..."
                echo "$pids" | xargs kill -9 2>/dev/null || true
            fi
            
            print_success "主程序已停止"
        else
            print_info "主程序未运行"
        fi
    fi
}

# 停止API服务
stop_api() {
    print_info "检查API服务..."
    
    # 从PID文件读取
    if [ -f "$API_PID_FILE" ]; then
        local pid=$(cat "$API_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_info "停止API服务 (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            
            # 等待进程结束
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                ((count++))
                echo -n "."
            done
            echo ""
            
            # 强制杀死
            if kill -0 "$pid" 2>/dev/null; then
                print_warning "API服务未响应，强制停止..."
                kill -9 "$pid" 2>/dev/null || true
            fi
            
            print_success "API服务已停止"
        else
            print_warning "API服务PID文件存在但进程未运行"
        fi
        rm -f "$API_PID_FILE"
    else
        # 通过进程名查找
        local pids=$(pgrep -f "python src/api_server.py" || true)
        if [ -n "$pids" ]; then
            print_info "停止API服务进程: $pids"
            echo "$pids" | xargs kill 2>/dev/null || true
            sleep 2
            
            # 强制杀死
            pids=$(pgrep -f "python src/api_server.py" || true)
            if [ -n "$pids" ]; then
                print_warning "API服务未响应，强制停止..."
                echo "$pids" | xargs kill -9 2>/dev/null || true
            fi
            
            print_success "API服务已停止"
        else
            print_info "API服务未运行"
        fi
    fi
}

# 停止WebUI
stop_webui() {
    print_info "检查WebUI..."
    
    # 从PID文件读取
    if [ -f "$WEBUI_PID_FILE" ]; then
        local pid=$(cat "$WEBUI_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_info "停止WebUI (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            
            # 等待进程结束
            local count=0
            while [ $count -lt 5 ]; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    break
                fi
                sleep 1
                ((count++))
                echo -n "."
            done
            echo ""
            
            # 强制杀死
            if kill -0 "$pid" 2>/dev/null; then
                print_warning "WebUI未响应，强制停止..."
                kill -9 "$pid" 2>/dev/null || true
            fi
            
            print_success "WebUI已停止"
        else
            print_warning "WebUI PID文件存在但进程未运行"
        fi
        rm -f "$WEBUI_PID_FILE"
    else
        # 通过端口查找
        local pid=$(lsof -t -i:8080 2>/dev/null || true)
        if [ -n "$pid" ]; then
            print_info "停止WebUI (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            sleep 2
            
            # 强制杀死
            pid=$(lsof -t -i:8080 2>/dev/null || true)
            if [ -n "$pid" ]; then
                print_warning "WebUI未响应，强制停止..."
                kill -9 "$pid" 2>/dev/null || true
            fi
            
            print_success "WebUI已停止"
        else
            print_info "WebUI未运行"
        fi
    fi
}

# 停止所有Python进程（可选）
stop_all_python() {
    print_info "检查其他msearch相关进程..."
    
    local pids=$(pgrep -f "msearch" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        print_warning "发现其他msearch相关进程: $pids"
        read -p "是否停止这些进程? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "停止进程: $pids"
            echo "$pids" | xargs kill 2>/dev/null || true
            sleep 2
            
            # 强制杀死
            pids=$(pgrep -f "msearch" 2>/dev/null || true)
            if [ -n "$pids" ]; then
                echo "$pids" | xargs kill -9 2>/dev/null || true
            fi
            
            print_success "所有msearch进程已停止"
        else
            print_info "跳过"
        fi
    else
        print_info "没有其他msearch相关进程"
    fi
}

# 清理端口占用
cleanup_ports() {
    print_info "检查端口占用..."
    
    local ports=(8000 8080)
    for port in "${ports[@]}"; do
        local pid=$(lsof -t -i:$port 2>/dev/null || true)
        if [ -n "$pid" ]; then
            print_warning "端口 $port 被进程 $pid 占用"
            read -p "是否停止该进程? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                kill "$pid" 2>/dev/null || true
                sleep 1
                print_success "端口 $port 已释放"
            else
                print_info "跳过端口 $port"
            fi
        fi
    done
}

# 显示停止摘要
show_summary() {
    print_info ""
    print_info "========================================"
    print_success "msearch 服务停止完成"
    print_info "========================================"
    print_info ""
    print_info "PID文件已清理:"
    print_info "  - $MAIN_PID_FILE"
    print_info "  - $API_PID_FILE"
    print_info "  - $WEBUI_PID_FILE"
    print_info ""
    print_info "日志文件保留:"
    print_info "  - logs/main.log"
    print_info "  - logs/api.log"
    print_info "  - logs/webui.log"
    print_info ""
    print_info "如需重新启动，请运行:"
    print_info "  bash scripts/run.sh"
    print_info "========================================"
}

# 解析命令行参数
FORCE=false
CLEAN_PORTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE=true
            shift
            ;;
        -p|--cleanup-ports)
            CLEAN_PORTS=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -f, --force         强制停止所有进程"
            echo "  -p, --cleanup-ports 清理端口占用"
            echo "  -h, --help          显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                  # 停止所有服务"
            echo "  $0 -f              # 强制停止所有服务"
            echo "  $0 -p              # 停止服务并清理端口"
            exit 0
            ;;
        *)
            print_error "未知参数: $1"
            echo "使用 -h 或 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 执行停止操作
print_info "开始停止msearch服务..."
print_info ""

stop_main
echo ""

stop_api
echo ""

stop_webui
echo ""

if [ "$FORCE" = true ]; then
    stop_all_python
    echo ""
fi

if [ "$CLEAN_PORTS" = true ]; then
    cleanup_ports
    echo ""
fi

show_summary

exit 0
