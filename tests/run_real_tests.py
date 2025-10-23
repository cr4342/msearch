#!/usr/bin/env python3
"""
运行真实模型和真实数据测试
按照@docs/test_strategy.md要求进行测试
"""
import sys
import os
import argparse
import subprocess
from pathlib import Path

def run_real_model_tests():
    """运行真实模型测试"""
    print("=== 运行真实模型测试 ===")
    
    # 确保测试数据目录存在
    test_data_dir = Path("data/models")
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    # 运行真实模型测试
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/real_model/test_real_model.py",
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"运行真实模型测试时出错: {e}")
        return False

def run_real_data_tests():
    """运行真实数据测试"""
    print("\n=== 运行真实数据测试 ===")
    
    # 确保测试数据目录存在
    test_data_dir = Path("tests/test_data")
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    # 运行真实数据测试
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/real_data/test_real_data.py",
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"运行真实数据测试时出错: {e}")
        return False

def run_all_real_tests():
    """运行所有真实测试"""
    print("开始运行所有真实模型和真实数据测试...")
    
    # 创建必要的目录
    dirs_to_create = ["data/models", "tests/test_data"]
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # 运行测试
    model_tests_passed = run_real_model_tests()
    data_tests_passed = run_real_data_tests()
    
    # 输出汇总结果
    print("\n=== 测试结果汇总 ===")
    print(f"真实模型测试: {'通过' if model_tests_passed else '失败'}")
    print(f"真实数据测试: {'通过' if data_tests_passed else '失败'}")
    
    all_passed = model_tests_passed and data_tests_passed
    print(f"总体结果: {'全部通过' if all_passed else '部分失败'}")
    
    return all_passed

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行真实模型和真实数据测试")
    parser.add_argument(
        "--model-only",
        action="store_true",
        help="只运行真实模型测试"
    )
    parser.add_argument(
        "--data-only",
        action="store_true",
        help="只运行真实数据测试"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="运行所有真实测试（默认）"
    )
    
    args = parser.parse_args()
    
    # 确保在项目根目录运行
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # 运行相应的测试
    if args.model_only:
        success = run_real_model_tests()
    elif args.data_only:
        success = run_real_data_tests()
    else:
        success = run_all_real_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())