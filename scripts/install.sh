#!/bin/bash
# MSearch 统一安装脚本
# 整合了 install_auto.sh、install_offline.sh 和 download_all_resources.sh 的功能
# 支持自动检测离线资源，优先使用离线包，否则自动下载

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 路径定义
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_DIR="$(pwd)"

# 安装模式：auto（自动检测）、online（在线）、offline（离线）
INSTALL_MODE="auto"

# 日志文件
LOG_FILE=""

# 默认日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL="INFO"

# 日志级别映射
LOG_LEVEL_DEBUG=0
LOG_LEVEL_INFO=1
LOG_LEVEL_WARNING=2
LOG_LEVEL_ERROR=3
LOG_LEVEL_CRITICAL=4

# 转换日志级别为数字
level_to_num() {
    case "$1" in
        DEBUG) echo $LOG_LEVEL_DEBUG ;;
        INFO) echo $LOG_LEVEL_INFO ;;
        WARNING) echo $LOG_LEVEL_WARNING ;;
        ERROR) echo $LOG_LEVEL_ERROR ;;
        CRITICAL) echo $LOG_LEVEL_CRITICAL ;;
        *) echo $LOG_LEVEL_INFO ;;
    esac
}

# 检查消息级别是否应该被记录
should_log() {
    local msg_level="$1"
    local current_level="$(level_to_num "$LOG_LEVEL")"
    local msg_level_num="$(level_to_num "$msg_level")"
    [ "$msg_level_num" -ge "$current_level" ]
}

# 格式化日志消息
format_log() {
    local level="$1"
    local message="$2"
    local timestamp="$(date +"%Y-%m-%d %H:%M:%S")"
    echo "[$timestamp] [${level}] $message"
}

# 输出带颜色的日志到控制台
log_to_console() {
    local level="$1"
    local message="$2"
    local formatted="$(format_log "$level" "$message")"
    
    case "$level" in
        DEBUG) echo -e "${BLUE}${formatted}${NC}" ;;
        INFO) echo -e "${GREEN}${formatted}${NC}" ;;
        WARNING) echo -e "${YELLOW}${formatted}${NC}" ;;
        ERROR) echo -e "${RED}${formatted}${NC}" ;;
        CRITICAL) echo -e "${PURPLE}${formatted}${NC}" ;;
        *) echo -e "${formatted}" ;;
    esac
}

# 日志函数 - 支持多级别和文件记录
log() {
    # 兼容原有调用方式，默认INFO级别
    if [ $# -eq 1 ]; then
        log_to_console "INFO" "$1"
        # 写入日志文件
        if [ -n "$LOG_FILE" ]; then
            formatted_log="$(format_log "INFO" "$1")"
            echo "$formatted_log" >> "$LOG_FILE"
        fi
        return
    fi
    
    # 新的多级别调用方式
    local level="$1"
    local message="$2"
    
    if should_log "$level"; then
        # 输出到控制台
        log_to_console "$level" "$message"
        
        # 写入日志文件
        if [ -n "$LOG_FILE" ]; then
            formatted_log="$(format_log "$level" "$message")"
            echo "$formatted_log" >> "$LOG_FILE"
        fi
    fi
}

# 便捷日志函数
log_debug() {
    log "DEBUG" "$1"
}

log_info() {
    log "INFO" "$1"
}

log_success() {
    log "INFO" "$1"
}

log_warning() {
    log "WARNING" "$1"
}

log_error() {
    log "ERROR" "$1"
}

log_critical() {
    log "CRITICAL" "$1"
}

# 错误处理函数
handle_error() {
    log_error "步骤失败: $1"
    log_info "安装过程中断，请检查日志: ${LOG_FILE}"
    exit 1
}

# 检测项目根目录
detect_project_root() {
    log_debug "检测项目根目录..."
    
    # 1. 如果脚本在项目内部运行，使用脚本所在目录的上级目录
    if [ -d "${SCRIPT_DIR}/../src" ] || [ -d "${SCRIPT_DIR}/../tests" ]; then
        PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
        log_success "[自动检测] 从脚本位置找到项目根目录: ${PROJECT_ROOT}"
    # 2. 如果脚本在项目外部运行，尝试在当前目录查找
    elif [ -d "${CURRENT_DIR}/src" ] || [ -d "${CURRENT_DIR}/tests" ]; then
        PROJECT_ROOT="${CURRENT_DIR}"
        log_success "[自动检测] 从当前目录找到项目根目录: ${PROJECT_ROOT}"
    # 3. 尝试在同级目录查找项目
    elif [ -d "${CURRENT_DIR}/msearch" ] && [ -d "${CURRENT_DIR}/msearch/src" ]; then
        PROJECT_ROOT="${CURRENT_DIR}/msearch"
        log_success "[自动检测] 在同级目录找到项目根目录: ${PROJECT_ROOT}"
    else
        # 默认使用当前目录作为项目根目录
        PROJECT_ROOT="${CURRENT_DIR}"
        log_warning "[警告] 未找到明确的项目结构，使用当前目录作为项目根目录: ${PROJECT_ROOT}"
    fi
    
    # 初始化日志文件
    LOG_FILE="${PROJECT_ROOT}/logs/install_$(date +%Y%m%d_%H%M%S).log"
    mkdir -p "$(dirname "${LOG_FILE}")"
    
    # 写入日志文件头
    echo "MSearch 安装日志" > "${LOG_FILE}"
    echo "开始时间: $(date)" >> "${LOG_FILE}"
    echo "当前目录: ${CURRENT_DIR}" >> "${LOG_FILE}"
    echo "脚本目录: ${SCRIPT_DIR}" >> "${LOG_FILE}"
    echo "项目目录: ${PROJECT_ROOT}" >> "${LOG_FILE}"  
    echo "安装模式: ${INSTALL_MODE}" >> "${LOG_FILE}"
    echo "日志级别: ${LOG_LEVEL}" >> "${LOG_FILE}"
    echo "===============================================" >> "${LOG_FILE}"
    
    return 0
}

# 执行硬件分析
perform_hardware_analysis() {
    log_info "==============================================="
    log_info "        执行硬件分析"
    log_info "==============================================="
    
    # 检查Python是否可用
    if ! command -v python3 &> /dev/null; then
        log_warning "Python3 不可用，跳过硬件分析"
        return
    fi
    
    # 检查psutil是否已安装，如未安装则尝试安装
    if ! python3 -c "import psutil" 2>/dev/null; then
        log_info "安装psutil用于硬件分析..."
        pip install psutil -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade || true
    fi
    
    # 执行硬件分析脚本
    log_info "执行硬件分析脚本..."
    hardware_analysis_script="${SCRIPT_DIR}/hardware_analysis.py"
    
    if [ -f "${hardware_analysis_script}" ]; then
        python3 "${hardware_analysis_script}" "${PROJECT_ROOT}/hardware_info.json"
        
        if [ $? -eq 0 ]; then
            log_success "硬件分析完成，结果已保存到: ${PROJECT_ROOT}/hardware_info.json"
        else
            log_warning "硬件分析失败，使用默认配置"
        fi
    else
        log_warning "硬件分析脚本不存在，跳过硬件分析"
    fi
    
    # 如果硬件分析结果存在，生成配置建议
    if [ -f "${PROJECT_ROOT}/hardware_info.json" ]; then
        log_info "生成配置建议..."
        generate_config_from_hardware
    fi
    
    log_info "==============================================="
}

# 根据硬件分析生成配置建议
generate_config_from_hardware() {
    # 检查jq是否可用，如不可用则跳过配置生成
    if ! command -v jq &> /dev/null; then
        log_warning "jq 不可用，跳过配置生成"
        return
    fi
    
    # 读取硬件信息
    hardware_info="${PROJECT_ROOT}/hardware_info.json"
    if [ ! -f "${hardware_info}" ]; then
        return
    fi
    
    # 生成配置文件
    config_dir="${PROJECT_ROOT}/config"
    mkdir -p "${config_dir}"
    
    # 读取推荐配置
    clip_model=$(jq -r '.recommendations.model_selection.clip' "${hardware_info}")
    clap_model=$(jq -r '.recommendations.model_selection.clap' "${hardware_info}")
    whisper_model=$(jq -r '.recommendations.model_selection.whisper' "${hardware_info}")
    backend=$(jq -r '.recommendations.model_selection.backend' "${hardware_info}")
    batch_size=$(jq -r '.recommendations.optimization.batch_size' "${hardware_info}")
    num_workers=$(jq -r '.recommendations.optimization.num_workers' "${hardware_info}")
    use_half_precision=$(jq -r '.recommendations.optimization.use_half_precision' "${hardware_info}")
    max_concurrent_tasks=$(jq -r '.recommendations.configuration.max_concurrent_tasks' "${hardware_info}")
    check_interval=$(jq -r '.recommendations.configuration.check_interval' "${hardware_info}")
    
    # 写入配置文件
    config_file="${config_dir}/hardware_recommended_config.yml"
    cat > "${config_file}" << EOF
# 基于硬件分析的推荐配置
# 生成时间: $(date)

# 模型配置
models:
  clip:
    model_name: "${clip_model}"
    device: "${backend}"
  clap:
    model_name: "${clap_model}"
    device: "${backend}"
  whisper:
    model_name: "${whisper_model}"
    device: "${backend}"

# 优化配置
optimization:
  batch_size: ${batch_size}
  num_workers: ${num_workers}
  use_half_precision: ${use_half_precision}
  max_concurrent_tasks: ${max_concurrent_tasks}

# 调度器配置
orchestrator:
  check_interval: ${check_interval}
EOF
    
    log_success "推荐配置已生成: ${config_file}"
    
    # 如果主配置文件不存在，复制推荐配置为主配置
    if [ ! -f "${config_dir}/config.yml" ]; then
        log_info "主配置文件不存在，使用推荐配置作为主配置"
        cp "${config_file}" "${config_dir}/config.yml"
    fi
}

# 显示帮助信息
show_help() {
    echo -e "${CYAN}MSearch 统一安装脚本${NC}"
    echo -e "${CYAN}====================${NC}"
    echo -e "\n${GREEN}功能：${NC}支持自动检测离线资源，优先使用离线包，否则自动下载"
    echo -e "\n${GREEN}使用方法：${NC}"
    echo -e "  ${BLUE}./install.sh [选项]${NC}"
    echo -e "\n${GREEN}选项：${NC}"
    echo -e "  ${YELLOW}--auto${NC}         自动检测模式（默认），优先使用离线资源，否则自动下载"
    echo -e "  ${YELLOW}--online${NC}       在线模式，直接在线下载安装"
    echo -e "  ${YELLOW}--offline${NC}      离线模式，仅使用本地离线资源"
    echo -e "  ${YELLOW}--download-only${NC} 仅下载离线资源，不进行安装"
    echo -e "  ${YELLOW}--debug${NC}        启用调试日志"
    echo -e "  ${YELLOW}--help${NC}         显示帮助信息"
    echo -e "\n${GREEN}示例：${NC}"
    echo -e "  ${BLUE}# 自动检测模式安装${NC}"
    echo -e "  ./install.sh"
    echo -e "\n  ${BLUE}# 在线模式安装${NC}"
    echo -e "  ./install.sh --online"
    echo -e "\n  ${BLUE}# 离线模式安装${NC}"
    echo -e "  ./install.sh --offline"
    echo -e "\n  ${BLUE}# 仅下载离线资源${NC}"
    echo -e "  ./install.sh --download-only"
    exit 0
}

# 解析命令行参数
parse_args() {
    for arg in "$@"; do
        case "$arg" in
            --auto)
                INSTALL_MODE="auto"
                ;;
            --online)
                INSTALL_MODE="online"
                ;;
            --offline)
                INSTALL_MODE="offline"
                ;;
            --download-only)
                INSTALL_MODE="download-only"
                ;;
            --debug)
                LOG_LEVEL="DEBUG"
                ;;
            --help)
                show_help
                ;;
            *)
                log_warning "未知参数: $arg"
                show_help
                ;;
        esac
    done
}

