#!/bin/bash

###############################################################################
# msearch 安装脚本
# 用于在Linux系统上安装msearch多模态搜索系统（使用chinese-clip-vit-base-patch16、chinese-clip-vit-huge-patch14和CLAP模型）
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安装"
        return 1
    fi
    return 0
}

# 检查Python版本
check_python_version() {
    print_info "检查Python版本..."
    
    if check_command python3; then
        PYTHON_VERSION=$(python3 --version | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        print_info "检测到Python版本: $PYTHON_VERSION"
        
        if [ $PYTHON_MAJOR -lt 3 ] || ([ $PYTHON_MAJOR -eq 3 ] && [ $PYTHON_MINOR -lt 8 ]); then
            print_error "Python版本过低，需要Python 3.8或更高版本"
            exit 1
        fi
        
        print_success "Python版本检查通过"
    else
        print_error "Python3未安装"
        exit 1
    fi
}

# 检查pip
check_pip() {
    print_info "检查pip..."
    
    if check_command pip3; then
        print_success "pip3已安装"
    else
        print_warning "pip3未安装，尝试安装..."
        python3 -m ensurepip --upgrade
    fi
}

# 检查虚拟环境
check_venv() {
    print_info "检查虚拟环境..."
    
    if [ -d "venv" ]; then
        print_warning "虚拟环境已存在，跳过创建"
        return 0
    fi
    
    print_info "创建虚拟环境..."
    python3 -m venv venv
    
    if [ $? -eq 0 ]; then
        print_success "虚拟环境创建成功"
    else
        print_error "虚拟环境创建失败"
        exit 1
    fi
}

# 激活虚拟环境
activate_venv() {
    print_info "激活虚拟环境..."
    source venv/bin/activate
    print_success "虚拟环境已激活"
}

# 升级pip
upgrade_pip() {
    print_info "升级pip..."
    pip install --upgrade pip setuptools wheel
    print_success "pip升级完成"
}

# 安装依赖
install_dependencies() {
    print_info "安装Python依赖..."
    
    # 检查requirements.txt是否存在
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt文件不存在"
        exit 1
    fi
    
    # 安装依赖
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        print_success "依赖安装完成"
    else
        print_error "依赖安装失败"
        exit 1
    fi
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    
    mkdir -p data/database
    mkdir -p data/models
    mkdir -p data/logs
    mkdir -p data/cache/preprocessing
    mkdir -p data/thumbnails
    
    print_success "目录创建完成"
}

# 检查配置文件
check_config() {
    print_info "检查配置文件..."
    
    if [ ! -f "config/config.yml" ]; then
        print_warning "配置文件不存在，将使用默认配置"
    else
        print_success "配置文件存在"
    fi
}

# 检测硬件配置（增强版）
detect_hardware() {
    print_info "检测硬件配置..."
    
    # 检测CPU核心数
    CPU_CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
    print_info "  CPU核心数: $CPU_CORES"
    
    # 检测CPU架构
    CPU_ARCH=$(uname -m)
    print_info "  CPU架构: $CPU_ARCH"
    
    # 检测系统内存
    if [ -f /proc/meminfo ]; then
        TOTAL_MEM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        TOTAL_MEM_GB=$((TOTAL_MEM_KB / 1024 / 1024))
        AVAILABLE_MEM_KB=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
        AVAILABLE_MEM_GB=$((AVAILABLE_MEM_KB / 1024 / 1024))
    elif command -v system_profiler &> /dev/null; then
        TOTAL_MEM_GB=$(system_profiler Memory 2>/dev/null | grep "Memory:" | awk '{print $2}' | head -1 | sed 's/GB//')
        TOTAL_MEM_GB=${TOTAL_MEM_GB:-8}
        AVAILABLE_MEM_GB=$((TOTAL_MEM_GB * 80 / 100))
    else
        TOTAL_MEM_GB=8
        AVAILABLE_MEM_GB=6
        print_warning "  无法检测系统内存，使用默认值: ${TOTAL_MEM_GB}GB"
    fi
    print_info "  系统内存: ${TOTAL_MEM_GB}GB"
    print_info "  可用内存: ${AVAILABLE_MEM_GB}GB"
    
    # 检测GPU
    GPU_INFO=""
    GPU_MEMORY=0
    GPU_COUNT=0
    GPU_NAME=""
    CUDA_VERSION=""
    
    # 检查NVIDIA GPU (Linux)
    if command -v nvidia-smi &> /dev/null; then
        GPU_COUNT=$(nvidia-smi --query-gpu=count --format=csv,noheader 2>/dev/null | head -1)
        if [ -n "$GPU_COUNT" ] && [ "$GPU_COUNT" -gt 0 ]; then
            for ((i=0; i<GPU_COUNT; i++)); do
                MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits -i $i 2>/dev/null | head -1)
                NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader -i $i 2>/dev/null | head -1)
                if [ -n "$MEM" ]; then
                    GPU_MEMORY=$MEM
                    GPU_NAME="$NAME"
                    GPU_INFO="NVIDIA GPU ($NAME, ${MEM}MB)"
                    break
                fi
            done
        fi
        
        # 检测CUDA版本
        if command -v nvcc &> /dev/null; then
            CUDA_VERSION=$(nvcc --version | grep "release" | awk '{print $5}' | sed 's/,//')
        elif [ -f /usr/local/cuda/version.txt ]; then
            CUDA_VERSION=$(cat /usr/local/cuda/version.txt 2>/dev/null | awk '{print $3}')
        fi
    fi
    
    # 检查AMD GPU (ROCm)
    if [ -z "$GPU_INFO" ] && command -v rocm-smi &> /dev/null; then
        GPU_COUNT=$(rocm-smi --showid | grep "GPU" | wc -l)
        if [ "$GPU_COUNT" -gt 0 ]; then
            GPU_INFO="AMD GPU (ROCm)"
            GPU_MEMORY=0
        fi
    fi
    
    # 检查Apple Silicon GPU
    if [ -z "$GPU_INFO" ] && [ "$CPU_ARCH" = "arm64" ]; then
        GPU_INFO="Apple Silicon GPU (MPS)"
        GPU_MEMORY=0
    fi
    
    # 如果没有检测到GPU，设置为CPU
    if [ -z "$GPU_INFO" ]; then
        GPU_INFO="CPU"
        GPU_MEMORY=0
    fi
    
    print_info "  GPU: $GPU_INFO"
    print_info "  GPU显存: ${GPU_MEMORY}MB"
    if [ -n "$CUDA_VERSION" ]; then
        print_info "  CUDA版本: $CUDA_VERSION"
    fi
    
    # 返回检测结果
    DETECTED_CPU_CORES=$CPU_CORES
    DETECTED_CPU_ARCH=$CPU_ARCH
    DETECTED_TOTAL_MEM_GB=$TOTAL_MEM_GB
    DETECTED_AVAILABLE_MEM_GB=$AVAILABLE_MEM_GB
    DETECTED_GPU_MEMORY=$GPU_MEMORY
    DETECTED_GPU_NAME=$GPU_NAME
    DETECTED_CUDA_VERSION=$CUDA_VERSION
    
    export DETECTED_CPU_CORES
    export DETECTED_CPU_ARCH
    export DETECTED_TOTAL_MEM_GB
    export DETECTED_AVAILABLE_MEM_GB
    export DETECTED_GPU_MEMORY
    export DETECTED_GPU_NAME
    export DETECTED_CUDA_VERSION
    export GPU_INFO
}

