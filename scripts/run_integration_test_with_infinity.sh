#!/bin/bash
# 集成测试脚本 - 解决预训练模型权重文件缺失问题
# 先启动Infinity服务，然后以CPU模式运行模型进行集成测试和性能测试

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
LOG_FILE="${LOG_DIR}/integration_test_${TIMESTAMP}.log"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日志函数
log_info() {
    local message="$1"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "${GREEN}[INFO]${NC} $timestamp - $message" | tee -a "$LOG_FILE"
}

log_warning() {
    local message="$1"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "${YELLOW}[WARNING]${NC} $timestamp - $message" | tee -a "$LOG_FILE"
}

log_error() {
    local message="$1"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "${RED}[ERROR]${NC} $timestamp - $message" | tee -a "$LOG_FILE"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    # 检查Python
    if command -v python3 &> /dev/null; then
        log_info "Python 3 已安装: $(python3 --version)"
    else
        log_error "Python 3 未安装"
        exit 1
    fi
    
    # 检查pip
    if command -v pip3 &> /dev/null; then
        log_info "pip 已安装: $(pip3 --version)"
    else
        log_error "pip 未安装"
        exit 1
    fi
    
    # 检查infinity_emb
    if python3 -c "import infinity_emb" &> /dev/null; then
        log_info "infinity_emb 已安装"
    else
        log_warning "infinity_emb 未安装，尝试安装..."
        pip3 install infinity-emb -i https://pypi.tuna.tsinghua.edu.cn/simple || {
            log_error "infinity_emb 安装失败"
            exit 1
        }
        log_info "infinity_emb 安装成功"
    fi
}

# 检查模型文件
download_missing_models() {
    log_info "检查模型文件..."
    
    local models_dir="$PROJECT_ROOT/offline/models"
    local models=(
        "clip-vit-base-patch32"
        "clap-htsat-fused" 
        "whisper-base"
    )
    
    local missing_models=()
    
    for model in "${models[@]}"; do
        if [ ! -d "$models_dir/$model" ]; then
            missing_models+=("$model")
            log_warning "模型 $model 不存在"
        else
            log_info "模型 $model 已存在"
        fi
    done
    
    if [ ${#missing_models[@]} -gt 0 ]; then
        log_info "开始下载缺失的模型..."
        
        # 设置HuggingFace镜像（国内优化）
        export HF_ENDPOINT=https://hf-mirror.com
        
        # 确保huggingface_hub已安装
        pip3 install huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade
        
        for model in "${missing_models[@]}"; do
            case $model in
                "clip-vit-base-patch32")
                    log_info "下载 CLIP 模型 (openai/clip-vit-base-patch32)..."
                    huggingface-cli download \
                        openai/clip-vit-base-patch32 \
                        --resume-download \
                        --local-dir-use-symlinks False \
                        --local-dir "$models_dir/clip-vit-base-patch32" || {
                        log_error "CLIP 模型下载失败"
                        return 1
                    }
                    ;;
                "clap-htsat-fused")
                    log_info "下载 CLAP 模型 (laion/clap-htsat-fused)..."
                    huggingface-cli download \
                        laion/clap-htsat-fused \
                        --resume-download \
                        --local-dir-use-symlinks False \
                        --local-dir "$models_dir/clap-htsat-fused" || {
                        log_error "CLAP 模型下载失败"
                        return 1
                    }
                    ;;
                "whisper-base")
                    log_info "下载 Whisper 模型 (openai/whisper-base)..."
                    huggingface-cli download \
                        openai/whisper-base \
                        --resume-download \
                        --local-dir-use-symlinks False \
                        --local-dir "$models_dir/whisper-base" || {
                        log_error "Whisper 模型下载失败"
                        return 1
                    }
                    ;;
            esac
        done
        
        log_info "所有缺失模型下载完成"
    else
        log_info "所有模型文件都已存在，跳过下载"
    fi
}

