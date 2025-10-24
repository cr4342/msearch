#!/bin/bash
# 整合的离线资源下载脚本
# 合并了download_model_resources.sh和download_qdrant_fixed.sh的功能

set -e
set -u
set -o pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/download_resources_${TIMESTAMP}.log"
LOG_LEVEL="INFO"  # 可选: DEBUG, INFO, WARNING, ERROR, CRITICAL

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日志级别映射
declare -A LOG_LEVEL_MAP
LOG_LEVEL_MAP["DEBUG"]=0
LOG_LEVEL_MAP["INFO"]=1
LOG_LEVEL_MAP["WARNING"]=2
LOG_LEVEL_MAP["ERROR"]=3
LOG_LEVEL_MAP["CRITICAL"]=4

# 日志级别转换函数
level_to_num() {
    echo "${LOG_LEVEL_MAP[$1]:-1}"
}

# 判断是否应该记录该级别的日志
should_log() {
    local log_level="$1"
    local current_level="$LOG_LEVEL"
    
    [ $(level_to_num "$log_level") -ge $(level_to_num "$current_level") ]
}

# 格式化日志信息
format_log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    echo "[$timestamp] [$level] $message"
}

# 输出日志到控制台
log_to_console() {
    local level="$1"
    local message="$2"
    
    case "$level" in
        DEBUG)
            echo -e "${BLUE}$message${NC}"
            ;;
        INFO)
            echo -e "${GREEN}$message${NC}"
            ;;
        WARNING)
            echo -e "${YELLOW}$message${NC}"
            ;;
        ERROR|CRITICAL)
            echo -e "${RED}$message${NC}"
            ;;
    esac
}

# 通用日志函数
log() {
    local level="${1:-INFO}"
    local message="$2"
    
    if should_log "$level"; then
        local formatted_message=$(format_log "$level" "$message")
        
        # 输出到控制台
        log_to_console "$level" "$formatted_message"
        
        # 输出到文件
        echo "$formatted_message" >> "$LOG_FILE"
    fi
}

# 便捷日志函数
log_info() {
    log "INFO" "$1"
}

log_warning() {
    log "WARNING" "$1"
}

log_error() {
    log "ERROR" "$1"
}

# 初始化日志
log_info "==========================================="
log_info "开始下载离线资源..."
log_info "日志文件: ${LOG_FILE}"
log_info "==========================================="

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
    mkdir -p "$PROJECT_ROOT/offline/bin"
    
    QDRANT_VERSION="1.11.3"
    QDRANT_URL="https://github.com/qdrant/qdrant/releases/download/v${QDRANT_VERSION}/${QDRANT_FILENAME}"
    
    # 使用GitHub代理加速下载
    QDRANT_PROXY_URL="https://gh-proxy.com/${QDRANT_URL}"
    
    log_info "正在下载Qdrant ${QDRANT_VERSION} for ${ARCH}-${OS}..."
    log_info "下载地址: ${QDRANT_PROXY_URL}"
    
    # 尝试使用wget下载
    if command -v wget &> /dev/null; then
        wget --timeout=60 --tries=3 -O "$PROJECT_ROOT/offline/bin/${QDRANT_FILENAME}" "$QDRANT_PROXY_URL" || \
        wget --timeout=60 --tries=3 -O "$PROJECT_ROOT/offline/bin/${QDRANT_FILENAME}" "$QDRANT_URL"
    elif command -v curl &> /dev/null; then
        curl --connect-timeout 60 --retry 3 -L -o "$PROJECT_ROOT/offline/bin/${QDRANT_FILENAME}" "$QDRANT_PROXY_URL" || \
        curl --connect-timeout 60 --retry 3 -L -o "$PROJECT_ROOT/offline/bin/${QDRANT_FILENAME}" "$QDRANT_URL"
    else
        log_error "未找到wget或curl命令"
        return 1
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
    
    log_info "Qdrant二进制文件下载并解压成功！"
    return 0
}

