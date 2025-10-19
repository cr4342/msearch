#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境测试脚本
"""

import sys
import os

print("Python环境测试")
print(f"Python版本: {sys.version}")
print(f"Python路径: {sys.executable}")
print(f"当前工作目录: {os.getcwd()}")

# 测试基本导入
try:
    import pathlib
    print("✓ pathlib导入成功")
except Exception as e:
    print(f"✗ pathlib导入失败: {e}")

try:
    import sys
    print("✓ sys导入成功")
except Exception as e:
    print(f"✗ sys导入失败: {e}")

print("环境测试完成")