# 创建CPU模式配置
create_cpu_config() {
    log_info "创建CPU模式配置文件..."
    
    local cpu_config_file="$PROJECT_ROOT/config/config_cpu.yml"
    
    cat > "$cpu_config_file" << 'EOF'
# CPU模式配置 - 用于集成测试和性能测试

# 系统配置
system:
  log_level: INFO
  max_workers: 4
  data_dir: "./data"

# 模型配置
models_storage:
  models_dir: "./offline/models"
  offline_mode: true
  force_local: true

# Infinity服务配置
infinity:
  enabled: true
  models:
    clip:
      model_name: "./offline/models/clip-vit-base-patch32"
      local_path: "./offline/models/clip-vit-base-patch32"
      device: "cpu"
      batch_size: 8
      engine_args:
        model_warmup: true
        served_model_name: "clip"
        port: 7997
    clap:
      model_name: "./offline/models/clap-htsat-fused"
      local_path: "./offline/models/clap-htsat-fused"
      device: "cpu"
      batch_size: 4
      engine_args:
        model_warmup: true
        served_model_name: "clap"
        port: 7998
    whisper:
      model_name: "./offline/models/whisper-base"
      local_path: "./offline/models/whisper-base"
      device: "cpu"
      batch_size: 2
      engine_args:
        model_warmup: true
        served_model_name: "whisper"
        port: 7999

# 处理配置
processing:
  batch_size: 8
  max_concurrent_tasks: 2
  image:
    target_size: 224
    max_resolution: [1920, 1080]
    quality_threshold: 0.5
  video:
    target_size: 224
    max_resolution: [1280, 720]
    scene_threshold: 0.3
    frame_interval: 2.0
  audio:
    target_sample_rate: 16000
    target_channels: 1
    segment_duration: 10.0
    quality_threshold: 0.5
  text:
    max_file_size: 10485760  # 10MB
    encoding_priority: ["utf-8", "gbk", "gb2312", "latin-1"]

# 数据库配置
database:
  sqlite:
    path: "./data/database/msearch.db"
  qdrant:
    host: "localhost"
    port: 6333
    collection_name: "msearch_vectors"

# 搜索配置
search:
  top_k: 10
  similarity_threshold: 0.7
  multimodal_fusion:
    weights:
      text: 0.4
      image: 0.3
      audio: 0.3

# 人脸识别配置
face_recognition:
  enabled: true
  detector: "mtcnn"
  recognizer: "facenet"
  confidence_threshold: 0.7
  max_faces: 10

# 音频分类配置
audio_classification:
  enabled: true
  classifier: "inaSpeechSegmenter"
  quality_threshold: 0.6

EOF

    log_info "CPU模式配置文件已创建: $cpu_config_file"
}

# 启动Infinity服务
start_infinity_services() {
    log_info "启动Infinity服务..."
    
    local infinity_script="$PROJECT_ROOT/scripts/start_infinity_services.sh"
    
    # 创建Infinity服务启动脚本
    cat > "$infinity_script" << 'EOF'
#!/bin/bash
# Infinity服务启动脚本 - CPU模式

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} 启动Infinity服务..."

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "项目根目录: $PROJECT_ROOT"

# 检查infinity_emb是否安装
if ! python3 -c "import infinity_emb" &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} infinity_emb未安装"
    echo "请运行: pip install infinity-emb"
    exit 1
fi

# 检查模型文件是否存在
if [ ! -d "$PROJECT_ROOT/offline/models/clip-vit-base-patch32" ]; then
    echo -e "${RED}[ERROR]${NC} CLIP模型文件不存在"
    echo "请先运行: bash scripts/run_integration_test_with_infinity.sh"
    exit 1
fi

if [ ! -d "$PROJECT_ROOT/offline/models/clap-htsat-fused" ]; then
    echo -e "${YELLOW}[WARNING]${NC} CLAP模型文件不存在，跳过CLAP服务"
    CLAP_ENABLED=false
else
    CLAP_ENABLED=true
fi

if [ ! -d "$PROJECT_ROOT/offline/models/whisper-base" ]; then
    echo -e "${YELLOW}[WARNING]${NC} Whisper模型文件不存在，跳过Whisper服务"
    WHISPER_ENABLED=false
else
    WHISPER_ENABLED=true
fi

# 启动CLIP服务
echo -e "${GREEN}[INFO]${NC} 启动CLIP服务 (端口: 7997)..."
infinity_emb v2 \
    --model-name-or-path "$PROJECT_ROOT/offline/models/clip-vit-base-patch32" \
    --device "cpu" \
    --port 7997 \
    --model-warmup \
    --engine "torch" &
CLIP_PID=$!
echo "CLIP服务PID: $CLIP_PID"

# 启动CLAP服务（如果可用）
if [ "$CLAP_ENABLED" = true ]; then
    echo -e "${GREEN}[INFO]${NC} 启动CLAP服务 (端口: 7998)..."
    infinity_emb v2 \
        --model-name-or-path "$PROJECT_ROOT/offline/models/clap-htsat-fused" \
        --device "cpu" \
        --port 7998 \
        --model-warmup \
        --engine "torch" &
    CLAP_PID=$!
    echo "CLAP服务PID: $CLAP_PID"
fi

# 启动Whisper服务（如果可用）
if [ "$WHISPER_ENABLED" = true ]; then
    echo -e "${GREEN}[INFO]${NC} 启动Whisper服务 (端口: 7999)..."
    infinity_emb v2 \
        --model-name-or-path "$PROJECT_ROOT/offline/models/whisper-base" \
        --device "cpu" \
        --port 7999 \
        --model-warmup \
        --engine "torch" &
    WHISPER_PID=$!
    echo "Whisper服务PID: $WHISPER_PID"