# 下载依赖包函数
download_dependencies() {
    log_info "2. 下载Python依赖包..."
    
    # 创建offline目录结构
    mkdir -p "$PROJECT_ROOT/offline/packages"
    
    # 下载requirements.txt中列出的所有依赖包（使用国内镜像优化）
    log_info "下载requirements.txt中所有依赖包..."
    pip download -r "$PROJECT_ROOT/requirements.txt" \
        --dest "$PROJECT_ROOT/offline/packages" \
        --disable-pip-version-check \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --timeout 60 \
        --retries 3 || {
            log_warning "使用默认PyPI源重试..."
            pip download -r "$PROJECT_ROOT/requirements.txt" \
                --dest "$PROJECT_ROOT/offline/packages" \
                --disable-pip-version-check \
                --timeout 60 \
                --retries 3
        }
    
    # 特别处理inaSpeechSegmenter包（可能需要额外依赖）
    log_info "特别处理inaSpeechSegmenter包..."
    pip download inaspeechsegmenter \
        --dest "$PROJECT_ROOT/offline/packages" \
        --disable-pip-version-check \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --timeout 60 \
        --retries 3 || {
            log_warning "使用默认PyPI源重试..."
            pip download inaspeechsegmenter \
                --dest "$PROJECT_ROOT/offline/packages" \
                --disable-pip-version-check \
                --timeout 60 \
                --retries 3
        }
    
    # 验证下载结果
    requirements_count=$(find "$PROJECT_ROOT/offline/packages" -type f -name "*.whl" | wc -l)
    log_info "依赖包下载完成:"
    log_info "  - Wheel文件数量: $requirements_count"
    log_info "  - 保存位置: $PROJECT_ROOT/offline/packages/"
    
    # 检查关键依赖包是否下载成功
    key_packages=("torch" "transformers" "fastapi" "qdrant-client" "inaspeechsegmenter")
    missing_packages=()
    
    for package in "${key_packages[@]}"; do
        if ! find "$PROJECT_ROOT/offline/packages" -type f -name "*${package}*" | grep -q .; then
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -eq 0 ]; then
        log_info "所有关键依赖包下载成功！"
        return 0
    else
        log_warning "以下关键依赖包可能未下载成功: ${missing_packages[*]}"
        log_warning "请检查网络连接或手动下载这些包"
        return 1
    fi
}

# 下载PySide6函数
download_pyside6() {
    log_info "3. 下载PySide6跨平台GUI框架..."
    
    # 创建offline目录结构
    mkdir -p "$PROJECT_ROOT/offline/packages"
    
    log_info "开始下载PySide6离线包..."
    
    # 下载PySide6及其依赖
    pip download PySide6 \
        --dest "$PROJECT_ROOT/offline/packages" \
        --no-deps \
        --disable-pip-version-check \
        --timeout 60 \
        --retries 3 || {
            log_warning "PySide6下载失败"
            return 1
        }
    
    # 验证下载结果
    pyside6_count=$(find "$PROJECT_ROOT/offline/packages" -type f -name "*.whl" | wc -l)
    log_info "PySide6下载完成:"
    log_info "  - Wheel文件数量: $pyside6_count"
    log_info "  - 保存位置: $PROJECT_ROOT/offline/packages/"
    
    if [ "$pyside6_count" -gt 0 ]; then
        log_info "PySide6离线包下载成功！"
        return 0
    else
        log_warning "PySide6离线包下载失败！"
        return 1
    fi
}

# 下载模型函数
download_models() {
    log_info "4. 下载AI模型..."
    
    # 确保huggingface_hub已安装（用于模型下载）
    log_info "确保huggingface_hub已安装..."
    if command -v pip &> /dev/null; then
        pip install huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade || true
    else
        log_warning "未找到pip，跳过huggingface_hub安装"
    fi
    
    # 设置HuggingFace镜像（国内优化）
    export HF_ENDPOINT=https://hf-mirror.com
    
    # 创建模型目录结构
    mkdir -p "$PROJECT_ROOT/offline/models"
    
    # 检查是否已有模型
    if [ -d "$PROJECT_ROOT/offline/models/clip-vit-base-patch32" ] && [ -d "$PROJECT_ROOT/offline/models/clap-htsat-fused" ] && [ -d "$PROJECT_ROOT/offline/models/whisper-base" ]; then
        log_info "所有模型已存在，跳过下载"
        return 0
    fi
    
    # 下载CLIP模型（文本-图像检索）
    log_info "1. 下载CLIP模型 (openai/clip-vit-base-patch32)..."
    huggingface-cli download \
        openai/clip-vit-base-patch32 \
        --resume-download \
        --local-dir-use-symlinks False \
        --local-dir "$PROJECT_ROOT/offline/models/clip-vit-base-patch32" || {
            log_warning "CLIP模型下载失败"
        }
    
    # 下载CLAP模型（文本-音频检索）
    log_info "2. 下载CLAP模型 (laion/clap-htsat-fused)..."
    huggingface-cli download \
        laion/clap-htsat-fused \
        --resume-download \
        --local-dir-use-symlinks False \
        --local-dir "$PROJECT_ROOT/offline/models/clap-htsat-fused" || {
            log_warning "CLAP模型下载失败"
        }
    
    # 下载Whisper模型（语音转文本）
    log_info "3. 下载Whisper模型 (openai/whisper-base)..."
    huggingface-cli download \
        openai/whisper-base \
        --resume-download \
        --local-dir-use-symlinks False \
        --local-dir "$PROJECT_ROOT/offline/models/whisper-base" || {
            log_warning "Whisper模型下载失败"
        }
    
    # 验证下载结果
    log_info "4. 验证模型下载结果..."
    models_count=$(find "$PROJECT_ROOT/offline/models" -type f | wc -l)
    log_info "模型下载完成:"
    log_info "  - 模型文件数量: $models_count"
    log_info "  - 保存位置: $PROJECT_ROOT/offline/models/"
    
    if [ "$models_count" -gt 0 ]; then
        log_info "模型下载完成！"
        return 0
    else
        log_warning "模型下载可能不完整"
        return 1
    fi
}

