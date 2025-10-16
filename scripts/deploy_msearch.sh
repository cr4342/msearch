#!/bin/bash

# msearch 一键部署脚本
# 支持离线部署和在线部署两种模式

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

# 显示帮助信息
show_help() {
    echo "msearch 一键部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -o, --offline  离线部署模式"
    echo "  -f, --force    强制重新部署（删除现有资源）"
    echo ""
    echo "示例:"
    echo "  $0              # 在线部署"
    echo "  $0 -o           # 离线部署"
    echo "  $0 -f           # 强制重新部署"
}

# 解析命令行参数
OFFLINE_MODE=false
FORCE_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -o|--offline)
            OFFLINE_MODE=true
            shift
            ;;
        -f|--force)
            FORCE_MODE=true
            shift
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log_info "开始部署 msearch 项目..."
log_info "部署模式: $([ "$OFFLINE_MODE" = true ] && echo "离线部署" || echo "在线部署")"
log_info "强制模式: $([ "$FORCE_MODE" = true ] && echo "是" || echo "否")"

# 检查是否需要强制重新部署
if [ "$FORCE_MODE" = true ]; then
    log_info "强制重新部署模式已启用"
    read -p "这将删除现有的离线资源，是否继续？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "删除现有离线资源..."
        rm -rf "$PROJECT_ROOT/offline/"
        log_info "现有离线资源已删除"
    else
        log_info "取消强制重新部署"
        exit 0
    fi
fi

# 创建必要的目录
mkdir -p "$PROJECT_ROOT/offline/models"
mkdir -p "$PROJECT_ROOT/offline/packages"
mkdir -p "$PROJECT_ROOT/logs"

log_info "检查系统环境..."

# 检查系统环境
check_environment() {
    log_info "检查系统环境..."
    
    # 检查操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        log_info "检测到 Linux 系统"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        log_info "检测到 macOS 系统"
    else
        log_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    
    # 检查 Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        log_info "检测到 Python: $PYTHON_VERSION"
    else
        log_error "未检测到 Python3，请先安装 Python3"
        exit 1
    fi
    
    # 检查 pip
    if command -v pip3 &> /dev/null; then
        PIP_VERSION=$(pip3 --version)
        log_info "检测到 pip: $PIP_VERSION"
    else
        log_warning "未检测到 pip3，将尝试使用 python3 -m pip"
        if ! python3 -m pip --version &> /dev/null; then
            log_error "未检测到 pip，请先安装 pip"
            exit 1
        fi
    fi
    
    # 检查 Git
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version)
        log_info "检测到 Git: $GIT_VERSION"
    else
        log_error "未检测到 Git，请先安装 Git"
        exit 1
    fi
    
    # 检查 FFmpeg
    if command -v ffmpeg &> /dev/null; then
        FFMPEG_VERSION=$(ffmpeg -version | head -n 1)
        log_info "检测到 FFmpeg: $FFMPEG_VERSION"
    else
        log_warning "未检测到 FFmpeg，某些功能可能无法正常工作"
    fi
    
    # 检查 wget 或 curl
    if command -v wget &> /dev/null; then
        WGET_VERSION=$(wget --version | head -n 1)
        log_info "检测到 wget: $WGET_VERSION"
        DOWNLOAD_TOOL="wget"
    elif command -v curl &> /dev/null; then
        CURL_VERSION=$(curl --version | head -n 1)
        log_info "检测到 curl: $CURL_VERSION"
        DOWNLOAD_TOOL="curl"
    else
        log_error "未检测到 wget 或 curl，请先安装其中一个下载工具"
        exit 1
    fi
    
    log_info "系统环境检查完成"
}

# 检查离线资源
check_offline_resources() {
    log_info "检查离线资源..."
    
    if [ -d "$PROJECT_ROOT/offline/" ]; then
        if [ -d "$PROJECT_ROOT/offline/models/" ] && [ -d "$PROJECT_ROOT/offline/packages/" ]; then
            models_count=$(find "$PROJECT_ROOT/offline/models" -type f | wc -l)
            packages_count=$(find "$PROJECT_ROOT/offline/packages" -type f | wc -l)
            
            if [ "$models_count" -gt 0 ] && [ "$packages_count" -gt 0 ]; then
                log_info "检测到离线资源:"
                log_info "  - 模型文件: $models_count 个"
                log_info "  - 依赖包: $packages_count 个"
                return 0
            fi
        fi
    fi
    
    log_info "未检测到完整的离线资源"
    return 1
}

# 设置国内镜像源
setup_china_mirrors() {
    log_info "设置国内镜像源..."
    
    # 设置 HuggingFace 镜像
    export HF_ENDPOINT=https://hf-mirror.com
    log_info "已设置 HF_ENDPOINT=https://hf-mirror.com"
    
    # 设置 PyPI 镜像 (清华源)
    export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
    export PIP_EXTRA_INDEX_URL=https://pypi.org/simple
    log_info "已设置 PyPI 镜像源"
    
    # 设置 Git 镜像
    git config --global url."https://kkgithub.com/".insteadOf "https://github.com/"
    log_info "已设置 Git 镜像源"
}