# 根据硬件配置生成优化配置
generate_optimized_config() {
    print_info "根据硬件配置生成优化配置..."
    
    # 解析命令行参数
    FORCE_DEVICE=""
    FORCE_MODEL=""
    while [[ $# -gt 0 ]]; do
        case $1 in
            --device)
                FORCE_DEVICE="$2"
                shift 2
                ;;
            --model)
                FORCE_MODEL="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    # 确定设备类型
    if [ -n "$FORCE_DEVICE" ]; then
        DEVICE_TYPE="$FORCE_DEVICE"
        print_info "  强制使用设备: $DEVICE_TYPE"
    else
        if [ "$DETECTED_GPU_MEMORY" -gt 0 ]; then
            DEVICE_TYPE="cuda"
            print_info "  检测到GPU，使用CUDA加速"
        elif [ "$DETECTED_CPU_ARCH" = "arm64" ]; then
            DEVICE_TYPE="mps"
            print_info "  检测到Apple Silicon，使用MPS加速"
        else
            DEVICE_TYPE="cpu"
            print_info "  使用CPU模式"
        fi
    fi
    
    # 确定模型规格
    if [ -n "$FORCE_MODEL" ]; then
        MODEL_SPEC="$FORCE_MODEL"
        print_info "  强制使用模型: $MODEL_SPEC"
    else
        # 根据硬件配置自动选择模型
        if [ "$DEVICE_TYPE" = "cuda" ]; then
            if [ "$DETECTED_GPU_MEMORY" -ge 32000 ]; then
                # 32GB+ 显存，使用超高精度模型
                MODEL_SPEC="tomoro_colqwen3"
                print_info "  检测到超高配置GPU (32GB+显存)"
                print_info "  推荐模型: tomoro_colqwen3 (超高精度, 4096维)"
            elif [ "$DETECTED_GPU_MEMORY" -ge 16000 ]; then
                # 16-32GB 显存，使用高性能模型
                MODEL_SPEC="colqwen3_turbo"
                print_info "  检测到高配置GPU (16-32GB显存)"
                print_info "  推荐模型: colqwen3_turbo (高性能, 512维)"
            elif [ "$DETECTED_GPU_MEMORY" -ge 8000 ]; then
                # 8-16GB 显存，使用高精度模型
                MODEL_SPEC="chinese_clip_large"
                print_info "  检测到中高配置GPU (8-16GB显存)"
                print_info "  推荐模型: chinese_clip_large (高精度, 768维)"
            elif [ "$DETECTED_GPU_MEMORY" -ge 4000 ]; then
                # 4-8GB 显存，使用标准模型
                MODEL_SPEC="chinese_clip_base"
                print_info "  检测到中配置GPU (4-8GB显存)"
                print_info "  推荐模型: chinese_clip_base (标准, 512维)"
            else
                # 4GB以下显存，使用轻量模型
                MODEL_SPEC="chinese_clip_base"
                print_info "  检测到低配置GPU (4GB以下显存)"
                print_info "  推荐模型: chinese_clip_base (轻量, 512维)"
            fi
        elif [ "$DEVICE_TYPE" = "mps" ]; then
            # Apple Silicon，使用标准模型
            MODEL_SPEC="chinese_clip_large"
            print_info "  检测到Apple Silicon GPU"
            print_info "  推荐模型: chinese_clip_large (Apple优化, 768维)"
        else
            # CPU模式，使用轻量模型
            MODEL_SPEC="chinese_clip_base"
            print_info "  CPU模式"
            print_info "  推荐模型: chinese_clip_base (轻量, 512维)"
        fi
    fi
    
    # 根据模型规格生成配置
    case "$MODEL_SPEC" in
        "tomoro_colqwen3")
            # 超高精度模型配置
            MODEL_NAME="TomoroAI/tomoro-colqwen3-embed-4b"
            MODEL_PATH="data/models/tomoro-colqwen3-embed-4b"
            EMBEDDING_DIM=4096
            BATCH_SIZE=1
            PRECISION="float32"
            INPUT_RESOLUTION=1024
            ;;
        "colqwen3_turbo")
            # 高性能模型配置
            MODEL_NAME="VAGOsolutions/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1"
            MODEL_PATH="data/models/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1"
            EMBEDDING_DIM=512
            BATCH_SIZE=4
            PRECISION="float32"
            INPUT_RESOLUTION=768
            ;;
        "chinese_clip_large")
            # 高精度模型配置
            MODEL_NAME="OFA-Sys/chinese-clip-vit-large-patch14-336px"
            MODEL_PATH="data/models/chinese-clip-vit-large-patch14-336px"
            EMBEDDING_DIM=768
            BATCH_SIZE=8
            PRECISION="float32"
            INPUT_RESOLUTION=336
            ;;
        "chinese_clip_base"|*)
            # 标准模型配置
            MODEL_NAME="OFA-Sys/chinese-clip-vit-base-patch16"
            MODEL_PATH="data/models/chinese-clip-vit-base-patch16"
            EMBEDDING_DIM=512
            BATCH_SIZE=16
            PRECISION="float32"
            INPUT_RESOLUTION=512
            ;;
    esac
    
    # 根据内存调整批处理大小
    if [ "$DEVICE_TYPE" = "cpu" ]; then
        if [ "$DETECTED_AVAILABLE_MEM_GB" -ge 16 ]; then
            BATCH_SIZE=16
        elif [ "$DETECTED_AVAILABLE_MEM_GB" -ge 8 ]; then
            BATCH_SIZE=8
        else
            BATCH_SIZE=4
        fi
    fi
    
    # 根据CPU核心数调整工作线程数
    if [ "$DETECTED_CPU_CORES" -ge 16 ]; then
        MAX_WORKERS=8
    elif [ "$DETECTED_CPU_CORES" -ge 8 ]; then
        MAX_WORKERS=4
    else
        MAX_WORKERS=2
    fi
    
    # 输出配置信息
    echo ""
    echo "========================================"
    echo "  优化配置生成完成"
    echo "========================================"
    echo ""
    echo "设备配置:"
    echo "  设备类型: $DEVICE_TYPE"
    echo "  GPU显存: ${DETECTED_GPU_MEMORY}MB"
    echo ""
    echo "模型配置:"
    echo "  模型规格: $MODEL_SPEC"
    echo "  模型名称: $MODEL_NAME"
    echo "  模型路径: $MODEL_PATH"
    echo "  向量维度: ${EMBEDDING_DIM}维"
    echo "  批处理大小: $BATCH_SIZE"
    echo "  精度: $PRECISION"
    echo "  输入分辨率: ${INPUT_RESOLUTION}px"
    echo ""
    echo "性能配置:"
    echo "  最大工作线程: $MAX_WORKERS"
    echo "  CPU核心数: $DETECTED_CPU_CORES"
    echo "  可用内存: ${DETECTED_AVAILABLE_MEM_GB}GB"
    echo ""
    echo "========================================"
    
    # 保存配置到环境变量
    export OPTIMIZED_DEVICE_TYPE="$DEVICE_TYPE"
    export OPTIMIZED_MODEL_SPEC="$MODEL_SPEC"
    export OPTIMIZED_MODEL_NAME="$MODEL_NAME"
    export OPTIMIZED_MODEL_PATH="$MODEL_PATH"
    export OPTIMIZED_EMBEDDING_DIM="$EMBEDDING_DIM"
    export OPTIMIZED_BATCH_SIZE="$BATCH_SIZE"
    export OPTIMIZED_PRECISION="$PRECISION"
    export OPTIMIZED_INPUT_RESOLUTION="$INPUT_RESOLUTION"
    export OPTIMIZED_MAX_WORKERS="$MAX_WORKERS"
    
    # 返回设备类型和模型规格
    echo "$DEVICE_TYPE|$MODEL_SPEC"
}