# 生成服务脚本函数
generate_service_scripts() {
    log_info "5. 生成服务启动脚本..."
    
    # 生成Qdrant服务启动脚本
    cat > "$PROJECT_ROOT/scripts/start_qdrant.sh" << 'EOF'
#!/bin/bash
# Qdrant向量数据库服务启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} 启动Qdrant向量数据库服务..."

# 设置Qdrant数据目录
export QDRANT_DATA_DIR="$PROJECT_ROOT/offline/qdrant_data"
mkdir -p "$QDRANT_DATA_DIR"

# 使用离线下载的Qdrant二进制文件
if [ -f "$PROJECT_ROOT/offline/bin/qdrant" ]; then
    echo "使用离线Qdrant二进制文件启动服务..."
    "$PROJECT_ROOT/offline/bin/qdrant" --config-path "$PROJECT_ROOT/config/qdrant.yml" &
    QDRANT_PID=$!
else
    echo "离线Qdrant二进制文件不存在，尝试使用系统安装的qdrant..."
    if command -v qdrant &> /dev/null; then
        qdrant --config-path "$PROJECT_ROOT/config/qdrant.yml" &
        QDRANT_PID=$!
    else
        echo "错误：未找到Qdrant二进制文件"
        exit 1
    fi
fi

# 保存PID文件
echo $QDRANT_PID > /tmp/qdrant.pid

echo -e "${GREEN}[INFO]${NC} Qdrant服务启动完成！"
echo "Qdrant服务PID: $QDRANT_PID"
echo "服务地址: http://localhost:6333"
echo "Web UI: http://localhost:6333"
echo ""
echo "服务健康检查:"
echo "curl http://localhost:6333/health"
EOF

    chmod +x "$PROJECT_ROOT/scripts/start_qdrant.sh"

    # 生成Qdrant服务停止脚本
    cat > "$PROJECT_ROOT/scripts/stop_qdrant.sh" << 'EOF'
#!/bin/bash
# Qdrant服务停止脚本

echo "停止Qdrant服务..."

if [ -f /tmp/qdrant.pid ]; then
    kill $(cat /tmp/qdrant.pid) 2>/dev/null && rm /tmp/qdrant.pid
    echo "Qdrant服务已停止"
else
    echo "Qdrant服务未运行"
fi
EOF

    chmod +x "$PROJECT_ROOT/scripts/stop_qdrant.sh"

    log_info "服务启动脚本已生成:"
    log_info "  - Qdrant启动脚本: $PROJECT_ROOT/scripts/start_qdrant.sh"
    log_info "  - Qdrant停止脚本: $PROJECT_ROOT/scripts/stop_qdrant.sh"
}

# 主函数
main() {
    log_info "开始执行整合的离线资源下载..."
    
    # 检测系统架构
    detect_architecture
    
    # 执行下载任务
    download_qdrant
    download_dependencies
    download_pyside6
    download_models
    
    # 生成服务脚本
    generate_service_scripts
    
    # 验证下载结果
    log_info "6. 验证下载结果..."
    if [ -d "$PROJECT_ROOT/offline/bin" ] && [ -d "$PROJECT_ROOT/offline/packages" ] && [ -d "$PROJECT_ROOT/offline/models" ]; then
        bin_count=$(find "$PROJECT_ROOT/offline/bin" -type f | wc -l)
        packages_count=$(find "$PROJECT_ROOT/offline/packages" -type f | wc -l)
        models_count=$(find "$PROJECT_ROOT/offline/models" -type f | wc -l)
        
        log_info "离线资源下载完成:"
        log_info "  - 二进制文件数量: $bin_count"
        log_info "  - 依赖包数量: $packages_count"
        log_info "  - 模型文件数量: $models_count"
        log_info "  - 保存位置: $PROJECT_ROOT/offline/"
        
        log_info "所有离线资源下载脚本执行完成！"
        log_info ""
        log_info "后续操作指南："
        echo "1. 安装依赖包："
        echo "   pip install --no-index --find-links=offline/packages -r requirements.txt"
        echo ""
        echo "2. 安装PySide6："
        echo "   pip install --no-index --find-links=offline/packages PySide6"
        echo ""
        echo "3. 启动Qdrant服务："
        echo "   ./scripts/start_qdrant.sh"
        echo ""
        echo "4. 启动主服务："
        echo "   python src/api/main.py"
        echo ""
        echo "5. 停止服务："
        echo "   ./scripts/stop_qdrant.sh"
    else
        log_error "离线资源下载失败，请检查目录结构"
        exit 1
    fi
}

# 执行主函数
main
