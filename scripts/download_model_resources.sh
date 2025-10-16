#!/bin/bash

# msearch 离线资源下载脚本
# 一键下载所有依赖和模型到本地offline目录
# 整合版 - 所有功能在一个脚本中

set -e
set -u
set -o pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 下载依赖包函数
download_dependencies() {
    log_info "1. 下载Python依赖包..."
    
    # 创建offline目录结构
    mkdir -p "$PROJECT_ROOT/offline/packages/requirements"
    
    # 下载requirements.txt中列出的所有依赖包（使用国内镜像优化）
    log_info "下载requirements.txt中所有依赖包..."
    pip download -r "$PROJECT_ROOT/requirements.txt" \
        --dest "$PROJECT_ROOT/offline/packages/requirements" \
        --disable-pip-version-check \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --timeout 60 \
        --retries 3
    
    # 特别处理inaSpeechSegmenter包（可能需要额外依赖）
    log_info "特别处理inaSpeechSegmenter包..."
    pip download inaspeechsegmenter \
        --dest "$PROJECT_ROOT/offline/packages/requirements" \
        --disable-pip-version-check \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --timeout 60 \
        --retries 3
    
    # 下载Qdrant standalone二进制文件
    log_info "下载Qdrant standalone二进制文件..."
    mkdir -p "$PROJECT_ROOT/offline/bin"
    
    # 检测系统架构
    ARCH=$(uname -m)
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    
    case "$ARCH" in
        x86_64)
            ARCH="x86_64"
            ;;
        aarch64)
            ARCH="aarch64"
            ;;
        arm64)
            ARCH="aarch64"
            ;;
        *)
            log_error "不支持的架构: $ARCH"
            return 1
            ;;
    esac
    
    case "$OS" in
        linux)
            OS="linux"
            ;;
        darwin)
            OS="macos"
            ;;
        *)
            log_error "不支持的操作系统: $OS"
            return 1
            ;;
    esac
    
    QDRANT_VERSION="1.11.3"
    QDRANT_FILENAME="qdrant-${ARCH}-${OS}"
    QDRANT_URL="https://github.com/qdrant/qdrant/releases/download/v${QDRANT_VERSION}/${QDRANT_FILENAME}"
    
    # 使用GitHub代理加速下载
    QDRANT_PROXY_URL="https://gh-proxy.com/${QDRANT_URL}"
    
    log_info "正在下载Qdrant ${QDRANT_VERSION} for ${OS}-${ARCH}..."
    log_info "下载地址: ${QDRANT_PROXY_URL}"
    
    if command -v wget &> /dev/null; then
        wget --timeout=60 --tries=3 -O "$PROJECT_ROOT/offline/bin/qdrant" "$QDRANT_PROXY_URL" || \
        wget --timeout=60 --tries=3 -O "$PROJECT_ROOT/offline/bin/qdrant" "$QDRANT_URL"
    elif command -v curl &> /dev/null; then
        curl --connect-timeout 60 --retry 3 -L -o "$PROJECT_ROOT/offline/bin/qdrant" "$QDRANT_PROXY_URL" || \
        curl --connect-timeout 60 --retry 3 -L -o "$PROJECT_ROOT/offline/bin/qdrant" "$QDRANT_URL"
    else
        log_error "未找到wget或curl命令，无法下载Qdrant"
        return 1
    fi
    
    if [ -f "$PROJECT_ROOT/offline/bin/qdrant" ]; then
        chmod +x "$PROJECT_ROOT/offline/bin/qdrant"
        log_info "Qdrant二进制文件下载成功"
    else
        log_error "Qdrant二进制文件下载失败"
        return 1
    fi
    
    # 验证下载结果
    requirements_count=$(find "$PROJECT_ROOT/offline/packages/requirements" -type f -name "*.whl" | wc -l)
    log_info "依赖包下载完成:"
    log_info "  - Wheel文件数量: $requirements_count"
    log_info "  - 保存位置: $PROJECT_ROOT/offline/packages/requirements/"
    
    # 检查关键依赖包是否下载成功
    key_packages=("torch" "transformers" "fastapi" "qdrant-client" "inaspeechsegmenter")
    missing_packages=()
    
    for package in "${key_packages[@]}"; do
        if ! find "$PROJECT_ROOT/offline/packages/requirements" -type f -name "*${package}*" | grep -q .; then
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -eq 0 ]; then
        log_info "所有关键依赖包下载成功！"
    else
        log_warning "以下关键依赖包可能未下载成功: ${missing_packages[*]}"
        log_warning "请检查网络连接或手动下载这些包"
    fi
    
    if [ "$requirements_count" -gt 0 ]; then
        return 0
    else
        return 1
    fi
}

