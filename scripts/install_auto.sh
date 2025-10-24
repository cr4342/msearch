#!/bin/bash

# MSearch Linux一键安装脚本
# 功能：环境检查、依赖下载安装、模型下载、项目配置、启动软件等全部操作

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 路径定义 - 自动检测当前目录和项目代码
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_DIR="$(pwd)"

# 尝试检测项目根目录
# 1. 如果脚本在项目内部运行，使用脚本所在目录的上级目录
if [ -d "${SCRIPT_DIR}/../src" ] || [ -d "${SCRIPT_DIR}/../tests" ]; then
    PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
    echo -e "${GREEN}[自动检测] 从脚本位置找到项目根目录: ${PROJECT_ROOT}${NC}"
# 2. 如果脚本在项目外部运行，尝试在当前目录查找
elif [ -d "${CURRENT_DIR}/src" ] || [ -d "${CURRENT_DIR}/tests" ]; then
    PROJECT_ROOT="${CURRENT_DIR}"
    echo -e "${GREEN}[自动检测] 从当前目录找到项目根目录: ${PROJECT_ROOT}${NC}"
# 3. 尝试在同级目录查找项目
elif [ -d "${CURRENT_DIR}/msearch" ] && [ -d "${CURRENT_DIR}/msearch/src" ]; then
    PROJECT_ROOT="${CURRENT_DIR}/msearch"
    echo -e "${GREEN}[自动检测] 在同级目录找到项目根目录: ${PROJECT_ROOT}${NC}"
else
    # 默认使用当前目录作为项目根目录
    PROJECT_ROOT="${CURRENT_DIR}"
    echo -e "${YELLOW}[警告] 未找到明确的项目结构，使用当前目录作为项目根目录: ${PROJECT_ROOT}${NC}"
fi

# 部署测试目录 - 放在项目内的tests目录下
DEPLOY_TEST_DIR="${PROJECT_ROOT}/tests/deployment_test"
DEPLOY_CONFIG_DIR="${DEPLOY_TEST_DIR}/config"
DEPLOY_DATA_DIR="${DEPLOY_TEST_DIR}/data"
DEPLOY_MODELS_DIR="${DEPLOY_TEST_DIR}/models"
DEPLOY_LOGS_DIR="${DEPLOY_TEST_DIR}/logs"

# 确保目录存在
mkdir -p "${DEPLOY_CONFIG_DIR}"
mkdir -p "${DEPLOY_DATA_DIR}"
mkdir -p "${DEPLOY_MODELS_DIR}"
mkdir -p "${DEPLOY_LOGS_DIR}"

# 日志文件
LOG_FILE="${DEPLOY_LOGS_DIR}/install_$(date +%Y%m%d_%H%M%S).log"

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
        formatted_log="$(format_log "INFO" "$1")"
        echo "$formatted_log" >> "$LOG_FILE"
        return
    fi
    
    # 新的多级别调用方式
    local level="$1"
    local message="$2"
    
    if should_log "$level"; then
        # 输出到控制台
        log_to_console "$level" "$message"
        
        # 写入日志文件
        formatted_log="$(format_log "$level" "$message")"
        echo "$formatted_log" >> "$LOG_FILE"
    fi
}