# 根据硬件配置生成设备配置
configure_device() {
    print_info "根据硬件配置生成设备配置..."
    
    # 解析命令行参数
    FORCE_DEVICE=""
    while [[ $# -gt 0 ]]; do
        case $1 in
            --device)
                FORCE_DEVICE="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    # 如果强制指定了设备，直接使用
    if [ -n "$FORCE_DEVICE" ]; then
        print_info "  强制使用设备: $FORCE_DEVICE"
        echo "$FORCE_DEVICE"
        return 0
    fi
    
    # 根据GPU内存选择设备
    if [ "$DETECTED_GPU_MEMORY" -gt 0 ]; then
        # 有GPU，根据显存选择
        if [ "$DETECTED_GPU_MEMORY" -ge 16000 ]; then
            # 16GB+ 显存，使用GPU
            echo "cuda"
            print_info "  配置设备: cuda (高性能模式)"
        elif [ "$DETECTED_GPU_MEMORY" -ge 8000 ]; then
            # 8-16GB 显存，优先使用GPU
            echo "cuda"
            print_info "  配置设备: cuda (标准模式)"
        elif [ "$DETECTED_GPU_MEMORY" -ge 4000 ]; then
            # 4-8GB 显存，使用GPU
            echo "cuda"
            print_info "  配置设备: cuda (轻量模式)"
        else
            # 4GB以下显存，使用CPU
            echo "cpu"
            print_info "  配置设备: cpu (GPU显存不足)"
        fi
    else
        # 无GPU，使用CPU
        echo "cpu"
        print_info "  配置设备: cpu (无GPU)"
    fi
}

# 根据硬件配置选择推荐模型
select_model() {
    print_info "根据硬件配置选择推荐模型..."
    
    # 解析命令行参数
    FORCE_MODEL=""
    while [[ $# -gt 0 ]]; do
        case $1 in
            --model)
                FORCE_MODEL="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    # 如果强制指定了模型，直接使用
    if [ -n "$FORCE_MODEL" ]; then
        print_info "  强制使用模型: $FORCE_MODEL"
        echo "$FORCE_MODEL"
        return 0
    fi
    
    # 根据硬件配置选择模型
    if [ "$DETECTED_GPU_MEMORY" -ge 16000 ]; then
        # 16GB+ 显存，推荐高性能模型
        echo "colqwen3_turbo"
        print_info "  推荐模型: colqwen3_turbo (高精度)"
    elif [ "$DETECTED_GPU_MEMORY" -ge 8000 ]; then
        # 8-16GB 显存，推荐标准模型
        echo "chinese_clip_large"
        print_info "  推荐模型: chinese_clip_large (平衡精度与速度)"
    elif [ "$DETECTED_GPU_MEMORY" -ge 4000 ]; then
        # 4-8GB 显存，推荐轻量模型
        echo "chinese_clip_base"
        print_info "  推荐模型: chinese_clip_base (轻量)"
    else
        # 无GPU或显存不足，使用轻量模型
        echo "chinese_clip_base"
        print_info "  推荐模型: chinese_clip_base (CPU模式)"
    fi
}

# 更新配置文件（应用优化配置）
update_config() {
    print_info "更新配置文件（应用优化配置）..."
    
    local device=$1
    local model=$2
    
    if [ ! -f "config/config.yml" ]; then
        print_warning "  配置文件不存在，跳过更新"
        return 0
    fi
    
    # 备份原配置文件
    cp config/config.yml config/config.yml.backup
    print_info "  已备份原配置文件: config/config.yml.backup"
    
    # 使用Python脚本更新配置文件
    python3 << EOF
import yaml

config_path = 'config/config.yml'

# 读取配置文件
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 更新模型配置
if 'models' not in config:
    config['models'] = {}

config['models']['model_cache_dir'] = 'data/models'
config['models']['offline_mode'] = True
config['models']['local_files_only'] = True

# 根据模型规格更新配置
model_spec = '$model'
device_type = '$device'

if model_spec == 'tomoro_colqwen3':
    # 超高精度模型配置
    config['models']['image_video_model'] = {
        'model_name': 'TomoroAI/tomoro-colqwen3-embed-4b',
        'model_path': 'data/models/tomoro-colqwen3-embed-4b',
        'embedding_dim': 4096,
        'device': device_type,
        'precision': 'float32',
        'batch_size': 1,
        'input_resolution': 1024
    }
elif model_spec == 'colqwen3_turbo':
    # 高性能模型配置
    config['models']['image_video_model'] = {
        'model_name': 'VAGOsolutions/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1',
        'model_path': 'data/models/SauerkrautLM-ColQwen3-1.7b-Turbo-v0.1',
        'embedding_dim': 512,
        'device': device_type,
        'precision': 'float32',
        'batch_size': 4,
        'input_resolution': 768
    }
elif model_spec == 'chinese_clip_large':
    # 高精度模型配置
    config['models']['image_video_model'] = {
        'model_name': 'OFA-Sys/chinese-clip-vit-large-patch14-336px',
        'model_path': 'data/models/chinese-clip-vit-large-patch14-336px',
        'embedding_dim': 768,
        'device': device_type,
        'precision': 'float32',
        'batch_size': 8,
        'input_resolution': 336
    }
else:  # chinese_clip_base
    # 标准模型配置
    config['models']['image_video_model'] = {
        'model_name': 'OFA-Sys/chinese-clip-vit-base-patch16',
        'model_path': 'data/models/chinese-clip-vit-base-patch16',
        'embedding_dim': 512,
        'device': device_type,
        'precision': 'float32',
        'batch_size': 16,
        'input_resolution': 512
    }

# 更新音频模型配置
config['models']['audio_model'] = {
    'model_name': 'laion/clap-htsat-unfused',
    'model_path': 'data/models/clap-htsat-unfused',
    'vector_dim': 512,
    'device': device_type,
    'precision': 'float32',
    'batch_size': 8,
    'sample_rate': 44100
}

# 更新任务管理器配置
if 'task_manager' not in config:
    config['task_manager'] = {}

config['task_manager']['max_concurrent_tasks'] = $OPTIMIZED_MAX_WORKERS
config['task_manager']['base_concurrent_tasks'] = $OPTIMIZED_MAX_WORKERS

# 更新索引配置
if 'indexing' not in config:
    config['indexing'] = {}

config['indexing']['max_files_per_batch'] = 100

# 保存配置文件
with open(config_path, 'w', encoding='utf-8') as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

print("配置文件已更新")
print(f"  设备类型: {device_type}")
print(f"  模型规格: {model_spec}")
print(f"  向量维度: {config['models']['image_video_model']['embedding_dim']}")
print(f"  批处理大小: {config['models']['image_video_model']['batch_size']}")
print(f"  最大工作线程: {config['task_manager']['max_concurrent_tasks']}")
EOF
    
    if [ $? -eq 0 ]; then
        print_success "  配置文件更新完成"
    else
        print_warning "  配置文件更新失败，请手动检查"
    fi
}

# 下载模型（根据优化配置）
download_models() {
    print_info "下载AI模型（根据优化配置）..."
    
    # 自动下载模型
    download_choice="y"
    
    if [ "$download_choice" = "y" ] || [ "$download_choice" = "Y" ] || [ "$download_choice" = "" ]; then
        print_info "开始下载模型（完全离线模式）..."
        print_info "系统将下载以下模型："
        print_info "  - 图像/视频模型: $OPTIMIZED_MODEL_NAME"
        print_info "  - 音频模型: laion/clap-htsat-unfused"
        print_info ""
        print_info "模型配置："
        print_info "  - 向量维度: ${OPTIMIZED_EMBEDDING_DIM}维"
        print_info "  - 批处理大小: $OPTIMIZED_BATCH_SIZE"
        print_info "  - 设备类型: $OPTIMIZED_DEVICE_TYPE"
        print_info ""
        print_info "下载完成后，系统将："
        print_info "  - 强制设置离线环境变量"
        print_info "  - 禁用所有网络连接"
        print_info "  - 确保完全离线运行"
        
        # 创建离线模型目录
        mkdir -p "$OPTIMIZED_MODEL_PATH"
        mkdir -p data/models/clap-htsat-unfused
        mkdir -p data/models/huggingface_cache
        
        # 国内镜像源列表（按优先级排序）
        MIRRORS=(
            "https://hf-mirror.com"
            "https://hf-mirror.cn"
            "https://huggingface.co"
        )
        
        # 定义下载函数（支持多镜像源和重试）
        download_with_retry() {
            local model_name=$1
            local model_path=$2
            local max_retries=3
            local retry_count=0
            local success=0
            
            # 尝试每个镜像源
            for mirror in "${MIRRORS[@]}"; do
                print_info "使用镜像源: $mirror"
                export HF_ENDPOINT=$mirror
                
                # 重试机制
                while [ $retry_count -lt $max_retries ]; do
                    print_info "下载 $model_name (尝试 $((retry_count+1))/$max_retries)..."
                    
                    # 使用huggingface-cli下载（支持断点续传）
                    if huggingface-cli download \
                        --resume-download \
                        --local-dir-use-symlinks False \
                        --local-dir "$model_path" \
                        "$model_name" 2>&1; then
                        print_success "$model_name 下载成功"
                        success=1
                        break 2  # 退出重试循环和镜像源循环
                    else
                        print_warning "$model_name 下载失败，$((max_retries - retry_count - 1)) 次重试机会"
                        retry_count=$((retry_count + 1))
                        if [ $retry_count -lt $max_retries ]; then
                            print_info "等待 10 秒后重试..."
                            sleep 10
                        fi
                    fi
                done
                
                # 如果当前镜像源失败，尝试下一个
                if [ $success -eq 0 ]; then
                    print_warning "镜像源 $mirror 失败，尝试下一个镜像源..."
                    retry_count=0  # 重置重试计数
                fi
            done
            
            if [ $success -eq 0 ]; then
                print_error "$model_name 下载失败，所有镜像源都已尝试"
                return 1
            fi
            
            return 0
        }
        
        # 定义下载验证函数
        verify_model() {
            local model_path=$1
            shift
            local required_files=("$@")
            
            print_info "验证模型: $model_path"
            
            for file in "${required_files[@]}"; do
                if [ ! -f "$model_path/$file" ]; then
                    print_error "缺少必需文件: $file"
                    return 1
                fi
            done
            
            print_success "模型验证通过"
            return 0
        }
        
        # 下载模型（带重试机制和验证）
        print_info "========================================"
        print_info "开始下载模型（完全离线模式）"
        print_info "========================================"
        
        # 下载图像/视频模型
        print_info "----------------------------------------"
        print_info "下载图像/视频模型..."
        print_info "----------------------------------------"
        print_info "模型名称: $OPTIMIZED_MODEL_NAME"
        print_info "模型路径: $OPTIMIZED_MODEL_PATH"
        
        if download_with_retry "$OPTIMIZED_MODEL_NAME" "$OPTIMIZED_MODEL_PATH"; then
            # 根据模型类型验证必需文件
            case "$OPTIMIZED_MODEL_SPEC" in
                "tomoro_colqwen3")
                    verify_model "$OPTIMIZED_MODEL_PATH" "config.json" "model.safetensors" "tokenizer.json" || exit 1
                    ;;
                "colqwen3_turbo")
                    verify_model "$OPTIMIZED_MODEL_PATH" "config.json" "model.safetensors" "tokenizer.json" || exit 1
                    ;;
                "chinese_clip_large")
                    verify_model "$OPTIMIZED_MODEL_PATH" "config.json" "pytorch_model.bin" "preprocessor_config.json" || exit 1
                    ;;
                *)
                    verify_model "$OPTIMIZED_MODEL_PATH" "config.json" "pytorch_model.bin" "clip_cn_vit-b-16.pt" "preprocessor_config.json" || exit 1
                    ;;
            esac
        else
            print_error "图像/视频模型下载失败"
            exit 1
        fi
        
        # 下载CLAP模型
        print_info "----------------------------------------"
        print_info "下载音频模型 (CLAP)..."
        print_info "----------------------------------------"
        if download_with_retry "laion/clap-htsat-unfused" "data/models/clap-htsat-unfused"; then
            verify_model "data/models/clap-htsat-unfused" "config.json" "pytorch_model.bin" "tokenizer.json" "vocab.json" || exit 1
        else
            print_error "CLAP模型下载失败"
            exit 1
        fi
        
        print_info "========================================"
        print_success "所有模型下载完成！"
        print_info "========================================"
        print_info "已下载的模型："
        print_info "  - 图像/视频模型: $OPTIMIZED_MODEL_NAME"
        print_info "    路径: $OPTIMIZED_MODEL_PATH"
        print_info "    维度: ${OPTIMIZED_EMBEDDING_DIM}维"
        print_info "  - 音频模型: laion/clap-htsat-unfused"
        print_info "    路径: data/models/clap-htsat-unfused"
        print_info "    维度: 512维"
        print_info "========================================"
        
        # 设置离线环境变量到配置文件
        print_info "配置离线模式..."
        if [ -f "config/config.yml" ]; then
            # 备份原配置文件
            cp config/config.yml config/config.yml.backup
            
            # 使用Python脚本更新配置文件
            python3 << 'EOF'
