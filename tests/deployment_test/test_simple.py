#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试脚本
"""

import sys
import os
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

print(f"项目根目录: {PROJECT_ROOT}")

# 测试基本导入
try:
    from src.core.config import load_config
    print("✓ config模块导入成功")
except Exception as e:
    print(f"✗ config模块导入失败: {e}")

print("测试完成")