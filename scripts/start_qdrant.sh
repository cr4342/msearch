#!/bin/bash
# Qdrant 启动脚本
# 支持单机二进制和Docker两种模式

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置
QDRANT_HOST=${QDRANT_HOST:-localhost}
QDRANT_PORT=${QDRANT_PORT:-6333}
DATA_DIR=${DATA_DIR:-./data/qdrant}
USE_DOCKER=${USE_DOCKER:-false}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查必要目录
    mkdir -p "$DATA_DIR"
    mkdir -p "$DATA_DIR/bin"
    
    log_success "依赖检查完成"
}

# 检查Qdrant是否已运行
is_qdrant_running() {
    if command -v curl &> /dev/null; then
        if curl -s "http://$QDRANT_HOST:$QDRANT_PORT/health" &> /dev/null; then
            return 0
        fi
    fi
    return 1
}

# 下载Qdrant二进制文件
download_qdrant_binary() {
    log_info "下载Qdrant二进制文件..."
    
    # 获取系统信息
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m | tr '[:upper:]' '[:lower:]')
    
    # 确定文件名
    case "$OS" in
        "linux")
            if [[ "$ARCH" == "x86_64" ]] || [[ "$ARCH" == "amd64" ]]; then
                BINARY_NAME="qdrant-x86_64-unknown-linux-musl"
            else
                log_error "不支持的架构: $ARCH"
                return 1
            fi
            ;;
        "darwin")
            if [[ "$ARCH" == "x86_64" ]] || [[ "$ARCH" == "amd64" ]]; then
                BINARY_NAME="qdrant-x86_64-apple-darwin"
            elif [[ "$ARCH" == "arm64" ]] || [[ "$ARCH" == "aarch64" ]]; then
                BINARY_NAME="qdrant-aarch64-apple-darwin"
            else
                log_error "不支持的架构: $ARCH"
                return 1
            fi
            ;;
        *)
            log_error "不支持的操作系统: $OS"
            return 1
            ;;
    esac
    
    QDRANT_VERSION="v1.7.0"
    DOWNLOAD_URL="https://github.com/qdrant/qdrant/releases/download/$QDRANT_VERSION/$BINARY_NAME"
    BINARY_PATH="$DATA_DIR/bin/$BINARY_NAME"
    
    # 检查是否已存在
    if [[ -f "$BINARY_PATH" ]] && [[ -x "$BINARY_PATH" ]]; then
        log_info "Qdrant二进制文件已存在: $BINARY_PATH"
        return 0
    fi
    
    # 下载文件
    log_info "从 $DOWNLOAD_URL 下载..."
    
    if command -v wget &> /dev/null; then
        wget -O "$BINARY_PATH" "$DOWNLOAD_URL"
    elif command -v curl &> /dev/null; then
        curl -L -o "$BINARY_PATH" "$DOWNLOAD_URL"
    else
        log_error "需要 wget 或 curl 来下载文件"
        return 1
    fi
    
    # 设置执行权限
    chmod +x "$BINARY_PATH"
    
    # 验证文件
    if [[ ! -f "$BINARY_PATH" ]] || [[ $(stat -f%z "$BINARY_PATH") -lt 1048576 ]]; then
        log_error "下载的文件无效或太小"
        rm -f "$BINARY_PATH"
        return 1
    fi
    
    log_success "Qdrant二进制文件下载完成"
}

# 使用二进制启动Qdrant
start_with_binary() {
    log_info "使用二进制文件启动Qdrant..."
    
    BINARY_PATH="$DATA_DIR/bin/qdrant-x86_64-unknown-linux-musl"
    
    # 如果二进制文件不存在，尝试下载
    if [[ ! -f "$BINARY_PATH" ]]; then
        # 尝试其他可能的二进制文件名
        BINARY_PATH=$(find "$DATA_DIR/bin" -name "qdrant-*" -type f -executable | head -1)
        
        if [[ -z "$BINARY_PATH" ]]; then
            log_warning "未找到Qdrant二进制文件，尝试下载..."
            if ! download_qdrant_binary; then
                log_error "下载Qdrant二进制文件失败"
                return 1
            fi
            BINARY_PATH="$DATA_DIR/bin/$BINARY_NAME"
        fi
    fi
    
    log_info "启动Qdrant: $BINARY_PATH"
    log_info "数据目录: $DATA_DIR"
    log_info "监听地址: $QDRANT_HOST:$QDRANT_PORT"
    
    # 启动Qdrant
    exec "$BINARY_PATH" \
        --host "$QDRANT_HOST" \
        --port "$QDRANT_PORT" \
        --storage-path "$DATA_DIR" \
        --log-level INFO
}

