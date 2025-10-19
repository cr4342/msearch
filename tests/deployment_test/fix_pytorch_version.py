#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyTorch版本修复脚本
将PyTorch版本降级到2.0.1以解决兼容性问题
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

def fix_pytorch_version():
    """修复PyTorch版本"""
    print("=== 修复PyTorch版本 ===")
    
    # 降级PyTorch到2.0.1版本（稳定版本，兼容性最佳）
    cmd = f"{sys.executable} -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 -i https://pypi.tuna.tsinghua.edu.cn/simple"
    return run_command(cmd)

def fix_transformers():
    """修复transformers库"""
    print("=== 修复transformers库 ===")
    
    # 安装兼容版本的transformers
    cmd = f"{sys.executable} -m pip install transformers==4.35.0 -i https://pypi.tuna.tsinghua.edu.cn/simple"
    return run_command(cmd)

def main():
    """主函数"""
    print("开始修复PyTorch和transformers版本问题...")
    
    # 1. 修复PyTorch版本
    if not fix_pytorch_version():
        print("PyTorch版本修复失败")
        return 1
    
    # 2. 修复transformers
    if not fix_transformers():
        print("transformers修复失败")
        return 1
    
    print("版本修复完成！请重新运行测试。")
    return 0

if __name__ == "__main__":
    sys.exit(main())