#!/bin/bash
# MSearch完整停止脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 项目根目录
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "==============================================="
echo "          MSearch 服务停止脚本                "
echo "==============================================="
echo ""

# 使用stop_services.py停止所有服务
echo "1. 停止所有MSearch服务..."
python3 "$SCRIPT_DIR/stop_services.py" --all

echo ""
echo "==============================================="
echo "所有服务已停止！"
echo "==============================================="