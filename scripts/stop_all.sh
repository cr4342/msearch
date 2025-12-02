#!/bin/bash
# MSearch完整停止脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 尝试检测项目根目录
if [ -d "${SCRIPT_DIR}/../src" ] || [ -d "${SCRIPT_DIR}/../tests" ]; then
    PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
else
    PROJECT_ROOT="${SCRIPT_DIR}"
fi

echo "==============================================="
echo "          MSearch 服务停止脚本                "
echo "==============================================="
echo ""

# 1. 停止API服务
echo "1. 停止API服务..."
if pgrep -f "uvicorn src.api.app:app" > /dev/null; then
    pkill -f "uvicorn src.api.app:app"
    echo "API服务已停止"
else
    echo "API服务未运行"
fi
echo ""

# 2. 停止Qdrant服务
echo "2. 停止Qdrant向量数据库服务..."
"${SCRIPT_DIR}/stop_qdrant.sh"
echo ""

# 3. 停止其他相关服务
echo "3. 停止其他相关服务..."
# 停止媒体处理器
echo "   停止媒体处理器..."
pkill -f "processor" 2>/dev/null || echo "   媒体处理器未运行"

# 停止UI服务
echo "   停止UI服务..."
pkill -f "pyside6" 2>/dev/null || echo "   UI服务未运行"
echo ""

echo "==============================================="
echo "所有服务已停止！"
echo "==============================================="