fi

# 保存PID文件
echo "$CLIP_PID" > /tmp/infinity_clip.pid
if [ "$CLAP_ENABLED" = true ]; then
    echo "$CLAP_PID" > /tmp/infinity_clap.pid
fi
if [ "$WHISPER_ENABLED" = true ]; then
    echo "$WHISPER_PID" > /tmp/infinity_whisper.pid
fi

echo -e "${GREEN}[INFO]${NC} Infinity服务启动完成！"
echo "CLIP服务: http://localhost:7997"
if [ "$CLAP_ENABLED" = true ]; then
    echo "CLAP服务: http://localhost:7998"
fi
if [ "$WHISPER_ENABLED" = true ]; then
    echo "Whisper服务: http://localhost:7999"
fi
echo ""
echo "服务健康检查:"
echo "curl http://localhost:7997/health"
if [ "$CLAP_ENABLED" = true ]; then
    echo "curl http://localhost:7998/health"
fi
if [ "$WHISPER_ENABLED" = true ]; then
    echo "curl http://localhost:7999/health"
fi
EOF

    chmod +x "$infinity_script"
    
    # 启动Infinity服务
    log_info "执行Infinity服务启动脚本..."
    bash "$infinity_script" &
    INFINITY_PID=$!
    
    # 等待服务启动
    log_info "等待Infinity服务启动..."
    sleep 10
    
    # 检查服务状态
    if curl -s http://localhost:7997/health > /dev/null; then
        log_info "CLIP服务启动成功"
    else
        log_error "CLIP服务启动失败"
        return 1
    fi
    
    # 检查CLAP服务（如果可用）
    if curl -s http://localhost:7998/health > /dev/null 2>&1; then
        log_info "CLAP服务启动成功"
    else
        log_warning "CLAP服务未启动或不可用"
    fi
    
    # 检查Whisper服务（如果可用）
    if curl -s http://localhost:7999/health > /dev/null 2>&1; then
        log_info "Whisper服务启动成功"
    else
        log_warning "Whisper服务未启动或不可用"
    fi
    
    echo "$INFINITY_PID" > /tmp/infinity_services.pid
    log_info "Infinity服务启动完成，PID: $INFINITY_PID"
}

# 停止Infinity服务
stop_infinity_services() {
    log_info "停止Infinity服务..."
    
    if [ -f /tmp/infinity_services.pid ]; then
        local infinity_pid=$(cat /tmp/infinity_services.pid)
        if ps -p "$infinity_pid" > /dev/null; then
            kill "$infinity_pid" 2>/dev/null
            log_info "Infinity服务已停止 (PID: $infinity_pid)"
        fi
        rm -f /tmp/infinity_services.pid
    fi
    
    # 停止各个服务
    for service in clip clap whisper; do
        if [ -f "/tmp/infinity_${service}.pid" ]; then
            local service_pid=$(cat "/tmp/infinity_${service}.pid")
            if ps -p "$service_pid" > /dev/null; then
                kill "$service_pid" 2>/dev/null
                log_info "${service^^}服务已停止 (PID: $service_pid)"
            fi
            rm -f "/tmp/infinity_${service}.pid"
        fi
    done
    
    log_info "所有Infinity服务已停止"
}

# 运行集成测试
run_integration_tests() {
    log_info "开始运行集成测试..."
    
    # 设置环境变量，使用CPU模式配置
    export MSEARCH_CONFIG_FILE="$PROJECT_ROOT/config/config_cpu.yml"
    
    # 运行集成测试
    cd "$PROJECT_ROOT"
    
    log_info "运行基本功能测试..."
    python3 tests/unit/test_basic_imports_fast.py
    
    log_info "运行配置管理器测试..."
    python3 -m pytest tests/unit/test_config_manager.py -v
    
    log_info "运行文件类型检测器测试..."
    python3 -m pytest tests/unit/test_file_type_detector.py -v
    
    log_info "运行核心组件测试..."
    python3 tests/unit/test_core_components.py
    
    log_info "运行简单功能测试..."
    python3 tests/unit/test_simple_functionality.py
    
    log_info "运行嵌入引擎测试 (mock模式)..."
    python3 -m pytest tests/unit/test_embedding_engine.py -v
    
    log_info "运行处理编排器测试..."
    python3 -m pytest tests/unit/test_processing_orchestrator.py -v
    
    log_info "运行搜索功能测试..."
    python3 -m pytest tests/unit/test_search_engine.py -v
    
    log_info "运行智能检索测试..."
    python3 -m pytest tests/unit/test_smart_retrieval.py -v
    
    log_info "所有集成测试完成"
}

