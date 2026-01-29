#!/bin/bash
###############################################################################
# msearch 启动脚本
# 一键启动完整应用（API服务 + WebUI）
###############################################################################

set -e

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

# 设置离线环境变量
export HF_HOME="$PROJECT_ROOT/data/models"
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HUB_OFFLINE=1
export INFINITY_LOCAL_MODE=1
export NO_PROXY='*'
export no_proxy='*'

print_info "========================================"
print_info "  msearch 多模态搜索系统 - 启动"
print_info "========================================"
print_info ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    print_error "虚拟环境不存在，请先运行安装脚本: bash scripts/install.sh"
    exit 1
fi

# 激活虚拟环境
print_info "激活虚拟环境..."
source venv/bin/activate

# 检查依赖
print_info "检查依赖..."
python -c "import fastapi; import infinity_emb" 2>/dev/null || {
    print_error "依赖未安装，请先运行: bash scripts/install.sh"
    exit 1
}

# 检查模型
print_info "检查模型..."
python scripts/setup_models.py check || {
    print_warning "模型未完整下载，尝试下载..."
    python scripts/setup_models.py setup || {
        print_error "模型下载失败，请手动下载: python scripts/setup_models.py setup"
        exit 1
    }
}

# 创建日志目录
mkdir -p logs

# 启动主程序
print_info "启动主程序..."
MAIN_PID=""
python src/main.py > logs/main.log 2>&1 &
MAIN_PID=$!

# 等待主程序启动
print_info "等待主程序启动..."
sleep 5

# 检查主程序是否成功启动
if ! kill -0 $MAIN_PID 2>/dev/null; then
    print_error "主程序启动失败，查看日志: tail -f logs/main.log"
    exit 1
fi

print_success "主程序已启动 (PID: $MAIN_PID)"

# 启动API服务
print_info "启动API服务..."
API_PID=""
python src/api_server.py > logs/api.log 2>&1 &
API_PID=$!

# 等待API服务启动
print_info "等待API服务启动..."
sleep 5

# 检查API服务是否成功启动
if ! kill -0 $API_PID 2>/dev/null; then
    print_error "API服务启动失败，查看日志: tail -f logs/api.log"
    exit 1
fi

print_success "API服务已启动 (PID: $API_PID)"

# 获取API服务端口
API_PORT=$(grep -E "port:\s*[0-9]+" config/config.yml 2>/dev/null | awk '{print $2}' || echo "8000")

# 启动WebUI
print_info "启动WebUI..."
if [ -f "webui/index.html" ]; then
    # 使用Python内置HTTP服务器
    WEBUI_PID=""
    python -m http.server 8080 --directory webui > logs/webui.log 2>&1 &
    WEBUI_PID=$!
    
    sleep 2
    
    if ! kill -0 $WEBUI_PID 2>/dev/null; then
        print_warning "WebUI启动失败，但API服务仍在运行"
    else
        print_success "WebUI已启动 (PID: $WEBUI_PID)"
    fi
else
    print_warning "WebUI文件不存在，跳过启动"
fi

print_info ""
print_info "========================================"
print_success "msearch 已成功启动！"
print_info "========================================"
print_info ""
print_info "服务地址："
print_info "  - API服务: http://localhost:$API_PORT"
print_info "  - WebUI:   http://localhost:8080"
print_info "  - API文档: http://localhost:$API_PORT/docs"
print_info ""
print_info "使用方法："
print_info "  1. 打开浏览器访问: http://localhost:8080"
print_info "  2. 选择搜索类型（文本/图像/音频）"
print_info "  3. 输入查询或上传文件"
print_info "  4. 点击搜索查看结果"
print_info ""
print_info "停止服务："
print_info "  按 Ctrl+C 停止"
print_info "  或运行: pkill -f 'python src/api_server.py'"
print_info ""
print_info "========================================"
print_info "进程信息"
print_info "========================================"
print_info "主程序 PID:  $MAIN_PID"
print_info "API服务 PID:  $API_PID"
if [ -n "$WEBUI_PID" ]; then
    print_info "WebUI PID:   $WEBUI_PID"
fi
print_info ""
print_info "日志文件："
print_info "  - 主程序日志: logs/main.log"
print_info "  - API日志:    logs/api.log"
print_info "  - WebUI日志:  logs/webui.log"
print_info "========================================"
print_info ""

# 捕获退出信号，清理进程
cleanup() {
    print_info ""
    print_info "正在停止服务..."
    
    if [ -n "$MAIN_PID" ] && kill -0 $MAIN_PID 2>/dev/null; then
        print_info "停止主程序 (PID: $MAIN_PID)..."
        kill $MAIN_PID 2>/dev/null || true
        wait $MAIN_PID 2>/dev/null || true
    fi
    
    if [ -n "$API_PID" ] && kill -0 $API_PID 2>/dev/null; then
        print_info "停止API服务 (PID: $API_PID)..."
        kill $API_PID 2>/dev/null || true
        wait $API_PID 2>/dev/null || true
    fi
    
    if [ -n "$WEBUI_PID" ] && kill -0 $WEBUI_PID 2>/dev/null; then
        print_info "停止WebUI (PID: $WEBUI_PID)..."
        kill $WEBUI_PID 2>/dev/null || true
        wait $WEBUI_PID 2>/dev/null || true
    fi
    
    print_success "所有服务已停止"
    exit 0
}

# 注册信号处理
trap cleanup SIGINT SIGTERM

# 保持脚本运行
wait