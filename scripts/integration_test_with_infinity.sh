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
CYAN='\033[0;36m'
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
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local formatted_message="[$timestamp] [$level] $message"
    
    # 输出到控制台
    case "$level" in
        INFO) echo -e "${GREEN}$formatted_message${NC}" ;;
        WARNING) echo -e "${YELLOW}$formatted_message${NC}" ;;
        ERROR) echo -e "${RED}$formatted_message${NC}" ;;
        DEBUG) echo -e "${BLUE}$formatted_message${NC}" ;;
        *) echo -e "${CYAN}$formatted_message${NC}" ;;
    esac
    
    # 输出到文件
    echo "$formatted_message" >> "$LOG_FILE"
}

log_info() {
    log "INFO" "$1"
}

log_warning() {
    log "WARNING" "$1"
}

log_error() {
    log "ERROR" "$1"
}

# 检查命令是否存在
check_command() {
    local cmd="$1"
    if ! command -v "$cmd" &> /dev/null; then
        log_error "命令 '$cmd' 未找到，请先安装"
        return 1
    fi
    return 0
}

# 检查Python环境
check_python_environment() {
    log_info "检查Python环境..."
    
    if ! check_command "python3"; then
        return 1
    fi
    
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    log_info "Python版本: $python_version"
    
    # 检查关键依赖
    if ! python3 -c "import torch, transformers, fastapi, qdrant_client" 2>/dev/null; then
        log_warning "部分Python依赖缺失，尝试安装..."
        pip install -r "$PROJECT_ROOT/requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple || {
            log_error "依赖安装失败"
            return 1
        }
    fi
    
    log_info "Python环境检查通过"
    return 0
}

# 检查Infinity依赖
check_infinity_deps() {
    log_info "检查Infinity依赖..."
    
    if ! python3 -c "import infinity_emb" 2>/dev/null; then
        log_warning "infinity_emb未安装，尝试安装..."
        pip install infinity-emb -i https://pypi.tuna.tsinghua.edu.cn/simple || {
            log_error "infinity_emb安装失败"
            return 1
        }
    fi
    
    log_info "Infinity依赖检查通过"
    return 0
}