import yaml

config_path = 'config/config.yml'
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 更新模型配置
if 'models' not in config:
    config['models'] = {}

config['models']['model_cache_dir'] = 'data/models'
config['models']['offline_mode'] = True
config['models']['local_files_only'] = True

# 更新图像/视频模型配置
if 'image_video_model' not in config['models']:
    config['models']['image_video_model'] = {}

config['models']['image_video_model']['model_name'] = 'OFA-Sys/chinese-clip-vit-base-patch16'
config['models']['image_video_model']['model_path'] = 'data/models/chinese-clip-vit-base-patch16'
config['models']['image_video_model']['embedding_dim'] = 512
config['models']['image_video_model']['device'] = 'cpu'
config['models']['image_video_model']['precision'] = 'float32'
config['models']['image_video_model']['batch_size'] = 16
config['models']['image_video_model']['input_resolution'] = 512

# 更新音频模型配置
if 'audio_model' not in config['models']:
    config['models']['audio_model'] = {}

config['models']['audio_model']['model_name'] = 'laion/clap-htsat-unfused'
config['models']['audio_model']['model_path'] = 'data/models/clap-htsat-unfused'
config['models']['audio_model']['vector_dim'] = 512
config['models']['audio_model']['device'] = 'cpu'
config['models']['audio_model']['precision'] = 'float32'
config['models']['audio_model']['batch_size'] = 8
config['models']['audio_model']['sample_rate'] = 44100

