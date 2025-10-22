#!/usr/bin/env python3
"""
手动测试时间定位引擎
用于调试具体问题
"""

import sys
import os
import asyncio

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
    import traceback
    traceback.print_exc()
    sys.exit(1)


async def test_fuse_temporal_results():
    """测试fuse_temporal_results方法"""
    try:
        engine = TemporalLocalizationEngine()
        print("成功创建时间定位引擎实例")
        
        # 测试所有参数为None的情况
        result = await engine.fuse_temporal_results(None, None, None)
        print(f"None输入测试通过，结果: {result}")
        
        # 测试所有参数为空列表的情况
        result = await engine.fuse_temporal_results([], [], [])
        print(f"空列表输入测试通过，结果: {result}")
        
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行异步测试
    try:
        result = asyncio.run(test_fuse_temporal_results())
        if result:
            print("所有手动测试通过")
        else:
            print("手动测试失败")
            sys.exit(1)
    except Exception as e:
        print(f"运行测试时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)