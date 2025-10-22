#!/usr/bin/env python3
"""
全面性能测试脚本
按照@docs/test_strategy.md要求进行完整的性能测试
"""

import sys
import os
import time
import asyncio
import psutil

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.business.temporal_localization_engine import TemporalLocalizationEngine
from src.business.temporal_localization_engine import TimestampMatch
from src.processors.timestamp_processor import TimestampProcessor


def test_timestamp_query_performance():
    """测试时间戳查询性能 (设计文档要求: 50个查询<50ms)"""
    print("=== 时间戳查询性能测试 ===")
    
    engine = TemporalLocalizationEngine()
    
    # 创建测试数据
    visual_matches = [TimestampMatch(timestamp=i*0.5, similarity=0.5+i*0.01, modality="visual") 
                      for i in range(20)]
    audio_matches = [TimestampMatch(timestamp=i*0.5+0.1, similarity=0.6+i*0.005, modality="audio") 
                      for i in range(15)]
    speech_matches = [TimestampMatch(timestamp=i*0.5+0.2, similarity=0.7+i*0.008, modality="speech") 
                      for i in range(10)]
    
    # 多次测试取平均值
    total_time = 0
    iterations = 10
    
    for i in range(iterations):
        start_time = time.time()
        
        # 执行融合操作
        results = asyncio.run(engine.fuse_temporal_results(
            visual_matches, 
            audio_matches, 
            speech_matches
        ))
        
        end_time = time.time()
        total_time += (end_time - start_time) * 1000  # 转换为毫秒
    
    avg_time = total_time / iterations
    
    print(f"平均处理时间: {avg_time:.2f}ms")
    print(f"处理结果数量: {len(results)}")
    
    # 验证性能要求：平均时间<50ms
    if avg_time < 50:
        print("✓ 时间戳查询性能达标 (<50ms)")
        return True
    else:
        print(f"✗ 时间戳查询性能不达标 ({avg_time:.2f}ms >= 50ms)")
        return False


def test_single_query_performance():
    """测试单次查询性能 (设计文档要求: <10ms)"""
    print("\n=== 单次查询性能测试 ===")
    
    processor = TimestampProcessor()
    
    start_time = time.time()
    
    # 执行帧级时间戳计算
    for i in range(100):
        timestamp = processor.calculate_frame_timestamp(i, 30.0)
    
    end_time = time.time()
    query_time = (end_time - start_time) * 1000  # 转换为毫秒
    
    print(f"100次帧级时间戳计算时间: {query_time:.2f}ms")
    print(f"单次计算平均时间: {query_time/100:.4f}ms")
    
    # 验证性能要求：单次计算<1ms
    if query_time/100 < 1:
        print("✓ 单次查询性能达标 (<1ms)")
        return True
    else:
        print(f"✗ 单次查询性能不达标 ({query_time/100:.4f}ms >= 1ms)")
        return False


def test_multimodal_sync_performance():
    """测试多模态同步性能 (设计文档要求: <5ms)"""
    print("\n=== 多模态同步性能测试 ===")
    
    processor = TimestampProcessor()
    
    start_time = time.time()
    
    # 执行多模态同步验证
    for i in range(50):
        is_synced = processor.validate_multimodal_sync(
            10.0, 10.05, 'audio_music'
        )
    
    end_time = time.time()
    sync_time = (end_time - start_time) * 1000  # 转换为毫秒
    
    print(f"50次同步验证时间: {sync_time:.2f}ms")
    print(f"单次验证平均时间: {sync_time/50:.4f}ms")
    
    # 验证性能要求：单次验证<5ms
    if sync_time/50 < 5:
        print("✓ 多模态同步性能达标 (<5ms)")
        return True
    else:
        print(f"✗ 多模态同步性能不达标 ({sync_time/50:.4f}ms >= 5ms)")
        return False


def test_memory_usage():
    """测试内存使用情况"""
    print("\n=== 内存使用测试 ===")
    
    # 获取初始内存使用
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # 创建大量对象
    engine = TemporalLocalizationEngine()
    matches = []
    for i in range(1000):
        match = TimestampMatch(timestamp=i*0.1, similarity=0.5, modality="visual")
        matches.append(match)
    
    # 执行操作
    results = asyncio.run(engine.fuse_temporal_results(matches, [], []))
    
    # 获取最终内存使用
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    print(f"初始内存使用: {initial_memory:.2f} MB")
    print(f"最终内存使用: {final_memory:.2f} MB")
    print(f"内存增加: {memory_increase:.2f} MB")
    
    # 验证内存使用要求
    if memory_increase < 50:
        print("✓ 内存使用合理 (<50MB)")
        return True
    else:
        print(f"✗ 内存使用过高 ({memory_increase:.2f}MB >= 50MB)")
        return False


def test_concurrent_performance():
    """测试并发性能"""
    print("\n=== 并发性能测试 ===")
    
    async def concurrent_task(task_id):
        engine = TemporalLocalizationEngine()
        matches = [TimestampMatch(timestamp=i*0.1+task_id, similarity=0.5, modality="visual") 
                  for i in range(10)]
        return await engine.fuse_temporal_results(matches, [], [])
    
    start_time = time.time()
    
    # 创建并发任务
    async def run_concurrent_tasks():
        tasks = [concurrent_task(i) for i in range(10)]
        return await asyncio.gather(*tasks)
    
    results = asyncio.run(run_concurrent_tasks())
    
    end_time = time.time()
    concurrent_time = (end_time - start_time) * 1000  # 转换为毫秒
    
    print(f"10个并发任务处理时间: {concurrent_time:.2f}ms")
    print(f"平均每个任务处理时间: {concurrent_time/10:.2f}ms")
    
    # 验证并发性能
    if concurrent_time < 100:
        print("✓ 并发性能达标 (<100ms)")
        return True
    else:
        print(f"✗ 并发性能不达标 ({concurrent_time:.2f}ms >= 100ms)")
        return False


def main():
    """主测试函数"""
    print("=== 全面性能测试 ===")
    print("按照@docs/test_strategy.md要求进行性能测试")
    print()
    
    # 运行各项性能测试
    tests = [
        ("时间戳查询性能", test_timestamp_query_performance),
        ("单次查询性能", test_single_query_performance),
        ("多模态同步性能", test_multimodal_sync_performance),
        ("内存使用", test_memory_usage),
        ("并发性能", test_concurrent_performance)
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