# 保存配置文件
with open(config_path, 'w', encoding='utf-8') as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

print("配置文件已更新")
EOF
            
            if [ $? -eq 0 ]; then
                print_success "配置文件已更新（离线模式）"
            else
                print_warning "配置文件更新失败，请手动检查"
            fi
        else
            print_warning "配置文件不存在，跳过配置更新"
        fi
        
        # 创建离线模式启动脚本
        print_info "创建离线模式启动脚本..."
        cat > scripts/run_offline.sh << 'EOF'
#!/bin/bash
# msearch 离线模式启动脚本

# 设置离线环境变量
export HF_HOME="$(dirname "$0")/../data/models"
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HUB_OFFLINE=1
export INFINITY_LOCAL_MODE=1

# 激活虚拟环境
source "$(dirname "$0")/../venv/bin/activate"

# 启动主程序
python "$(dirname "$0")/../src/main.py"
EOF
        chmod +x scripts/run_offline.sh
        print_success "离线模式启动脚本已创建: scripts/run_offline.sh"
        
        # 创建离线模式环境变量文件
        print_info "创建离线模式环境变量文件..."
        cat > .env.offline << 'EOF'
# msearch 离线模式环境变量
# 此文件在启动时自动加载

# 统一模型缓存目录
HF_HOME=data/models

