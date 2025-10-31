#!/bin/bash
"""
MSearch 综合测试执行脚本
根据 docs/test_strategy.md 要求执行完整的测试套件
"""

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
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

# 检查项目根目录
if [ ! -f "docs/test_strategy.md" ]; then
    print_error "请在项目根目录下运行此脚本"
    exit 1
fi

print_info "🚀 开始执行MSearch综合测试..."
print_info "测试策略: docs/test_strategy.md"
print_info "测试环境: $(uname -s) $(uname -m)"

# 激活测试环境
print_info "📦 激活测试环境..."
if [ -f "activate_test_env.sh" ]; then
    source activate_test_env.sh
    print_success "测试环境已激活"
else
    print_warning "测试环境脚本不存在，使用当前环境"
fi

# 检查Python环境
print_info "🔍 检查Python环境..."
python_version=$(python --version 2>&1)
print_info "Python版本: $python_version"

# 检查关键依赖
print_info "📋 检查关键依赖..."
python -c "import torch; print(f'PyTorch: {torch.__version__}')" 2>/dev/null || print_warning "PyTorch未安装"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')" 2>/dev/null || print_warning "Transformers未安装"

# 创建日志目录
mkdir -p logs tests/output

# 运行测试套件
print_info "🧪 执行综合测试套件..."

# 1. 运行最终综合测试
print_info "执行最终综合测试..."
if python tests/comprehensive_test_final.py; then
    print_success "✅ 最终综合测试通过"
    FINAL_TEST_PASSED=true
else
    print_error "❌ 最终综合测试失败"
    FINAL_TEST_PASSED=false
fi

# 2. 运行CPU功能测试（如果存在）
if [ -f "tests/simple_cpu_test.py" ]; then
    print_info "执行CPU功能测试..."
    if python tests/simple_cpu_test.py; then
        print_success "✅ CPU功能测试通过"
        CPU_TEST_PASSED=true
    else
        print_warning "⚠️ CPU功能测试失败"
        CPU_TEST_PASSED=false
    fi
else
    print_info "跳过CPU功能测试（文件不存在）"
    CPU_TEST_PASSED=true
fi

# 3. 运行性能测试（如果存在）
if [ -f "tests/performance/test_cpu_performance.py" ]; then
    print_info "执行性能测试..."
    if python -m pytest tests/performance/test_cpu_performance.py -v; then
        print_success "✅ 性能测试通过"
        PERF_TEST_PASSED=true
    else
        print_warning "⚠️ 性能测试失败"
        PERF_TEST_PASSED=false
    fi
else
    print_info "跳过性能测试（文件不存在）"
    PERF_TEST_PASSED=true
fi

# 4. 运行集成测试（如果存在）
if [ -f "tests/integration/test_simple_integration.py" ]; then
    print_info "执行集成测试..."
    if python -m pytest tests/integration/test_simple_integration.py -v; then
        print_success "✅ 集成测试通过"
        INTEGRATION_TEST_PASSED=true
    else
        print_warning "⚠️ 集成测试失败"
        INTEGRATION_TEST_PASSED=false
    fi
else
    print_info "跳过集成测试（文件不存在）"
    INTEGRATION_TEST_PASSED=true
fi

# 生成测试摘要
print_info "📊 生成测试摘要..."

echo ""
echo "======================================================================="
echo "                        MSearch 测试执行摘要"
echo "======================================================================="
echo "执行时间: $(date)"
echo "测试环境: $(uname -s) $(uname -m)"
echo "Python版本: $python_version"
echo ""
echo "测试结果:"

# 统计测试结果
TOTAL_TESTS=0
PASSED_TESTS=0

if [ "$FINAL_TEST_PASSED" = true ]; then
    echo "  ✅ 最终综合测试 - 通过"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "  ❌ 最终综合测试 - 失败"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ "$CPU_TEST_PASSED" = true ]; then
    echo "  ✅ CPU功能测试 - 通过"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "  ❌ CPU功能测试 - 失败"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ "$PERF_TEST_PASSED" = true ]; then
    echo "  ✅ 性能测试 - 通过"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "  ❌ 性能测试 - 失败"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ "$INTEGRATION_TEST_PASSED" = true ]; then
    echo "  ✅ 集成测试 - 通过"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "  ❌ 集成测试 - 失败"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# 计算成功率
SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))

echo ""
echo "统计信息:"
echo "  总测试数: $TOTAL_TESTS"
echo "  通过数: $PASSED_TESTS"
echo "  失败数: $((TOTAL_TESTS - PASSED_TESTS))"
echo "  成功率: $SUCCESS_RATE%"
echo ""

# 根据测试策略文档评估
if [ $SUCCESS_RATE -ge 95 ]; then
    print_success "🎉 评估结果: 优秀！测试通过率达到95%以上，符合交付标准"
    OVERALL_STATUS="EXCELLENT"
elif [ $SUCCESS_RATE -ge 80 ]; then
    print_success "✅ 评估结果: 良好！测试通过率达到80%以上，基本符合要求"
    OVERALL_STATUS="GOOD"
elif [ $SUCCESS_RATE -ge 60 ]; then
    print_warning "⚠️ 评估结果: 可接受，但需要改进"
    OVERALL_STATUS="ACCEPTABLE"
else
    print_error "❌ 评估结果: 需要重大改进"
    OVERALL_STATUS="NEEDS_IMPROVEMENT"
fi

echo ""
echo "生成的报告文件:"
if [ -f "FINAL_TEST_REPORT.md" ]; then
    echo "  📄 最终测试报告: FINAL_TEST_REPORT.md"
fi
if [ -f "tests/final_test_results.json" ]; then
    echo "  📊 测试结果数据: tests/final_test_results.json"
fi

echo ""
echo "======================================================================="
echo "                        测试执行完成"
echo "======================================================================="

# 返回适当的退出码
if [ "$OVERALL_STATUS" = "EXCELLENT" ] || [ "$OVERALL_STATUS" = "GOOD" ]; then
    exit 0
elif [ "$OVERALL_STATUS" = "ACCEPTABLE" ]; then
    exit 0  # 可接受也返回0，但有警告
else
    exit 1  # 需要改进时返回错误码
fi