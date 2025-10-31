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