# 检测离线资源
detect_offline_resources() {
    log_info "检查离线资源..."
    
    # 离线资源目录
    OFFLINE_DIR="${PROJECT_ROOT}/temp"
    OFFLINE_BIN_DIR="${OFFLINE_DIR}/bin"
    OFFLINE_PACKAGES_DIR="${OFFLINE_DIR}/packages"
    OFFLINE_MODELS_DIR="${OFFLINE_DIR}/models"
    
    # 检查关键离线资源是否存在
    local has_offline_resources=false
    
    # 检查二进制文件
    if [ -d "${OFFLINE_BIN_DIR}" ] && [ -n "$(ls -A "${OFFLINE_BIN_DIR}" 2>/dev/null)" ]; then
        has_offline_resources=true
    fi
    
    # 检查依赖包
    if [ -d "${OFFLINE_PACKAGES_DIR}" ]; then
        local packages_count=$(find "${OFFLINE_PACKAGES_DIR}" -name "*.whl" | wc -l)
        if [ "$packages_count" -gt 50 ]; then
            has_offline_resources=true
        fi
    fi
    
    # 检查模型文件
    if [ -d "${OFFLINE_MODELS_DIR}" ]; then
        local models_count=$(find "${OFFLINE_MODELS_DIR}" -type f | wc -l)
        if [ "$models_count" -gt 20 ]; then
            has_offline_resources=true
        fi
    fi
    
    log_info "离线资源检测结果: ${has_offline_resources}"
    echo "${has_offline_resources}"
}

# 检测系统架构
detect_architecture() {
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
            log_error "不支持的架构: $ARCH"
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
            log_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac
    
    log_info "检测到系统架构: ${ARCH}-${OS}"
}

# 下载Qdrant函数
download_qdrant() {
    log_info "1. 下载Qdrant向量数据库..."
    
    # 创建目录
    mkdir -p "$PROJECT_ROOT/data/qdrant/bin"
    
    # 使用稳定版本1.10.0，该版本支持--storage-path参数
    QDRANT_VERSION="1.10.0"
    QDRANT_URL="https://github.com/qdrant/qdrant/releases/download/v${QDRANT_VERSION}/${QDRANT_FILENAME}"
    
    # 使用GitHub代理加速下载
    QDRANT_PROXY_URL="https://gh-proxy.com/${QDRANT_URL}"
    
    log_info "正在下载Qdrant ${QDRANT_VERSION} for ${ARCH}-${OS}..."
    log_info "下载地址: ${QDRANT_PROXY_URL}"
    
    # 尝试使用wget下载
    if command -v wget &> /dev/null; then
        wget --timeout=60 --tries=3 -O "$PROJECT_ROOT/data/qdrant/bin/${QDRANT_FILENAME}" "$QDRANT_PROXY_URL" || \
        wget --timeout=60 --tries=3 -O "$PROJECT_ROOT/data/qdrant/bin/${QDRANT_FILENAME}" "$QDRANT_URL"
    elif command -v curl &> /dev/null; then
        curl --connect-timeout 60 --retry 3 -L -o "$PROJECT_ROOT/data/qdrant/bin/${QDRANT_FILENAME}" "$QDRANT_PROXY_URL" || \
        curl --connect-timeout 60 --retry 3 -L -o "$PROJECT_ROOT/data/qdrant/bin/${QDRANT_FILENAME}" "$QDRANT_URL"
    else
        log_error "未找到wget或curl命令"
        return 1
    fi
    
    # 解压文件
    cd "$PROJECT_ROOT/data/qdrant/bin"
    if [ "$FILE_EXT" = "tar.gz" ]; then
        tar -xzf "${QDRANT_FILENAME}"
    elif [ "$FILE_EXT" = "zip" ]; then
        unzip "${QDRANT_FILENAME}"
    fi
    
    # 清理压缩包
    rm "${QDRANT_FILENAME}"
    
    # 添加执行权限
    chmod +x "$PROJECT_ROOT/data/qdrant/bin/qdrant"
    
    log_success "Qdrant二进制文件下载并解压成功！"
    return 0
}

