#!/bin/bash

# MSearch 优化测试运行脚本
# 支持不同环境和测试模式

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

# 检查Python环境
check_python_environment() {
    print_info "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_info "Python版本: $PYTHON_VERSION"
    
    # 检查Python版本是否 >= 3.8
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        print_error "需要Python 3.8或更高版本"
        exit 1
    fi
    
    print_success "Python环境检查通过"
}

# 检查和安装依赖
install_dependencies() {
    print_info "检查和安装测试依赖..."
    
    # 检查是否存在虚拟环境
    if [ ! -d "venv" ]; then
        print_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装基础依赖
    if [ -f "requirements.txt" ]; then
        print_info "安装基础依赖..."
        pip install -r requirements.txt
    fi
    
    # 安装测试依赖
    if [ -f "requirements-test.txt" ]; then
        print_info "安装测试依赖..."
        pip install -r requirements-test.txt
    else
        print_info "安装测试依赖包..."
        pip install pytest pytest-asyncio pytest-cov pytest-mock numpy pillow
    fi
    
    print_success "依赖安装完成"
}

# 设置测试环境
setup_test_environment() {
    print_info "设置测试环境..."
    
    # 设置环境变量
    export MSEARCH_TEST_MODE=1
    export PYTHONPATH=$(pwd)
    export MSEARCH_LOG_LEVEL=DEBUG
    
    # 创建测试目录
    mkdir -p tests/output
    mkdir -p tests/logs
    mkdir -p tests/temp
    mkdir -p data/test_models
    mkdir -p logs
    
    # 清理旧的测试输出
    rm -f tests/output/*.json
    rm -f tests/logs/*.log
    
    print_success "测试环境设置完成"
}

# 检查系统资源
check_system_resources() {
    print_info "检查系统资源..."
    
    # 检查内存
    if command -v free &> /dev/null; then
        TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.1f", $2/1024}')
        AVAIL_MEM=$(free -m | awk 'NR==2{printf "%.1f", $7/1024}')
        print_info "系统内存: ${TOTAL_MEM}GB 总计, ${AVAIL_MEM}GB 可用"
        
        # 检查是否有足够内存
        if (( $(echo "$AVAIL_MEM < 2.0" | bc -l) )); then
            print_warning "可用内存不足2GB，可能影响测试性能"
        fi
    fi
    
    # 检查CPU核心数
    if command -v nproc &> /dev/null; then
        CPU_CORES=$(nproc)
        print_info "CPU核心数: $CPU_CORES"
    fi
    
    # 检查GPU
    if command -v nvidia-smi &> /dev/null; then
        print_info "检测到NVIDIA GPU"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | head -1
    else
        print_info "未检测到GPU，将使用CPU模式"
    fi
}

# 运行单元测试
run_unit_tests() {
    print_info "运行单元测试..."
    
    python3 -m pytest tests/unit/ \
        -v \
        --tb=short \
        --cov=src \
        --cov-report=html:tests/output/coverage_html \
        --cov-report=term \
        --cov-report=json:tests/output/coverage.json \
        -m "not slow" \
        --junitxml=tests/output/unit_tests.xml
    
    UNIT_EXIT_CODE=$?
    
    if [ $UNIT_EXIT_CODE -eq 0 ]; then
        print_success "单元测试通过"
    else
        print_error "单元测试失败"
    fi
    
    return $UNIT_EXIT_CODE
}

# 运行集成测试
run_integration_tests() {
    print_info "运行集成测试..."
    
    python3 -m pytest tests/integration/ \
        -v \
        --tb=short \
        -m "not slow and not gpu" \
        --junitxml=tests/output/integration_tests.xml
    
    INTEGRATION_EXIT_CODE=$?
    
    if [ $INTEGRATION_EXIT_CODE -eq 0 ]; then
        print_success "集成测试通过"
    else
        print_error "集成测试失败"
    fi
    
    return $INTEGRATION_EXIT_CODE
}

# 运行时间戳精度测试
run_timestamp_tests() {
    print_info "运行时间戳精度测试..."
    
    python3 -m pytest tests/ \
        -v \
        --tb=short \
        -m "timestamp" \
        --junitxml=tests/output/timestamp_tests.xml
    
    TIMESTAMP_EXIT_CODE=$?
    
    if [ $TIMESTAMP_EXIT_CODE -eq 0 ]; then
        print_success "时间戳精度测试通过"
    else
        print_error "时间戳精度测试失败"
    fi
    
    return $TIMESTAMP_EXIT_CODE
}

# 运行性能测试
run_performance_tests() {
    print_info "运行性能测试..."
    
    python3 -m pytest tests/ \
        -v \
        --tb=short \
        -m "performance" \
        --junitxml=tests/output/performance_tests.xml
    
    PERFORMANCE_EXIT_CODE=$?
    
    if [ $PERFORMANCE_EXIT_CODE -eq 0 ]; then
        print_success "性能测试通过"
    else
        print_error "性能测试失败"
    fi
    
    return $PERFORMANCE_EXIT_CODE
}

# 生成测试报告
generate_test_report() {
    print_info "生成测试报告..."
    
    # 创建测试报告
    cat > tests/output/test_summary.json << EOF
{
    "timestamp": "$(date -Iseconds)",
    "environment": {
        "python_version": "$(python3 --version | cut -d' ' -f2)",
        "platform": "$(uname -s)",
        "architecture": "$(uname -m)"
    },
    "test_results": {
        "unit_tests": $UNIT_RESULT,
        "integration_tests": $INTEGRATION_RESULT,
        "timestamp_tests": $TIMESTAMP_RESULT,
        "performance_tests": $PERFORMANCE_RESULT
    },
    "coverage_report": "tests/output/coverage_html/index.html"
}
EOF
    
    # 打印测试摘要
    echo ""
    echo "=========================================="
    echo "           测试结果摘要"
    echo "=========================================="
    echo "单元测试:     $([ $UNIT_RESULT -eq 0 ] && echo "✅ 通过" || echo "❌ 失败")"
    echo "集成测试:     $([ $INTEGRATION_RESULT -eq 0 ] && echo "✅ 通过" || echo "❌ 失败")"
    echo "时间戳测试:   $([ $TIMESTAMP_RESULT -eq 0 ] && echo "✅ 通过" || echo "❌ 失败")"
    echo "性能测试:     $([ $PERFORMANCE_RESULT -eq 0 ] && echo "✅ 通过" || echo "❌ 失败")"
    echo "=========================================="
    echo "测试报告: tests/output/test_summary.json"
    echo "覆盖率报告: tests/output/coverage_html/index.html"
    echo "=========================================="
}

# 清理函数
cleanup() {
    print_info "清理测试环境..."
    
    # 停止可能的后台进程
    pkill -f "qdrant" 2>/dev/null || true
    
    # 清理临时文件
    rm -rf tests/temp/*
    
    print_success "清理完成"
}

# 主函数
main() {
    print_info "开始运行MSearch优化测试套件"
    
    # 设置清理陷阱
    trap cleanup EXIT
    
    # 解析命令行参数
    UNIT_ONLY=false
    INTEGRATION_ONLY=false
    TIMESTAMP_ONLY=false
    PERFORMANCE_ONLY=false
    SETUP_ONLY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit)
                UNIT_ONLY=true
                shift
                ;;
            --integration)
                INTEGRATION_ONLY=true
                shift
                ;;
            --timestamp)
                TIMESTAMP_ONLY=true
                shift
                ;;
            --performance)
                PERFORMANCE_ONLY=true
                shift
                ;;
            --setup-only)
                SETUP_ONLY=true
                shift
                ;;
            --help|-h)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --unit          只运行单元测试"
                echo "  --integration   只运行集成测试"
                echo "  --timestamp     只运行时间戳测试"
                echo "  --performance   只运行性能测试"
                echo "  --setup-only    只设置环境"
                echo "  --help, -h      显示帮助信息"
                exit 0
                ;;
            *)
                print_error "未知选项: $1"
                exit 1
                ;;
        esac
    done
    
    # 基础环境检查和设置
    check_python_environment
    install_dependencies
    setup_test_environment
    check_system_resources
    
    if [ "$SETUP_ONLY" = true ]; then
        print_success "环境设置完成，退出"
        exit 0
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 创建测试数据
    print_info "创建测试数据..."
    python3 tests/fixtures/create_test_data.py || print_warning "测试数据创建失败，继续执行"
    
    # 初始化结果变量
    UNIT_RESULT=0
    INTEGRATION_RESULT=0
    TIMESTAMP_RESULT=0
    PERFORMANCE_RESULT=0
    
    # 根据参数运行相应测试
    if [ "$UNIT_ONLY" = true ]; then
        run_unit_tests
        UNIT_RESULT=$?
    elif [ "$INTEGRATION_ONLY" = true ]; then
        run_integration_tests
        INTEGRATION_RESULT=$?
    elif [ "$TIMESTAMP_ONLY" = true ]; then
        run_timestamp_tests
        TIMESTAMP_RESULT=$?
    elif [ "$PERFORMANCE_ONLY" = true ]; then
        run_performance_tests
        PERFORMANCE_RESULT=$?
    else
        # 运行所有测试
        run_unit_tests
        UNIT_RESULT=$?
        
        run_integration_tests
        INTEGRATION_RESULT=$?
        
        run_timestamp_tests
        TIMESTAMP_RESULT=$?
        
        run_performance_tests
        PERFORMANCE_RESULT=$?
    fi
    
    # 生成测试报告
    generate_test_report
    
    # 计算总体结果
    TOTAL_FAILURES=$((UNIT_RESULT + INTEGRATION_RESULT + TIMESTAMP_RESULT + PERFORMANCE_RESULT))
    
    if [ $TOTAL_FAILURES -eq 0 ]; then
        print_success "所有测试通过！"
        exit 0
    else
        print_error "有测试失败，请查看详细报告"
        exit 1
    fi
}

# 运行主函数
main "$@"