# 运行性能测试
run_performance_tests() {
    log_info "开始运行性能测试..."
    
    cd "$PROJECT_ROOT"
    
    # 创建性能测试脚本
    local performance_script="$PROJECT_ROOT/tests/performance_test.py"
    
    cat > "$performance_script" << 'EOF'
#!/usr/bin/env python3
"""
性能测试脚本 - 测试CPU模式下的模型性能
"""
import time
import numpy as np
import asyncio
from src.core.config_manager import ConfigManager
from src.business.embedding_engine import EmbeddingEngine
from src.business.orchestrator import ProcessingOrchestrator

async def test_embedding_performance():
    """测试嵌入性能"""
    print("=== 嵌入性能测试 ===")
    
    # 加载CPU配置
    config_manager = ConfigManager("config/config_cpu.yml")
    config = config_manager.get_config()
    
    # 创建嵌入引擎
    engine = EmbeddingEngine(config)
    
    # 测试文本嵌入
    test_texts = ["这是一个测试文本", "另一个测试文本", "性能测试文本"]
    
    start_time = time.time()
    for i, text in enumerate(test_texts):
        try:
            vector = await engine.embed_text(text)
            print(f"文本 {i+1}: 向量维度 {len(vector)}")
        except Exception as e:
            print(f"文本 {i+1} 嵌入失败: {e}")
    
    end_time = time.time()
    print(f"文本嵌入总耗时: {end_time - start_time:.2f}秒")
    
    # 测试图像嵌入（模拟）
    print("\n=== 图像嵌入性能测试 ===")
    try:
        test_image = np.random.rand(224, 224, 3).astype(np.float32)
        start_time = time.time()
        vector = await engine.embed_image(test_image)
        end_time = time.time()
        print(f"图像嵌入耗时: {end_time - start_time:.2f}秒")
        print(f"图像向量维度: {len(vector)}")
    except Exception as e:
        print(f"图像嵌入失败: {e}")

def test_orchestrator_performance():
    """测试处理编排器性能"""
    print("\n=== 处理编排器性能测试 ===")
    
    # 加载CPU配置
    config_manager = ConfigManager("config/config_cpu.yml")
    config = config_manager.get_config()
    
    # 创建处理编排器
    orchestrator = ProcessingOrchestrator(config)
    
    start_time = time.time()
    
    # 测试文件类型检测
    file_types = ["test.jpg", "test.mp4", "test.mp3", "test.txt"]
    for file_path in file_types:
        try:
            file_type = orchestrator.file_type_detector.detect_file_type(file_path)
            print(f"文件 {file_path}: {file_type['type']} (置信度: {file_type['confidence']:.2f})")
        except Exception as e:
            print(f"文件 {file_path} 类型检测失败: {e}")
    
    end_time = time.time()
    print(f"文件类型检测总耗时: {end_time - start_time:.2f}秒")

async def main():
    print("开始性能测试...")
    print("配置: CPU模式，Infinity服务")
    print("=" * 50)
    
    # 运行嵌入性能测试
    await test_embedding_performance()
    
    # 运行编排器性能测试
    test_orchestrator_performance()
    
    print("\n" + "=" * 50)
    print("性能测试完成")

if __name__ == "__main__":
    asyncio.run(main())
EOF
    
    # 运行性能测试
    python3 "$performance_script"
    
    # 清理临时文件
    rm -f "$performance_script"
    
    log_info "性能测试完成"
}

# 主函数
main() {
    log_info "==========================================="
    log_info "开始集成测试和性能测试"
    log_info "日志文件: ${LOG_FILE}"
    log_info "==========================================="
    
    # 设置错误处理
    trap 'stop_infinity_services; exit 1' ERR
    trap 'stop_infinity_services; exit 0' INT TERM
    
    # 检查依赖
    check_dependencies
    
    # 检查并下载缺失的模型
    download_missing_models
    
    # 创建CPU模式配置
    create_cpu_config
    
    # 启动Infinity服务
    start_infinity_services
    
    # 运行集成测试
    run_integration_tests
    
    # 运行性能测试
    run_performance_tests
    
    # 停止Infinity服务
    stop_infinity_services
    
    log_info "==========================================="
    log_info "集成测试和性能测试完成"
    log_info "==========================================="
    
    log_info "测试总结："
    log_info "- 模型文件检查和下载完成"
    log_info "- CPU模式配置已创建"
    log_info "- Infinity服务已启动和停止"
    log_info "- 集成测试已完成"
    log_info "- 性能测试已完成"
    log_info ""
    log_info "后续操作："
    log_info "1. 查看详细日志: cat $LOG_FILE"
    log_info "2. 启动应用: python src/api/main.py --config config/config_cpu.yml"
    log_info "3. 手动启动Infinity服务: bash scripts/start_infinity_services.sh"
    log_info "4. 手动停止Infinity服务: bash scripts/stop_infinity_services.sh"
}

# 执行主函数
main