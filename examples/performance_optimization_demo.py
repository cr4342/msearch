"""
性能优化演示脚本
展示各种优化技术的效果：缓存、批处理、性能监控等
"""

import asyncio
import time
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config_manager import get_config_manager
from src.core.logging_config import setup_logging
from src.core.cache_manager import CacheManager
from src.core.performance_monitor import PerformanceMonitor
from src.core.batch_processor import BatchProcessor
from src.common.embedding.embedding_engine_optimized import OptimizedEmbeddingEngine


async def demo_cache_performance():
    """演示缓存性能"""
    print("\n=== 缓存性能演示 ===")
    
    # 初始化配置和日志
    config_manager = get_config_manager()
    setup_logging("INFO")
    
    # 初始化缓存管理器
    cache_manager = CacheManager(config_manager)
    
    # 测试数据
    test_data = "这是一个测试文本数据" * 100
    test_key = "test_cache_key"
    
    print("1. 测试缓存写入...")
    start_time = time.time()
    cache_manager.memory_cache.set(test_key, test_data)
    write_time = time.time() - start_time
    print(f"   缓存写入耗时: {write_time:.4f}秒")
    
    print("2. 测试缓存读取（首次）...")
    start_time = time.time()
    cached_data = cache_manager.memory_cache.get(test_key)
    read_time_1 = time.time() - start_time
    print(f"   缓存读取耗时: {read_time_1:.4f}秒")
    print(f"   数据完整性: {'✓' if cached_data == test_data else '✗'}")
    
    print("3. 测试缓存读取（命中）...")
    start_time = time.time()
    cached_data_2 = cache_manager.memory_cache.get(test_key)
    read_time_2 = time.time() - start_time
    print(f"   缓存读取耗时: {read_time_2:.4f}秒")
    print(f"   缓存命中: {'✓' if read_time_2 < read_time_1 else '✗'}")
    
    # 获取缓存统计
    stats = cache_manager.get_cache_stats()
    print(f"4. 缓存统计:")
    print(f"   内存缓存 - 命中率: {stats['memory']['hit_rate']:.2%}")
    print(f"   总请求数: {stats['memory']['hits'] + stats['memory']['misses']}")


async def demo_performance_monitoring():
    """演示性能监控"""
    print("\n=== 性能监控演示 ===")
    
    # 初始化配置
    config_manager = get_config_manager()
    
    # 初始化性能监控器
    monitor = PerformanceMonitor(config_manager)
    
    print("1. 启动性能监控...")
    await monitor.start()
    
    # 模拟组件执行
    print("2. 模拟组件执行...")
    
    for i in range(10):
        # 模拟快速操作
        await asyncio.sleep(0.1)
        monitor.record_component_performance("demo_component", 0.1, True)
        
        # 模拟慢操作
        if i == 5:
            monitor.record_component_performance("demo_component", 2.0, False, "模拟错误")
    
    print("3. 获取性能统计...")
    await asyncio.sleep(2)  # 等待收集系统指标
    
    summary = monitor.get_performance_summary()
    print(f"   CPU使用率: {summary['system']['cpu_percent']:.1f}%")
    print(f"   内存使用率: {summary['system']['memory_percent']:.1f}%")
    print(f"   磁盘使用率: {summary['system']['disk_usage_percent']:.1f}%")
    
    component_metrics = summary.get('components', {})
    if 'demo_component' in component_metrics:
        demo_stats = component_metrics['demo_component']
        print(f"   组件执行次数: {demo_stats['execution_count']}")
        print(f"   成功率: {demo_stats['success_rate']:.2%}")
        print(f"   平均执行时间: {demo_stats['average_time']:.3f}秒")
    
    # 停止监控
    await monitor.stop()
    print("4. 性能监控已停止")


async def demo_batch_processing():
    """演示批处理性能"""
    print("\n=== 批处理性能演示 ===")
    
    # 初始化配置
    config_manager = get_config_manager()
    
    # 创建简单的批处理器
    async def simple_processing_task(data):
        """简单的处理任务"""
        await asyncio.sleep(0.1)  # 模拟处理时间
        return f"处理结果: {data}"
    
    # 初始化批处理器
    batch_processor = BatchProcessor(
        max_batch_size=5,
        batch_timeout=0.5,
        max_workers=2
    )
    
    print("1. 启动批处理器...")
    await batch_processor.start()
    
    # 提交多个任务
    print("2. 提交10个任务...")
    tasks = []
    for i in range(10):
        task_id = f"task_{i}"
        task = await batch_processor.submit_task(task_id, f"数据_{i}", simple_processing_task)
        tasks.append(task_id)
    
    # 收集结果
    print("3. 收集任务结果...")
    start_time = time.time()
    results = []
    for task_id in tasks:
        try:
            result = await batch_processor.get_result(task_id, timeout=5)
            results.append(result)
        except Exception as e:
            print(f"   任务 {task_id} 失败: {e}")
    
    total_time = time.time() - start_time
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   成功任务数: {len(results)}")
    print(f"   平均每任务: {total_time/len(results):.2f}秒")
    
    # 获取批处理统计
    stats = batch_processor.stats
    print(f"4. 批处理统计:")
    print(f"   总任务数: {stats['total_tasks']}")
    print(f"   完成任务数: {stats['completed_tasks']}")
    print(f"   失败任务数: {stats['failed_tasks']}")
    print(f"   处理批次: {stats['batches_processed']}")
    print(f"   平均批次大小: {stats['average_batch_size']:.1f}")
    
    # 停止批处理器
    await batch_processor.stop()
    print("5. 批处理器已停止")


