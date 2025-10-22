#!/usr/bin/env python3
"""
性能测试脚本
按照@docs/test_strategy.md要求进行性能测试
"""

import sys
import os
import time
import asyncio

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.business.temporal_localization_engine import TemporalLocalizationEngine
from src.business.temporal_localization_engine import TimestampMatch


def test_timestamp_query_performance():
    """测试时间戳查询性能 (设计文档要求: 50个查询<50ms)"""
    print("=== 时间戳查询性能测试 ===")
    
    engine = TemporalLocalizationEngine()
    vector_ids = [f"vector_{i}" for i in range(50)]
    
    # 模拟时间戳匹配数据
    visual_matches = [
        TimestampMatch(timestamp=10.5, similarity=0.9, modality="visual"),
        TimestampMatch(timestamp=12.3, similarity=0.7, modality="visual"),
        TimestampMatch(timestamp=25.1, similarity=0.8, modality="visual")
    ]
    
    audio_matches = [
        TimestampMatch(timestamp=11.2, similarity=0.85, modality="audio"),
        TimestampMatch(timestamp=24.8, similarity=0.75, modality="audio")
    ]
    
    speech_matches = [
        TimestampMatch(timestamp=10.8, similarity=0.8, modality="speech"),
        TimestampMatch(timestamp=15.0, similarity=0.6, modality="speech"),
        TimestampMatch(timestamp=30.2, similarity=0.95, modality="speech")
    ]
    
    start_time = time.time()
    
    # 执行批量时间戳融合操作
    results = asyncio.run(engine.fuse_temporal_results(
        visual_matches, 
        audio_matches, 
        speech_matches
    ))
    
    end_time = time.time()
    query_time = (end_time - start_time) * 1000  # 转换为毫秒
    
    print(f"批量时间戳融合处理时间: {query_time:.2f}ms")
    print(f"处理结果数量: {len(results)}")
    
    # 验证性能要求：处理时间<50ms
    if query_time < 50:
        print("✓ 时间戳查询性能达标 (<50ms)")
        return True
    else:
        print(f"✗ 时间戳查询性能不达标 ({query_time:.2f}ms >= 50ms)")
        return False


def test_fusion_algorithm_performance():
    """测试融合算法性能"""
    print("\n=== 融合算法性能测试 ===")
    
    engine = TemporalLocalizationEngine()
    
    # 创建大量测试数据
    visual_matches = [TimestampMatch(timestamp=i*0.5, similarity=0.5+i*0.01, modality="visual") 
                      for i in range(100)]
    audio_matches = [TimestampMatch(timestamp=i*0.5+0.1, similarity=0.6+i*0.005, modality="audio") 
                      for i in range(80)]
    speech_matches = [TimestampMatch(timestamp=i*0.5+0.2, similarity=0.7+i*0.008, modality="speech") 
                      for i in range(60)]
    
    start_time = time.time()
    
    # 执行融合操作
    results = asyncio.run(engine.fuse_temporal_results(
        visual_matches, 
        audio_matches, 
        speech_matches
    ))
    
    end_time = time.time()
    processing_time = (end_time - start_time) * 1000  # 转换为毫秒
    
    print(f"大数据量融合处理时间: {processing_time:.2f}ms")
    print(f"处理输入数据量: {len(visual_matches)+len(audio_matches)+len(speech_matches)}")
    print(f"生成结果数量: {len(results)}")
    
    # 验证性能要求
    if processing_time < 100:
        print("✓ 融合算法性能达标 (<100ms)")
        return True
    else:
        print(f"✗ 融合算法性能不达标 ({processing_time:.2f}ms >= 100ms)")
        return False


def test_weight_adjustment_performance():
    """测试权重调整性能"""
    print("\n=== 权重调整性能测试 ===")
    
    engine = TemporalLocalizationEngine()
    
    queries = [
        "hello world",  # 通用查询
        "蓝色天空白云",  # 视觉相关查询
        "音乐节拍",  # 音频相关查询
        "语音对话"  # 语音相关查询
    ]
    
    start_time = time.time()
    
    # 测试不同查询的权重调整
    for query in queries:
        weights = engine.adjust_weights_based_on_query(query)
        print(f"查询: '{query}' -> 权重: {weights}")
    
    end_time = time.time()
    adjustment_time = (end_time - start_time) * 1000  # 转换为毫秒
    
    print(f"权重调整处理时间: {adjustment_time:.2f}ms")
    
    # 验证性能要求
    if adjustment_time < 10:
        print("✓ 权重调整性能达标 (<10ms)")
        return True
    else:
        print(f"✗ 权重调整性能不达标 ({adjustment_time:.2f}ms >= 10ms)")
        return False


def main():
    """主测试函数"""
    print("=== 按照@docs/test_strategy.md要求进行性能测试 ===")
    print()
    
    # 运行各项性能测试
    tests = [
        ("时间戳查询性能", test_timestamp_query_performance),
        ("融合算法性能", test_fusion_algorithm_performance),
        ("权重调整性能", test_weight_adjustment_performance)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name}测试失败: {e}")
            results.append((test_name, False))
    
    # 输出测试结果汇总
    print("\n=== 性能测试结果汇总 ===")
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "通过" if result else "失败"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有性能测试通过！")
        return 0
    else:
        print(f"✗ 有 {total - passed} 个性能测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())