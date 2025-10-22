#!/bin/bash
# 优化的测试运行脚本
# 解决Python 3.12兼容性、Qdrant启动和OpenCV依赖问题

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    MSearch 优化测试套件${NC}"
echo -e "${BLUE}========================================${NC}"

# 显示系统信息
echo -e "${GREEN}[INFO]${NC} 系统信息:"
echo "  Python版本: $(python3 --version)"
echo "  操作系统: $(uname -s)"
echo "  架构: $(uname -m)"
echo "  项目根目录: $PROJECT_ROOT"
echo ""

# 步骤1: 检查并安装依赖
echo -e "${GREEN}[STEP 1]${NC} 检查并安装Python 3.12兼容依赖..."
if python3 "$PROJECT_ROOT/scripts/install_python312_compatible.py" --check-only; then
    echo -e "${GREEN}[INFO]${NC} 环境检查通过"
else
    echo -e "${YELLOW}[WARNING]${NC} 环境检查失败，尝试安装依赖..."
    if python3 "$PROJECT_ROOT/scripts/install_python312_compatible.py"; then
        echo -e "${GREEN}[SUCCESS]${NC} 依赖安装完成"
    else
        echo -e "${RED}[ERROR]${NC} 依赖安装失败"
        exit 1
    fi
fi

# 步骤2: 启动Qdrant服务
echo -e "${GREEN}[STEP 2]${NC} 启动Qdrant服务..."
if bash "$PROJECT_ROOT/scripts/start_qdrant_optimized.sh"; then
    echo -e "${GREEN}[SUCCESS]${NC} Qdrant服务启动成功"
    QDRANT_STARTED=true
else
    echo -e "${RED}[ERROR]${NC} Qdrant服务启动失败"
    exit 1
fi

# 清理函数
cleanup() {
    echo -e "${GREEN}[INFO]${NC} 清理测试环境..."
    
    # 停止Qdrant服务
    if [ "$QDRANT_STARTED" = true ]; then
        if [ -f /tmp/qdrant.pid ]; then
            local pid=$(cat /tmp/qdrant.pid)
            if kill -0 $pid 2>/dev/null; then
                echo "停止Qdrant服务 (PID: $pid)..."
                kill $pid 2>/dev/null || true
                sleep 2
                kill -9 $pid 2>/dev/null || true
            fi
            rm -f /tmp/qdrant.pid
        fi
    fi
    
    echo -e "${GREEN}[INFO]${NC} 清理完成"
}

# 注册清理函数
trap cleanup EXIT INT TERM

# 步骤3: 运行测试
echo -e "${GREEN}[STEP 3]${NC} 运行优化测试套件..."

# 设置环境变量
export PYTHONPATH="$PROJECT_ROOT"
export MSEARCH_CONFIG="$PROJECT_ROOT/tests/configs/cpu_test_config_optimized.yml"

# 创建测试输出目录
mkdir -p "$PROJECT_ROOT/tests/output"
mkdir -p "$PROJECT_ROOT/logs"

# 运行测试
echo -e "${GREEN}[INFO]${NC} 开始运行测试..."

if python3 "$PROJECT_ROOT/tests/run_optimized_tests.py"; then
    echo -e "${GREEN}[SUCCESS]${NC} 所有测试通过！"
    TEST_RESULT=0
else
    echo -e "${RED}[ERROR]${NC} 部分测试失败"
    TEST_RESULT=1
fi

# 步骤4: 生成测试报告
echo -e "${GREEN}[STEP 4]${NC} 生成测试报告..."

# 创建简单的测试报告
REPORT_FILE="$PROJECT_ROOT/tests/output/test_report_$(date +%Y%m%d_%H%M%S).txt"

cat > "$REPORT_FILE" << EOF
MSearch 优化测试报告
==================

测试时间: $(date)
Python版本: $(python3 --version)
操作系统: $(uname -s) $(uname -r)

测试结果: $([ $TEST_RESULT -eq 0 ] && echo "通过" || echo "失败")

测试环境:
- 项目根目录: $PROJECT_ROOT
- 配置文件: $MSEARCH_CONFIG
- Qdrant服务: $([ "$QDRANT_STARTED" = true ] && echo "已启动" || echo "未启动")

日志文件:
- 测试日志: $PROJECT_ROOT/logs/cpu_test.log
- Qdrant日志: $PROJECT_ROOT/logs/qdrant.log

EOF

echo -e "${GREEN}[INFO]${NC} 测试报告已生成: $REPORT_FILE"

# 显示测试摘要
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}           测试摘要${NC}"
echo -e "${BLUE}========================================${NC}"

if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ 测试状态: 通过${NC}"
else
    echo -e "${RED}✗ 测试状态: 失败${NC}"
fi

echo -e "📊 测试报告: $REPORT_FILE"

if [ -f "$PROJECT_ROOT/logs/cpu_test.log" ]; then
    echo -e "📋 测试日志: $PROJECT_ROOT/logs/cpu_test.log"
fi

if [ -f "$PROJECT_ROOT/logs/qdrant.log" ]; then
    echo -e "🗄️  Qdrant日志: $PROJECT_ROOT/logs/qdrant.log"
fi

echo ""
echo -e "${GREEN}[INFO]${NC} 测试完成！"

exit $TEST_RESULT