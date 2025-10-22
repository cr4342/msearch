#!/usr/bin/env python3
"""
测试无效匹配对象处理
"""

import sys
import os
import asyncio

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.business.temporal_localization_engine import (
    TemporalLocalizationEngine,
    TimestampMatch,
    FusedTimestamp
)


async def test_invalid_match_objects():
    """测试处理无效匹配对象"""
    engine = TemporalLocalizationEngine()
    
    # 测试包含无效匹配对象的情况
    invalid_matches = [{"invalid": "object"}]  # 不是TimestampMatch对象
    result = await engine.fuse_temporal_results(invalid_matches, [], [])
    print(f"无效匹配对象测试结果: {result}")
    print(f"结果类型: {type(result)}")
    print(f"结果长度: {len(result)}")
    
    return True


if __name__ == "__main__":
    # 运行异步测试
    try:
        result = asyncio.run(test_invalid_match_objects())
        if result:
            print("无效匹配对象测试通过")
        else:
            print("无效匹配对象测试失败")
            sys.exit(1)
    except Exception as e:
        print(f"运行测试时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)