# 检查模型文件
check_model_files() {
    log_info "检查预训练模型权重文件..."
    
    local models_dir="$PROJECT_ROOT/offline/models"
    local missing_models=()
    
    # 检查关键模型
    required_models=(
        "clip-vit-base-patch32"
        "clap-htsat-fused" 
        "whisper-base"
    )
    
    for model in "${required_models[@]}"; do
        if [ ! -d "$models_dir/$model" ]; then
            missing_models+=("$model")
            log_warning "模型 '$model' 缺失"
        fi
    done
    
    if [ ${#missing_models[@]} -gt 0 ]; then
        log_error "以下模型文件缺失: ${missing_models[*]}"
        log_info "请先运行下载脚本: ./scripts/download_all_resources.sh"
        return 1
    else
        log_info "所有模型文件检查通过"
        return 0
    fi
}

# 生成CPU模式配置文件
generate_cpu_config() {
    log_info "生成CPU模式配置文件..."
    
    local config_file="$PROJECT_ROOT/config/config_cpu.yml"
    
    cat > "$config_file" << 'EOF'
# CPU模式专用配置 - 集成测试使用
general:
  log_level: INFO
  data_dir: ./data
  device: cpu

models_storage:
  models_dir: ./offline/models
  offline_mode: true
  force_local: true

models:
  clip:
    model_name: ./offline/models/clip-vit-base-patch32
    local_path: ./offline/models/clip-vit-base-patch32
    device: cpu
    batch_size: 8
  
  clap:
    model_name: ./offline/models/clap-htsat-fused
    local_path: ./offline/models/clap-htsat-fused
    device: cpu
    batch_size: 4
  
  whisper:
    model_name: ./offline/models/whisper-base
    local_path: ./offline/models/whisper-base
    device: cpu
    batch_size: 2

processing:
  batch_size: 4
  max_concurrent_tasks: 2
  
  image:
    target_size: 224
    max_resolution: [640, 480]
    quality_threshold: 0.5
  
  video:
    target_size: 224
    max_resolution: [640, 480]
    scene_threshold: 0.3
    frame_interval: 5.0
  
  audio:
    target_sample_rate: 16000
    target_channels: 1
    segment_duration: 5.0
    quality_threshold: 0.5

storage:
  qdrant:
    host: localhost
    port: 6333
    collection_name: test_collection
    
  sqlite:
    path: ./data/test_database.db

features:
  enable_clip: true
  enable_clap: true
  enable_whisper: true
  enable_face_recognition: false  # CPU模式下禁用复杂功能
  enable_audio_classification: true

logging:
  level: INFO
  file: ./logs/integration_test.log
  max_size: 10MB
  backup_count: 5
EOF

    log_info "CPU模式配置文件已生成: $config_file"
    return 0
}

# 启动Infinity服务
start_infinity_services() {
    log_info "启动Infinity服务..."
    
    # 创建Infinity服务启动脚本
    local infinity_script="$PROJECT_ROOT/scripts/start_infinity_services.sh"
    
    cat > "$infinity_script" << 'EOF'
#!/bin/bash
# Infinity服务启动脚本 - CPU模式

set -e

# 颜色定义
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} 启动Infinity服务..."

# 设置环境变量
export HF_HUB_DISABLE_SYMLINKS_WARNING=1
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1

# 启动CLIP模型服务 (端口7997)
echo "启动CLIP模型服务 (端口7997)..."
infinity_emb v2 --model-id ./offline/models/clip-vit-base-patch32 --port 7997 --device cpu &
CLIP_PID=$!
echo $CLIP_PID > /tmp/infinity_clip.pid

# 启动CLAP模型服务 (端口7998)
echo "启动CLAP模型服务 (端口7998)..."
infinity_emb v2 --model-id ./offline/models/clap-htsat-fused --port 7998 --device cpu &
CLAP_PID=$!
echo $CLAP_PID > /tmp/infinity_clap.pid

# 启动Whisper模型服务 (端口7999)
echo "启动Whisper模型服务 (端口7999)..."
infinity_emb v2 --model-id ./offline/models/whisper-base --port 7999 --device cpu &
WHISPER_PID=$!
echo $WHISPER_PID > /tmp/infinity_whisper.pid

# 等待服务启动
sleep 10

echo -e "${GREEN}[INFO]${NC} Infinity服务启动完成！"
echo "CLIP服务PID: $CLIP_PID (端口: 7997)"
echo "CLAP服务PID: $CLAP_PID (端口: 7998)"
echo "Whisper服务PID: $WHISPER_PID (端口: 7999)"
EOF

    chmod +x "$infinity_script"
    
    # 启动Infinity服务
    cd "$PROJECT_ROOT"
    bash "$infinity_script"
    
    # 检查服务是否启动成功
    sleep 5
    
    local services_running=0
    for port in 7997 7998 7999; do
        if nc -z localhost $port 2>/dev/null; then
            log_info "Infinity服务端口 $port 启动成功"
            ((services_running++))
        else
            log_warning "Infinity服务端口 $port 启动失败"
        fi
    done
    
    if [ $services_running -eq 3 ]; then
        log_info "所有Infinity服务启动成功"
        return 0
    else
        log_error "部分Infinity服务启动失败"
        return 1
    fi
}

# 停止Infinity服务
stop_infinity_services() {
    log_info "停止Infinity服务..."
    
    # 停止Infinity服务
    for service in clip clap whisper; do
        pid_file="/tmp/infinity_${service}.pid"
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null && rm "$pid_file"
                log_info "停止Infinity $service 服务 (PID: $pid)"
            fi
        fi
    done
    
    # 清理可能的残留进程
    pkill -f "infinity_emb" 2>/dev/null || true
    
    log_info "Infinity服务已停止"
}

# 运行集成测试
run_integration_tests() {
    log_info "运行集成测试..."
    
    # 设置环境变量使用CPU模式
    export MSEARCH_CONFIG_FILE="$PROJECT_ROOT/config/config_cpu.yml"
    export MSEARCH_DEVICE="cpu"
    
    # 运行核心集成测试
    local test_results=()
    
    log_info "1. 运行基本导入测试..."
    if python3 -m pytest tests/unit/test_basic_imports_fast.py -v; then
        test_results+=("基本导入测试: 通过")
    else
        test_results+=("基本导入测试: 失败")
    fi
    
    log_info "2. 运行配置管理器测试..."
    if python3 -m pytest tests/unit/test_config_manager.py -v; then
        test_results+=("配置管理器测试: 通过")
    else
        test_results+=("配置管理器测试: 失败")
    fi
    
    log_info "3. 运行核心组件测试..."
    if python3 -m pytest tests/unit/test_core_components.py -v; then
        test_results+=("核心组件测试: 通过")
    else
        test_results+=("核心组件测试: 失败")
    fi
    
    log_info "4. 运行简单功能测试..."
    if python3 tests/unit/test_simple_functionality.py; then
        test_results+=("简单功能测试: 通过")
    else
        test_results+=("简单功能测试: 失败")
    fi
    
    # 输出测试结果
    log_info "=== 集成测试结果 ==="
    for result in "${test_results[@]}"; do
        log_info "$result"
    done
    
    # 统计通过率
    local total_tests=${#test_results[@]}
    local passed_tests=0
    for result in "${test_results[@]}"; do
        if [[ "$result" == *"通过"* ]]; then
            ((passed_tests++))
        fi
    done
    
    local pass_rate=$((passed_tests * 100 / total_tests))
    log_info "测试通过率: $passed_tests/$total_tests ($pass_rate%)"
    
    if [ $passed_tests -eq $total_tests ]; then
        log_info "所有集成测试通过！"
        return 0
    else
        log_warning "部分集成测试失败"
        return 1
    fi
}

# 运行性能测试
run_performance_tests() {
    log_info "运行性能测试..."
    
    # 创建性能测试脚本
    local perf_script="$PROJECT_ROOT/tests/performance_test.py"
    
    cat > "$perf_script" << 'EOF'
#!/usr/bin/env python3
"""
性能测试脚本 - CPU模式
测试模型加载时间、推理速度等性能指标
"""
import time
import asyncio
import numpy as np
from src.core.config_manager import ConfigManager
from src.business.embedding_engine import EmbeddingEngine

async def test_model_loading_performance():
    """测试模型加载性能"""
    print("=== 模型加载性能测试 ===")
    
    config_manager = ConfigManager()
    config = config_manager.config
    
    start_time = time.time()
    
    try:
        engine = EmbeddingEngine(config)
        loading_time = time.time() - start_time
        
        print(f"✓ 模型加载时间: {loading_time:.2f}秒")
        print(f"✓ 模型健康状态: {engine.model_health}")
        
        return loading_time
    except Exception as e:
        print(f"✗ 模型加载失败: {e}")
        return None

async def test_inference_performance():
    """测试推理性能"""
    print("\n=== 推理性能测试 ===")
    
    config_manager = ConfigManager()
    config = config_manager.config
    
    try:
        engine = EmbeddingEngine(config)
        
        # 测试文本推理
        test_texts = ["这是一个测试文本", "另一个测试文本", "性能测试文本"]
        
        start_time = time.time()
        results = []
        for text in test_texts:
            result = await engine.embed_text(text)
            results.append(result)
        inference_time = time.time() - start_time
        
        avg_time = inference_time / len(test_texts)
        print(f"✓ 文本推理测试:")
        print(f"  - 总时间: {inference_time:.2f}秒")
        print(f"  - 平均每文本: {avg_time:.2f}秒")
        print(f"  - 处理文本数: {len(test_texts)}")
        
        return avg_time
    except Exception as e:
        print(f"✗ 推理测试失败: {e}")
        return None

async def test_batch_performance():
    """测试批量处理性能"""
    print("\n=== 批量处理性能测试 ===")
    
    config_manager = ConfigManager()
    config = config_manager.config
    
    try:
        engine = EmbeddingEngine(config)
        
        # 测试批量文本推理
        batch_texts = [f"批量测试文本 {i}" for i in range(10)]
        
        start_time = time.time()
        batch_result = await engine.batch_embed_text(batch_texts)
        batch_time = time.time() - start_time
        
        print(f"✓ 批量处理测试:")
        print(f"  - 批量大小: {len(batch_texts)}")
        print(f"  - 处理时间: {batch_time:.2f}秒")
        print(f"  - 平均每文本: {batch_time/len(batch_texts):.3f}秒")
        
        return batch_time
    except Exception as e:
        print(f"✗ 批量处理测试失败: {e}")
        return None

async def main():
    """主测试函数"""
    print("开始性能测试...")
    
    # 运行各项测试
    loading_time = await test_model_loading_performance()
    inference_time = await test_inference_performance()
    batch_time = await test_batch_performance()
    
    # 性能评估
    print("\n=== 性能评估 ===")
    
    if loading_time and loading_time < 30:
        print("✓ 模型加载性能: 优秀 (<30秒)")
    elif loading_time and loading_time < 60:
        print("✓ 模型加载性能: 良好 (<60秒)")
    elif loading_time:
        print("⚠ 模型加载性能: 较慢 (>60秒)")
    
    if inference_time and inference_time < 1.0:
        print("✓ 单文本推理性能: 优秀 (<1秒)")
    elif inference_time and inference_time < 3.0:
        print("✓ 单文本推理性能: 良好 (<3秒)")
    elif inference_time:
        print("⚠ 单文本推理性能: 较慢 (>3秒)")
    
    if batch_time and batch_time < 5.0:
        print("✓ 批量处理性能: 优秀 (<5秒)")
    elif batch_time and batch_time < 10.0:
        print("✓ 批量处理性能: 良好 (<10秒)")
    elif batch_time:
        print("⚠ 批量处理性能: 较慢 (>10秒)")
    
    print("\n性能测试完成！")

if __name__ == "__main__":
    asyncio.run(main())
EOF

    chmod +x "$perf_script"
    
    # 运行性能测试
    if python3 "$perf_script"; then
        log_info "性能测试完成"
        return 0
    else
        log_warning "性能测试失败"
        return 1
    fi
}

# 清理测试环境
cleanup_test_environment() {
    log_info "清理测试环境..."
    
    # 停止Infinity服务
    stop_infinity_services
    
    # 清理临时文件
    rm -f /tmp/infinity_*.pid
    rm -f /tmp/qdrant.pid
    
    # 清理测试数据库
    if [ -f "$PROJECT_ROOT/data/test_database.db" ]; then
        rm "$PROJECT_ROOT/data/test_database.db"
    fi
    
    log_info "测试环境清理完成"
}

# 主函数
main() {
    log_info "==========================================="
    log_info "开始集成测试 - Infinity服务 + CPU模式"
    log_info "日志文件: $LOG_FILE"
    log_info "==========================================="
    
    # 设置错误处理
    trap cleanup_test_environment EXIT
    
    # 执行测试流程
    if ! check_python_environment; then
        log_error "Python环境检查失败"
        exit 1
    fi
    
    if ! check_infinity_deps; then
        log_error "Infinity依赖检查失败"
        exit 1
    fi
    
    if ! check_model_files; then
        log_error "模型文件检查失败"
        exit 1
    fi
    
    if ! generate_cpu_config; then
        log_error "配置文件生成失败"
        exit 1
    fi
    
    if ! start_infinity_services; then
        log_error "Infinity服务启动失败"
        exit 1
    fi
    
    if ! run_integration_tests; then
        log_warning "集成测试部分失败"
    fi
    
    if ! run_performance_tests; then
        log_warning "性能测试部分失败"
    fi
    
    log_info "==========================================="
    log_info "集成测试执行完成"
    log_info "==========================================="
    
    # 显示测试结果摘要
    echo ""
    echo "=== 测试结果摘要 ==="
    echo "日志文件: $LOG_FILE"
    echo "配置文件: $PROJECT_ROOT/config/config_cpu.yml"
    echo ""
    echo "后续操作:"
    echo "1. 查看详细日志: tail -f $LOG_FILE"
    echo "2. 手动停止服务: ./scripts/integration_test_with_infinity.sh --stop"
    echo "3. 重新运行测试: ./scripts/integration_test_with_infinity.sh"
    echo ""
}

# 处理命令行参数
case "${1:-}" in
    "--stop")
        cleanup_test_environment
        exit 0
        ;;
    "--help"|"-h")
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --stop     停止所有测试服务"
        echo "  --help     显示此帮助信息"
        echo ""
        echo "功能:"
        echo "  1. 检查Python环境和依赖"
        echo "  2. 检查模型文件完整性"
        echo "  3. 生成CPU模式配置文件"
        echo "  4. 启动Infinity服务"
        echo "  5. 运行集成测试"
        echo "  6. 运行性能测试"
        echo "  7. 自动清理测试环境"
        exit 0
        ;;
    *)
        main
        ;;
esac
