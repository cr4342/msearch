#!/bin/bash
# Qdrant向量数据库服务启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "\033[0;32m[INFO]\033[0m 启动Qdrant向量数据库服务..."

# 获取脚本目录
SCRIPT_DIR="/data/project/msearch/scripts"
PROJECT_ROOT="/data/project/msearch"

# 设置Qdrant数据目录
QDRANT_DATA_DIR="${PROJECT_ROOT}/data/qdrant"
STORAGE_PATH="${QDRANT_DATA_DIR}/storage"
PID_FILE="${QDRANT_DATA_DIR}/qdrant.pid"

# 创建必要的目录
mkdir -p "${STORAGE_PATH}"

# 使用本地下载的Qdrant二进制文件
QDRANT_BIN="${QDRANT_DATA_DIR}/bin/qdrant"
if [ -f "${QDRANT_BIN}" ]; then
    echo "使用本地Qdrant二进制文件启动服务..."
    # 从Qdrant数据目录启动，使用默认配置文件
    cd "${QDRANT_DATA_DIR}" && "${QDRANT_BIN}" &
    QDRANT_PID=$!
    # 保存PID文件
    echo "${QDRANT_PID}" > "${PID_FILE}"
elif command -v qdrant &> /dev/null; then
    echo "使用系统安装的Qdrant二进制文件启动服务..."
    # 从Qdrant数据目录启动，使用默认配置文件
    cd "${QDRANT_DATA_DIR}" && qdrant &
    QDRANT_PID=$!
    # 保存PID文件
    echo "${QDRANT_PID}" > "${PID_FILE}"
else
    echo -e "\033[1;33m警告：未找到Qdrant二进制文件，尝试使用Docker...\033[0m"
    if command -v docker &> /dev/null; then
        docker run -d --name qdrant-msearch -p 6333:6333 -p 6334:6334 -v "${STORAGE_PATH}:/qdrant/storage" qdrant/qdrant:latest
        echo "Qdrant Docker容器已启动"
        return 0
    else
        echo "错误：未找到Qdrant二进制文件或Docker"
        exit 1
    fi
fi

echo -e "\033[0;32m[INFO]\033[0m Qdrant服务启动完成！"
echo "Qdrant服务PID: ${QDRANT_PID}"
echo "服务地址: http://localhost:6333"
echo "Web UI: http://localhost:6333/dashboard"
echo ""
echo "服务健康检查:"
echo "curl http://localhost:6333/health"
