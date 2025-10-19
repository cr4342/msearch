#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MSearch 依赖修复脚本
解决版本兼容性问题
"""

import subprocess
import sys
import os

def run_command(cmd):
    """运行命令"""
    print(f"执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(f"输出: {result.stdout}")
    if result.stderr:
        print(f"错误: {result.stderr}")
    return result.returncode == 0

def fix_numpy_compatibility():
    """修复NumPy兼容性问题"""
    print("=== 修复NumPy兼容性问题 ===")
    
    # 降级NumPy到1.x版本
    return run_command(f"{sys.executable} -m pip install 'numpy<2.0' -i https://pypi.tuna.tsinghua.edu.cn/simple")

def upgrade_pytorch():
    """升级PyTorch"""
    print("=== 升级PyTorch ===")
    
    # 升级PyTorch到2.1.0版本
    return run_command(f"{sys.executable} -m pip install torch==2.1.0 torchvision -i https://pypi.tuna.tsinghua.edu.cn/simple")

def fix_transformers():
    """修复transformers库"""
    print("=== 修复transformers库 ===")
    
    # 重新安装transformers
    return run_command(f"{sys.executable} -m pip install --upgrade transformers -i https://pypi.tuna.tsinghua.edu.cn/simple")

def install_missing_packages():
    """安装缺失的包"""
    print("=== 安装缺失的包 ===")
    
    packages = [
        "infinity_emb",
        "transformers[torch]",
        "sentence_transformers",
        "pillow",
        "opencv-python"
    ]
    
    for package in packages:
        print(f"安装 {package}...")
        if not run_command(f"{sys.executable} -m pip install {package} -i https://pypi.tuna.tsinghua.edu.cn/simple"):
            print(f"警告: {package} 安装失败")

def main():
    """主函数"""
    print("开始修复MSearch依赖问题...")
    
    # 1. 修复NumPy兼容性
    if not fix_numpy_compatibility():
        print("NumPy修复失败")
        return 1
    
    # 2. 升级PyTorch
    if not upgrade_pytorch():
        print("PyTorch升级失败")
        return 1
    
    # 3. 修复transformers
    if not fix_transformers():
        print("transformers修复失败")
        return 1
    
    # 4. 安装缺失的包
    install_missing_packages()
    
    print("依赖修复完成！")
    return 0

if __name__ == "__main__":
    sys.exit(main())