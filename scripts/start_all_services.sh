#!/bin/bash
# 启动所有服务脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} 开始启动所有服务..."
echo ""

# 启动Qdrant服务
echo -e "${BLUE}[INFO]${NC} 启动Qdrant向量数据库服务..."
"$SCRIPT_DIR/start_qdrant.sh"
echo ""

# 等待Qdrant服务完全启动
echo -e "${YELLOW}[INFO]${NC} 等待Qdrant服务启动完成..."
sleep 5

# 启动Infinity服务
echo -e "${BLUE}[INFO]${NC} 启动Infinity嵌入服务..."
"$SCRIPT_DIR/start_infinity_services.sh"
echo ""

echo -e "${GREEN}[INFO]${NC} 所有服务启动完成！"
echo ""
echo "服务状态检查:"
echo "- Qdrant: curl http://localhost:6333/health"
echo "- Infinity: curl http://localhost:7997/health"
echo ""
echo "Web界面:"
echo "- Qdrant UI: http://localhost:6333"
echo ""
echo "要停止所有服务，请运行:"
echo "  $SCRIPT_DIR/stop_all_services.sh"
