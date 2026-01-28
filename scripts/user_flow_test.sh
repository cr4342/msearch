#!/bin/bash
# msearch 用户流程测试脚本
# 模拟真实用户的安装和使用流程

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

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

print_step() {
    local step=$1
    local total=$2
    local message=$3
    echo -e "\n${CYAN}[STEP ${step}/${total}]${NC} ${message}"
    echo -e "${CYAN}=====================================================${NC}"
}

# 检查系统环境
check_system() {
    print_step 1 5 "检查系统环境"
    
    # 检查操作系统
    print_info "检测操作系统..."
    OS="$(uname -s)"
    print_info "操作系统: $OS"
    
    # 检查内存
    print_info "检测系统内存..."
    if [ -f /proc/meminfo ]; then
        TOTAL_MEM=$(grep MemTotal /proc/meminfo | awk '{print $2/1024/1024 " GB"}')
    else
        TOTAL_MEM="未知"
    fi
    print_info "系统内存: $TOTAL_MEM"
    
    # 检查 CPU
    print_info "检测 CPU 核心数..."
    CPU_CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
    print_info "CPU 核心数: $CPU_CORES"
    
    # 检查 Python
    print_info "检查 Python 版本..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | awk '{print $2}')
        print_info "Python 版本: $PYTHON_VERSION"
        
        # 检查 Python 版本是否满足要求
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ $PYTHON_MAJOR -lt 3 ] || ([ $PYTHON_MAJOR -eq 3 ] && [ $PYTHON_MINOR -lt 8 ]); then
            print_error "Python 版本过低，需要 Python 3.8 或更高版本"
            return 1
        fi
        print_success "Python 版本检查通过"
    else
        print_error "Python 3 未安装"
        return 1
    fi
    
    # 检查网络连接
    print_info "检查网络连接..."
    if ping -c 1 -W 2 google.com &> /dev/null; then
        print_success "网络连接正常"
        NETWORK_AVAILABLE=true
    else
        print_warning "网络连接不可用，将使用离线模式"
        NETWORK_AVAILABLE=false
    fi
    
    print_success "系统环境检查完成"
    return 0
}

# 安装依赖和模型
install_dependencies() {
    print_step 2 5 "安装依赖和模型"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        print_info "创建虚拟环境..."
        python3 -m venv venv
        print_success "虚拟环境创建成功"
    else
        print_info "虚拟环境已存在，跳过创建"
    fi
    
    # 激活虚拟环境
    print_info "激活虚拟环境..."
    source venv/bin/activate
    print_success "虚拟环境已激活"
    
    # 升级 pip
    print_info "升级 pip..."
    pip install --upgrade pip setuptools wheel
    print_success "pip 升级完成"
    
    # 安装项目依赖
    print_info "安装项目依赖..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "依赖安装完成"
    else
        print_error "requirements.txt 文件不存在"
        return 1
    fi
    
    # 创建必要的目录
    print_info "创建必要的目录..."
    mkdir -p data/database
    mkdir -p data/models
    mkdir -p data/logs
    mkdir -p data/cache/preprocessing
    mkdir -p data/thumbnails
    mkdir -p data/pids
    mkdir -p logs
    print_success "目录创建完成"
    
    print_success "依赖安装和配置完成"
    return 0
}

# 配置系统
configure_system() {
    print_step 3 5 "配置系统"
    
    # 检查配置文件
    if [ ! -f "config/config.yml" ]; then
        print_warning "配置文件不存在，创建默认配置..."
        mkdir -p config
        cat > config/config.yml << 'EOF'
# msearch 配置文件

# 基础配置
base:
  project_name: "msearch"
  version: "1.0.0"
  debug: true

# 服务器配置
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4

# 模型配置
models:
  model_cache_dir: "data/models"
  offline_mode: true
  local_files_only: true
  
  # 图像/视频模型
  image_video_model:
    model_name: "OFA-Sys/chinese-clip-vit-base-patch16"
    model_path: "data/models/chinese-clip-vit-huge-patch14"
    embedding_dim: 512
    device: "cpu"
    precision: "float32"
    batch_size: 16
    input_resolution: 512
  
  # 音频模型
  audio_model:
    model_name: "laion/clap-htsat-unfused"
    model_path: "data/models/clap-htsat-unfused"
    vector_dim: 512
    device: "cpu"
    precision: "float32"
    batch_size: 8
    sample_rate: 44100

# 数据库配置
database:
  type: "faiss"
  index_path: "data/database/index.faiss"
  metadata_path: "data/database/metadata.json"
  batch_size: 1000
  use_gpu: false

# 文件监控配置
file_monitor:
  enabled: true
  watch_directories:
    - "testdata"
  extensions:
    - "jpg"
    - "jpeg"
    - "png"
    - "gif"
    - "bmp"
    - "mp4"
    - "avi"
    - "mov"
    - "wmv"
    - "mp3"
    - "wav"
    - "flac"
  scan_interval: 30

# 搜索配置
search:
  top_k: 20
  threshold: 0.5
  max_results: 100
  enable_cache: true
  cache_size: 1000

# 日志配置
logging:
  level: "INFO"
  file: "data/logs/msearch.log"
  rotation: "10MB"
  retention: 7
EOF
        print_success "默认配置文件创建成功"
    else
        print_info "配置文件已存在，跳过创建"
    fi
    
    # 检查测试数据目录
    if [ ! -d "testdata" ]; then
        print_info "创建测试数据目录..."
        mkdir -p testdata
        print_success "测试数据目录创建成功"
    else
        print_info "测试数据目录已存在，跳过创建"
    fi
    
    print_success "系统配置完成"
    return 0
}

