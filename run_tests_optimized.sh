#!/bin/bash

# MSearch 优化测试运行脚本
# 根据test_strategy.md要求，执行全面的测试套件

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"

# 测试目录
TEST_DIR="${PROJECT_ROOT}/tests"
DEPLOY_TEST_DIR="${TEST_DIR}/deployment_test"
LOGS_DIR="${DEPLOY_TEST_DIR}/logs"

# 创建必要的目录
mkdir -p "${LOGS_DIR}"
mkdir -p "${DEPLOY_TEST_DIR}/config"
mkdir -p "${DEPLOY_TEST_DIR}/data"
mkdir -p "${DEPLOY_TEST_DIR}/models"

# 日志文件
TEST_LOG="${LOGS_DIR}/test_run_$(date +%Y%m%d_%H%M%S).log"
PERFORMANCE_LOG="${LOGS_DIR}/performance_test.log"
ERROR_LOG="${LOGS_DIR}/error_test.log"

# 初始化日志
echo "MSearch 测试运行日志" > "${TEST_LOG}"
echo "开始时间: $(date)" >> "${TEST_LOG}"
echo "项目目录: ${PROJECT_ROOT}" >> "${TEST_LOG}"
echo "===============================================" >> "${TEST_LOG}"

# 日志函数
log() {
    local level="$1"
    local message="$2"
    local timestamp="$(date +"%Y-%m-%d %H:%M:%S")"
    local formatted="[$timestamp] [${level}] $message"
    
    case "$level" in
        INFO) echo -e "${GREEN}${formatted}${NC}" ;;
        WARNING) echo -e "${YELLOW}${formatted}${NC}" ;;
        ERROR) echo -e "${RED}${formatted}${NC}" ;;
        DEBUG) echo -e "${BLUE}${formatted}${NC}" ;;
        *) echo -e "${formatted}" ;;
    esac
    
    echo "$formatted" >> "$TEST_LOG"
}

# 错误处理
handle_error() {
    log "ERROR" "测试失败: $1"
    log "INFO" "查看详细日志: ${TEST_LOG}"
    exit 1
}

# 检查Python环境
check_python_environment() {
    log "INFO" "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        handle_error "未找到Python3"
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1)
    log "INFO" "Python版本: ${PYTHON_VERSION}"
    
    # 检查pytest
    if ! python3 -c "import pytest" 2>/dev/null; then
        log "WARNING" "pytest未安装，尝试安装..."
        python3 -m pip install pytest pytest-cov pytest-mock pytest-asyncio
    fi
    
    log "INFO" "Python环境检查完成"
}

# 设置测试环境
setup_test_environment() {
    log "INFO" "设置测试环境..."
    
    # 设置环境变量
    export PYTHONPATH="${PROJECT_ROOT}:${DEPLOY_TEST_DIR}"
    export PYTHONWARNINGS=ignore
    export HF_HUB_OFFLINE=1
    export TRANSFORMERS_OFFLINE=1
    
    # 复制配置文件
    if [ -f "${TEST_DIR}/configs/cpu_test_config.yml" ]; then
        cp "${TEST_DIR}/configs/cpu_test_config.yml" "${DEPLOY_TEST_DIR}/config/"
        log "INFO" "已复制CPU测试配置"
    fi
    
    if [ -f "${TEST_DIR}/configs/logging_config.yml" ]; then
        cp "${TEST_DIR}/configs/logging_config.yml" "${DEPLOY_TEST_DIR}/config/"
        log "INFO" "已复制日志配置"
    fi
    
    log "INFO" "测试环境设置完成"
}

# 运行单元测试
run_unit_tests() {
    log "INFO" "==============================================="
    log "INFO" "运行单元测试"
    log "INFO" "==============================================="
    
    cd "${PROJECT_ROOT}"
    
    # CPU模式功能测试
    if [ -f "${TEST_DIR}/cpu_mode/test_cpu_functionality.py" ]; then
        log "INFO" "运行CPU模式功能测试..."
        python3 -m pytest "${TEST_DIR}/cpu_mode/test_cpu_functionality.py" -v -s --tb=short >> "${TEST_LOG}" 2>&1
        if [ $? -eq 0 ]; then
            log "INFO" "CPU模式功能测试通过"
        else
            log "WARNING" "CPU模式功能测试部分失败"
        fi
    fi
    
    # 真实模型部署测试
    if [ -f "${TEST_DIR}/real_model/test_model_deployment.py" ]; then
        log "INFO" "运行真实模型部署测试..."
        python3 -m pytest "${TEST_DIR}/real_model/test_model_deployment.py" -v -s --tb=short >> "${TEST_LOG}" 2>&1
        if [ $? -eq 0 ]; then
            log "INFO" "真实模型部署测试通过"
        else
            log "WARNING" "真实模型部署测试部分失败"
        fi
    fi
    
    # 运行现有单元测试
    if [ -d "${TEST_DIR}/unit" ]; then
        log "INFO" "运行现有单元测试..."
        
        # 选择几个关键的测试文件
        key_tests=(
            "test_config_manager.py"
            "test_file_type_detector.py"
            "test_embedding_engine.py"
            "test_basic_imports_fast.py"
        )
        
        for test_file in "${key_tests[@]}"; do
            if [ -f "${TEST_DIR}/unit/${test_file}" ]; then
                log "INFO" "运行测试: ${test_file}"
                python3 -m pytest "${TEST_DIR}/unit/${test_file}" -v --tb=short >> "${TEST_LOG}" 2>&1
                if [ $? -eq 0 ]; then
                    log "INFO" "${test_file} 测试通过"
                else
                    log "WARNING" "${test_file} 测试失败"
                fi
            fi
        done
    fi
    
    log "INFO" "单元测试完成"
}