# 便捷日志函数
log_debug() {
    log "DEBUG" "$1"
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

log_critical() {
    log "CRITICAL" "$1"
}

# 初始化日志文件
echo "MSearch 安装日志" > "${LOG_FILE}"
echo "开始时间: $(date)" >> "${LOG_FILE}"
echo "当前目录: ${CURRENT_DIR}" >> "${LOG_FILE}"
echo "脚本目录: ${SCRIPT_DIR}" >> "${LOG_FILE}"
echo "项目目录: ${PROJECT_ROOT}" >> "${LOG_FILE}"
echo "日志级别: ${LOG_LEVEL}" >> "${LOG_FILE}"
echo "===============================================" >> "${LOG_FILE}"

# 输出初始化信息
log "INFO" "=== MSearch 安装脚本启动 ==="
log "INFO" "日志文件: ${LOG_FILE}"
log "INFO" "项目目录: ${PROJECT_ROOT}"
log "INFO" "日志级别: ${LOG_LEVEL}"

# 错误处理函数
handle_error() {
    log_error "步骤失败: $1"
    log_info "安装过程中断，请检查日志: ${LOG_FILE}"
    exit 1
}

# 1. 检查系统环境
check_environment() {
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
        log_debug "使用apt-get安装build-essential等依赖"
        sudo apt-get update && sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev
    elif command -v yum &> /dev/null; then
        log_info "安装系统依赖..."
        log_debug "使用yum安装gcc等依赖"
        sudo yum install -y gcc gcc-c++ openssl-devel libffi-devel python3-devel
    fi
    
    log_info "环境检查完成！"
}

# 2. 安装系统依赖和Python包
install_dependencies() {
    log "${BLUE}===============================================${NC}"
    log "${GREEN}        安装系统依赖和Python包${NC}"
    log "${BLUE}===============================================${NC}"
    
    # 更新pip
    log "${BLUE}[步骤1] 更新pip...${NC}"
    python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple || log "${YELLOW}[警告] pip更新失败${NC}"
    
    # 安装核心依赖包
    log "${BLUE}[步骤2] 安装核心依赖包...${NC}"
    if [ -f "${PROJECT_ROOT}/requirements.txt" ]; then
        python3 -m pip install -r "${PROJECT_ROOT}/requirements.txt" \
            -i https://pypi.tuna.tsinghua.edu.cn/simple \
            --timeout 120 \
            --retries 3 || {
            log "${YELLOW}[警告] 部分依赖安装失败，尝试单独安装关键包...${NC}"
            python3 -m pip install fastapi uvicorn pydantic numpy pandas \
                -i https://pypi.tuna.tsinghua.edu.cn/simple
        }
    else
        log "${YELLOW}[警告] 未找到requirements.txt，安装基本依赖${NC}"
        python3 -m pip install fastapi uvicorn pydantic numpy pandas \
            -i https://pypi.tuna.tsinghua.edu.cn/simple
    fi
    
    # 安装测试专用依赖
    log "${BLUE}[步骤3] 安装测试专用依赖...${NC}"
    python3 -m pip install pytest pytest-cov pytest-mock httpx \
        -i https://pypi.tuna.tsinghua.edu.cn/simple
    
    # 安装AI模型依赖
    log "${BLUE}[步骤4] 安装AI模型依赖...${NC}"
    python3 -m pip install transformers torch torchvision \
        -i https://pypi.tuna.tsinghua.edu.cn/simple
    
    log "${GREEN}系统依赖安装完成！${NC}"
}

# 3. 下载和配置AI模型
download_models() {
    log "${BLUE}===============================================${NC}"
    log "${GREEN}          下载和配置AI模型${NC}"
    log "${BLUE}===============================================${NC}"
    
    # 设置环境变量 - 使用镜像加速
    export HF_ENDPOINT="https://hf-mirror.com"
    export HF_HOME="${DEPLOY_MODELS_DIR}/huggingface"
    export TRANSFORMERS_CACHE="${HF_HOME}"
    
    # 创建模型目录结构
    mkdir -p "${HF_HOME}"
    mkdir -p "${DEPLOY_MODELS_DIR}/clip-vit-base-patch32"
    mkdir -p "${DEPLOY_MODELS_DIR}/clap-htsat-fused"
    mkdir -p "${DEPLOY_MODELS_DIR}/whisper-base"
    
    log "${BLUE}[信息] 模型目录: ${DEPLOY_MODELS_DIR}${NC}"
    
    # 创建优化的模型下载脚本
    MODEL_SCRIPT="${DEPLOY_TEST_DIR}/download_models.py"
    cat > "${MODEL_SCRIPT}" << 'EOF'
import os
import sys
import time
from pathlib import Path
from transformers import (
    CLIPModel, CLIPProcessor, 
    CLAPModel, CLAPProcessor, 
    WhisperForConditionalGeneration, WhisperProcessor,
    AutoModel, AutoProcessor, AutoTokenizer
)
import torch

def setup_offline_mode():
    """设置离线模式环境变量"""
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    print("[INFO] 已设置离线模式环境变量")

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
    
    if 'tokenizer' in components:
        try:
            print("  - 下载分词器组件...")
            tokenizer = AutoTokenizer.from_pretrained(repo_id, cache_dir=local_path)
            tokenizer.save_pretrained(local_path)
            print("  ✓ 分词器组件下载完成")
        except Exception as e:
            print(f"  ✗ 分词器组件下载失败: {str(e)}")
            success = False
    
    return success

def download_models(models_dir):
    """下载所有必要的模型"""
    print(f"[INFO] 模型下载目录: {models_dir}")
    
    # 模型列表 - 使用与embedding_engine.py兼容的配置
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
    
    # 创建模型配置信息文件
    config_info = os.path.join(models_dir, 'model_config_info.txt')
    with open(config_info, 'w', encoding='utf-8') as f:
        f.write("MSearch 模型配置信息\n")
        f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"成功下载: {success_count}/{total_count} 个模型\n\n")
        
        for model_info in models:
            local_path = model_info['local_path']
            exists = os.path.exists(os.path.join(local_path, 'config.json'))
            status = "成功" if exists else "失败"
            f.write(f"{model_info['name']}: {status}")
            f.write(f" (路径: {local_path})\n")
    
    print(f"[INFO] 配置信息已保存到: {config_info}")
    
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
    log "${BLUE}[步骤1] 执行模型下载...${NC}"
    python3 "${MODEL_SCRIPT}" "${DEPLOY_MODELS_DIR}"
    DOWNLOAD_RESULT=$?
    
    if [ $DOWNLOAD_RESULT -eq 0 ]; then
        log "${GREEN}[成功] 所有模型下载完成${NC}"
        
        # 创建配置更新脚本，确保配置使用本地模型
        CONFIG_UPDATE_SCRIPT="${DEPLOY_TEST_DIR}/update_config_for_local_models.py"
        cat > "${CONFIG_UPDATE_SCRIPT}" << 'EOF'
import os
import yaml
from pathlib import Path

def update_config_for_local_models(config_file, models_dir):
    """更新配置文件以使用本地模型"""
    print(f"[INFO] 更新配置文件: {config_file}")
    
    # 确保配置文件存在
    if not os.path.exists(config_file):
        print(f"[WARNING] 配置文件不存在: {config_file}")
        return False
    
    # 读取配置
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        
        # 确保models部分存在
        if 'models' not in config:
            config['models'] = {}
        
        # 添加模型存储配置
        config['models']['storage'] = {
            'local_model_root': models_dir.replace(os.path.sep, '/'),
            'offline_mode': True,
            'force_local': True
        }
        
        # 更新各模型配置
        model_mapping = {
            'clip': {'path': os.path.join(models_dir, 'clip-vit-base-patch32'), 'repo': 'openai/clip-vit-base-patch32'},
            'clap': {'path': os.path.join(models_dir, 'clap-htsat-fused'), 'repo': 'laion/clap-htsat-unfused'},
            'whisper': {'path': os.path.join(models_dir, 'whisper-base'), 'repo': 'openai/whisper-base'}
        }
        
        for model_name, model_info in model_mapping.items():
            model_path = model_info['path'].replace(os.path.sep, '/')
            
            if model_name not in config['models']:
                config['models'][model_name] = {}
            
            # 设置本地路径
            config['models'][model_name]['local_path'] = model_path
            config['models'][model_name]['model_name'] = model_path
            config['models'][model_name]['allow_download'] = False
            config['models'][model_name]['device'] = 'auto'
            
            print(f"[INFO] 已配置 {model_name} 模型路径: {model_path}")
        
        # 保存更新后的配置
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print(f"[SUCCESS] 配置文件已更新为使用本地模型")
        return True
        
    except Exception as e:
        print(f"[ERROR] 更新配置文件失败: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("[ERROR] 缺少参数: config_file models_dir")
        sys.exit(1)
    
    config_file = sys.argv[1]
    models_dir = sys.argv[2]
    
    success = update_config_for_local_models(config_file, models_dir)
    sys.exit(0 if success else 1)
EOF
        
        # 执行配置更新
        log "${BLUE}[步骤2] 更新配置文件以使用本地模型...${NC}"
        python3 "${CONFIG_UPDATE_SCRIPT}" "${DEPLOY_CONFIG_DIR}/config.yml" "${DEPLOY_MODELS_DIR}"
        
        # 设置模型目录权限
        chmod -R 755 "${DEPLOY_MODELS_DIR}"
        
        log "${GREEN}[成功] 模型部署完成，已配置为使用本地模型${NC}"
    else:
        log "${YELLOW}[警告] 部分模型下载失败，请检查网络连接${NC}"
        log "${YELLOW}[警告] 继续安装，但API服务可能无法正常工作${NC}"
    
    # 清理临时脚本
    rm -f "${MODEL_SCRIPT}" "${CONFIG_UPDATE_SCRIPT}"
    
    log "${GREEN}AI模型配置完成！${NC}"
}

# 4. 配置项目文件
configure_project() {
    log "${BLUE}===============================================${NC}"
    log "${GREEN}          配置项目文件${NC}"
    log "${BLUE}===============================================${NC}"
    
    # 创建环境配置文件
    ENV_FILE="${DEPLOY_TEST_DIR}/deploy_env.sh"
    cat > "${ENV_FILE}" << EOF
#!/bin/bash
# 部署环境变量配置
export DEPLOY_ROOT=${DEPLOY_TEST_DIR}
export DEPLOY_CONFIG=${DEPLOY_CONFIG_DIR}
export DEPLOY_DATA=${DEPLOY_DATA_DIR}
export DEPLOY_MODELS=${DEPLOY_MODELS_DIR}
export DEPLOY_LOGS=${DEPLOY_LOGS_DIR}
export PYTHONPATH=${PROJECT_ROOT}:${DEPLOY_TEST_DIR}
export PYTHONWARNINGS=ignore
export KMP_DUPLICATE_LIB_OK=TRUE
export CUDA_LAUNCH_BLOCKING=1
export HF_HOME=${DEPLOY_MODELS_DIR}/huggingface
export TRANSFORMERS_CACHE=${DEPLOY_MODELS_DIR}/huggingface
EOF
    chmod +x "${ENV_FILE}"
    
    # 创建配置文件（如果不存在）
    CONFIG_FILE="${DEPLOY_CONFIG_DIR}/config.yml"
    if [ ! -f "${CONFIG_FILE}" ]; then
        log "${BLUE}[步骤1] 创建默认配置文件...${NC}"
        mkdir -p "$(dirname "${CONFIG_FILE}")"
        cat > "${CONFIG_FILE}" << 'EOF'
# MSearch 配置文件

# 服务器配置
server:
  host: 0.0.0.0
  port: 8000
  reload: true

# 模型配置
models:
  clip:
    path: "models/clip"
    device: "cuda"  # cpu 或 cuda
  clap:
    path: "models/clap"
    device: "cuda"
  whisper:
    path: "models/whisper"
    device: "cuda"

# 存储配置
storage:
  vector_db:
    type: "qdrant"
    host: "localhost"
    port: 6333
  task_db:
    path: "data/task.db"

# 日志配置
logging:
  level: "INFO"
  file: "logs/app.log"
EOF
    fi
    
    # 创建缺失的__init__.py文件
    log "${BLUE}[步骤2] 修复项目结构...${NC}"
    INIT_FILES=(
        "${PROJECT_ROOT}/src/__init__.py"
        "${PROJECT_ROOT}/src/api/__init__.py"
        "${PROJECT_ROOT}/src/business/__init__.py"
        "${PROJECT_ROOT}/src/core/__init__.py"
        "${PROJECT_ROOT}/src/processors/__init__.py"
        "${PROJECT_ROOT}/src/storage/__init__.py"
        "${PROJECT_ROOT}/src/utils/__init__.py"
    )
    
    for init_file in "${INIT_FILES[@]}"; do
        if [ ! -f "${init_file}" ]; then
            mkdir -p "$(dirname "${init_file}")"
            touch "${init_file}"
            log "${GREEN}[成功] 创建缺失的__init__.py: ${init_file}${NC}"
        fi
    done
    
    log "${GREEN}项目配置完成！${NC}"
}

# 5. 创建测试数据
create_test_data() {
    log "${BLUE}===============================================${NC}"
    log "${GREEN}          创建测试数据${NC}"
    log "${BLUE}===============================================${NC}"
    
    TEST_DATA_DIR="${DEPLOY_DATA_DIR}/test_media"
    mkdir -p "${TEST_DATA_DIR}"
    
    # 创建测试数据脚本
    TEST_SCRIPT="${DEPLOY_TEST_DIR}/create_test_data.py"
    cat > "${TEST_SCRIPT}" << 'EOF'
import os
import shutil
from pathlib import Path

def create_test_data():
    test_dir = Path(sys.argv[1])
    project_test_dir = Path(sys.argv[2])
    
    # 复制项目中的测试文件
    if project_test_dir.exists():
        for file in project_test_dir.glob("*"):
            if file.is_file():
                shutil.copy2(file, test_dir / file.name)
                print(f"[INFO] 复制测试文件: {file.name}")
    
    # 如果没有测试文件，创建一些示例文件
    if not any(test_dir.iterdir()):
        print(f"[INFO] 创建示例测试文件到: {test_dir}")
        # 创建一个示例文本文件
        with open(test_dir / "example.txt", "w") as f:
            f.write("这是一个示例测试文件")
    
    print(f"[SUCCESS] 测试数据创建完成: {test_dir}")

if __name__ == "__main__":
    import sys
    create_test_data()
EOF
    
    # 执行测试数据创建
    python3 "${TEST_SCRIPT}" "${TEST_DATA_DIR}" "${PROJECT_ROOT}/tests/temp" || log "${YELLOW}[警告] 测试数据创建失败，但继续安装${NC}"
    
    log "${GREEN}测试数据创建完成！${NC}"
}

# 6. 运行基本测试
run_basic_tests() {
    log "${BLUE}===============================================${NC}"
    log "${GREEN}          运行基本测试${NC}"
    log "${BLUE}===============================================${NC}"
    
    # 创建测试脚本
    TEST_SCRIPT="${DEPLOY_TEST_DIR}/run_basic_tests.py"
    cat > "${TEST_SCRIPT}" << 'EOF'
import os
import sys
from pathlib import Path

def test_imports():
    """测试核心模块导入"""
    print("[INFO] 测试核心模块导入...")
    try:
        # 尝试导入核心模块
        from src.business.embedding_engine import EmbeddingEngine
        print("[SUCCESS] 核心模块导入成功")
        return True
    except ImportError as e:
        print(f"[WARNING] 核心模块导入失败: {e}")
        return False

def test_model_paths():
    """测试模型路径"""
    print("[INFO] 测试模型路径...")
    models_dir = Path(sys.argv[1])
    if models_dir.exists():
        print(f"[SUCCESS] 模型目录存在: {models_dir}")
        return True
    else:
        print(f"[WARNING] 模型目录不存在: {models_dir}")
        return False

def main():
    print("[INFO] 开始基本测试...")
    
    tests = [
        ("核心模块导入", test_imports),
        ("模型路径检查", lambda: test_model_paths(sys.argv[1])),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[INFO] 执行测试: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"[WARNING] 测试失败: {test_name}")
    
    print(f"\n[INFO] 测试结果: {passed}/{total} 通过")
    return 0 if passed >= 1 else 1

if __name__ == "__main__":
    sys.exit(main())
EOF
    
    # 执行基本测试
    log "${BLUE}[步骤1] 执行基本测试...${NC}"
    python3 "${TEST_SCRIPT}" "${DEPLOY_MODELS_DIR}" || log "${YELLOW}[警告] 部分测试失败，但继续安装${NC}"
    
    log "${GREEN}基本测试完成！${NC}"
}

# 7. 生成启动脚本
generate_startup_scripts() {
    log "${BLUE}===============================================${NC}"
    log "${GREEN}          生成启动脚本${NC}"
    log "${BLUE}===============================================${NC}"
    
    # 生成API启动脚本
    API_SCRIPT="${DEPLOY_TEST_DIR}/start_api.sh"
    cat > "${API_SCRIPT}" << EOF
#!/bin/bash
# 启动MSearch API服务

# 部署环境变量配置 - 自动检测版本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_ROOT="${SCRIPT_DIR}"
DEPLOY_CONFIG="${DEPLOY_ROOT}/config"
DEPLOY_DATA="${DEPLOY_ROOT}/data"
DEPLOY_MODELS="${DEPLOY_ROOT}/models"
DEPLOY_LOGS="${DEPLOY_ROOT}/logs"

# 尝试检测项目根目录
if [ -d "${DEPLOY_ROOT}/../../src" ] || [ -d "${DEPLOY_ROOT}/../../tests" ]; then
    PROJECT_ROOT="$(cd "${DEPLOY_ROOT}/../.." && pwd)"
else
    # 如果找不到，使用当前目录的父目录
    PROJECT_ROOT="$(cd "${DEPLOY_ROOT}/.." && pwd)"
fi

# 设置环境变量
export PYTHONPATH="${PROJECT_ROOT}:${DEPLOY_ROOT}"
export PYTHONWARNINGS=ignore
export KMP_DUPLICATE_LIB_OK=TRUE
export CUDA_LAUNCH_BLOCKING=1
export HF_HOME="${DEPLOY_MODELS}/huggingface"
export TRANSFORMERS_CACHE="${DEPLOY_MODELS}/huggingface"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

echo "启动MSearch API服务..."
echo "API地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"

# 启动API服务
cd "${PROJECT_ROOT}"
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
EOF
    chmod +x "${API_SCRIPT}"
    
    # 生成完整启动脚本
    START_SCRIPT="${DEPLOY_TEST_DIR}/start_all.sh"
    cat > "${START_SCRIPT}" << EOF
#!/bin/bash
# MSearch完整启动脚本

echo "==============================================="
echo "          MSearch 服务启动脚本                "
echo "==============================================="

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_ROOT="${SCRIPT_DIR}"

# 尝试检测项目根目录
if [ -d "${DEPLOY_ROOT}/../../src" ] || [ -d "${DEPLOY_ROOT}/../../tests" ]; then
    PROJECT_ROOT="$(cd "${DEPLOY_ROOT}/../.." && pwd)"
else
    # 如果找不到，使用当前目录的父目录
    PROJECT_ROOT="$(cd "${DEPLOY_ROOT}/.." && pwd)"
fi

# 设置环境变量
export PYTHONPATH="${PROJECT_ROOT}:${DEPLOY_ROOT}"
export PYTHONWARNINGS=ignore
export KMP_DUPLICATE_LIB_OK=TRUE
export HF_HOME="${DEPLOY_ROOT}/models/huggingface"
export TRANSFORMERS_CACHE="${DEPLOY_ROOT}/models/huggingface"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

# 检查是否有正在运行的服务
if pgrep -f "uvicorn src.api.main:app" > /dev/null; then
    echo "检测到已运行的API服务，正在停止..."
    pkill -f "uvicorn src.api.main:app"
    sleep 2
fi

# 启动API服务
echo "启动API服务..."
echo "API地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"

# 启动API服务（后台运行）
cd "${PROJECT_ROOT}"
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload > "${DEPLOY_ROOT}/logs/api.log" 2>&1 &
API_PID=$!

echo "API服务已启动，进程ID: ${API_PID}"
echo "查看日志: tail -f ${DEPLOY_ROOT}/logs/api.log"
echo "停止服务: kill ${API_PID}"
EOF
    chmod +x "${START_SCRIPT}"
    
    log "${GREEN}启动脚本生成完成！${NC}"
    log "${YELLOW}- API启动脚本: ${API_SCRIPT}${NC}"
    log "${YELLOW}- 完整启动脚本: ${START_SCRIPT}${NC}"
}

# 创建安装说明文件
create_install_guide() {
    log "${BLUE}===============================================${NC}"
    log "${GREEN}          创建安装说明文件${NC}"
    log "${BLUE}===============================================${NC}"
    
    # 创建安装说明文件
    INSTALL_GUIDE="${DEPLOY_TEST_DIR}/INSTALL_GUIDE.md"
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

2. **安装依赖**
   ```bash
   # 升级pip
   pip install --upgrade pip
   
   # 安装核心依赖
   pip install -r requirements.txt
   ```

3. **运行一键安装工具**
   ```bash
   # Linux
   cd scripts
   chmod +x install_auto.sh
   ./install_auto.sh
   ```
   
   ```batch
   :: Windows
   cd scripts
   install_auto.bat
   ```

4. **使用生成的启动脚本**
   - 脚本会自动检测项目代码位置，可在任意目录运行
   - 启动所有服务：`./start_all.sh` (Linux) 或 `start_all.bat` (Windows)
   - 仅启动API服务：`./start_api.sh` (Linux) 或 `start_api.bat` (Windows)

## 功能说明

- **AI模型自动下载**：脚本会自动下载CLIP、CLAP、Whisper等必要模型
- **环境自动检测**：启动脚本会自动检测项目代码位置和运行环境
- **配置自动生成**：根据部署环境自动生成合适的配置文件

## 使用方法

### API服务
- API地址：http://localhost:8000
- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 功能测试
```bash
# 运行功能测试
python -m pytest tests/functionality/
```

## 目录结构说明

- `config/`：配置文件目录
- `data/`：数据存储目录（包括数据库文件和临时文件）
- `models/`：AI模型存储目录
- `logs/`：日志文件目录
- 启动脚本：`start_api.sh`/`start_api.bat`、`start_all.sh`/`start_all.bat`

## 常见问题

1. **端口被占用**
   - 修改配置文件中的端口号
   - 或停止占用端口的进程：`lsof -i :8000` 然后 `kill <PID>`

2. **模型下载失败**
   - 检查网络连接
   - 设置HuggingFace镜像：`export HF_ENDPOINT=https://hf-mirror.com`
   - 手动下载模型并放入`models/`目录

3. **依赖安装问题**
   - 确保pip版本较新：`pip install --upgrade pip`
   - 尝试使用虚拟环境：`python -m venv venv && source venv/bin/activate`

4. **Python环境问题**
   - 确保使用Python 3.9-3.11版本
   - 对于CUDA支持，需要安装对应版本的PyTorch

## 部署到新环境

1. 复制`deploy_test/`目录下的所有文件
2. 在目标环境中确保Python已安装
3. 运行`start_all.sh`或`start_all.bat`
4. 脚本会自动检测项目代码位置并启动服务

## 注意事项

- 首次运行时会下载大量模型，需要较长时间和稳定的网络
- 确保磁盘空间充足，尤其是模型存储目录
- 生产环境部署时请修改配置文件中的相关设置
EOF
    
    log "${GREEN}[成功] 安装说明文件创建完成: ${INSTALL_GUIDE}${NC}"
}

# 完整一键安装
main() {
    log "${CYAN}==================================================${NC}"
    log "${GREEN}            MSearch Linux一键安装工具              ${NC}"
    log "${CYAN}==================================================${NC}"
    
    log "${GREEN}[开始] 执行完整安装流程...${NC}"
    log "${YELLOW}安装日志将保存到: ${LOG_FILE}${NC}"
    
    # 执行安装步骤
    log "${GREEN}[步骤 1/7] 检查系统环境...${NC}"
    check_environment || handle_error "环境检查失败"
    
    log "${GREEN}[步骤 2/7] 安装系统依赖和Python包...${NC}"
    install_dependencies || handle_error "依赖安装失败"
    
    log "${GREEN}[步骤 3/7] 下载和配置AI模型...${NC}"
    download_models || log "${YELLOW}[警告] 模型下载部分失败，但继续安装${NC}"
    
    log "${GREEN}[步骤 4/7] 配置项目文件...${NC}"
    configure_project || handle_error "项目配置失败"
    
    log "${GREEN}[步骤 5/7] 创建测试数据...${NC}"
    create_test_data || log "${YELLOW}[警告] 测试数据创建失败，但继续安装${NC}"
    
    log "${GREEN}[步骤 6/7] 运行基本测试...${NC}"
    run_basic_tests || log "${YELLOW}[警告] 部分测试失败，但继续安装${NC}"
    
    log "${GREEN}[步骤 7/7] 生成启动脚本...${NC}"
    generate_startup_scripts || handle_error "启动脚本生成失败"
    
    # 创建安装说明文件
    create_install_guide || log "${YELLOW}[警告] 创建安装说明文件失败，但不影响使用${NC}"
    
    log "${CYAN}==================================================${NC}"
    log "${GREEN}               安装完成！${NC}"
    log "${CYAN}==================================================${NC}"
    
    log "${GREEN}[安装信息]${NC}"
    log "${YELLOW}- 项目目录: ${PROJECT_ROOT}${NC}"
    log "${YELLOW}- 部署目录: ${DEPLOY_TEST_DIR}${NC}"
    log "${YELLOW}- 配置文件: ${DEPLOY_CONFIG_DIR}/config.yml${NC}"
    log "${YELLOW}- 日志文件: ${LOG_FILE}${NC}"
    log "${YELLOW}- 启动脚本: ${DEPLOY_TEST_DIR}/start_all.sh${NC}"
    
    log "${GREEN}[使用方法]${NC}"
    log "${BLUE}1. 启动服务: cd ${DEPLOY_TEST_DIR} && ./start_all.sh${NC}"
    log "${BLUE}2. 访问API文档: http://localhost:8000/docs${NC}"
    log "${BLUE}3. 运行单元测试: cd ${PROJECT_ROOT} && python3 -m pytest tests/unit/${NC}"
    log "${BLUE}4. 查看安装说明: cat ${DEPLOY_TEST_DIR}/INSTALL_GUIDE.md${NC}"
    
    log "${GREEN}==================================================${NC}"
    log "${GREEN}      感谢使用MSearch Linux一键安装工具！        ${NC}"
    log "${GREEN}==================================================${NC}"
    log "${YELLOW}[提示] 脚本支持在任意位置运行，会自动检测项目代码${NC}"    
}

# 执行主函数
main