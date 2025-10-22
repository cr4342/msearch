#!/bin/bash
# 优化的Qdrant启动脚本
# 解决Python 3.12环境下的启动问题

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} 启动优化的Qdrant服务..."

# 获取脚本目录和项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 设置环境变量
export QDRANT_DATA_DIR="$PROJECT_ROOT/data/database/qdrant"
export QDRANT_CONFIG_PATH="$PROJECT_ROOT/config/qdrant_config.yaml"

# 创建必要的目录
mkdir -p "$QDRANT_DATA_DIR"
mkdir -p "$PROJECT_ROOT/logs"

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}[WARNING]${NC} 端口 $port 已被占用"
        return 1
    fi
    return 0
}

# 停止现有的Qdrant进程
stop_existing_qdrant() {
    echo -e "${GREEN}[INFO]${NC} 检查并停止现有的Qdrant进程..."
    
    # 通过PID文件停止
    if [ -f /tmp/qdrant.pid ]; then
        local pid=$(cat /tmp/qdrant.pid)
        if kill -0 $pid 2>/dev/null; then
            echo "停止PID为 $pid 的Qdrant进程..."
            kill $pid 2>/dev/null || true
            sleep 2
            kill -9 $pid 2>/dev/null || true
        fi
        rm -f /tmp/qdrant.pid
    fi
    
    # 通过进程名停止
    pkill -f "qdrant" 2>/dev/null || true
    
    # 等待端口释放
    local count=0
    while ! check_port 6333 && [ $count -lt 10 ]; do
        echo "等待端口6333释放..."
        sleep 1
        count=$((count + 1))
    done
}

# 检查Qdrant二进制文件
check_qdrant_binary() {
    local qdrant_bin="$PROJECT_ROOT/offline/bin/qdrant"
    
    if [ -f "$qdrant_bin" ]; then
        echo -e "${GREEN}[INFO]${NC} 找到离线Qdrant二进制文件: $qdrant_bin"
        chmod +x "$qdrant_bin"
        echo "$qdrant_bin"
        return 0
    fi
    
    # 检查系统安装的qdrant
    if command -v qdrant &> /dev/null; then
        echo -e "${GREEN}[INFO]${NC} 使用系统安装的Qdrant"
        echo "qdrant"
        return 0
    fi
    
    echo -e "${RED}[ERROR]${NC} 未找到Qdrant二进制文件"
    return 1
}

# 创建简化的配置文件
create_simple_config() {
    local config_file="$PROJECT_ROOT/config/qdrant_simple.yaml"
    
    cat > "$config_file" << EOF
storage:
  storage_path: $QDRANT_DATA_DIR

service:
  host: 127.0.0.1
  http_port: 6333
  grpc_port: 6334

cluster:
  enabled: false

log_level: INFO

telemetry_disabled: true
EOF
    
    echo "$config_file"
}

# 启动Qdrant服务
start_qdrant() {
    local qdrant_binary=$1
    local config_file=$2
    
    echo -e "${GREEN}[INFO]${NC} 启动Qdrant服务..."
    echo "二进制文件: $qdrant_binary"
    echo "配置文件: $config_file"
    echo "数据目录: $QDRANT_DATA_DIR"
    
    # 启动服务
    nohup "$qdrant_binary" --config-path "$config_file" > "$PROJECT_ROOT/logs/qdrant.log" 2>&1 &
    local pid=$!
    
    # 保存PID
    echo $pid > /tmp/qdrant.pid
    
    echo -e "${GREEN}[INFO]${NC} Qdrant服务已启动，PID: $pid"
    
    # 等待服务启动
    echo "等待服务启动..."
    local count=0
    while [ $count -lt 30 ]; do
        if curl -s http://127.0.0.1:6333/health >/dev/null 2>&1; then
            echo -e "${GREEN}[SUCCESS]${NC} Qdrant服务启动成功！"
            echo "服务地址: http://127.0.0.1:6333"
            echo "健康检查: curl http://127.0.0.1:6333/health"
            echo "Web UI: http://127.0.0.1:6333/dashboard"
            return 0
        fi
        
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    
    echo -e "\n${RED}[ERROR]${NC} Qdrant服务启动超时"
    
    # 显示日志以便调试
    if [ -f "$PROJECT_ROOT/logs/qdrant.log" ]; then
        echo -e "${YELLOW}[DEBUG]${NC} Qdrant日志:"
        tail -20 "$PROJECT_ROOT/logs/qdrant.log"
    fi
    
    return 1
}

# 主执行流程
main() {
    # 停止现有进程
    stop_existing_qdrant
    
    # 检查二进制文件
    local qdrant_binary
    if ! qdrant_binary=$(check_qdrant_binary); then
        echo -e "${RED}[ERROR]${NC} 无法找到Qdrant二进制文件"
        echo "请运行以下命令下载Qdrant:"
        echo "  bash scripts/download_qdrant_fixed.sh"
        exit 1
    fi
    
    # 创建简化配置
    local config_file
    config_file=$(create_simple_config)
    
    # 启动服务
    if start_qdrant "$qdrant_binary" "$config_file"; then
        echo -e "${GREEN}[SUCCESS]${NC} Qdrant服务启动完成！"
        exit 0
    else
        echo -e "${RED}[ERROR]${NC} Qdrant服务启动失败"
        exit 1
    fi
}

# 执行主函数
main "$@"