# 运行性能测试
run_performance_tests() {
    log "INFO" "==============================================="
    log "INFO" "运行性能测试"
    log "INFO" "==============================================="
    
    cd "${PROJECT_ROOT}"
    
    if [ -f "${TEST_DIR}/performance/test_cpu_performance.py" ]; then
        log "INFO" "运行CPU性能基准测试..."
        python3 -m pytest "${TEST_DIR}/performance/test_cpu_performance.py" -v -s --tb=short >> "${TEST_LOG}" 2>&1
        if [ $? -eq 0 ]; then
            log "INFO" "CPU性能基准测试通过"
        else
            log "WARNING" "CPU性能基准测试部分失败"
        fi
    fi
    
    log "INFO" "性能测试完成"
}

# 运行集成测试
run_integration_tests() {
    log "INFO" "==============================================="
    log "INFO" "运行集成测试"
    log "INFO" "==============================================="
    
    cd "${PROJECT_ROOT}"
    
    if [ -f "${TEST_DIR}/integration/test_end_to_end.py" ]; then
        log "INFO" "运行端到端集成测试..."
        python3 -m pytest "${TEST_DIR}/integration/test_end_to_end.py" -v -s --tb=short >> "${TEST_LOG}" 2>&1
        if [ $? -eq 0 ]; then
            log "INFO" "端到端集成测试通过"
        else
            log "WARNING" "端到端集成测试部分失败"
        fi
    fi
    
    log "INFO" "集成测试完成"
}

# 生成测试报告
generate_test_report() {
    log "INFO" "==============================================="
    log "INFO" "生成测试报告"
    log "INFO" "==============================================="
    
    REPORT_FILE="${LOGS_DIR}/test_report_$(date +%Y%m%d_%H%M%S).json"
    
    # 创建测试报告脚本
    cat > "${DEPLOY_TEST_DIR}/generate_report.py" << 'EOF'
import json
import os
import sys
from datetime import datetime
from pathlib import Path

def analyze_test_logs(log_file):
    """分析测试日志"""
    if not os.path.exists(log_file):
        return {"error": "日志文件不存在"}
    
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 统计测试结果
    passed_count = content.count("测试通过")
    failed_count = content.count("测试失败")
    warning_count = content.count("WARNING")
    error_count = content.count("ERROR")
    
    return {
        "passed_tests": passed_count,
        "failed_tests": failed_count,
        "warnings": warning_count,
        "errors": error_count,
        "total_lines": len(content.split('\n'))
    }

def generate_report(log_file, output_file):
    """生成测试报告"""
    log_analysis = analyze_test_logs(log_file)
    
    report = {
        "test_run_info": {
            "timestamp": datetime.now().isoformat(),
            "log_file": log_file,
            "report_file": output_file
        },
        "test_results": log_analysis,
        "summary": {
            "total_tests": log_analysis.get("passed_tests", 0) + log_analysis.get("failed_tests", 0),
            "success_rate": 0
        }
    }
    
    # 计算成功率
    total_tests = report["summary"]["total_tests"]
    if total_tests > 0:
        report["summary"]["success_rate"] = log_analysis.get("passed_tests", 0) / total_tests
    
    # 保存报告
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"测试报告已生成: {output_file}")
    print(f"测试总数: {total_tests}")
    print(f"通过: {log_analysis.get('passed_tests', 0)}")
    print(f"失败: {log_analysis.get('failed_tests', 0)}")
    print(f"成功率: {report['summary']['success_rate']:.2%}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python generate_report.py <log_file> <output_file>")
        sys.exit(1)
    
    log_file = sys.argv[1]
    output_file = sys.argv[2]
    generate_report(log_file, output_file)
EOF
    
    # 生成报告
    python3 "${DEPLOY_TEST_DIR}/generate_report.py" "${TEST_LOG}" "${REPORT_FILE}"
    
    log "INFO" "测试报告已生成: ${REPORT_FILE}"
}

# 清理测试环境
cleanup_test_environment() {
    log "INFO" "清理测试环境..."
    
    # 清理临时文件
    if [ -f "${DEPLOY_TEST_DIR}/generate_report.py" ]; then
        rm -f "${DEPLOY_TEST_DIR}/generate_report.py"
    fi
    
    log "INFO" "测试环境清理完成"
}

# 主函数
main() {
    log "INFO" "=================================================="
    log "INFO" "MSearch 优化测试套件"
    log "INFO" "=================================================="
    
    # 解析命令行参数
    case "${1:-all}" in
        "setup-only")
            log "INFO" "仅设置环境..."
            check_python_environment
            setup_test_environment
            ;;
        "unit")
            log "INFO" "仅运行单元测试..."
            check_python_environment
            setup_test_environment
            run_unit_tests
            generate_test_report
            ;;
        "performance")
            log "INFO" "仅运行性能测试..."
            check_python_environment
            setup_test_environment
            run_performance_tests
            generate_test_report
            ;;
        "integration")
            log "INFO" "仅运行集成测试..."
            check_python_environment
            setup_test_environment
            run_integration_tests
            generate_test_report
            ;;
        "all"|*)
            log "INFO" "运行完整测试套件..."
            check_python_environment
            setup_test_environment
            run_unit_tests
            run_performance_tests
            run_integration_tests
            generate_test_report
            cleanup_test_environment
            ;;
    esac
    
    log "INFO" "=================================================="
    log "INFO" "测试完成！"
    log "INFO" "=================================================="
    log "INFO" "测试日志: ${TEST_LOG}"
    log "INFO" "性能日志: ${PERFORMANCE_LOG}"
    log "INFO" "错误日志: ${ERROR_LOG}"
    log "INFO" "=================================================="
}

# 执行主函数
main "$@"