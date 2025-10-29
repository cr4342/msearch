#!/bin/bash
# 测试集成测试脚本的简化版本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} 测试集成测试脚本..."

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 检查脚本是否存在
if [ ! -f "$PROJECT_ROOT/scripts/run_integration_test_with_infinity.sh" ]; then
    echo -e "${RED}[ERROR]${NC} 集成测试脚本不存在"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/scripts/stop_infinity_services.sh" ]; then
    echo -e "${RED}[ERROR]${NC} Infinity服务停止脚本不存在"
    exit 1
fi

echo -e "${GREEN}[INFO]${NC} 检查脚本权限..."
chmod +x "$PROJECT_ROOT/scripts/run_integration_test_with_infinity.sh"
chmod +x "$PROJECT_ROOT/scripts/stop_infinity_services.sh"

# 检查依赖
echo -e "${GREEN}[INFO]${NC} 检查Python依赖..."
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}[INFO]${NC} Python 3 已安装: $(python3 --version)"
else
    echo -e "${RED}[ERROR]${NC} Python 3 未安装"
    exit 1
fi

# 检查模型文件
echo -e "${GREEN}[INFO]${NC} 检查模型文件..."
models_dir="$PROJECT_ROOT/offline/models"
models=("clip-vit-base-patch32" "clap-htsat-fused" "whisper-base")

for model in "${models[@]}"; do
    if [ -d "$models_dir/$model" ]; then
        echo -e "${GREEN}[INFO]${NC} 模型 $model 存在"
    else
        echo -e "${YELLOW}[WARNING]${NC} 模型 $model 不存在"
    fi
done

# 创建CPU模式配置
echo -e "${GREEN}[INFO]${NC} 创建CPU模式配置文件..."
"$PROJECT_ROOT/scripts/run_integration_test_with_infinity.sh" --help 2>/dev/null || {
    echo -e "${YELLOW}[WARNING]${NC} 脚本执行有警告，但配置文件可能已创建"
}

# 检查配置文件是否创建
if [ -f "$PROJECT_ROOT/config/config_cpu.yml" ]; then
    echo -e "${GREEN}[INFO]${NC} CPU模式配置文件已创建"
else
    echo -e "${RED}[ERROR]${NC} CPU模式配置文件未创建"
fi

echo -e "${GREEN}[INFO]${NC} 测试完成！"
echo ""
echo "下一步操作："
echo "1. 运行完整集成测试: bash scripts/run_integration_test_with_infinity.sh"
echo "2. 手动启动Infinity服务: bash scripts/start_infinity_services.sh"
echo "3. 手动停止Infinity服务: bash scripts/stop_infinity_services.sh"
echo ""
echo "脚本功能总结："
echo "- 自动检查并下载缺失的模型文件"
echo "- 创建CPU模式配置文件"
echo "- 启动Infinity服务（CLIP、CLAP、Whisper）"
echo "- 运行集成测试和性能测试"
echo "- 自动清理测试环境"