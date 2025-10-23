#!/bin/bash
# 使用国内镜像下载Qdrant的脚本

set -e

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 创建目录
mkdir -p "$PROJECT_ROOT/offline/bin"

# 检测系统架构
ARCH=$(uname -m)
OS=$(uname -s | tr '[:upper:]' '[:lower:]')

case "$ARCH" in
    x86_64)
        ARCH="x86_64"
        ;;
    aarch64|arm64)
        ARCH="aarch64"
        ;;
    *)
        echo "不支持的架构: $ARCH"
        exit 1
        ;;
esac

case "$OS" in
    linux)
        OS="linux"
        FILE_EXT="tar.gz"
        QDRANT_FILENAME="qdrant-${ARCH}-unknown-linux-gnu.${FILE_EXT}"
        ;;
    darwin)
        OS="apple-darwin"
        FILE_EXT="tar.gz"
        QDRANT_FILENAME="qdrant-${ARCH}-${OS}.${FILE_EXT}"
        ;;
    *)
        echo "不支持的操作系统: $OS"
        exit 1
        ;;
esac

QDRANT_VERSION="1.11.3"
QDRANT_URL="https://github.com/qdrant/qdrant/releases/download/v${QDRANT_VERSION}/${QDRANT_FILENAME}"

# 使用GitHub代理加速下载
QDRANT_PROXY_URL="https://gh-proxy.com/${QDRANT_URL}"

echo "正在使用国内镜像下载Qdrant ${QDRANT_VERSION} for ${ARCH}-${OS}..."
echo "下载地址: ${QDRANT_PROXY_URL}"

# 尝试使用wget下载
if command -v wget &> /dev/null; then
    wget --timeout=60 --tries=3 -O "$PROJECT_ROOT/offline/bin/${QDRANT_FILENAME}" "$QDRANT_PROXY_URL" || \
    wget --timeout=60 --tries=3 -O "$PROJECT_ROOT/offline/bin/${QDRANT_FILENAME}" "$QDRANT_URL"
elif command -v curl &> /dev/null; then
    curl --connect-timeout 60 --retry 3 -L -o "$PROJECT_ROOT/offline/bin/${QDRANT_FILENAME}" "$QDRANT_PROXY_URL" || \
    curl --connect-timeout 60 --retry 3 -L -o "$PROJECT_ROOT/offline/bin/${QDRANT_FILENAME}" "$QDRANT_URL"
else
    echo "错误：未找到wget或curl命令"
    exit 1
fi

# 解压文件
cd "$PROJECT_ROOT/offline/bin"
if [ "$FILE_EXT" = "tar.gz" ]; then
    tar -xzf "${QDRANT_FILENAME}"
elif [ "$FILE_EXT" = "zip" ]; then
    unzip "${QDRANT_FILENAME}"
fi

# 清理压缩包
rm "${QDRANT_FILENAME}"

# 添加执行权限
chmod +x "$PROJECT_ROOT/offline/bin/qdrant"

echo "Qdrant二进制文件下载并解压成功！"