# 安装Python依赖
install_python_dependencies() {
    log_info "安装Python依赖..."
    
    # 检查requirements.txt是否存在
    if [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
        log_error "未找到 requirements.txt 文件"
        exit 1
    fi
    
    # 根据部署模式选择安装方式
    if [ "$OFFLINE_MODE" = true ] || check_offline_resources; then
        log_info "使用离线模式安装依赖..."
        
        # 检查离线依赖包是否存在
        if [ ! -d "$PROJECT_ROOT/offline/packages/" ]; then
            log_error "离线依赖包目录不存在: $PROJECT_ROOT/offline/packages/"
            exit 1
        fi
        
        # 使用离线包安装依赖
        if command -v pip3 &> /dev/null; then
            pip3 install --no-index --find-links="$PROJECT_ROOT/offline/packages/" -r "$PROJECT_ROOT/requirements.txt"
        else
            python3 -m pip install --no-index --find-links="$PROJECT_ROOT/offline/packages/" -r "$PROJECT_ROOT/requirements.txt"
        fi
    else
        log_info "使用在线模式安装依赖..."
        
        # 设置国内镜像源
        setup_china_mirrors
        
        # 在线安装依赖
        if command -v pip3 &> /dev/null; then
            pip3 install -r "$PROJECT_ROOT/requirements.txt"
        else
            python3 -m pip install -r "$PROJECT_ROOT/requirements.txt"
        fi
    fi
    
    log_info "Python依赖安装完成"
}

# 下载模型文件
download_models() {
    log_info "下载模型文件..."
    
    # 检查是否已经存在模型文件
    if check_offline_resources && [ "$FORCE_MODE" = false ]; then
        log_info "模型文件已存在，跳过下载"
        return 0
    fi
    
    # 根据部署模式选择下载方式
    if [ "$OFFLINE_MODE" = true ]; then
        log_error "离线部署模式下无法下载模型文件，请提供离线模型资源"
        exit 1
    fi
    
    # 创建模型目录
    mkdir -p "$PROJECT_ROOT/offline/models"
    
    # 设置环境变量
    setup_china_mirrors
    
    # 下载模型文件
    log_info "开始下载模型文件..."
    
    # 下载CLIP模型
    log_info "下载CLIP模型: openai/clip-vit-base-patch32"
    if command -v huggingface-cli &> /dev/null; then
        huggingface-cli download --resume-download --local-dir-use-symlinks False "openai/clip-vit-base-patch32" --local-dir "$PROJECT_ROOT/offline/models/clip-vit-base-patch32"
    else
        log_error "未安装 huggingface_hub，请先安装: pip install huggingface_hub"
        exit 1
    fi
    
    # 下载CLAP模型
    log_info "下载CLAP模型: laion/clap-htsat-fused"
    if command -v huggingface-cli &> /dev/null; then
        huggingface-cli download --resume-download --local-dir-use-symlinks False "laion/clap-htsat-fused" --local-dir "$PROJECT_ROOT/offline/models/clap-htsat-fused"
    else
        log_error "未安装 huggingface_hub，请先安装: pip install huggingface_hub"
        exit 1
    fi
    
    # 下载Whisper模型
    log_info "下载Whisper模型: openai/whisper-base"
    if command -v huggingface-cli &> /dev/null; then
        huggingface-cli download --resume-download --local-dir-use-symlinks False "openai/whisper-base" --local-dir "$PROJECT_ROOT/offline/models/whisper-base"
    else
        log_error "未安装 huggingface_hub，请先安装: pip install huggingface_hub"
        exit 1
    fi
    
    log_info "模型文件下载完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 生成infinity服务启动脚本
    log_info "生成infinity服务启动脚本..."
    cat > "$PROJECT_ROOT/scripts/start_infinity_services.sh" << 'EOF'
#!/bin/bash
# Infinity多模型服务启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} 启动Infinity多模型服务..."

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 设置模型缓存路径（指向离线下载的模型）
export HF_HOME="$PROJECT_ROOT/offline/models/huggingface"
export TRANSFORMERS_CACHE="$HF_HOME"

# 创建缓存目录
mkdir -p "$HF_HOME"

# 启动CLIP模型服务（端口7997）
echo "启动CLIP模型服务 (端口7997)..."
infinity_emb v2 --model-id "$PROJECT_ROOT/offline/models/clip-vit-base-patch32" --port 7997 --device cpu &
CLIP_PID=$!

# 启动CLAP模型服务（端口7998）
echo "启动CLAP模型服务 (端口7998)..."
infinity_emb v2 --model-id "$PROJECT_ROOT/offline/models/clap-htsat-fused" --port 7998 --device cpu &
CLAP_PID=$!

# 启动Whisper模型服务（端口7999）
echo "启动Whisper模型服务 (端口7999)..."
infinity_emb v2 --model-id "$PROJECT_ROOT/offline/models/whisper-base" --port 7999 --device cpu &
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
    log_info "生成服务停止脚本..."
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
    
    log_info "服务脚本生成完成"
    log_info "启动服务: ./scripts/start_infinity_services.sh"
    log_info "停止服务: ./scripts/stop_infinity_services.sh"
}

# 主部署流程
main() {
    log_info "开始执行部署流程..."
    
    # 1. 安装Python依赖
    install_python_dependencies
    
    # 2. 下载模型文件（在线模式）
    if [ "$OFFLINE_MODE" = false ]; then
        download_models
    fi
    
    # 3. 生成并启动服务
    start_services
    
    log_info "部署完成！"
    log_info ""
    log_info "下一步操作:"
    log_info "1. 启动服务: ./scripts/start_infinity_services.sh"
    log_info "2. 启动API服务: python3 src/api/main.py"
}

# 执行主流程
main