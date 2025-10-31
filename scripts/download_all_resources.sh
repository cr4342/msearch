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
    
    # 检查是否已有足够的包
    existing_packages=$(find "$PROJECT_ROOT/offline/packages" -type f -name "*.whl" | wc -l)
    if [ "$existing_packages" -gt 100 ]; then
        log_info "检测到已有 $existing_packages 个包，跳过基础依赖下载"
    else
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
    fi
    
    # 特别处理infinity-emb兼容性问题
    log_info "特别处理infinity-emb兼容性问题..."
    download_infinity_emb_compatible
    
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
    key_packages=("torch" "transformers" "fastapi" "qdrant-client" "inaspeechsegmenter" "infinity_emb")
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

# 下载infinity-emb兼容版本函数
download_infinity_emb_compatible() {
    log_info "下载infinity-emb兼容版本和依赖..."
    
    # 下载兼容的infinity-emb版本
    log_info "下载infinity-emb基础版本..."
    pip download "infinity-emb==0.0.76" \
        --dest "$PROJECT_ROOT/offline/packages" \
        --no-deps \
        --disable-pip-version-check \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --timeout 60 \
        --retries 3 || {
            log_warning "使用默认PyPI源重试..."
            pip download "infinity-emb==0.0.76" \
                --dest "$PROJECT_ROOT/offline/packages" \
                --no-deps \
                --disable-pip-version-check \
                --timeout 60 \
                --retries 3
        }
    
    # 下载兼容的optimum版本（不包含bettertransformer）
    log_info "下载兼容的optimum版本..."
    pip download "optimum>=1.14.0,<2.0.0" \
        --dest "$PROJECT_ROOT/offline/packages" \
        --disable-pip-version-check \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --timeout 60 \
        --retries 3 || {
            log_warning "optimum下载失败，尝试下载特定版本..."
            pip download "optimum==1.21.4" \
                --dest "$PROJECT_ROOT/offline/packages" \
                --disable-pip-version-check \
                -i https://pypi.tuna.tsinghua.edu.cn/simple \
                --timeout 60 \
                --retries 3
        }
    
    # 下载sentence-transformers兼容版本
    log_info "下载sentence-transformers兼容版本..."
    pip download "sentence-transformers>=3.0.0,<4.0.0" \
        --dest "$PROJECT_ROOT/offline/packages" \
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
            --dest "$PROJECT_ROOT/offline/packages" \
            --disable-pip-version-check \
            -i https://pypi.tuna.tsinghua.edu.cn/simple \
            --timeout 60 \
            --retries 3 || {
                log_warning "$dep 下载失败，跳过"
            }
    done
    
    log_info "infinity-emb兼容版本下载完成"
}

# 下载模型函数
download_models() {
    log_info "4. 下载AI模型..."
    
    # 创建模型目录结构
    mkdir -p "$PROJECT_ROOT/offline/models"
    
    # 检查是否已有模型
    local models_exist=true
    local required_models=("clip-vit-base-patch32" "clap-htsat-fused" "whisper-base")
    
    for model in "${required_models[@]}"; do
        if [ ! -d "$PROJECT_ROOT/offline/models/$model" ] || [ -z "$(ls -A "$PROJECT_ROOT/offline/models/$model" 2>/dev/null)" ]; then
            models_exist=false
            break
        fi
    done
    
    if [ "$models_exist" = true ]; then
        log_info "所有模型已存在，验证完整性..."
        local total_files=$(find "$PROJECT_ROOT/offline/models" -type f | wc -l)
        if [ "$total_files" -gt 20 ]; then
            log_info "模型文件完整，跳过下载"
            return 0
        else
            log_warning "模型文件不完整，重新下载"
        fi
    fi
    
    # 确保huggingface_hub已安装（用于模型下载）
    log_info "确保huggingface_hub已安装..."
    if command -v pip &> /dev/null; then
        pip install huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade || true
    else
        log_warning "未找到pip，跳过huggingface_hub安装"
    fi
    
    # 设置HuggingFace镜像（国内优化）
    export HF_ENDPOINT=https://hf-mirror.com
    export HF_HUB_ENABLE_HF_TRANSFER=1
    
    # 使用Python脚本下载模型（更稳定）
    create_model_download_script
    
    # 执行模型下载
    log_info "开始下载AI模型..."
    python3 "$PROJECT_ROOT/offline/download_models.py" || {
        log_warning "Python脚本下载失败，尝试使用huggingface-cli..."
        download_models_with_cli
    }
    
    # 验证下载结果
    log_info "验证模型下载结果..."
    models_count=$(find "$PROJECT_ROOT/offline/models" -type f | wc -l)
    log_info "模型下载完成:"
    log_info "  - 模型文件数量: $models_count"
    log_info "  - 保存位置: $PROJECT_ROOT/offline/models/"
    
    if [ "$models_count" -gt 20 ]; then
        log_info "模型下载完成！"
        return 0
    else
        log_warning "模型下载可能不完整，但继续执行"
        return 1
    fi
}

