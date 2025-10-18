#!/bin/bash

# 简化版 msearch 部署脚本（使用虚拟环境）

set -e

# 颜色定义
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log_info "开始简化版部署（使用虚拟环境）..."

# 创建必要的目录
mkdir -p "$PROJECT_ROOT/offline/models"
mkdir -p "$PROJECT_ROOT/offline/packages"
mkdir -p "$PROJECT_ROOT/logs"

# 创建虚拟环境
log_info "创建虚拟环境..."
python3 -m venv "$PROJECT_ROOT/venv"

# 激活虚拟环境
source "$PROJECT_ROOT/venv/bin/activate"

# 1. 下载离线依赖包
log_info "1. 下载离线依赖包..."
pip download -r "$PROJECT_ROOT/requirements.txt" \
    --dest "$PROJECT_ROOT/offline/packages" \
    --disable-pip-version-check \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --timeout 120 \
    --retries 5

# 2. 安装Python依赖
log_info "2. 安装Python依赖..."
pip install --no-index --find-links="$PROJECT_ROOT/offline/packages/" -r "$PROJECT_ROOT/requirements.txt"

# 3. 下载模型文件
log_info "3. 下载模型文件..."
export HF_ENDPOINT=https://hf-mirror.com

# 确保huggingface_hub已安装
pip install huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade

# 下载CLIP模型
log_info "下载CLIP模型: openai/clip-vit-base-patch32"
if command -v huggingface-cli &> /dev/null; then
    huggingface-cli download --resume-download --local-dir-use-symlinks False "openai/clip-vit-base-patch32" --local-dir "$PROJECT_ROOT/offline/models/clip-vit-base-patch32"
fi

# 下载CLAP模型
log_info "下载CLAP模型: laion/clap-htsat-fused"
if command -v huggingface-cli &> /dev/null; then
    huggingface-cli download --resume-download --local-dir-use-symlinks False "laion/clap-htsat-fused" --local-dir "$PROJECT_ROOT/offline/models/clap-htsat-fused"
fi

# 下载Whisper模型
log_info "下载Whisper模型: openai/whisper-base"
if command -v huggingface-cli &> /dev/null; then
    huggingface-cli download --resume-download --local-dir-use-symlinks False "openai/whisper-base" --local-dir "$PROJECT_ROOT/offline/models/whisper-base"
fi

log_info "简化版部署完成！"
log_info "要激活虚拟环境，请运行: source $PROJECT_ROOT/venv/bin/activate"