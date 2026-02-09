#!/bin/bash
# msearch 桌面客户端启动脚本

cd "$(dirname "$0")/.." || exit 1

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 检查依赖
if ! python3 -c "import PySide6" 2>/dev/null; then
    echo "错误: PySide6 未安装"
    echo "请运行: pip install PySide6"
    exit 1
fi

# 启动桌面客户端
echo "启动 msearch 桌面客户端..."
python3 -m src.ui.ui_launcher "$@"