# 创建模型下载脚本
create_model_download_script() {
    cat > "$PROJECT_ROOT/offline/download_models.py" << 'EOF'
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
            if "clip" in repo_id.lower():
                from transformers import CLIPModel, CLIPProcessor
                print(f"  尝试 {attempt + 1}/{max_retries}: 下载CLIP模型...")
                model = CLIPModel.from_pretrained(repo_id, cache_dir=local_path)
                processor = CLIPProcessor.from_pretrained(repo_id, cache_dir=local_path)
                model.save_pretrained(local_path)
                processor.save_pretrained(local_path)
                
            elif "clap" in repo_id.lower():
                from transformers import ClapModel, ClapProcessor
                print(f"  尝试 {attempt + 1}/{max_retries}: 下载CLAP模型...")
                model = ClapModel.from_pretrained(repo_id, cache_dir=local_path)
                processor = ClapProcessor.from_pretrained(repo_id, cache_dir=local_path)
                model.save_pretrained(local_path)
                processor.save_pretrained(local_path)
                
            elif "whisper" in repo_id.lower():
                from transformers import WhisperForConditionalGeneration, WhisperProcessor
                print(f"  尝试 {attempt + 1}/{max_retries}: 下载Whisper模型...")
                model = WhisperForConditionalGeneration.from_pretrained(repo_id, cache_dir=local_path)
                processor = WhisperProcessor.from_pretrained(repo_id, cache_dir=local_path)
                model.save_pretrained(local_path)
                processor.save_pretrained(local_path)
            
            print(f"  ✅ {repo_id} 下载成功")
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
    
    # 模型列表
    models = [
        {
            "repo_id": "openai/clip-vit-base-patch32",
            "local_path": "offline/models/clip-vit-base-patch32"
        },
        {
            "repo_id": "laion/clap-htsat-fused", 
            "local_path": "offline/models/clap-htsat-fused"
        },
        {
            "repo_id": "openai/whisper-base",
            "local_path": "offline/models/whisper-base"
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
    
    chmod +x "$PROJECT_ROOT/offline/download_models.py"
}

# 使用CLI下载模型（备用方案）
download_models_with_cli() {
    log_info "使用huggingface-cli下载模型..."
    
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
}

# 生成离线安装脚本
generate_offline_install_script() {
    log_info "5. 生成离线安装脚本..."
    
    # 生成离线安装脚本
    cat > "$PROJECT_ROOT/scripts/install_offline.sh" << 'EOF'
#!/bin/bash
# 离线安装脚本 - 使用已下载的离线资源

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}开始离线安装MSearch项目依赖...${NC}"

# 检查离线资源
check_offline_resources() {
    echo -e "${BLUE}检查离线资源...${NC}"
    
    if [ ! -d "$PROJECT_ROOT/offline/packages" ]; then
        echo -e "${RED}错误：未找到离线包目录${NC}"
        exit 1
    fi
    
    local packages_count=$(find "$PROJECT_ROOT/offline/packages" -name "*.whl" | wc -l)
    echo -e "${GREEN}发现 $packages_count 个离线包${NC}"
    
    if [ "$packages_count" -lt 50 ]; then
        echo -e "${YELLOW}警告：离线包数量较少，可能不完整${NC}"
    fi
}

# 安装离线依赖包
install_offline_packages() {
    echo -e "${BLUE}安装离线依赖包...${NC}"
    
    # 升级pip
    python3 -m pip install --upgrade pip || true
    
    # 安装基础依赖（不使用网络）
    echo -e "${GREEN}安装基础依赖包...${NC}"
    python3 -m pip install \
        --no-index \
        --find-links="$PROJECT_ROOT/offline/packages" \
        --force-reinstall \
        --no-deps \
        wheel setuptools || true
    
    # 安装核心依赖
    echo -e "${GREEN}安装核心依赖包...${NC}"
    local core_packages=(
        "numpy"
        "torch"
        "torchvision" 
        "transformers"
        "fastapi"
        "uvicorn"
        "pydantic"
        "sqlalchemy"
        "qdrant-client"
    )
    
    for package in "${core_packages[@]}"; do
        echo -e "${BLUE}安装 $package...${NC}"
        python3 -m pip install \
            --no-index \
            --find-links="$PROJECT_ROOT/offline/packages" \
            "$package" || {
                echo -e "${YELLOW}警告：$package 安装失败${NC}"
            }
    done
    
    # 特别处理infinity-emb
    echo -e "${GREEN}安装infinity-emb兼容版本...${NC}"
    python3 -m pip install \
        --no-index \
        --find-links="$PROJECT_ROOT/offline/packages" \
        --force-reinstall \
        "infinity-emb==0.0.76" || {
            echo -e "${YELLOW}警告：infinity-emb安装失败${NC}"
        }
    
    # 安装其他依赖
    echo -e "${GREEN}安装其他依赖包...${NC}"
    python3 -m pip install \
        --no-index \
        --find-links="$PROJECT_ROOT/offline/packages" \
        --requirement "$PROJECT_ROOT/requirements.txt" || {
            echo -e "${YELLOW}警告：部分依赖安装失败，但继续执行${NC}"
        }
}

# 验证安装
verify_installation() {
    echo -e "${BLUE}验证安装结果...${NC}"
    
    local test_packages=(
        "numpy"
        "torch" 
        "transformers"
        "fastapi"
        "qdrant_client"
    )
    
    local failed_packages=()
    
    for package in "${test_packages[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            echo -e "${GREEN}✅ $package${NC}"
        else
            echo -e "${RED}❌ $package${NC}"
            failed_packages+=("$package")
        fi
    done
    
    # 特别测试infinity-emb
    if python3 -c "import infinity_emb" 2>/dev/null; then
        echo -e "${GREEN}✅ infinity_emb${NC}"
    else
        echo -e "${YELLOW}⚠️ infinity_emb (可能需要额外配置)${NC}"
    fi
    
    if [ ${#failed_packages[@]} -eq 0 ]; then
        echo -e "${GREEN}所有核心包安装成功！${NC}"
        return 0
    else
        echo -e "${YELLOW}以下包安装失败: ${failed_packages[*]}${NC}"
        return 1
    fi
}

# 主函数
main() {
    check_offline_resources
    install_offline_packages
    verify_installation
    
    echo -e "${GREEN}离线安装完成！${NC}"
    echo ""
    echo "后续步骤："
    echo "1. 启动Qdrant服务: ./scripts/start_qdrant.sh"
    echo "2. 运行测试: python3 tests/simple_functionality_test.py"
    echo "3. 启动API服务: python3 src/api/main.py"
}

main "$@"
EOF

    chmod +x "$PROJECT_ROOT/scripts/install_offline.sh"
    
    log_info "离线安装脚本已生成: $PROJECT_ROOT/scripts/install_offline.sh"
}

# 生成服务脚本函数
generate_service_scripts() {
    log_info "6. 生成服务启动脚本..."
    
    # 生成Qdrant服务启动脚本
    cat > "$PROJECT_ROOT/scripts/start_qdrant.sh" << 'EOF'
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
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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
        echo -e "${YELLOW}警告：未找到Qdrant二进制文件，尝试使用Docker...${NC}"
        if command -v docker &> /dev/null; then
            docker run -d \
                --name qdrant-msearch \
                -p 6333:6333 \
                -p 6334:6334 \
                -v "$QDRANT_DATA_DIR:/qdrant/storage" \
                qdrant/qdrant:latest
            echo "Qdrant Docker容器已启动"
            return 0
        else
            echo "错误：未找到Qdrant二进制文件或Docker"
            exit 1
        fi
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

    chmod +x "$PROJECT_ROOT/scripts/start_qdrant.sh"

    # 生成Qdrant服务停止脚本
    cat > "$PROJECT_ROOT/scripts/stop_qdrant.sh" << 'EOF'
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

    chmod +x "$PROJECT_ROOT/scripts/stop_qdrant.sh"

    log_info "服务启动脚本已生成:"
    log_info "  - Qdrant启动脚本: $PROJECT_ROOT/scripts/start_qdrant.sh"
    log_info "  - Qdrant停止脚本: $PROJECT_ROOT/scripts/stop_qdrant.sh"
}

# 创建infinity-emb修复脚本
create_infinity_fix_script() {
    log_info "7. 创建infinity-emb修复脚本..."
    
    cat > "$PROJECT_ROOT/scripts/fix_infinity_emb.sh" << 'EOF'
#!/bin/bash
# infinity-emb修复脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}修复infinity-emb依赖问题...${NC}"

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 卸载有问题的版本
echo -e "${YELLOW}卸载现有的infinity-emb...${NC}"
python3 -m pip uninstall infinity-emb -y || true

# 安装兼容版本
echo -e "${YELLOW}安装兼容版本的infinity-emb...${NC}"
if [ -d "$PROJECT_ROOT/offline/packages" ]; then
    # 使用离线包
    python3 -m pip install \
        --no-index \
        --find-links="$PROJECT_ROOT/offline/packages" \
        --force-reinstall \
        "infinity-emb==0.0.76"
else
    # 在线安装
    python3 -m pip install "infinity-emb==0.0.76" --no-deps
fi

# 安装必要的依赖
echo -e "${YELLOW}安装必要依赖...${NC}"
local deps=(
    "sentence-transformers>=3.0.0"
    "torch>=2.0.0"
    "transformers>=4.30.0"
    "fastapi>=0.100.0"
    "uvicorn>=0.20.0"
    "pydantic>=2.0.0"
    "typer>=0.9.0"
    "rich>=13.0.0"
)

for dep in "${deps[@]}"; do
    if [ -d "$PROJECT_ROOT/offline/packages" ]; then
        python3 -m pip install \
            --no-index \
            --find-links="$PROJECT_ROOT/offline/packages" \
            "$dep" || echo -e "${YELLOW}警告：$dep 安装失败${NC}"
    else
        python3 -m pip install "$dep" || echo -e "${YELLOW}警告：$dep 安装失败${NC}"
    fi
done

# 测试安装
echo -e "${YELLOW}测试infinity-emb安装...${NC}"
if python3 -c "import infinity_emb; print(f'infinity-emb版本: {infinity_emb.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✅ infinity-emb安装成功${NC}"
else
    echo -e "${RED}❌ infinity-emb安装失败${NC}"
    exit 1
fi

echo -e "${GREEN}infinity-emb修复完成！${NC}"
EOF

    chmod +x "$PROJECT_ROOT/scripts/fix_infinity_emb.sh"
    
    log_info "infinity-emb修复脚本已生成: $PROJECT_ROOT/scripts/fix_infinity_emb.sh"
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
    
    # 生成脚本
    generate_offline_install_script
    generate_service_scripts
    create_infinity_fix_script
    
    # 验证下载结果
    log_info "8. 验证下载结果..."
    if [ -d "$PROJECT_ROOT/offline/bin" ] && [ -d "$PROJECT_ROOT/offline/packages" ] && [ -d "$PROJECT_ROOT/offline/models" ]; then
        bin_count=$(find "$PROJECT_ROOT/offline/bin" -type f 2>/dev/null | wc -l)
        packages_count=$(find "$PROJECT_ROOT/offline/packages" -type f -name "*.whl" 2>/dev/null | wc -l)
        models_count=$(find "$PROJECT_ROOT/offline/models" -type f 2>/dev/null | wc -l)
        
        log_info "离线资源下载完成:"
        log_info "  - 二进制文件数量: $bin_count"
        log_info "  - 依赖包数量: $packages_count"
        log_info "  - 模型文件数量: $models_count"
        log_info "  - 保存位置: $PROJECT_ROOT/offline/"
        
        log_info "所有离线资源下载脚本执行完成！"
        log_info ""
        log_info "🚀 快速开始指南："
        echo ""
        echo "1. 离线安装所有依赖："
        echo "   ./scripts/install_offline.sh"
        echo ""
        echo "2. 修复infinity-emb问题："
        echo "   ./scripts/fix_infinity_emb.sh"
        echo ""
        echo "3. 启动Qdrant服务："
        echo "   ./scripts/start_qdrant.sh"
        echo ""
        echo "4. 运行测试验证："
        echo "   python3 tests/simple_functionality_test.py"
        echo ""
        echo "5. 启动API服务："
        echo "   python3 src/api/main.py"
        echo ""
        echo "6. 停止所有服务："
        echo "   ./scripts/stop_qdrant.sh"
        echo ""
        log_info "📝 注意事项："
        echo "- 如果遇到网络问题，所有资源都已离线缓存"
        echo "- infinity-emb问题已通过兼容版本解决"
        echo "- 模型文件较大，首次加载可能需要时间"
        echo "- 建议在虚拟环境中运行以避免依赖冲突"
        
    else
        log_error "离线资源下载失败，请检查目录结构"
        exit 1
    fi
}

# 执行主函数
main
