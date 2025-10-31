#!/bin/bash
# Qdrant向量数据库服务启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} 启动Qdrant向量数据库服务..."

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 设置Qdrant数据目录
export QDRANT_DATA_DIR="$PROJECT_ROOT/offline/qdrant_data"
mkdir -p "$QDRANT_DATA_DIR"

# 使用离线下载的Qdrant二进制文件
if [ -f "$PROJECT_ROOT/offline/bin/qdrant" ]; then
    echo "使用离线Qdrant二进制文件启动服务..."
    "$PROJECT_ROOT/offline/bin/qdrant" --config-path "$PROJECT_ROOT/config/qdrant.yml" &
    QDRANT_PID=$!
else
    echo "离线Qdrant二进制文件不存在，尝试使用系统安装的qdrant..."
    if command -v qdrant &> /dev/null; then
        qdrant --config-path "$PROJECT_ROOT/config/qdrant.yml" &
        QDRANT_PID=$!
    else
        echo -e "${YELLOW}警告：未找到Qdrant二进制文件，尝试使用Docker...${NC}"
        if command -v docker &> /dev/null; then
            docker run -d \
                --name qdrant-msearch \
                -p 6333:6333 \
                -p 6334:6334 \
                -v "$QDRANT_DATA_DIR:/qdrant/storage" \
                qdrant/qdrant:latest
            echo "Qdrant Docker容器已启动"
            return 0
        else
            echo "错误：未找到Qdrant二进制文件或Docker"
            exit 1
        fi
    fi
fi

# 保存PID文件
echo $QDRANT_PID > /tmp/qdrant.pid

echo -e "${GREEN}[INFO]${NC} Qdrant服务启动完成！"
echo "Qdrant服务PID: $QDRANT_PID"
echo "服务地址: http://localhost:6333"
echo "Web UI: http://localhost:6333/dashboard"
echo ""
echo "服务健康检查:"
echo "curl http://localhost:6333/health"