#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单导入测试脚本
"""

import sys
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

print(f"项目根目录: {PROJECT_ROOT}")
print(f"Python路径: {sys.path[:5]}")

# 测试基本导入
try:
    from src.core.config import load_config
    print("✓ config模块导入成功")
except Exception as e:
    print(f"✗ config模块导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    import torch
    print(f"✓ PyTorch版本: {torch.__version__}")
except Exception as e:
    print(f"✗ PyTorch导入失败: {e}")

try:
    import transformers
    print(f"✓ Transformers版本: {transformers.__version__}")
except Exception as e:
    print(f"✗ Transformers导入失败: {e}")

print("导入测试完成")