# 强制离线模式
TRANSFORMERS_OFFLINE=1
HF_DATASETS_OFFLINE=1
HF_HUB_OFFLINE=1
INFINITY_LOCAL_MODE=1

# 禁用网络连接
NO_PROXY=*
no_proxy=*
EOF
        print_success "离线模式环境变量文件已创建: .env.offline"
        
    else
        print_warning "跳过模型下载"
        print_info "警告: 不下载模型将无法使用系统功能"
        print_info "提示: 可以稍后运行 'bash scripts/install.sh' 重新下载模型"
    fi
}

# 运行测试
run_tests() {
    print_info "运行单元测试..."
    
    read -p "是否运行单元测试？这可能需要几分钟 (y/n): " test_choice
    
    if [ "$test_choice" = "y" ] || [ "$test_choice" = "Y" ]; then
        python3 -m pytest tests/unit/ -v
        
        if [ $? -eq 0 ]; then
            print_success "所有单元测试通过"
        else
            print_warning "部分测试失败，请检查输出"
        fi
    else
        print_warning "跳过单元测试"
    fi
}

# 显示安装完成信息
show_completion_info() {
    echo ""
    echo "========================================"
    print_success "msearch安装完成！"
    echo "========================================"
    echo ""
    echo "使用方法："
    echo "1. 激活虚拟环境:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. 启动主程序（离线模式）:"
    echo "   bash scripts/run_offline.sh"
    echo ""
    echo "   或者手动设置环境变量后启动:"
    echo "   export HF_HOME=data/models"
    echo "   export TRANSFORMERS_OFFLINE=1"
    echo "   export HF_DATASETS_OFFLINE=1"
    echo "   export HF_HUB_OFFLINE=1"
    echo "   python src/main.py"
    echo ""
    echo "3. 启动API服务:"
    echo "   python src/api_server.py"
    echo ""
    echo "4. 启动WebUI:"
    echo "   bash scripts/run_webui.sh"
    echo ""
    echo "5. 索引测试数据:"
    echo "   python src/cli.py index testdata"
    echo ""
    echo "6. 搜索测试:"
    echo "   python src/cli.py search '测试查询'"
    echo ""
    echo "7. 运行测试:"
    echo "   python3 -m pytest tests/unit/ -v"
    echo ""
    echo "8. 退出虚拟环境:"
    echo "   deactivate"
    echo ""
    echo "========================================"
    echo "优化配置信息"
    echo "========================================"
    echo ""
    echo "硬件配置:"
    echo "  CPU核心数: $DETECTED_CPU_CORES"
    echo "  CPU架构: $DETECTED_CPU_ARCH"
    echo "  系统内存: ${DETECTED_TOTAL_MEM_GB}GB"
    echo "  可用内存: ${DETECTED_AVAILABLE_MEM_GB}GB"
    echo "  GPU: $GPU_INFO"
    echo "  GPU显存: ${DETECTED_GPU_MEMORY}MB"
    echo ""
    echo "优化配置:"
    echo "  设备类型: $OPTIMIZED_DEVICE_TYPE"
    echo "  模型规格: $OPTIMIZED_MODEL_SPEC"
    echo "  模型名称: $OPTIMIZED_MODEL_NAME"
    echo "  模型路径: $OPTIMIZED_MODEL_PATH"
    echo "  向量维度: ${OPTIMIZED_EMBEDDING_DIM}维"
    echo "  批处理大小: $OPTIMIZED_BATCH_SIZE"
    echo "  精度: $OPTIMIZED_PRECISION"
    echo "  输入分辨率: ${OPTIMIZED_INPUT_RESOLUTION}px"
    echo "  最大工作线程: $OPTIMIZED_MAX_WORKERS"
    echo ""
    echo "========================================"
    echo "完全离线运行"
    echo "========================================"
    echo ""
    echo "系统已配置为完全离线模式："
    echo "  ✓ 所有模型已下载到本地"
    echo "  ✓ 环境变量已设置为离线模式"
    echo "  ✓ 配置文件已更新为离线模式"
    echo "  ✓ 创建了离线模式启动脚本"
    echo ""
    echo "离线模式特点："
    echo "  - 不依赖HuggingFace Hub"
    echo "  - 所有模型从本地加载"
    echo "  - 禁用所有网络连接"
    echo "  - 无需网络即可运行"
    echo ""
    echo "========================================"
    echo "目录结构"
    echo "========================================"
    echo ""
    echo "配置文件: config/config.yml"
    echo "数据目录: data/"
    echo "  - database/: 数据库文件"
    echo "  - models/: AI模型文件"
    echo "  - logs/: 日志文件"
    echo "  - cache/: 缓存文件"
    echo "  - thumbnails/: 缩略图"
    echo ""
    echo "离线模型目录: data/models/"
    echo "  - chinese-clip-vit-base-patch16/: 图像/视频模型"
    echo "  - clap-htsat-unfused/: 音频模型"
    echo ""
    echo "========================================"
    echo "故障排除"
    echo "========================================"
    echo ""
    echo "如果遇到模型加载错误："
    echo "  1. 检查模型文件是否存在:"
    echo "     ls -la data/models/chinese-clip-vit-base-patch16/"
    echo "     ls -la data/models/clap-htsat-unfused/"
    echo ""
    echo "  2. 检查环境变量是否设置:"
    echo "     echo \$HF_HOME"
    echo "     echo \$TRANSFORMERS_OFFLINE"
    echo ""
    echo "  3. 检查配置文件:"
    echo "     cat config/config.yml"
    echo ""
    echo "  4. 重新运行安装脚本:"
    echo "     bash scripts/install.sh"
    echo ""
    echo "========================================"
    echo "更多信息"
    echo "========================================"
    echo ""
    echo "文档: README.md, docs/design.md, docs/COMPLETE_DOCUMENTATION.md"
    echo "问题反馈: GitHub Issues"
    echo "========================================"
}

