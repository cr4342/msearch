#!/usr/bin/env python3
"""
测试运行脚本
运行集成测试并报告结果
"""

import sys
import os
import subprocess
from pathlib import Path

def run_test_script(script_path, description):
    """运行单个测试脚本"""
    print(f"运行 {description}...")
    try:
        # 设置环境变量以正确处理编码
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run([
            sys.executable, 
            str(script_path)
        ], cwd=str(script_path.parent.parent.parent), 
           capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        print(f"返回码: {result.returncode}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"运行 {description} 时出错: {e}")
        return False

def run_integration_tests():
    """运行集成测试"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests" / "integration"
    
    print("开始运行集成测试...")
    print("=" * 50)
    
    # 运行基本集成测试
    print("1. 运行基本集成测试...")
    success1 = run_test_script(tests_dir / "test_basic_integration.py", "基本集成测试")
    
    print("\n" + "=" * 50)
    
    # 运行时间戳精度测试
    print("2. 运行时间戳精度测试...")
    success2 = run_test_script(tests_dir / "test_timestamp_accuracy.py", "时间戳精度测试")
    
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print(f"基本集成测试: {'通过' if success1 else '失败'}")
    print(f"时间戳精度测试: {'通过' if success2 else '失败'}")
    
    if success1 and success2:
        print("✓ 所有集成测试通过!")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(run_integration_tests())