# 下载依赖包函数
download_dependencies() {
    log_info "2. 下载Python依赖包..."
    
    # 创建temp目录结构
    mkdir -p "$PROJECT_ROOT/temp/packages"
    
    # 检查是否已有足够的包
    existing_packages=$(find "$PROJECT_ROOT/temp/packages" -type f -name "*.whl" | wc -l)
    if [ "$existing_packages" -gt 100 ]; then
        log_info "检测到已有 $existing_packages 个包，跳过基础依赖下载"
    else
        # 下载requirements.txt中列出的所有依赖包（使用国内镜像优化）
        log_info "下载requirements.txt中所有依赖包..."
        pip download -r "$PROJECT_ROOT/requirements.txt" \
            --dest "$PROJECT_ROOT/temp/packages" \
            --disable-pip-version-check \
            -i https://pypi.tuna.tsinghua.edu.cn/simple \
            --timeout 60 \
            --retries 3 || {
                log_warning "使用默认PyPI源重试..."
                pip download -r "$PROJECT_ROOT/requirements.txt" \
                    --dest "$PROJECT_ROOT/temp/packages" \
                    --disable-pip-version-check \
                    --timeout 60 \
                    --retries 3
            }
    fi
    
    # 特别处理infinity-emb兼容性问题
    log_info "特别处理infinity-emb兼容性问题..."
    download_infinity_emb_compatible
    
    # 特别处理inaSpeechSegmenter包（可能需要额外依赖）
    log_info "特别处理inaSpeechSegmenter包..."
    pip download inaspeechsegmenter \
        --dest "$PROJECT_ROOT/temp/packages" \
        --disable-pip-version-check \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --timeout 60 \
        --retries 3 || {
            log_warning "使用默认PyPI源重试..."
            pip download inaspeechsegmenter \
                --dest "$PROJECT_ROOT/temp/packages" \
                --disable-pip-version-check \
                --timeout 60 \
                --retries 3
        }
    
    # 验证下载结果
    requirements_count=$(find "$PROJECT_ROOT/temp/packages" -type f -name "*.whl" | wc -l)
    log_info "依赖包下载完成:"
    log_info "  - Wheel文件数量: $requirements_count"
    log_info "  - 保存位置: $PROJECT_ROOT/temp/packages/"
    
    # 检查关键依赖包是否下载成功
    key_packages=()
    missing_packages=()
    
    for package in "${key_packages[@]}"; do
        if ! find "$PROJECT_ROOT/temp/packages" -type f -name "*${package}*" | grep -q .; then
        missing_packages+=("$package")
    fi
    done
    
    if [ ${#missing_packages[@]} -eq 0 ]; then
        log_success "所有关键依赖包下载成功！"
        return 0
    else
        log_warning "以下关键依赖包可能未下载成功: ${missing_packages[*]}"
        log_warning "请检查网络连接或手动下载这些包"
        return 1
    fi
}

# 下载infinity-emb兼容版本函数
download_infinity_emb_compatible() {
    log_info "下载infinity-emb兼容版本和依赖..."
    
    # 下载兼容的infinity-emb版本
    log_info "下载infinity-emb基础版本..."
    pip download "infinity-emb==0.0.76" \
        --dest "$PROJECT_ROOT/temp/packages" \
        --no-deps \
        --disable-pip-version-check \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --timeout 60 \
        --retries 3 || {
            log_warning "使用默认PyPI源重试..."
            pip download "infinity-emb==0.0.76" \
                --dest "$PROJECT_ROOT/temp/packages" \
                --no-deps \
                --disable-pip-version-check \
                --timeout 60 \
                --retries 3
        }
    
    # 下载兼容的optimum版本（不包含bettertransformer）
    log_info "下载兼容的optimum版本..."
    pip download "optimum>=1.14.0,<2.0.0" \
        --dest "$PROJECT_ROOT/temp/packages" \
        --disable-pip-version-check \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --timeout 60 \
        --retries 3 || {
            log_warning "optimum下载失败，尝试下载特定版本..."
            pip download "optimum==1.21.4" \
                --dest "$PROJECT_ROOT/temp/packages" \
                --disable-pip-version-check \
                -i https://pypi.tuna.tsinghua.edu.cn/simple \
                --timeout 60 \
                --retries 3
        }
    
    # 下载sentence-transformers兼容版本
    log_info "下载sentence-transformers兼容版本..."
    pip download "sentence-transformers>=3.0.0,<4.0.0" \
        --dest "$PROJECT_ROOT/temp/packages" \
        --disable-pip-version-check \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --timeout 60 \
        --retries 3 || true
    
    # 下载其他infinity-emb依赖
    local infinity_deps=(
        "typer>=0.9.0"
        "rich>=13.0.0"
        "orjson>=3.9.0"
        "prometheus-fastapi-instrumentator>=6.1.0"
        "diskcache>=5.6.0"
        "einops>=0.7.0"
    )
    
    for dep in "${infinity_deps[@]}"; do
        log_info "下载infinity-emb依赖: $dep"
        pip download "$dep" \
            --dest "$PROJECT_ROOT/temp/packages" \
            --disable-pip-version-check \
            -i https://pypi.tuna.tsinghua.edu.cn/simple \
            --timeout 60 \
            --retries 3 || {
                log_warning "$dep 下载失败，跳过"
            }
    done
    
    log_success "infinity-emb兼容版本下载完成"
}

# 下载模型函数
download_models() {
    log_info "3. 下载AI模型..."
    
    # 创建模型目录结构
    mkdir -p "$PROJECT_ROOT/data/models"
    
    # 检查是否已有模型
    local models_exist=true
    local required_models=("clip-vit-base-patch32" "clap-htsat-fused" "whisper-base")
    
    for model in "${required_models[@]}"; do
        if [ ! -d "$PROJECT_ROOT/data/models/$model" ] || [ -z "$(ls -A "$PROJECT_ROOT/data/models/$model" 2>/dev/null)" ]; then
            models_exist=false
            break
        fi
    done
    
    if [ "$models_exist" = true ]; then
        log_info "所有模型已存在，验证完整性..."
        local total_files=$(find "$PROJECT_ROOT/data/models" -type f | wc -l)
        if [ "$total_files" -gt 20 ]; then
            log_info "模型文件完整，跳过下载"
            return 0
        else
            log_warning "模型文件不完整，重新下载"
        fi
    fi
    
    # 确保huggingface_hub已安装（用于模型下载）
    log_info "确保huggingface_hub已安装..."
    pip install huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade || true
    
    # 设置HuggingFace镜像（国内优化）
    export HF_ENDPOINT=https://hf-mirror.com
    export HF_HUB_ENABLE_HF_TRANSFER=1
    
    # 使用Python脚本下载模型（更稳定）
    create_model_download_script
    
    # 执行模型下载
    log_info "开始下载AI模型..."
    python3 "$PROJECT_ROOT/data/download_models.py" || {
        log_warning "Python脚本下载失败，尝试使用huggingface-cli..."
        download_models_with_cli
    }
    
    # 验证本地模型目录结构
    log_info "验证本地模型目录结构..."
    mkdir -p "$PROJECT_ROOT/data/models"
    
    # 确保模型目录结构正确
    for model_dir in clip-vit-base-patch32 clap-htsat-fused whisper-base;
    do
        if [ -d "$PROJECT_ROOT/data/models/$model_dir" ]; then
            local file_count=$(find "$PROJECT_ROOT/data/models/$model_dir" -type f | wc -l)
            log_info "模型目录 $model_dir 包含 $file_count 个文件"
            
            if [ "$file_count" -eq 0 ]; then
                log_warning "模型目录 $model_dir 为空，可能下载不完整"
            fi
        else
            log_warning "模型目录 $model_dir 不存在，可能下载失败"
        fi
done
    
    # 验证下载结果
    log_info "验证模型下载结果..."
    models_count=$(find "$PROJECT_ROOT/data/models" -type f | wc -l)
    log_info "模型下载完成:"
    log_info "  - 模型文件数量: $models_count"
    log_info "  - 保存位置: $PROJECT_ROOT/data/models/"
    
    if [ "$models_count" -gt 20 ]; then
        log_success "模型下载完成！"
        return 0
    else
        log_warning "模型下载可能不完整，但继续执行"
        return 1
    fi
}

# 创建模型下载脚本
create_model_download_script() {
    cat > "$PROJECT_ROOT/data/download_models.py" << 'EOF'
#!/usr/bin/env python3
"""
稳定的模型下载脚本
使用transformers库直接下载模型，避免网络问题
"""
import os
import sys
import time
from pathlib import Path

def download_model_safe(repo_id, local_path, max_retries=3):
    """安全下载模型"""
    print(f"下载模型: {repo_id} -> {local_path}")
    
    # 确保目录存在
    os.makedirs(local_path, exist_ok=True)
    
    for attempt in range(max_retries):
        try:
            # 强制使用hf-mirror.com镜像
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
            os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
            
            if "clip" in repo_id.lower():
                from transformers import CLIPModel, CLIPProcessor
                print(f"  尝试 {attempt + 1}/{max_retries}: 下载CLIP模型...")
                # 直接下载到本地目录，不使用cache_dir
                model = CLIPModel.from_pretrained(repo_id)
                processor = CLIPProcessor.from_pretrained(repo_id)
                model.save_pretrained(local_path)
                processor.save_pretrained(local_path)
                print(f"  ✅ {repo_id} 下载并保存到本地成功")
                return True
                
            elif "clap" in repo_id.lower():
                from transformers import ClapModel, ClapProcessor
                print(f"  尝试 {attempt + 1}/{max_retries}: 下载CLAP模型...")
                # 直接下载到本地目录，不使用cache_dir
                model = ClapModel.from_pretrained(repo_id)
                processor = ClapProcessor.from_pretrained(repo_id)
                model.save_pretrained(local_path)
                processor.save_pretrained(local_path)
                print(f"  ✅ {repo_id} 下载并保存到本地成功")
                return True
                
            elif "whisper" in repo_id.lower():
                from transformers import WhisperForConditionalGeneration, WhisperProcessor
                print(f"  尝试 {attempt + 1}/{max_retries}: 下载Whisper模型...")
                # 直接下载到本地目录，不使用cache_dir
                model = WhisperForConditionalGeneration.from_pretrained(repo_id)
                processor = WhisperProcessor.from_pretrained(repo_id)
                model.save_pretrained(local_path)
                processor.save_pretrained(local_path)
                print(f"  ✅ {repo_id} 下载并保存到本地成功")
                return True
            
        except Exception as e:
            print(f"  ❌ 尝试 {attempt + 1} 失败: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"  等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"  ❌ {repo_id} 下载失败，已达最大重试次数")
                return False
    
    return False

def main():
    """主函数"""
    # 设置环境变量
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
    
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 模型列表
    models = [
        {
            "repo_id": "openai/clip-vit-base-patch32",
            "local_path": os.path.join(project_root, "data", "models", "clip-vit-base-patch32")
        },
        {
            "repo_id": "laion/clap-htsat-fused", 
            "local_path": os.path.join(project_root, "data", "models", "clap-htsat-fused")
        },
        {
            "repo_id": "openai/whisper-base",
            "local_path": os.path.join(project_root, "data", "models", "whisper-base")
        }
    ]
    
    success_count = 0
    
    for model_info in models:
        if download_model_safe(model_info["repo_id"], model_info["local_path"]):
            success_count += 1
    
    print(f"\n模型下载完成: {success_count}/{len(models)} 成功")
    
    if success_count > 0:
        print("✅ 至少有部分模型下载成功")
        return 0
    else:
        print("❌ 所有模型下载失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF
    
    chmod +x "$PROJECT_ROOT/data/download_models.py"
}

# 使用CLI下载模型（备用方案）
download_models_with_cli() {
    log_info "使用huggingface-cli下载模型..."
    
    # 设置HuggingFace镜像
    export HF_ENDPOINT=https://hf-mirror.com
    
    # 下载CLIP模型（文本-图像检索）
    log_info "1. 下载CLIP模型 (openai/clip-vit-base-patch32)..."
    huggingface-cli download \
        openai/clip-vit-base-patch32 \
        --resume-download \
        --local-dir-use-symlinks False \
        --local-dir "$PROJECT_ROOT/data/models/clip-vit-base-patch32" || {
            log_warning "CLIP模型下载失败"
        }
    
    # 下载CLAP模型（文本-音频检索）
    log_info "2. 下载CLAP模型 (laion/clap-htsat-fused)..."
    huggingface-cli download \
        laion/clap-htsat-fused \
        --resume-download \
        --local-dir-use-symlinks False \
        --local-dir "$PROJECT_ROOT/data/models/clap-htsat-fused" || {
            log_warning "CLAP模型下载失败"
        }
    
    # 下载Whisper模型（语音转文本）
    log_info "3. 下载Whisper模型 (openai/whisper-base)..."
    huggingface-cli download \
        openai/whisper-base \
        --resume-download \
        --local-dir-use-symlinks False \
        --local-dir "$PROJECT_ROOT/data/models/whisper-base" || {
            log_warning "Whisper模型下载失败"
        }
}

# 下载所有离线资源
download_all_resources() {
    log_info "=================================================="
    log_info "            下载所有离线资源              "
    log_info "=================================================="
    
    # 检测系统架构
    detect_architecture
    
    # 执行下载任务
    log_info "FAISS不需要单独下载，通过pip安装即可"
    download_dependencies || log_warning "依赖包下载失败，但继续执行"
    download_models || log_warning "模型下载失败，但继续执行"
    
    # 验证下载结果
    log_info "验证下载结果..."
    if [ -d "$PROJECT_ROOT/offline/bin" ] && [ -d "$PROJECT_ROOT/offline/packages" ] && [ -d "$PROJECT_ROOT/data/models" ]; then
        bin_count=$(find "$PROJECT_ROOT/offline/bin" -type f 2>/dev/null | wc -l)
        packages_count=$(find "$PROJECT_ROOT/offline/packages" -type f -name "*.whl" 2>/dev/null | wc -l)
        models_count=$(find "$PROJECT_ROOT/data/models" -type f 2>/dev/null | wc -l)
        
        log_info "离线资源下载完成:"
        log_info "  - 二进制文件数量: $bin_count"
        log_info "  - 依赖包数量: $packages_count"
        log_info "  - 模型文件数量: $models_count"
        log_info "  - 二进制文件和依赖包保存位置: $PROJECT_ROOT/offline/"
        log_info "  - 模型保存位置: $PROJECT_ROOT/data/models/"
        
        log_success "所有离线资源下载完成！"
        return 0
    else
        log_error "离线资源下载失败，请检查目录结构"
        return 1
    fi
}

# 1. 检查系统环境（在线模式）
check_environment_online() {
    log_info "==============================================="
    log_info "        检查系统环境"
    log_info "==============================================="
    
    # 检查Python环境
    log_debug "[步骤1] 检查Python环境..."
    if ! command -v python3 &> /dev/null; then
        handle_error "未找到Python3，请先安装Python 3.9-3.11版本"
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1)
    log_info "[成功] Python环境检查通过: ${PYTHON_VERSION}"
    
    # 检查pip
    log_debug "[步骤2] 检查pip..."
    if ! command -v pip3 &> /dev/null; then
        log_warning "未找到pip3，尝试安装..."
        if command -v apt-get &> /dev/null; then
            log_info "使用apt-get安装pip3..."
            sudo apt-get update && sudo apt-get install -y python3-pip
        elif command -v yum &> /dev/null; then
            log_info "使用yum安装pip3..."
            sudo yum install -y python3-pip
        else
            handle_error "无法安装pip3，请手动安装"
        fi
    fi
    
    log_info "[成功] pip环境检查通过"
    
    # 检查Git
    log_debug "[步骤3] 检查Git..."
    if ! command -v git &> /dev/null; then
        log_warning "未找到Git，尝试安装..."
        if command -v apt-get &> /dev/null; then
            log_info "使用apt-get安装Git..."
            sudo apt-get update && sudo apt-get install -y git
        elif command -v yum &> /dev/null; then
            log_info "使用yum安装Git..."
            sudo yum install -y git
        else
            log_warning "无法安装Git，部分功能可能受限"
        fi
    else
        log_info "[成功] Git环境检查通过"
    fi
    
    # 检查系统依赖
    log_debug "[步骤4] 检查系统依赖..."
    if command -v apt-get &> /dev/null; then
        log_info "安装系统依赖..."
        sudo apt-get update && sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev
    elif command -v yum &> /dev/null; then
        log_info "安装系统依赖..."
        sudo yum install -y gcc gcc-c++ openssl-devel libffi-devel python3-devel
    fi
    
    log_success "环境检查完成！"
}

# 2. 安装系统依赖和Python包（在线模式）
install_dependencies_online() {
    log_info "==============================================="
    log_info "        安装系统依赖和Python包"
    log_info "==============================================="
    
    # 更新pip
    log_info "[步骤1] 更新pip..."
    python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple || log_warning "pip更新失败"
    
    # 安装核心依赖包
    log_info "[步骤2] 安装核心依赖包..."
    if [ -f "${PROJECT_ROOT}/requirements.txt" ]; then
        python3 -m pip install -r "${PROJECT_ROOT}/requirements.txt" \
            -i https://pypi.tuna.tsinghua.edu.cn/simple \
            --timeout 120 \
            --retries 3 || {
            log_warning "部分依赖安装失败，尝试单独安装关键包..."
            python3 -m pip install fastapi uvicorn pydantic numpy pandas \
                -i https://pypi.tuna.tsinghua.edu.cn/simple
        }
    else
        log_warning "未找到requirements.txt，安装基本依赖"
        python3 -m pip install fastapi uvicorn pydantic numpy pandas \
            -i https://pypi.tuna.tsinghua.edu.cn/simple
    fi
    
    # 安装测试专用依赖
    log_info "[步骤3] 安装测试专用依赖..."
    python3 -m pip install pytest pytest-cov pytest-mock httpx \
        -i https://pypi.tuna.tsinghua.edu.cn/simple
    
    # 安装AI模型依赖
    log_info "[步骤4] 安装AI模型依赖..."
    python3 -m pip install transformers torch torchvision \
        -i https://pypi.tuna.tsinghua.edu.cn/simple
    
    # 安装infinity-emb及其依赖
    log_info "[步骤5] 安装infinity-emb向量嵌入引擎..."
    python3 -m pip install "infinity-emb[all]" \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --timeout 180 \
        --retries 3 || {
        log_warning "infinity-emb完整版安装失败，尝试安装基础版本..."
        python3 -m pip install infinity-emb \
            -i https://pypi.tuna.tsinghua.edu.cn/simple
    }
    
    log_success "系统依赖安装完成！"
}

# 3. 下载和配置AI模型（在线模式）
download_models_online() {
    log_info "==============================================="
    log_info "          下载和配置AI模型"
    log_info "==============================================="
    
    # 设置环境变量 - 使用镜像加速
    export HF_ENDPOINT="https://hf-mirror.com"
    
    # 模型目录
    MODELS_DIR="${PROJECT_ROOT}/data/models"
    mkdir -p "${MODELS_DIR}"
    
    log_info "[信息] 模型目录: ${MODELS_DIR}"
    
    # 创建模型下载脚本
    MODEL_SCRIPT="${PROJECT_ROOT}/scripts/download_models.py"
    cat > "${MODEL_SCRIPT}" << 'EOF'
import os
import sys
import time
from pathlib import Path
from transformers import (
    CLIPModel, CLIPProcessor, 
    ClapModel, ClapProcessor, 
    WhisperForConditionalGeneration, WhisperProcessor,
    AutoModel, AutoProcessor, AutoTokenizer
)
import torch

def download_model(repo_id, local_path, components):
    """下载单个模型及其组件"""
    print(f"\n[INFO] 下载模型: {repo_id} 到 {local_path}")
    
    # 确保输出目录存在
    os.makedirs(local_path, exist_ok=True)
    
    # 下载模型组件
    success = True
    
    if 'model' in components:
        try:
            print("  - 下载模型组件...")
            model = AutoModel.from_pretrained(repo_id, cache_dir=local_path, trust_remote_code=True)
            model.save_pretrained(local_path)
            print("  ✓ 模型组件下载完成")
        except Exception as e:
            print(f"  ✗ 模型组件下载失败: {str(e)}")
            success = False
    
    if 'processor' in components:
        try:
            print("  - 下载处理器组件...")
            processor = AutoProcessor.from_pretrained(repo_id, cache_dir=local_path, trust_remote_code=True)
            processor.save_pretrained(local_path)
            print("  ✓ 处理器组件下载完成")
        except Exception as e:
            print(f"  ✗ 处理器组件下载失败: {str(e)}")
            success = False
    
    return success

def download_models(models_dir):
    """下载所有必要的模型"""
    print(f"[INFO] 模型下载目录: {models_dir}")
    
    # 模型列表
    models = [
        {
            'name': 'clip',
            'repo_id': 'openai/clip-vit-base-patch32',
            'local_path': os.path.join(models_dir, 'clip-vit-base-patch32'),
            'components': ['model', 'processor']
        },
        {
            'name': 'clap',
            'repo_id': 'laion/clap-htsat-unfused',
            'local_path': os.path.join(models_dir, 'clap-htsat-fused'),
            'components': ['model', 'processor']
        },
        {
            'name': 'whisper',
            'repo_id': 'openai/whisper-base',
            'local_path': os.path.join(models_dir, 'whisper-base'),
            'components': ['model', 'processor']
        }
    ]
    
    # 下载每个模型
    success_count = 0
    total_count = len(models)
    
    for i, model_info in enumerate(models, 1):
        print(f"\n[{i}/{total_count}] 开始下载 {model_info['name']}...")
        
        # 检查是否已存在
        if os.path.exists(os.path.join(model_info['local_path'], 'config.json')):
            print(f"[INFO] {model_info['name']} 模型已存在，跳过下载")
            success_count += 1
            continue
        
        # 尝试下载，最多3次重试
        max_retries = 3
        for retry in range(max_retries):
            if download_model(
                model_info['repo_id'],
                model_info['local_path'],
                model_info['components']
            ):
                success_count += 1
                break
            else:
                if retry < max_retries - 1:
                    wait_time = (retry + 1) * 5
                    print(f"[WARNING] 下载失败，{wait_time}秒后重试 ({retry + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"[ERROR] {model_info['name']} 模型下载失败，达到最大重试次数")
    
    print(f"\n[INFO] 模型下载完成: {success_count}/{total_count} 个模型成功")
    
    return success_count == total_count

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERROR] 缺少模型目录参数")
        sys.exit(1)
    
    models_dir = sys.argv[1]
    success = download_models(models_dir)
    sys.exit(0 if success else 1)
EOF
    
    # 执行模型下载
    log_info "[步骤1] 执行模型下载..."
    python3 "${MODEL_SCRIPT}" "${MODELS_DIR}"
    DOWNLOAD_RESULT=$?
    
    if [ $DOWNLOAD_RESULT -eq 0 ]; then
        log_success "所有模型下载完成"
    else
        log_warning "部分模型下载失败，请检查网络连接"
        log_warning "继续安装，但API服务可能无法正常工作"
    fi
    
    # 清理临时脚本
    rm -f "${MODEL_SCRIPT}"
    
    log_success "AI模型配置完成！"
}

# 4. 配置项目文件（在线模式）
configure_project_online() {
    log_info "==============================================="
    log_info "          配置项目文件"
    log_info "==============================================="
    
    # 初始化数据目录
    init_data_dirs
    
    # 初始化配置
    init_config
    
    # 初始化数据库
    init_database
    
    log_success "项目配置完成！"
}

# 1. 检查离线资源（离线模式）
check_offline_resources() {
    log_info "检查离线资源..."
    
    # 离线资源目录
    OFFLINE_DIR="${PROJECT_ROOT}/offline"
    OFFLINE_MODELS_DIR="${OFFLINE_DIR}/models"
    OFFLINE_PACKAGES_DIR="${OFFLINE_DIR}/packages"
    
    if [ ! -d "${OFFLINE_DIR}" ]; then
        log_error "离线资源目录不存在: ${OFFLINE_DIR}"
        log_info "请先在有网络环境下运行: ./scripts/install.sh --download-only"
        exit 1
    fi
    
    if [ ! -d "${OFFLINE_PACKAGES_DIR}" ]; then
        log_error "离线依赖目录不存在: ${OFFLINE_PACKAGES_DIR}"
        exit 1
    fi
    
    if [ ! -d "${OFFLINE_MODELS_DIR}" ]; then
        log_error "离线模型目录不存在: ${OFFLINE_MODELS_DIR}"
        exit 1
    fi
    
    # 检查必要的依赖文件
    if [ ! -f "${PROJECT_ROOT}/requirements.txt" ]; then
        log_error "未找到requirements.txt文件: ${PROJECT_ROOT}/requirements.txt"
        exit 1
    fi
    
    log_success "离线资源检查完成"
}

# 2. 检查系统依赖（离线模式）
check_system_dependencies_offline() {
    log_info "检查系统依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_info "Python版本: ${PYTHON_VERSION}"
    
    # 检查pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 未安装"
        exit 1
    fi
    
    # 检查FFmpeg
    if ! command -v ffmpeg &> /dev/null; then
        log_warning "FFmpeg 未安装，视频和音频处理功能将受限"
    fi
    
    # 检查Git
    if ! command -v git &> /dev/null; then
        log_warning "Git 未安装，版本控制功能将受限"
    fi
    
    log_success "系统依赖检查完成"
}

# 3. 创建虚拟环境（离线模式）
create_venv() {
    log_info "创建虚拟环境..."
    
    VENV_DIR="${PROJECT_ROOT}/venv"
    
    if [ -d "${VENV_DIR}" ]; then
        log_warning "虚拟环境已存在，将重新创建"
        rm -rf "${VENV_DIR}"
    fi
    
    python3 -m venv "${VENV_DIR}"
    
    # 激活虚拟环境
    source "${VENV_DIR}/bin/activate"
    
    # 升级pip
    log_info "升级pip..."
    pip install --upgrade pip
    
    log_success "虚拟环境创建完成"
}

# 4. 安装离线依赖（离线模式）
install_offline_deps() {
    log_info "安装离线依赖..."
    
    VENV_DIR="${PROJECT_ROOT}/venv"
    source "${VENV_DIR}/bin/activate"
    
    # 离线资源目录
    OFFLINE_PACKAGES_DIR="${PROJECT_ROOT}/offline/packages"
    
    # 安装离线依赖
    if [ -d "${OFFLINE_PACKAGES_DIR}" ]; then
        log_info "从 ${OFFLINE_PACKAGES_DIR} 安装依赖..."
        pip install --no-index --find-links="${OFFLINE_PACKAGES_DIR}" -r "${PROJECT_ROOT}/requirements.txt"
    else
        log_error "离线依赖目录不存在"
        exit 1
    fi
    
    log_success "离线依赖安装完成"
}

# 5. 复制模型文件（离线模式）
copy_models() {
    log_info "复制模型文件..."
    
    MODELS_DIR="${PROJECT_ROOT}/data/models"
    OFFLINE_MODELS_DIR="${PROJECT_ROOT}/offline/models"
    mkdir -p "${MODELS_DIR}"
    
    # 检查data/models目录是否已经有模型
    local models_exist=false
    local required_models=("clip-vit-base-patch32" "clap-htsat-fused" "whisper-base")
    
    for model in "${required_models[@]}"; do
        if [ -d "${MODELS_DIR}/${model}" ] && [ -n "$(ls -A "${MODELS_DIR}/${model}" 2>/dev/null)" ]; then
            models_exist=true
            break
        fi
    done
    
    if [ "$models_exist" = true ]; then
        log_info "data/models目录已存在模型，跳过复制"
        log_success "模型文件复制完成"
        return 0
    fi
    
    # 如果data/models目录没有模型，检查offline/models目录
    if [ -d "${OFFLINE_MODELS_DIR}" ]; then
        log_info "从 ${OFFLINE_MODELS_DIR} 复制模型到 ${MODELS_DIR}..."
        cp -r "${OFFLINE_MODELS_DIR}/"* "${MODELS_DIR}/"
        log_success "模型文件复制完成"
    else
        log_warning "离线模型目录不存在，跳过复制"
        log_success "模型文件复制完成"
    fi
}

# 初始化数据目录
init_data_dirs() {
    log_info "初始化数据目录..."
    
    mkdir -p "${PROJECT_ROOT}/data/database"
    mkdir -p "${PROJECT_ROOT}/data/qdrant"
    mkdir -p "${PROJECT_ROOT}/data/temp/images"
    mkdir -p "${PROJECT_ROOT}/data/temp/videos"
    mkdir -p "${PROJECT_ROOT}/data/temp/audio"
    mkdir -p "${PROJECT_ROOT}/logs"
    
    log_success "数据目录初始化完成"
}

# 初始化配置
init_config() {
    log_info "初始化配置..."
    
    CONFIG_DIR="${PROJECT_ROOT}/config"
    mkdir -p "${CONFIG_DIR}"
    
    # 复制默认配置文件
    if [ -f "${CONFIG_DIR}/config.yml" ]; then
        log_warning "配置文件已存在，跳过初始化"
    else
        # 创建默认配置文件
        cat > "${CONFIG_DIR}/config.yml" << EOF
# MSearch 配置文件

# 服务器配置
server:
  host: "0.0.0.0"
  port: 8000
  debug: false

# 数据库配置
database:
  sqlite:
    path: "./data/database/msearch.db"

# 向量数据库配置
vector_db:
  type: "qdrant"
  host: "localhost"
  port: 6333
  api_key: ""
  collection_name: "msearch"
  embedding_dim: 512

# 模型配置
models:
  clip:
    model_name: "ViT-B/32"
    device: "auto"
  whisper:
    model_name: "base"
    device: "auto"
  clap:
    model_name: "small"
    device: "auto"

# 媒体处理配置
media:
  image:
    max_size: 1024
    quality: 90
  video:
    frame_interval: 1.0
    max_frames: 100
  audio:
    sample_rate: 16000
    chunk_duration: 10.0

# 批处理配置
batch:
  size: 32
  timeout: 5.0

# 缓存配置
cache:
  enabled: true
  size: 1000
  ttl: 3600

# 日志配置
logging:
  level: "INFO"
  file: "./logs/msearch.log"
  rotation: "10 MB"
  retention: "30 days"

# 监控配置
monitoring:
  enabled: true
  interval: 60
  metrics_port: 9000
EOF
        log_success "配置文件创建完成"
    fi
    
    log_success "配置初始化完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    # 激活虚拟环境（如果存在）
    if [ -d "${PROJECT_ROOT}/venv" ]; then
        VENV_DIR="${PROJECT_ROOT}/venv"
        source "${VENV_DIR}/bin/activate"
    fi
    
    # 运行数据库初始化，设置PYTHONPATH
    PYTHONPATH="${PROJECT_ROOT}" python -c "from src.common.storage.database_adapter import DatabaseAdapter; db = DatabaseAdapter(); print('数据库初始化完成')"
    
    log_success "数据库初始化完成"
}

# 生成启动脚本
generate_startup_scripts() {
    log_info "==============================================="
    log_info "          生成启动脚本"
    log_info "==============================================="
    
    # 生成API启动脚本
    API_SCRIPT="${PROJECT_ROOT}/scripts/start_api.sh"
    cat > "${API_SCRIPT}" << EOF
#!/bin/bash
# 启动MSearch API服务

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 尝试检测项目根目录
if [ -d "${SCRIPT_DIR}/../src" ] || [ -d "${SCRIPT_DIR}/../tests" ]; then
    PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
else
    PROJECT_ROOT="${SCRIPT_DIR}"
fi

# 激活虚拟环境（如果存在）
if [ -d "${PROJECT_ROOT}/venv" ]; then
    echo "激活虚拟环境..."
    source "${PROJECT_ROOT}/venv/bin/activate"
fi

# 设置环境变量
export PYTHONPATH="${PROJECT_ROOT}"
export PYTHONWARNINGS=ignore
export KMP_DUPLICATE_LIB_OK=TRUE

# 检查是否有正在运行的服务
if pgrep -f "uvicorn src.api.app:app" > /dev/null; then
    echo "检测到已运行的API服务，正在停止..."
    pkill -f "uvicorn src.api.app:app"
    sleep 2
fi

echo "启动MSearch API服务..."
echo "API地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "查看日志: tail -f ${PROJECT_ROOT}/logs/msearch.log"
echo "按 Ctrl+C 停止服务"
echo ""

# 启动API服务
cd "${PROJECT_ROOT}"
python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
EOF
    chmod +x "${API_SCRIPT}"
    
    # 生成完整启动脚本
    START_SCRIPT="${PROJECT_ROOT}/scripts/start_all.sh"
    cat > "${START_SCRIPT}" << EOF
#!/bin/bash
# MSearch完整启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 尝试检测项目根目录
if [ -d "${SCRIPT_DIR}/../src" ] || [ -d "${SCRIPT_DIR}/../tests" ]; then
    PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
else
    PROJECT_ROOT="${SCRIPT_DIR}"
fi

# 激活虚拟环境（如果存在）
if [ -d "${PROJECT_ROOT}/venv" ]; then
    echo "激活虚拟环境..."
    source "${PROJECT_ROOT}/venv/bin/activate"
fi

# 设置环境变量
export PYTHONPATH="${PROJECT_ROOT}"
export PYTHONWARNINGS=ignore
export KMP_DUPLICATE_LIB_OK=TRUE

# 检查是否有正在运行的服务
if pgrep -f "uvicorn src.api.app:app" > /dev/null; then
    echo "检测到已运行的API服务，正在停止..."
    pkill -f "uvicorn src.api.app:app"
    sleep 2
fi

echo "==============================================="
echo "          MSearch 服务启动脚本                "
echo "==============================================="
echo ""
echo "启动API服务..."
echo "API地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "查看日志: tail -f ${PROJECT_ROOT}/logs/msearch.log"
echo "停止服务: pkill -f 'uvicorn src.api.app:app'"
echo ""

# 启动API服务（后台运行）
cd "${PROJECT_ROOT}"
python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload > "${PROJECT_ROOT}/logs/api.log" 2>&1 &
API_PID=$!

echo "API服务已启动，进程ID: ${API_PID}"
echo "==============================================="
EOF
    chmod +x "${START_SCRIPT}"
    
    # 生成Qdrant启动脚本

    cat > "${QDRANT_SCRIPT}" << EOF
#!/bin/bash
# Qdrant向量数据库服务启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} 启动Qdrant向量数据库服务..."

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

# 设置Qdrant数据目录
export QDRANT_DATA_DIR="${PROJECT_ROOT}/data/qdrant"
mkdir -p "${QDRANT_DATA_DIR}"

# 使用离线下载的Qdrant二进制文件
    if [ -f "${PROJECT_ROOT}/temp/bin/qdrant" ]; then
        echo "使用离线Qdrant二进制文件启动服务..."
        "${PROJECT_ROOT}/temp/bin/qdrant" --storage-path "${QDRANT_DATA_DIR}" &
        QDRANT_PID=$!
elif command -v qdrant &> /dev/null; then
    echo "使用系统安装的Qdrant二进制文件启动服务..."
    qdrant --storage-path "${QDRANT_DATA_DIR}" &
    QDRANT_PID=$!
else
    echo -e "${YELLOW}警告：未找到Qdrant二进制文件，尝试使用Docker...${NC}"
    if command -v docker &> /dev/null; then
        docker run -d \
            --name qdrant-msearch \
            -p 6333:6333 \
            -p 6334:6334 \
            -v "${QDRANT_DATA_DIR}:/qdrant/storage" \
            qdrant/qdrant:latest
        echo "Qdrant Docker容器已启动"
        return 0
    else
        echo "错误：未找到Qdrant二进制文件或Docker"
        exit 1
    fi
fi

# 保存PID文件
echo $QDRANT_PID > /tmp/qdrant.pid

echo -e "${GREEN}[INFO]${NC} Qdrant服务启动完成！"
echo "Qdrant服务PID: $QDRANT_PID"
echo "服务地址: http://localhost:6333"
echo "Web UI: http://localhost:6333/dashboard"
echo ""
echo "服务健康检查:"
echo "curl http://localhost:6333/health"
EOF
    chmod +x "${QDRANT_SCRIPT}"
    
    # 生成Qdrant停止脚本
    STOP_QDRANT_SCRIPT="${PROJECT_ROOT}/scripts/stop_qdrant.sh"
    cat > "${STOP_QDRANT_SCRIPT}" << EOF
#!/bin/bash
# Qdrant服务停止脚本

echo "停止Qdrant服务..."

# 停止进程
if [ -f /tmp/qdrant.pid ]; then
    kill $(cat /tmp/qdrant.pid) 2>/dev/null && rm /tmp/qdrant.pid
    echo "Qdrant进程已停止"
fi

# 停止Docker容器
if command -v docker &> /dev/null; then
    if docker ps -q -f name=qdrant-msearch | grep -q .; then
        docker stop qdrant-msearch
        docker rm qdrant-msearch
        echo "Qdrant Docker容器已停止"
    fi
fi

echo "Qdrant服务已完全停止"
EOF
    chmod +x "${STOP_QDRANT_SCRIPT}"
    
    log_success "启动脚本生成完成！"
    log_info "- API启动脚本: ${API_SCRIPT}"
    log_info "- 完整启动脚本: ${START_SCRIPT}"
    log_info "- Qdrant启动脚本: ${QDRANT_SCRIPT}"
    log_info "- Qdrant停止脚本: ${STOP_QDRANT_SCRIPT}"
}

# 创建安装说明文件
create_install_guide() {
    log_info "==============================================="
    log_info "          创建安装说明文件"
    log_info "==============================================="
    
    # 创建安装说明文件
    INSTALL_GUIDE="${PROJECT_ROOT}/INSTALL_GUIDE.md"
    cat > "${INSTALL_GUIDE}" << 'EOF'
# MSearch 安装指南

## 快速开始

### 环境要求
- Python 3.9-3.11
- Git
- 足够的磁盘空间（推荐至少10GB）
- 对于Linux系统：gcc, build-essential, libssl-dev, libffi-dev, python3-dev
- 对于Windows系统：Visual C++ Build Tools

### 安装步骤

1. **环境准备**
   ```bash
   # Linux
   # 安装系统依赖
   sudo apt-get update
   sudo apt-get install -y gcc build-essential libssl-dev libffi-dev python3-dev
   
   # 检查Python版本
   python --version
   
   # 克隆项目（如果需要）
   git clone <项目仓库地址>
   cd msearch
   ```
   
   ```batch
   :: Windows
   :: 请确保已安装Visual C++ Build Tools
   :: 检查Python版本
   python --version
   ```

2. **安装依赖和启动服务**
   ```bash
   # 自动检测模式（推荐）
   cd scripts
   chmod +x install.sh
   ./install.sh
   
   # 在线模式安装
   ./install.sh --online
   
   # 离线模式安装（需先准备离线资源）
   ./install.sh --offline
   
   # 仅下载离线资源
   ./install.sh --download-only
   ```

3. **启动服务**
   ```bash
   # 启动Qdrant服务
   ./start_qdrant.sh
   
   # 启动API服务（前台运行）
   ./start_api.sh
   
   # 启动所有服务（后台运行）
   ./start_all.sh
   ```

## 功能说明

- **自动检测模式**：优先使用离线资源，否则自动下载，适合大多数场景
- **在线模式**：自动下载依赖和模型，适合有网络环境
- **离线模式**：使用预下载的资源安装，适合无网络环境
- **虚拟环境**：离线模式默认创建虚拟环境，在线模式可选
- **自动配置**：自动生成配置文件和启动脚本
- **支持多种系统**：兼容Linux和Windows系统

## 使用说明

### API服务
- API地址：http://localhost:8000
- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### Qdrant服务
- 服务地址：http://localhost:6333
- Web UI：http://localhost:6333/dashboard
- 健康检查：http://localhost:6333/health

### 日志查看
```bash
# 查看API日志
tail -f logs/api.log

# 查看应用日志
tail -f logs/msearch.log
```

### 停止服务
```bash
# 停止前台运行的服务
Ctrl + C

# 停止后台运行的服务
pkill -f "uvicorn src.api.main:app"

# 停止Qdrant服务
./stop_qdrant.sh
```

## 常见问题

1. **端口被占用**
   - 修改配置文件中的端口号
   - 或停止占用端口的进程：`lsof -i :8000` 然后 `kill <PID>`

2. **模型下载失败**
   - 检查网络连接
   - 设置HuggingFace镜像：`export HF_ENDPOINT=https://hf-mirror.com`
   - 手动下载模型并放入`data/models/`目录

3. **依赖安装问题**
   - 确保pip版本较新：`pip install --upgrade pip`
   - 尝试使用虚拟环境：`python -m venv venv && source venv/bin/activate`

4. **Python环境问题**
   - 确保使用Python 3.9-3.11版本
   - 对于CUDA支持，需要安装对应版本的PyTorch

## 离线安装准备

1. **在有网络的环境下准备离线资源**
   ```bash
   ./install.sh --download-only
   ```

2. **复制离线资源到目标机器**
   - 将整个项目目录复制到目标机器
   - 确保`offline/`目录包含所有必要的资源

3. **在目标机器上执行离线安装**
   ```bash
   ./install.sh --offline
   ```

## 注意事项

- 首次运行时会下载大量模型，需要较长时间和稳定的网络
- 确保磁盘空间充足，尤其是模型存储目录
- 生产环境部署时请修改配置文件中的相关设置
- 离线模式需要先在有网络环境下准备离线资源
EOF
    
    log_success "安装说明文件创建完成: ${INSTALL_GUIDE}"
}

# 显示安装完成信息
show_completion() {
    log_success "\n======================================"
    log_success "MSearch 安装完成！"
    log_success "======================================\n"
    
    log_info "使用说明："
    log_info "1. 启动Qdrant服务:"
    log_info "   cd ${PROJECT_ROOT}/scripts && ./start_qdrant.sh"
    log_info ""
    log_info "2. 启动API服务（前台运行）:"
    log_info "   cd ${PROJECT_ROOT}/scripts && ./start_api.sh"
    log_info ""
    log_info "3. 启动所有服务（后台运行）:"
    log_info "   cd ${PROJECT_ROOT}/scripts && ./start_all.sh"
    log_info ""
    log_info "4. 访问API文档:"
    log_info "   http://localhost:8000/docs"
    log_info ""
    log_info "5. 查看安装说明:"
    log_info "   cat ${PROJECT_ROOT}/INSTALL_GUIDE.md"
    log_info ""
    log_success "======================================\n"
}

# 在线模式主流程
main_online() {
    log_info "=================================================="
    log_info "            MSearch 在线安装模式              "
    log_info "=================================================="
    
    # 1. 检查系统环境
    check_environment_online || handle_error "环境检查失败"
    
    # 2. 安装系统依赖和Python包
    install_dependencies_online || handle_error "依赖安装失败"
    
    # 3. 下载和配置AI模型
    download_models_online || log_warning "模型下载部分失败，但继续安装"
    
    # 4. 执行硬件分析
    perform_hardware_analysis
    
    # 5. 配置项目文件
    configure_project_online || handle_error "项目配置失败"
    
    # 6. 生成启动脚本
    generate_startup_scripts || handle_error "启动脚本生成失败"
    
    # 6. 创建安装说明文件
    create_install_guide || log_warning "创建安装说明文件失败，但不影响使用"
    
    # 显示安装完成信息
    show_completion
}

# 离线模式主流程
main_offline() {
    log_info "=================================================="
    log_info "            MSearch 离线安装模式              "
    log_info "=================================================="
    
    # 1. 检查离线资源
    check_offline_resources || handle_error "离线资源检查失败"
    
    # 2. 检查系统依赖
    check_system_dependencies_offline || handle_error "系统依赖检查失败"
    
    # 3. 创建虚拟环境
    create_venv || handle_error "虚拟环境创建失败"
    
    # 4. 安装离线依赖
    install_offline_deps || handle_error "离线依赖安装失败"
    
    # 5. 复制模型文件
    copy_models || handle_error "模型文件复制失败"
    
    # 6. 执行硬件分析
    perform_hardware_analysis
    
    # 7. 初始化配置
    init_config || handle_error "配置初始化失败"
    
    # 8. 初始化数据目录
    init_data_dirs || handle_error "数据目录初始化失败"
    
    # 9. 初始化数据库
    init_database || handle_error "数据库初始化失败"
    
    # 10. 生成启动脚本
    generate_startup_scripts || handle_error "启动脚本生成失败"
    
    # 10. 创建安装说明文件
    create_install_guide || log_warning "创建安装说明文件失败，但不影响使用"
    
    # 显示安装完成信息
    show_completion
}

# 自动检测模式主流程
main_auto() {
    log_info "=================================================="
    log_info "            MSearch 自动检测模式              "
    log_info "=================================================="
    
    # 检查是否存在离线资源
    has_offline_resources=$(detect_offline_resources)
    
    if [ "$has_offline_resources" = "true" ]; then
        log_info "检测到完整的离线资源，使用离线模式安装"
        main_offline
    else
        log_info "未检测到完整的离线资源，使用在线模式安装"
        main_online
    fi
}

# 主函数
main() {
    # 解析命令行参数
    parse_args "$@"
    
    # 检测项目根目录
    detect_project_root || handle_error "项目根目录检测失败"
    
    log_info "=== MSearch 安装脚本启动 ==="
    log_info "日志文件: ${LOG_FILE}"
    log_info "项目目录: ${PROJECT_ROOT}"
    log_info "安装模式: ${INSTALL_MODE}"
    log_info "日志级别: ${LOG_LEVEL}"
    
    # 根据安装模式执行不同的主流程
    case "${INSTALL_MODE}" in
        online)
            main_online
            ;;
        offline)
            main_offline
            ;;
        download-only)
            download_all_resources || handle_error "离线资源下载失败"
            ;;
        auto)
            main_auto
            ;;
        *)
            log_error "未知的安装模式: ${INSTALL_MODE}"
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"