#!/bin/bash
# Infinity服务启动脚本 - CPU模式

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} 启动Infinity服务..."

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "项目根目录: $PROJECT_ROOT"

# 检查infinity_emb是否安装
if ! python3 -c "import infinity_emb" &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} infinity_emb未安装"
    echo "请运行: pip install infinity-emb"
    exit 1
fi

# 检查模型文件是否存在
if [ ! -d "$PROJECT_ROOT/offline/models/clip-vit-base-patch32" ]; then
    echo -e "${RED}[ERROR]${NC} CLIP模型文件不存在"
    echo "请先运行: bash scripts/run_integration_test_with_infinity.sh"
    exit 1
fi

if [ ! -d "$PROJECT_ROOT/offline/models/clap-htsat-fused" ]; then
    echo -e "${YELLOW}[WARNING]${NC} CLAP模型文件不存在，跳过CLAP服务"
    CLAP_ENABLED=false
else
    CLAP_ENABLED=true
fi

if [ ! -d "$PROJECT_ROOT/offline/models/whisper-base" ]; then
    echo -e "${YELLOW}[WARNING]${NC} Whisper模型文件不存在，跳过Whisper服务"
    WHISPER_ENABLED=false
else
    WHISPER_ENABLED=true
fi

# 启动CLIP服务
echo -e "${GREEN}[INFO]${NC} 启动CLIP服务 (端口: 7997)..."
infinity_emb v2 \
    --model-name-or-path "$PROJECT_ROOT/offline/models/clip-vit-base-patch32" \
    --device "cpu" \
    --port 7997 \
    --model-warmup \
    --engine "torch" &
CLIP_PID=$!
echo "CLIP服务PID: $CLIP_PID"

# 启动CLAP服务（如果可用）
if [ "$CLAP_ENABLED" = true ]; then
    echo -e "${GREEN}[INFO]${NC} 启动CLAP服务 (端口: 7998)..."
    infinity_emb v2 \
        --model-name-or-path "$PROJECT_ROOT/offline/models/clap-htsat-fused" \
        --device "cpu" \
        --port 7998 \
        --model-warmup \
        --engine "torch" &
    CLAP_PID=$!
    echo "CLAP服务PID: $CLAP_PID"
fi

# 启动Whisper服务（如果可用）
if [ "$WHISPER_ENABLED" = true ]; then
    echo -e "${GREEN}[INFO]${NC} 启动Whisper服务 (端口: 7999)..."
    infinity_emb v2 \
        --model-name-or-path "$PROJECT_ROOT/offline/models/whisper-base" \
        --device "cpu" \
        --port 7999 \
        --model-warmup \
        --engine "torch" &
    WHISPER_PID=$!
    echo "Whisper服务PID: $WHISPER_PID"
fi

# 保存PID文件
echo "$CLIP_PID" > /tmp/infinity_clip.pid
if [ "$CLAP_ENABLED" = true ]; then
    echo "$CLAP_PID" > /tmp/infinity_clap.pid
fi
if [ "$WHISPER_ENABLED" = true ]; then
    echo "$WHISPER_PID" > /tmp/infinity_whisper.pid
fi

echo -e "${GREEN}[INFO]${NC} Infinity服务启动完成！"
echo "CLIP服务: http://localhost:7997"
if [ "$CLAP_ENABLED" = true ]; then
    echo "CLAP服务: http://localhost:7998"
fi
if [ "$WHISPER_ENABLED" = true ]; then
    echo "Whisper服务: http://localhost:7999"
fi
echo ""
echo "服务健康检查:"
echo "curl http://localhost:7997/health"
if [ "$CLAP_ENABLED" = true ]; then
    echo "curl http://localhost:7998/health"
fi
if [ "$WHISPER_ENABLED" = true ]; then
    echo "curl http://localhost:7999/health"
fi