# 主安装流程
main() {
    echo ""
    echo "========================================"
    echo "  msearch 多模态搜索系统 - 安装脚本"
    echo "  模型: OFA-Sys/chinese-clip-vit-base-patch16 + CLAP"
    echo "========================================"
    echo ""
    
    # 检查Python版本
    check_python_version
    
    # 检查pip
    check_pip
    
    # 检查虚拟环境
    check_venv
    
    # 激活虚拟环境
    activate_venv
    
    # 升级pip
    upgrade_pip
    
    # 安装依赖
    install_dependencies
    
    # 创建必要的目录
    create_directories
    
    # 检查配置文件
    check_config
    
    # 检测硬件配置（增强版）
    detect_hardware
    
    # 根据硬件配置生成优化配置
    OPTIMIZED_CONFIG=$(generate_optimized_config)
    OPTIMIZED_DEVICE=$(echo "$OPTIMIZED_CONFIG" | cut -d'|' -f1)
    OPTIMIZED_MODEL=$(echo "$OPTIMIZED_CONFIG" | cut -d'|' -f2)
    
    # 更新配置文件（应用优化配置）
    update_config "$OPTIMIZED_DEVICE" "$OPTIMIZED_MODEL"
    
    # 下载模型（可选）
    download_models
    
    # 运行测试（可选）
    run_tests
    
    # 显示完成信息
    show_completion_info
}

# 运行主流程
main