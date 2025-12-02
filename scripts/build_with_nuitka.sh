#!/bin/bash
# MSearch Nuitka打包脚本
# 功能：使用Nuitka将MSearch打包为可执行文件

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 路径定义
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"
DIST_DIR="${PROJECT_ROOT}/dist"
MAIN_FILE="${PROJECT_ROOT}/src/main.py"

# 检查依赖
check_dependencies() {
    log_info "检查构建依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查Nuitka
    if ! command -v nuitka3 &> /dev/null; then
        log_info "安装Nuitka..."
        pip install nuitka
    fi
    
    log_success "构建依赖检查完成"
}

# 清理旧构建
clean_old_build() {
    log_info "清理旧构建..."
    
    rm -rf "${BUILD_DIR}" "${DIST_DIR}"
    mkdir -p "${BUILD_DIR}" "${DIST_DIR}"
    
    log_success "旧构建清理完成"
}

# 安装项目依赖
install_deps() {
    log_info "安装项目依赖..."
    
    if [ -f "${PROJECT_ROOT}/requirements.txt" ]; then
        pip install -r "${PROJECT_ROOT}/requirements.txt"
    fi
    
    log_success "项目依赖安装完成"
}

# 打包应用
build_app() {
    log_info "开始打包应用..."
    
    log_info "项目根目录: ${PROJECT_ROOT}"
    log_info "主文件: ${MAIN_FILE}"
    log_info "构建目录: ${BUILD_DIR}"
    log_info "输出目录: ${DIST_DIR}"
    
    # Nuitka打包命令
    nuitka3 \
        --standalone \
        --onefile \
        --output-dir="${BUILD_DIR}" \
        --output-filename="msearch" \
        --include-package="src" \
        --follow-imports \
        --enable-plugin="numpy" \
        --enable-plugin="torch" \
        --enable-plugin="pydantic" \
        --enable-plugin="asyncio" \
        --remove-output \
        --show-progress \
        "${MAIN_FILE}"
    
    log_success "应用打包完成"
}

# 复制必要文件
copy_files() {
    log_info "复制必要文件..."
    
    # 创建输出目录结构
    mkdir -p "${DIST_DIR}/config" "${DIST_DIR}/data" "${DIST_DIR}/logs" "${DIST_DIR}/scripts"
    
    # 复制配置文件
    if [ -f "${PROJECT_ROOT}/config/config.yml" ]; then
        cp "${PROJECT_ROOT}/config/config.yml" "${DIST_DIR}/config/"
    fi
    
    # 复制脚本文件
    cp "${PROJECT_ROOT}/scripts/start_qdrant.sh" "${DIST_DIR}/scripts/"
    cp "${PROJECT_ROOT}/scripts/stop_qdrant.sh" "${DIST_DIR}/scripts/"
    
    # 复制可执行文件
    if [ -f "${BUILD_DIR}/msearch" ]; then
        cp "${BUILD_DIR}/msearch" "${DIST_DIR}/"
    elif [ -f "${BUILD_DIR}/msearch.exe" ]; then
        cp "${BUILD_DIR}/msearch.exe" "${DIST_DIR}/"
    fi
    
    # 复制README和LICENSE
    [ -f "${PROJECT_ROOT}/README.md" ] && cp "${PROJECT_ROOT}/README.md" "${DIST_DIR}/"
    [ -f "${PROJECT_ROOT}/LICENSE" ] && cp "${PROJECT_ROOT}/LICENSE" "${DIST_DIR}/"
    
    log_success "必要文件复制完成"
}

# 主函数
main() {
    log_info "开始MSearch打包..."
    
    check_dependencies
    clean_old_build
    install_deps
    build_app
    copy_files
    
    log_success "\n======================================"
    log_success "MSearch 打包完成！"
    log_success "======================================\n"
    log_info "打包结果位于: ${DIST_DIR}"
    log_info "可执行文件: ${DIST_DIR}/msearch"
    log_success "\n======================================\n"
}

# 执行主函数
main