# 启动服务
start_services() {
    print_step 4 5 "启动服务"
    
    # 停止已运行的服务
    print_info "停止已运行的服务..."
    if [ -f "data/pids/msearch-webui.pid" ]; then
        local pid=$(cat data/pids/msearch-webui.pid)
        kill $pid 2>/dev/null || true
        rm -f data/pids/msearch-webui.pid
        print_info "已停止旧的 WebUI 服务"
    fi
    
    # 启动 WebUI
    print_info "启动 WebUI 服务..."
    
    # 设置环境变量
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    export MSEARCH_CONFIG="$PROJECT_ROOT/config/config.yml"
    export MSEARCH_DATA_DIR="$PROJECT_ROOT/data"
    export MSEARCH_LOG_LEVEL="INFO"
    
    # 离线模式配置
    export HF_HOME="$PROJECT_ROOT/data/models"
    export TRANSFORMERS_OFFLINE=1
    export HF_DATASETS_OFFLINE=1
    export HF_HUB_OFFLINE=1
    export HF_HUB_DISABLE_IMPORT_ERROR=1
    
    # 使用端口 7860 避免冲突
    export GRADIO_SERVER_PORT=7860
    
    # 启动 WebUI 服务
    nohup python src/webui/app.py > logs/webui.log 2>&1 &
    
    local pid=$!
    echo "$pid" > data/pids/msearch-webui.pid
    
    # 等待服务启动
    print_info "等待 WebUI 服务启动..."
    sleep 5
    
    if kill -0 "$pid" 2>/dev/null; then
        print_success "WebUI 服务启动成功 (PID: $pid)"
        print_success "WebUI 地址: http://localhost:7860"
        print_success "日志文件: logs/webui.log"
        WEBUI_PID=$pid
    else
        print_error "WebUI 服务启动失败"
        print_info "查看日志: tail -f logs/webui.log"
        return 1
    fi
    
    print_success "服务启动完成"
    return 0
}

# 提供测试指南
provide_test_guide() {
    print_step 5 5 "测试指南"
    
    echo -e "\n${GREEN}=====================================================${NC}"
    echo -e "${GREEN}🎉 安装和启动完成！${NC}"
    echo -e "${GREEN}=====================================================${NC}"
    echo -e "\n${BLUE}【测试指南】${NC}"
    echo -e "\n1. ${YELLOW}打开 WebUI${NC}"
    echo -e "   - 地址: http://localhost:7860"
    echo -e "   - 请在浏览器中打开上述地址"
    echo -e "\n2. ${YELLOW}测试功能${NC}"
    echo -e "   - ${CYAN}文本搜索:${NC} 在搜索框中输入关键词，如 '猫', '风景', '人物' 等"
    echo -e "   - ${CYAN}图像搜索:${NC} 上传一张图片，系统会搜索相似的图片"
    echo -e "   - ${CYAN}音频搜索:${NC} 上传音频文件，系统会搜索相似的音频"
    echo -e "   - ${CYAN}视频搜索:${NC} 上传视频文件，系统会搜索相似的视频"
    echo -e "\n3. ${YELLOW}测试数据${NC}"
    echo -e "   - 测试数据目录: testdata/"
    echo -e "   - 您可以将测试文件放入此目录，系统会自动索引"
    echo -e "\n4. ${YELLOW}查看日志${NC}"
    echo -e "   - WebUI 日志: tail -f logs/webui.log"
    echo -e "   - 系统日志: tail -f data/logs/msearch.log"
    echo -e "\n5. ${YELLOW}停止服务${NC}"
    echo -e "   - 执行: bash scripts/run_webui.sh stop"
    echo -e "   - 或: kill $(cat data/pids/msearch-webui.pid)"
    echo -e "\n6. ${YELLOW}重新启动${NC}"
    echo -e "   - 执行: bash scripts/user_flow_test.sh"
    echo -e "\n${GREEN}=====================================================${NC}"
    echo -e "${GREEN}🚀 现在开始测试系统功能吧！${NC}"
    echo -e "${GREEN}=====================================================${NC}"
}

# 主函数
main() {
    echo -e "\n${CYAN}=====================================================${NC}"
    echo -e "${CYAN}        msearch 用户流程测试脚本${NC}"
    echo -e "${CYAN}=====================================================${NC}"
    echo -e "\n${BLUE}功能:${NC} 模拟真实用户的安装和使用流程"
    echo -e "${BLUE}步骤:${NC} 系统检查 → 依赖安装 → 系统配置 → 服务启动 → 测试指南"
    echo -e "\n${YELLOW}注意:${NC} 此脚本会自动处理安装和启动过程，无需手动干预"
    
    # 执行各步骤
    if ! check_system; then
        print_error "系统检查失败"
        return 1
    fi
    
    if ! install_dependencies; then
        print_error "依赖安装失败"
        return 1
    fi
    
    if ! configure_system; then
        print_error "系统配置失败"
        return 1
    fi
    
    if ! start_services; then
        print_error "服务启动失败"
        return 1
    fi
    
    # 提供测试指南
    provide_test_guide
    
    # 显示服务状态
    echo -e "\n${BLUE}【服务状态】${NC}"
    echo -e "- WebUI: ${GREEN}运行中${NC} (http://localhost:7860)"
    echo -e "- PID: ${WEBUI_PID:-N/A}"
    echo -e "- 状态: ${GREEN}就绪${NC}"
    
    return 0
}

# 执行主函数
main
