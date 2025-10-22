#!/usr/bin/env python3
"""
简化版时间定位引擎测试
用于调试测试环境问题
"""

import sys
import os
import pytest
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 检查是否能导入模块
try:
    from src.business.temporal_localization_engine import (
        TemporalLocalizationEngine,
        TimestampMatch,
        FusedTimestamp
    )
    print("成功导入模块")
except Exception as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)


def test_simple():
    """简单测试函数"""
    assert True


if __name__ == "__main__":
    # 简单测试
    try:
        test_simple()
        print("简单测试通过")
    except Exception as e:
        print(f"简单测试失败: {e}")
        sys.exit(1)
        
    print("所有测试准备完成")