#!/bin/bash
# infinity-emb修复脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}修复infinity-emb依赖问题...${NC}"

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 卸载有问题的版本
echo -e "${YELLOW}卸载现有的infinity-emb...${NC}"
python3 -m pip uninstall infinity-emb -y || true

# 安装兼容版本
echo -e "${YELLOW}安装兼容版本的infinity-emb...${NC}"
if [ -d "$PROJECT_ROOT/offline/packages" ]; then
    # 使用离线包
    python3 -m pip install \
        --no-index \
        --find-links="$PROJECT_ROOT/offline/packages" \
        --force-reinstall \
        "infinity-emb==0.0.76"
else
    # 在线安装
    python3 -m pip install "infinity-emb==0.0.76" --no-deps
fi

# 安装必要的依赖
echo -e "${YELLOW}安装必要依赖...${NC}"
local deps=(
    "sentence-transformers>=3.0.0"
    "torch>=2.0.0"
    "transformers>=4.30.0"
    "fastapi>=0.100.0"
    "uvicorn>=0.20.0"
    "pydantic>=2.0.0"
    "typer>=0.9.0"
    "rich>=13.0.0"
)

for dep in "${deps[@]}"; do
    if [ -d "$PROJECT_ROOT/offline/packages" ]; then
        python3 -m pip install \
            --no-index \
            --find-links="$PROJECT_ROOT/offline/packages" \
            "$dep" || echo -e "${YELLOW}警告：$dep 安装失败${NC}"
    else
        python3 -m pip install "$dep" || echo -e "${YELLOW}警告：$dep 安装失败${NC}"
    fi
done

# 测试安装
echo -e "${YELLOW}测试infinity-emb安装...${NC}"
if python3 -c "import infinity_emb; print(f'infinity-emb版本: {infinity_emb.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✅ infinity-emb安装成功${NC}"
else
    echo -e "${RED}❌ infinity-emb安装失败${NC}"
    exit 1
fi

echo -e "${GREEN}infinity-emb修复完成！${NC}"