# 下载PySide6函数
download_pyside6() {
    log_info "2. 下载PySide6跨平台GUI框架..."
    
    # 创建offline目录结构
    mkdir -p "$PROJECT_ROOT/offline/packages/pyside6"
    
    log_info "开始下载PySide6离线包..."
    
    # 下载PySide6及其依赖
    pip download PySide6 \
        --dest "$PROJECT_ROOT/offline/packages/pyside6" \
        --no-deps \
        --disable-pip-version-check \
        --timeout 60 \
        --retries 3
    
    # 验证下载结果
    pyside6_count=$(find "$PROJECT_ROOT/offline/packages/pyside6" -type f -name "*.whl" | wc -l)
    log_info "PySide6下载完成:"
    log_info "  - Wheel文件数量: $pyside6_count"
    log_info "  - 保存位置: $PROJECT_ROOT/offline/packages/pyside6/"
    
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
    log_info "3. 下载AI模型..."
    
    # 设置HuggingFace镜像（国内优化）
    export HF_ENDPOINT=https://hf-mirror.com
    
    # 创建模型目录结构
    mkdir -p "$PROJECT_ROOT/offline/models/huggingface"
    
    # 下载GitHub相关资源（使用代理加速）
    log_info "下载GitHub相关资源..."
    mkdir -p "$PROJECT_ROOT/offline/github"
    
    # 下载FFmpeg静态构建（用于音视频处理）
    log_info "下载FFmpeg静态构建..."
    FFMPEG_VERSION="6.1.1"
    
    case "$ARCH" in
        x86_64)
            FFMPEG_ARCH="x86_64"
            ;;
        aarch64)
            FFMPEG_ARCH="arm64"
            ;;
        *)
            log_warning "不支持的架构，跳过FFmpeg下载"
            ;;
    esac
    
    if [ -n "$FFMPEG_ARCH" ]; then
        FFMPEG_URL="https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux${FFMPEG_ARCH}-gpl-shared.tar.xz"
        FFMPEG_PROXY_URL="https://gh-proxy.com/${FFMPEG_URL}"
        
        log_info "正在下载FFmpeg..."
        if command -v wget &> /dev/null; then
            wget --timeout=60 --tries=3 -O "$PROJECT_ROOT/offline/github/ffmpeg.tar.xz" "$FFMPEG_PROXY_URL" || \
            wget --timeout=60 --tries=3 -O "$PROJECT_ROOT/offline/github/ffmpeg.tar.xz" "$FFMPEG_URL"
        elif command -v curl &> /dev/null; then
            curl --connect-timeout 60 --retry 3 -L -o "$PROJECT_ROOT/offline/github/ffmpeg.tar.xz" "$FFMPEG_PROXY_URL" || \
            curl --connect-timeout 60 --retry 3 -L -o "$PROJECT_ROOT/offline/github/ffmpeg.tar.xz" "$FFMPEG_URL"
        fi
        
        if [ -f "$PROJECT_ROOT/offline/github/ffmpeg.tar.xz" ]; then
            log_info "FFmpeg下载成功"
        else
            log_warning "FFmpeg下载失败"
        fi
    fi
    
    # 下载CLIP模型（文本-图像检索）
    log_info "1. 下载CLIP模型 (openai/clip-vit-base-patch32)..."
    huggingface-cli download \
        openai/clip-vit-base-patch32 \
        --resume-download \
        --local-dir-use-symlinks False \
        --local-dir "$PROJECT_ROOT/offline/models/clip-vit-base-patch32"
    
    # 下载CLAP模型（文本-音频检索）
    log_info "2. 下载CLAP模型 (laion/clap-htsat-fused)..."
    huggingface-cli download \
        laion/clap-htsat-fused \
        --resume-download \
        --local-dir-use-symlinks False \
        --local-dir "$PROJECT_ROOT/offline/models/clap-htsat-fused"
    
    # 下载Whisper模型（语音转文本）
    log_info "3. 下载Whisper模型 (openai/whisper-base)..."
    huggingface-cli download \
        openai/whisper-base \
        --resume-download \
        --local-dir-use-symlinks False \
        --local-dir "$PROJECT_ROOT/offline/models/whisper-base"
    
    # 下载人脸识别模型
    log_info "4. 下载人脸识别模型 (buffalo_l, buffalo_sc)..."
    
    # 下载buffalo_l模型
    huggingface-cli download \
        deepins/insightface \
        --include "models/buffalo_l/*" \
        --resume-download \
        --local-dir-use-symlinks False \
        --local-dir "$PROJECT_ROOT/offline/models/insightface"
    
    # 下载buffalo_sc模型
    huggingface-cli download \
        deepins/insightface \
        --include "models/buffalo_sc/*" \
        --resume-download \
        --local-dir-use-symlinks False \
        --local_dir "$PROJECT_ROOT/offline/models/insightface"
    
    # 验证下载结果
    log_info "5. 验证模型下载结果..."
    models_count=$(find "$PROJECT_ROOT/offline/models" -type f | wc -l)
    log_info "模型下载完成:"
    log_info "  - 模型文件数量: $models_count"
    log_info "  - 保存位置: $PROJECT_ROOT/offline/models/"
    
    # 检查关键模型是否下载成功
    key_models=("clip-vit-base-patch32" "clap-htsat-fused" "whisper-base" "insightface")
    missing_models=()
    
    for model in "${key_models[@]}"; do
        if [ ! -d "$PROJECT_ROOT/offline/models/$model" ] || [ -z "$(ls -A "$PROJECT_ROOT/offline/models/$model" 2>/dev/null)" ]; then
            missing_models+=("$model")
        fi
    done
    
    if [ ${#missing_models[@]} -eq 0 ]; then
        log_info "所有关键模型下载成功！"
    else
        log_warning "以下关键模型可能未下载成功: ${missing_models[*]}"
        log_warning "请检查网络连接或手动下载这些模型"
    fi
    
    if [ "$models_count" -gt 0 ]; then
        return 0
    else
        return 1
    fi
}

log_info "开始下载所有离线资源..."

# 确保huggingface_hub已安装（用于模型下载）
log_info "0. 确保huggingface_hub已安装..."
if command -v pip &> /dev/null; then
    pip install huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade || true
else
    log_warning "未找到pip，跳过huggingface_hub安装"
fi

# 执行下载任务
if download_dependencies; then
    log_info "依赖包下载成功"
else
    log_error "依赖包下载失败"
    exit 1
fi

if download_pyside6; then
    log_info "PySide6下载成功"
else
    log_warning "PySide6下载失败，但继续执行其他下载任务"
fi

if download_models; then
    log_info "模型下载成功"
else
    log_error "模型下载失败"
    exit 1
fi

# 验证下载结果
log_info "4. 验证下载结果..."
if [ -d "$PROJECT_ROOT/offline/packages" ] && [ -d "$PROJECT_ROOT/offline/models" ]; then
    packages_count=$(find "$PROJECT_ROOT/offline/packages" -type f | wc -l)
    models_count=$(find "$PROJECT_ROOT/offline/models" -type f | wc -l)
    
    log_info "离线资源下载完成:"
    log_info "  - 依赖包数量: $packages_count"
    log_info "  - 模型文件数量: $models_count"
    log_info "  - 保存位置: $PROJECT_ROOT/offline/"
    
    if [ "$packages_count" -gt 0 ] && [ "$models_count" -gt 0 ]; then
        log_info "所有离线资源下载完成！"
    else
        log_warning "部分资源下载可能不完整，请检查目录内容"
    fi
else
    log_error "离线资源下载失败，请检查目录结构"
    exit 1
fi

# 生成Qdrant服务启动脚本
log_info "6. 生成Qdrant服务启动脚本..."
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

# 生成infinity服务启动脚本
log_info "7. 生成infinity服务启动脚本..."
cat > "$PROJECT_ROOT/scripts/start_infinity_services.sh" << 'EOF'
#!/bin/bash
# Infinity多模型服务启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} 启动Infinity多模型服务..."

# 设置模型缓存路径（指向离线下载的模型）
export HF_HOME="$PROJECT_ROOT/offline/models/huggingface"
export TRANSFORMERS_CACHE="$HF_HOME"

# 创建缓存目录
mkdir -p "$HF_HOME"

# 启动CLIP模型服务（端口7997）
echo "启动CLIP模型服务 (端口7997)..."
infinity_emb v2 --model-id "openai/clip-vit-base-patch32" --port 7997 --device cpu &
CLIP_PID=$!

# 启动CLAP模型服务（端口7998）
echo "启动CLAP模型服务 (端口7998)..."
infinity_emb v2 --model-id "laion/clap-htsat-fused" --port 7998 --device cpu &
CLAP_PID=$!

# 启动Whisper模型服务（端口7999）
echo "启动Whisper模型服务 (端口7999)..."
infinity_emb v2 --model-id "openai/whisper-base" --port 7999 --device cpu &
WHISPER_PID=$!

# 保存PID文件
echo $CLIP_PID > /tmp/infinity_clip.pid
echo $CLAP_PID > /tmp/infinity_clap.pid
echo $WHISPER_PID > /tmp/infinity_whisper.pid

echo -e "${GREEN}[INFO]${NC} Infinity服务启动完成！"
echo "CLIP服务PID: $CLIP_PID"
echo "CLAP服务PID: $CLAP_PID"
echo "Whisper服务PID: $WHISPER_PID"
echo ""
echo "服务健康检查:"
echo "curl http://localhost:7997/health"
echo "curl http://localhost:7998/health"
echo "curl http://localhost:7999/health"
EOF

chmod +x "$PROJECT_ROOT/scripts/start_infinity_services.sh"

# 生成服务停止脚本
cat > "$PROJECT_ROOT/scripts/stop_infinity_services.sh" << 'EOF'
#!/bin/bash
# Infinity服务停止脚本

echo "停止Infinity服务..."

if [ -f /tmp/infinity_clip.pid ]; then
    kill $(cat /tmp/infinity_clip.pid) 2>/dev/null && rm /tmp/infinity_clip.pid
    echo "CLIP服务已停止"
fi

if [ -f /tmp/infinity_clap.pid ]; then
    kill $(cat /tmp/infinity_clap.pid) 2>/dev/null && rm /tmp/infinity_clap.pid
    echo "CLAP服务已停止"
fi

if [ -f /tmp/infinity_whisper.pid ]; then
    kill $(cat /tmp/infinity_whisper.pid) 2>/dev/null && rm /tmp/infinity_whisper.pid
    echo "Whisper服务已停止"
fi

echo "所有Infinity服务已停止"
EOF

chmod +x "$PROJECT_ROOT/scripts/stop_infinity_services.sh"

log_info "Infinity服务启动脚本已生成:"
log_info "  - 启动脚本: $PROJECT_ROOT/scripts/start_infinity_services.sh"
log_info "  - 停止脚本: $PROJECT_ROOT/scripts/stop_infinity_services.sh"

log_info "所有离线资源下载脚本执行完成！"
log_info ""
log_info "8. 后续操作指南："
echo "1. 安装依赖包："
echo "   pip install --no-index --find-links=offline/packages -r requirements.txt"
echo ""
echo "2. 安装PySide6："
echo "   pip install --no-index --find-links=offline/packages/pyside6 PySide6"
echo ""
echo "3. 启动Qdrant服务："
echo "   ./scripts/start_qdrant.sh"
echo ""
echo "4. 启动Infinity服务："
echo "   ./scripts/start_infinity_services.sh"
echo ""
echo "5. 启动主服务："
echo "   python src/api/main.py"
echo ""
echo "6. 停止服务："
echo "   ./scripts/stop_qdrant.sh"
echo "   ./scripts/stop_infinity_services.sh"