#!/bin/bash
# 停止所有服务脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色定义
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}[INFO]${NC} 开始停止所有服务..."
echo ""

# 停止Infinity服务
echo "停止Infinity嵌入服务..."
"$SCRIPT_DIR/stop_infinity_services.sh"
echo ""

# 停止Qdrant服务
echo "停止Qdrant向量数据库服务..."
"$SCRIPT_DIR/stop_qdrant.sh"
echo ""

echo -e "${RED}[INFO]${NC} 所有服务已停止！"