async def demo_embedding_engine_optimization():
    """演示优化后的向量化引擎（模拟）"""
    print("\n=== 向量化引擎优化演示 ===")
    
    try:
        print("1. 初始化优化的向量化引擎...")
        # 由于需要真实的AI模型，这里只是演示接口
        engine = OptimizedEmbeddingEngine()
        
        print("2. 获取缓存统计...")
        cache_stats = engine.get_cache_stats()
        print(f"   向量缓存大小: {cache_stats['vector']['size']}")
        
        print("3. 获取性能统计...")
        perf_stats = engine.get_performance_stats()
        print(f"   组件数量: {len(perf_stats.get('component_details', {}))}")
        
        print("4. 获取批处理统计...")
        batch_stats = engine.get_batch_stats()
        print(f"   总任务数: {batch_stats.get('total_tasks', 0)}")
        
        print("5. 健康检查...")
        health = await engine.health_check()
        for model, status in health.items():
            print(f"   {model}: {'健康' if status else '异常'}")
        
        print("6. 关闭引擎...")
        await engine.shutdown()
        
    except Exception as e:
        print(f"   向量化引擎演示跳过 (需要AI模型): {e}")


async def demo_performance_comparison():
    """演示优化前后性能对比"""
    print("\n=== 性能对比演示 ===")
    
    # 模拟传统方式（无优化）
    print("1. 模拟传统方式（无优化）...")
    
    async def traditional_processing(data_list):
        results = []
        for data in data_list:
            await asyncio.sleep(0.1)  # 模拟处理时间
            results.append(f"结果_{data}")
        return results
    
    data_size = 20
    start_time = time.time()
    traditional_results = await traditional_processing(range(data_size))
    traditional_time = time.time() - start_time
    
    print(f"   处理 {data_size} 个数据项")
    print(f"   传统方式耗时: {traditional_time:.2f}秒")
    print(f"   平均每项耗时: {traditional_time/data_size:.3f}秒")
    
    # 模拟优化方式（有批处理）
    print("2. 模拟优化方式（有批处理）...")
    
    async def optimized_processing(data_list):
        # 模拟批处理（每批5个）
        batch_size = 5
        results = []
        
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i+batch_size]
            # 并行处理批次
            batch_tasks = [asyncio.create_task(process_item(data)) for data in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
        
        return results
    
    async def process_item(data):
        await asyncio.sleep(0.05)  # 优化后处理时间减半
        return f"结果_{data}"
    
    start_time = time.time()
    optimized_results = await optimized_processing(range(data_size))
    optimized_time = time.time() - start_time
    
    print(f"   处理 {data_size} 个数据项")
    print(f"   优化方式耗时: {optimized_time:.2f}秒")
    print(f"   平均每项耗时: {optimized_time/data_size:.3f}秒")
    
    # 性能对比
    improvement = (traditional_time - optimized_time) / traditional_time * 100
    speedup = traditional_time / optimized_time
    
    print(f"3. 性能对比结果:")
    print(f"   性能提升: {improvement:.1f}%")
    print(f"   加速比: {speedup:.2f}x")
    print(f"   时间节省: {traditional_time - optimized_time:.2f}秒")


async def main():
    """主演示函数"""
    print("=" * 60)
    print("msearch 性能优化演示")
    print("=" * 60)
    
    try:
        # 运行各项演示
        await demo_cache_performance()
        await demo_performance_monitoring()
        await demo_batch_processing()
        await demo_embedding_engine_optimization()
        await demo_performance_comparison()
        
        print("\n" + "=" * 60)
        print("性能优化演示完成！")
        print("=" * 60)
        
        print("\n主要优化效果:")
        print("✓ 缓存机制: 减少重复计算，提升响应速度")
        print("✓ 批处理优化: 提高吞吐量，降低平均处理时间")
        print("✓ 性能监控: 实时监控系统状态，及时发现问题")
        print("✓ 连接池优化: 提高数据库并发访问性能")
        print("✓ 查询优化: 索引优化和FTS全文搜索")
        print("✓ 内存管理: 智能缓存清理，避免内存泄漏")
        
    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")
        logging.error(f"性能优化演示失败: {e}")


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行演示
    asyncio.run(main())