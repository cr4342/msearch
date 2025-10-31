#!/bin/bash

# 优化的Qdrant启动脚本
# 解决端口冲突、进程清理和配置问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_HOST="127.0.0.1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
QDRANT_DATA_DIR="${PROJECT_ROOT}/tests/deployment_test/data/qdrant"
QDRANT_CONFIG_DIR="${PROJECT_ROOT}/config"
QDRANT_LOG_FILE="${PROJECT_ROOT}/tests/deployment_test/logs/qdrant.log"

# 日志函数
log() {
    local level="$1"
    local message="$2"
    local timestamp="$(date +"%Y-%m-%d %H:%M:%S")"
    
    case "$level" in
        INFO) echo -e "${GREEN}[${timestamp}] [INFO] ${message}${NC}" ;;
        WARN) echo -e "${YELLOW}[${timestamp}] [WARN] ${message}${NC}" ;;
        ERROR) echo -e "${RED}[${timestamp}] [ERROR] ${message}${NC}" ;;
        DEBUG) echo -e "${BLUE}[${timestamp}] [DEBUG] ${message}${NC}" ;;
        *) echo -e "[${timestamp}] ${message}" ;;
    esac
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # 端口被占用
    else
        return 1  # 端口空闲
    fi
}

# 释放端口
free_port() {
    local port=$1
    log "INFO" "检查端口 $port..."
    
    if check_port $port; then
        log "WARN" "端口 $port 被占用，尝试释放..."
        
        # 查找占用端口的进程
        local pids=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null || true)
        
        if [ -n "$pids" ]; then
            log "INFO" "发现占用端口 $port 的进程: $pids"
            
            # 尝试优雅关闭
            for pid in $pids; do
                log "INFO" "尝试优雅关闭进程 $pid..."
                kill -TERM $pid 2>/dev/null || true
            done
            
            # 等待进程关闭
            sleep 3
            
            # 检查是否还有进程占用端口
            if check_port $port; then
                log "WARN" "进程未响应TERM信号，强制关闭..."
                for pid in $(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null || true); do
                    kill -KILL $pid 2>/dev/null || true
                done
                sleep 1
            fi
        fi
        
        # 最终检查
        if check_port $port; then
            log "ERROR" "无法释放端口 $port"
            return 1
        else
            log "INFO" "端口 $port 已释放"
            return 0
        fi
    else
        log "INFO" "端口 $port 空闲"
        return 0
    fi
}

# 停止现有的Qdrant进程
stop_existing_qdrant() {
    log "INFO" "停止现有的Qdrant进程..."
    
    # 查找Qdrant进程
    local qdrant_pids=$(pgrep -f "qdrant" 2>/dev/null || true)
    
    if [ -n "$qdrant_pids" ]; then
        log "INFO" "发现Qdrant进程: $qdrant_pids"
        
        for pid in $qdrant_pids; do
            log "INFO" "停止Qdrant进程 $pid..."
            kill -TERM $pid 2>/dev/null || true
        done
        
        # 等待进程关闭
        sleep 3
        
        # 检查是否还有Qdrant进程
        qdrant_pids=$(pgrep -f "qdrant" 2>/dev/null || true)
        if [ -n "$qdrant_pids" ]; then
            log "WARN" "强制关闭Qdrant进程..."
            for pid in $qdrant_pids; do
                kill -KILL $pid 2>/dev/null || true
            done
        fi
    else
        log "INFO" "未发现运行中的Qdrant进程"
    fi
}

# 创建Qdrant配置文件
create_qdrant_config() {
    log "INFO" "创建Qdrant配置文件..."
    
    mkdir -p "$QDRANT_CONFIG_DIR"
    
    local config_file="$QDRANT_CONFIG_DIR/qdrant_config.yaml"
    
    cat > "$config_file" << EOF
# Qdrant优化配置文件

storage:
  # 数据存储路径
  storage_path: "$QDRANT_DATA_DIR"
  
  # 性能优化
  performance:
    max_search_threads: 2
    max_optimization_threads: 1

service:
  # 服务配置
  host: $QDRANT_HOST
  http_port: $QDRANT_PORT
  grpc_port: $QDRANT_GRPC_PORT
  
  # 启用CORS（用于Web界面）
  enable_cors: true
  
  # 最大请求大小
  max_request_size_mb: 32

cluster:
  # 禁用集群模式（单机部署）
  enabled: false

# 日志配置
log_level: INFO

# 禁用遥测
telemetry_disabled: true

# 优化配置
optimization:
  # 自动优化
  auto_flush: true
  
  # 内存映射
  memmap_threshold_kb: 100000
  
  # 索引优化
  indexing_threshold_kb: 20000
EOF
    
    log "INFO" "Qdrant配置文件已创建: $config_file"
    echo "$config_file"
}