# 使用Docker启动Qdrant
start_with_docker() {
    log_info "使用Docker启动Qdrant..."
    
    # 检查Docker是否可用
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        return 1
    fi
    
    # 停止现有容器
    if docker ps -q -f name=msearch-qdrant | grep -q .; then
        log_info "停止现有Qdrant容器..."
        docker stop msearch-qdrant || true
        docker rm msearch-qdrant || true
    fi
    
    # 启动新容器
    log_info "启动Qdrant Docker容器..."
    log_info "数据目录: $DATA_DIR"
    log_info "监听地址: $QDRANT_HOST:$QDRANT_PORT"
    
    docker run -d \
        --name msearch-qdrant \
        -p "$QDRANT_PORT:6333" \
        -p "$((QDRANT_PORT + 1)):6334" \
        -v "$DATA_DIR:/qdrant/storage" \
        --restart unless-stopped \
        qdrant/qdrant:latest
    
    # 等待容器启动
    log_info "等待Qdrant服务启动..."
    for i in {1..30}; do
        if curl -s "http://$QDRANT_HOST:$QDRANT_PORT/health" &> /dev/null; then
            log_success "Qdrant服务已就绪"
            return 0
        fi
        sleep 1
    done
    
    log_error "Qdrant服务启动超时"
    return 1
}

# 停止Qdrant
stop_qdrant() {
    log_info "停止Qdrant服务..."
    
    # 停止Docker容器
    if command -v docker &> /dev/null; then
        if docker ps -q -f name=msearch-qdrant | grep -q .; then
            log_info "停止Qdrant Docker容器..."
            docker stop msearch-qdrant
            docker rm msearch-qdrant
            log_success "Qdrant Docker容器已停止"
        fi
    fi
    
    # 停止二进制进程
    if pgrep -f "qdrant" > /dev/null; then
        log_info "停止Qdrant进程..."
        pkill -f "qdrant" || true
        log_success "Qdrant进程已停止"
    fi
}

# 检查Qdrant状态
check_status() {
    log_info "检查Qdrant状态..."
    
    if is_qdrant_running; then
        log_success "Qdrant服务正在运行"
        
        # 获取版本信息
        if command -v curl &> /dev/null; then
            VERSION=$(curl -s "http://$QDRANT_HOST:$QDRANT_PORT/" | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', 'unknown'))" 2>/dev/null || echo "unknown")
            log_info "版本: $VERSION"
            
            # 获取集合信息
            COLLECTIONS=$(curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('result', {}).get('collections', [])))" 2>/dev/null || echo "0")
            log_info "集合数量: $COLLECTIONS"
        fi
    else
        log_warning "Qdrant服务未运行"
    fi
}

# 显示帮助信息
show_help() {
    echo "Qdrant 启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  start       启动Qdrant服务"
    echo "  stop        停止Qdrant服务"
    echo "  restart     重启Qdrant服务"
    echo "  status      检查Qdrant状态"
    echo "  help        显示帮助信息"
    echo ""
    echo "环境变量:"
    echo "  QDRANT_HOST     Qdrant监听地址 (默认: localhost)"
    echo "  QDRANT_PORT     Qdrant监听端口 (默认: 6333)"
    echo "  DATA_DIR        数据目录 (默认: ./data/qdrant)"
    echo "  USE_DOCKER      使用Docker模式 (默认: false)"
    echo ""
    echo "示例:"
    echo "  $0 start                    # 启动Qdrant"
    echo "  $0 start USE_DOCKER=true  # 使用Docker启动"
    echo "  $0 status                   # 检查状态"
}

# 主函数
main() {
    case "${1:-}" in
        "start")
            if is_qdrant_running; then
                log_warning "Qdrant服务已在运行"
                check_status
                exit 0
            fi
            
            check_dependencies
            
            if [[ "$USE_DOCKER" == "true" ]]; then
                start_with_docker
            else
                start_with_binary
            fi
            ;;
        "stop")
            stop_qdrant
            ;;
        "restart")
            stop_qdrant
            sleep 2
            main "start"
            ;;
        "status")
            check_status
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        "")
            show_help
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 捕获信号
trap 'log_info "收到停止信号，正在清理..."; stop_qdrant; exit 0' SIGTERM SIGINT

# 执行主函数
main "$@"