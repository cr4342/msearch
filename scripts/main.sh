#!/bin/bash
# msearch 统一启动脚本
# 功能：启动 API 服务器、WebUI 和文件监控服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 默认配置
CONFIG_FILE="config/config.yml"
VENV_DIR="venv"
API_PORT=8000

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    print_message "$CYAN" "═══════════════════════════════════════════════════════════════"
    print_message "$CYAN" "  $1"
    print_message "$CYAN" "═══════════════════════════════════════════════════════════════"
    echo ""
}

# 检查 Python 环境
check_python() {
    print_header "检查 Python 环境"
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD=python3
        print_message "$GREEN" "✓ 找到 Python 3"
        python3 --version
    elif command -v python &> /dev/null; then
        PYTHON_CMD=python
        print_message "$GREEN" "✓ 找到 Python"
        python --version
    else
        print_message "$RED" "✗ 未找到 Python，请先安装 Python 3.8+"
        exit 1
    fi
}

# 检查虚拟环境
check_venv() {
    print_header "检查虚拟环境"
    
    if [ -d "$VENV_DIR" ]; then
        print_message "$GREEN" "✓ 虚拟环境存在: $VENV_DIR"
        source "$VENV_DIR/bin/activate"
        print_message "$GREEN" "✓ 虚拟环境已激活"
        PYTHON_CMD="$VENV_DIR/bin/python"
    else
        print_message "$YELLOW" "⚠ 虚拟环境不存在，使用系统 Python"
        PYTHON_CMD=python3
    fi
    
    # 验证 Python 版本
    PY_VERSION=$($PYTHON_CMD --version 2>&1)
    print_message "$GREEN" "使用 Python: $PY_VERSION"
}

# 检查依赖
check_dependencies() {
    print_header "检查依赖"
    
    local missing_deps=0
    
    # 检查核心依赖
    for pkg in fastapi uvicorn; do
        if $PYTHON_CMD -c "import ${pkg//-/_}" 2>/dev/null; then
            print_message "$GREEN" "✓ $pkg 已安装"
        else
            print_message "$RED" "✗ $pkg 未安装"
            missing_deps=1
        fi
    done
    
    # 检查项目依赖
    if [ -f "requirements.txt" ]; then
        print_message "$BLUE" "检查项目依赖..."
        if $PYTHON_CMD -c "import src" 2>/dev/null; then
            print_message "$GREEN" "✓ 项目模块可导入"
        else
            print_message "$RED" "✗ 项目模块导入失败"
            missing_deps=1
        fi
    fi
    
    if [ $missing_deps -eq 1 ]; then
        print_message "$YELLOW" "请运行: pip install -r requirements.txt"
        exit 1
    fi
}

# 验证配置
check_config() {
    print_header "验证配置"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_message "$RED" "✗ 配置文件不存在: $CONFIG_FILE"
        exit 1
    fi
    print_message "$GREEN" "✓ 配置文件存在: $CONFIG_FILE"
    
    # 检查监控目录
    local watch_dir=$(grep -A 5 "file_monitor:" "$CONFIG_FILE" | grep "watch_directories" -A 3 | head -4 | grep -oP '"\K[^"]+' | head -1)
    if [ -n "$watch_dir" ]; then
        print_message "$GREEN" "✓ 监控目录: $watch_dir"
        if [ -d "$watch_dir" ]; then
            print_message "$GREEN" "✓ 监控目录存在"
        else
            print_message "$YELLOW" "⚠ 监控目录不存在，将自动创建"
            mkdir -p "$watch_dir"
        fi
    else
        print_message "$YELLOW" "⚠ 未配置监控目录，使用默认: testdata"
    fi
    
    # 检查 WebUI 目录
    if [ -d "webui" ] && [ -f "webui/index.html" ]; then
        print_message "$GREEN" "✓ WebUI 文件存在"
    else
        print_message "$RED" "✗ WebUI 文件不存在"
        exit 1
    fi
}

# 检查端口占用
check_port() {
    print_header "检查端口占用"
    
    if lsof -i:$API_PORT &> /dev/null; then
        print_message "$YELLOW" "⚠ 端口 $API_PORT 已被占用"
        print_message "$YELLOW" "  尝试终止占用端口的进程..."
        
        # 查找并终止占用端口的进程
        local pid=$(lsof -t -i:$API_PORT)
        if [ -n "$pid" ]; then
            kill $pid 2>/dev/null || true
            sleep 2
            print_message "$GREEN" "✓ 已终止进程 PID: $pid"
        fi
        
        # 再次检查
        if lsof -i:$API_PORT &> /dev/null; then
            print_message "$RED" "✗ 无法释放端口 $API_PORT"
            print_message "$YELLOW" "  请手动停止占用端口的进程，或使用其他端口"
            exit 1
        fi
    else
        print_message "$GREEN" "✓ 端口 $API_PORT 可用"
    fi
}

# 显示启动信息
show_info() {
    print_header "启动信息"
    
    print_message "$BLUE" "项目目录: $PROJECT_DIR"
    print_message "$BLUE" "配置文件: $CONFIG_FILE"
    print_message "$BLUE" "监控目录: ${watch_dir:-testdata}"
    print_message "$BLUE" "API 端口: $API_PORT"
    echo ""
    print_message "$GREEN" "API 服务器: http://localhost:$API_PORT"
    print_message "$GREEN" "WebUI 地址: http://localhost:$API_PORT/webui/index.html"
    echo ""
    print_message "$YELLOW" "按 Ctrl+C 停止服务器"
}

# 启动服务
start_server() {
    print_header "启动服务"
    
    print_message "$BLUE" "正在启动 API 服务器..."
    print_message "$BLUE" "请稍候..."
    echo ""
    
    # 启动 API 服务器
    exec $PYTHON_CMD src/api_server.py --config "$CONFIG_FILE"
}

# 主函数
main() {
    echo ""
    print_message "$CYAN" "╔═══════════════════════════════════════════════════════════════╗"
    print_message "$CYAN" "║                                                              ║"
    print_message "$CYAN" "║                    msearch 统一启动脚本                      ║"
    print_message "$CYAN" "║                   多模态检索系统 v1.0                        ║"
    print_message "$CYAN" "║                                                              ║"
    print_message "$CYAN" "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -p|--port)
                API_PORT="$2"
                shift 2
                ;;
            -h|--help)
                echo "用法: $0 [选项]"
                echo ""
                echo "选项:"
                echo "  -c, --config <文件>  配置文件路径 (默认: config/config.yml)"
                echo "  -p, --port <端口>    API 服务器端口 (默认: 8000)"
                echo "  -h, --help           显示帮助信息"
                echo ""
                echo "示例:"
                echo "  $0                   # 使用默认配置启动"
                echo "  $0 -c myconfig.yml   # 使用自定义配置"
                echo "  $0 -p 8080           # 使用端口 8080"
                exit 0
                ;;
            *)
                print_message "$RED" "未知参数: $1"
                exit 1
                ;;
        esac
    done
    
    # 执行检查
    check_python
    check_venv
    check_dependencies
    check_config
    check_port
    
    # 显示启动信息并启动服务
    show_info
    start_server
}

# 捕获 Ctrl+C 信号
trap 'print_message "\n$YELLOW" "\n正在停止服务器..."; exit 0' INT

# 运行主函数
main "$@"