# 检查Qdrant是否已安装
check_qdrant_installation() {
    log "INFO" "检查Qdrant安装..."
    
    if command -v qdrant >/dev/null 2>&1; then
        local version=$(qdrant --version 2>/dev/null || echo "未知版本")
        log "INFO" "发现Qdrant: $version"
        return 0
    elif command -v docker >/dev/null 2>&1; then
        log "INFO" "未发现Qdrant二进制文件，但Docker可用"
        return 1
    else
        log "ERROR" "未发现Qdrant，且Docker不可用"
        return 2
    fi
}

# 使用Docker启动Qdrant
start_qdrant_docker() {
    log "INFO" "使用Docker启动Qdrant..."
    
    # 创建数据目录
    mkdir -p "$QDRANT_DATA_DIR"
    mkdir -p "$(dirname "$QDRANT_LOG_FILE")"
    
    # 停止现有的Qdrant容器
    if docker ps -q -f name=qdrant-msearch >/dev/null 2>&1; then
        log "INFO" "停止现有的Qdrant容器..."
        docker stop qdrant-msearch >/dev/null 2>&1 || true
        docker rm qdrant-msearch >/dev/null 2>&1 || true
    fi
    
    # 启动Qdrant容器
    log "INFO" "启动Qdrant Docker容器..."
    
    docker run -d \
        --name qdrant-msearch \
        -p $QDRANT_PORT:6333 \
        -p $QDRANT_GRPC_PORT:6334 \
        -v "$QDRANT_DATA_DIR:/qdrant/storage" \
        -e QDRANT__SERVICE__HTTP_PORT=6333 \
        -e QDRANT__SERVICE__GRPC_PORT=6334 \
        -e QDRANT__LOG_LEVEL=INFO \
        qdrant/qdrant:latest \
        > "$QDRANT_LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        log "INFO" "Qdrant Docker容器启动成功"
        return 0
    else
        log "ERROR" "Qdrant Docker容器启动失败"
        return 1
    fi
}

# 使用二进制文件启动Qdrant
start_qdrant_binary() {
    log "INFO" "使用二进制文件启动Qdrant..."
    
    # 创建必要目录
    mkdir -p "$QDRANT_DATA_DIR"
    mkdir -p "$(dirname "$QDRANT_LOG_FILE")"
    
    # 创建配置文件
    local config_file=$(create_qdrant_config)
    
    # 启动Qdrant
    log "INFO" "启动Qdrant服务..."
    
    nohup qdrant \
        --config-path "$config_file" \
        > "$QDRANT_LOG_FILE" 2>&1 &
    
    local qdrant_pid=$!
    
    # 保存PID
    echo $qdrant_pid > "${PROJECT_ROOT}/tests/deployment_test/qdrant.pid"
    
    log "INFO" "Qdrant已启动，PID: $qdrant_pid"
    return 0
}

# 等待Qdrant启动
wait_for_qdrant() {
    log "INFO" "等待Qdrant启动..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "http://$QDRANT_HOST:$QDRANT_PORT/health" >/dev/null 2>&1; then
            log "INFO" "Qdrant健康检查通过"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log "DEBUG" "等待Qdrant启动... ($attempt/$max_attempts)"
        sleep 2
    done
    
    log "ERROR" "Qdrant启动超时"
    return 1
}

