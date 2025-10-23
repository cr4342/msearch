#!/bin/bash
# MSearch 安装脚本

set -e

echo "MSearch 安装脚本"
echo "================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.9或更高版本"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "错误: 未找到pip3，请先安装pip"
    exit 1
fi

# 安装依赖
echo "正在安装Python依赖..."
pip3 install -r requirements.txt

# 检查安装是否成功
echo "检查核心模块..."
python3 -c "import src.api.main; print('核心模块导入成功')"

echo "安装完成！"
echo ""
echo "使用说明："
echo "1. 启动API服务: python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000"
echo "2. 启动桌面GUI: python src/gui/main.py"
echo ""
echo "请确保在项目根目录运行上述命令。"