# 验证Qdrant功能
verify_qdrant() {
    log "INFO" "验证Qdrant功能..."
    
    # 检查健康状态
    local health_response=$(curl -s "http://$QDRANT_HOST:$QDRANT_PORT/health" 2>/dev/null || echo "")
    
    if [ -n "$health_response" ]; then
        log "INFO" "Qdrant健康检查: $health_response"
    else
        log "ERROR" "Qdrant健康检查失败"
        return 1
    fi
    
    # 检查集合列表
    local collections_response=$(curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections" 2>/dev/null || echo "")
    
    if [ -n "$collections_response" ]; then
        log "INFO" "Qdrant集合API响应正常"
    else
        log "WARN" "Qdrant集合API响应异常"
    fi
    
    return 0
}

# 主函数
main() {
    log "INFO" "开始启动Qdrant服务..."
    
    # 释放端口
    if ! free_port $QDRANT_PORT || ! free_port $QDRANT_GRPC_PORT; then
        log "ERROR" "无法释放必要端口"
        exit 1
    fi
    
    # 停止现有进程
    stop_existing_qdrant
    
    # 检查Qdrant安装
    check_qdrant_installation
    local install_status=$?
    
    # 根据安装状态选择启动方式
    case $install_status in
        0)
            # 使用二进制文件启动
            if start_qdrant_binary; then
                log "INFO" "Qdrant二进制启动成功"
            else
                log "ERROR" "Qdrant二进制启动失败"
                exit 1
            fi
            ;;
        1)
            # 使用Docker启动
            if start_qdrant_docker; then
                log "INFO" "Qdrant Docker启动成功"
            else
                log "ERROR" "Qdrant Docker启动失败"
                exit 1
            fi
            ;;
        2)
            log "ERROR" "无法启动Qdrant：未安装且Docker不可用"
            log "INFO" "请安装Qdrant或Docker："
            log "INFO" "1. 安装Qdrant: https://qdrant.tech/documentation/quick-start/"
            log "INFO" "2. 安装Docker: https://docs.docker.com/get-docker/"
            exit 1
            ;;
    esac
    
    # 等待启动
    if wait_for_qdrant; then
        log "INFO" "Qdrant启动完成"
    else
        log "ERROR" "Qdrant启动失败"
        exit 1
    fi
    
    # 验证功能
    if verify_qdrant; then
        log "INFO" "Qdrant功能验证通过"
    else
        log "WARN" "Qdrant功能验证失败，但服务已启动"
    fi
    
    # 显示连接信息
    log "INFO" "Qdrant服务信息："
    log "INFO" "- HTTP API: http://$QDRANT_HOST:$QDRANT_PORT"
    log "INFO" "- gRPC API: $QDRANT_HOST:$QDRANT_GRPC_PORT"
    log "INFO" "- 健康检查: http://$QDRANT_HOST:$QDRANT_PORT/health"
    log "INFO" "- Web界面: http://$QDRANT_HOST:$QDRANT_PORT/dashboard"
    log "INFO" "- 数据目录: $QDRANT_DATA_DIR"
    log "INFO" "- 日志文件: $QDRANT_LOG_FILE"
    
    log "INFO" "Qdrant启动完成！"
}

# 显示使用说明
show_usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -s, --status   检查Qdrant状态"
    echo "  -t, --test     测试Qdrant连接"
    echo ""
    echo "示例:"
    echo "  $0             # 启动Qdrant"
    echo "  $0 --status    # 检查状态"
    echo "  $0 --test      # 测试连接"
}

# 检查Qdrant状态
check_status() {
    log "INFO" "检查Qdrant状态..."
    
    if check_port $QDRANT_PORT; then
        log "INFO" "Qdrant端口 $QDRANT_PORT 正在监听"
        
        if curl -s "http://$QDRANT_HOST:$QDRANT_PORT/health" >/dev/null 2>&1; then
            log "INFO" "Qdrant服务正常运行"
        else
            log "WARN" "Qdrant端口开放但服务异常"
        fi
    else
        log "INFO" "Qdrant未运行"
    fi
}

# 测试Qdrant连接
test_connection() {
    log "INFO" "测试Qdrant连接..."
    
    # 健康检查
    log "INFO" "执行健康检查..."
    curl -s "http://$QDRANT_HOST:$QDRANT_PORT/health" || {
        log "ERROR" "健康检查失败"
        return 1
    }
    
    # 获取集合列表
    log "INFO" "获取集合列表..."
    curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections" || {
        log "ERROR" "获取集合列表失败"
        return 1
    }
    
    log "INFO" "Qdrant连接测试通过"
}

# 解析命令行参数
case "${1:-}" in
    -h|--help)
        show_usage
        exit 0
        ;;
    -s|--status)
        check_status
        exit 0
        ;;
    -t|--test)
        test_connection
        exit 0
        ;;
    "")
        main
        ;;
    *)
        echo "未知选项: $1"
        show_usage
        exit 1
        ;;
esac