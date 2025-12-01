"""
错误处理系统演示脚本
展示错误分类、重试机制、优雅降级等功能
"""

import asyncio
import time
import logging
import sys
from pathlib import Path
from typing import Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config_manager import get_config_manager
from src.core.logging_config import setup_logging
from src.utils.error_handling import (
    ErrorHandler, ErrorCategory, ErrorSeverity, RetryStrategy, RetryConfig,
    error_handler, get_error_handler, TemporaryError, DatabaseError
)


class MockComponent:
    """模拟组件用于测试"""
    
    def __init__(self, name: str):
        self.name = name
        self.failure_rate = 0.5  # 50%失败率
        self.response_delay = 0.1
    
    @error_handler(context={"component": "mock_component"})
    async def unreliable_operation(self, data: Any) -> Any:
        """不可靠的操作"""
        await asyncio.sleep(self.response_delay)
        
        if time.time() % 2 < self.failure_rate:  # 模拟随机失败
            raise TemporaryError(f"组件 {self.name} 临时故障")
        
        return f"处理结果: {data}"
    
    def network_operation(self, data: Any) -> Any:
        """网络操作"""
        import random
        
        if random.random() < 0.3:  # 30%失败率
            raise ConnectionError("网络连接失败")
        
        return f"网络响应: {data}"
    
    def database_operation(self, data: Any) -> Any:
        """数据库操作"""
        import random
        
        if random.random() < 0.4:  # 40%失败率
            raise DatabaseError("数据库连接失败")
        
        return f"数据库结果: {data}"


async def demo_error_classification():
    """演示错误分类"""
    print("\n=== 错误分类演示 ===")
    
    # 创建错误处理器
    error_handler = ErrorHandler()
    
    # 测试各种错误类型
    test_errors = [
        (ConnectionError("网络错误"), "网络错误"),
        (MemoryError("内存不足"), "内存错误"),
        (FileNotFoundError("文件未找到"), "文件错误"),
        (DatabaseError("数据库错误"), "数据库错误"),
        (Exception("未知错误"), "未知错误")
    ]
    
    print("1. 测试错误分类:")
    for error, description in test_errors:
        error_info = error_handler.handle_error(error)
        print(f"   {description}:")
        print(f"     分类: {error_info.category.value}")
        print(f"     严重级别: {error_info.severity.value}")
        print(f"     错误ID: {error_info.error_id}")


async def demo_retry_mechanism():
    """演示重试机制"""
    print("\n=== 重试机制演示 ===")
    
    # 创建重试配置
    retry_config = RetryConfig(
        max_attempts=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=0.5,
        max_delay=5.0
    )
    
    # 创建重试管理器
    retry_manager = get_error_handler().retry_manager
    
    # 模拟成功操作
    print("1. 模拟成功操作:")
    async def successful_operation():
        await asyncio.sleep(0.1)
        return "操作成功"
    
    try:
        result = await retry_manager.execute_with_retry(successful_operation, retry_config=retry_config)
        print(f"   结果: {result}")
    except Exception as e:
        print(f"   失败: {e}")
    
    # 模拟失败操作
    print("2. 模拟失败操作:")
    async def failing_operation():
        await asyncio.sleep(0.1)
        raise TemporaryError("模拟的临时错误")
    
    try:
        result = await retry_manager.execute_with_retry(failing_operation, retry_config=retry_config)
        print(f"   结果: {result}")
    except Exception as e:
        print(f"   最终失败: {e}")
    
    # 显示重试统计
    stats = retry_manager.get_retry_stats()
    print(f"3. 重试统计:")
    print(f"   总重试次数: {stats['total_retries']}")
    print(f"   成功重试: {stats['successful_retries']}")
    print(f"   失败重试: {stats['failed_retries']}")
    print(f"   成功率高: {stats['success_rate']:.2%}")


async def demo_graceful_degradation():
    """演示优雅降级"""
    print("\n=== 优雅降级演示 ===")
    
    error_handler = get_error_handler()
    degradation_manager = error_handler.degradation_manager
    
    # 模拟组件状态变化
    print("1. 模拟组件状态变化:")
    
    # 健康状态
    degradation_manager.update_component_health("ai_model", "healthy")
    degradation_manager.update_component_health("database", "healthy")
    
    print(f"   AI模型状态: {degradation_manager.system_health['ai_model']}")
    print(f"   数据库状态: {degradation_manager.system_health['database']}")
    
    # 变为不健康
    degradation_manager.update_component_health("ai_model", "unhealthy", Exception("模型加载失败"))
    degradation_manager.update_component_health("database", "unhealthy", DatabaseError("连接失败"))
    
    print(f"   AI模型状态: {degradation_manager.system_health['ai_model']}")
    print(f"   数据库状态: {degradation_manager.system_health['database']}")
    
    # 显示降级统计
    stats = degradation_manager.get_degradation_stats()
    print(f"2. 降级统计:")
    print(f"   总降级次数: {stats['total_degradations']}")
    print(f"   成功降级: {stats['successful_degradations']}")
    print(f"   失败降级: {stats['failed_degradations']}")


async def demo_error_handling_decorator():
    """演示错误处理装饰器"""
    print("\n=== 错误处理装饰器演示 ===")
    
    # 创建模拟组件
    component = MockComponent("测试组件")
    
    print("1. 测试装饰器错误处理:")
    
    # 测试成功情况
    for i in range(3):
        try:
            result = await component.unreliable_operation(f"数据_{i}")
            print(f"   成功: {result}")
        except Exception as e:
            print(f"   失败: {e}")
    
    # 获取错误统计
    error_stats = get_error_handler().get_error_statistics()
    print(f"2. 错误统计:")
    for category, stats in error_stats['error_statistics'].items():
        print(f"   {category}: {stats['count']} 次错误")


async def demo_comprehensive_error_handling():
    """演示综合错误处理"""
    print("\n=== 综合错误处理演示 ===")
    
    error_handler = get_error_handler()
    
    # 创建多个组件进行测试
    components = [
        MockComponent("网络组件"),
        MockComponent("数据库组件"),
        MockComponent("AI组件")
    ]
    
    print("1. 并发执行多个组件:")
    
    # 并发执行操作
    tasks = []
    for component in components:
        for i in range(3):
            task = component.unreliable_operation(f"请求_{i}")
            tasks.append(task)
    
    # 等待所有任务完成
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = sum(1 for result in results if not isinstance(result, Exception))
    failure_count = len(results) - success_count
    
    print(f"   总任务数: {len(results)}")
    print(f"   成功: {success_count}")
    print(f"   失败: {failure_count}")
    print(f"   成功率: {success_count/len(results):.2%}")
    
    # 显示最终统计
    final_stats = error_handler.get_error_statistics()
    print(f"2. 最终统计:")
    
    # 系统健康状态
    print(f"   系统健康状态:")
    for component, health in final_stats['system_health'].items():
        print(f"     {component}: {health}")
    
    # 重试统计
    retry_stats = final_stats['retry_statistics']
    print(f"   重试统计:")
    print(f"     总重试: {retry_stats['total_retries']}")
    print(f"     成功重试: {retry_stats['successful_retries']}")
    
    # 降级统计
    degradation_stats = final_stats['degradation_statistics']
    print(f"   降级统计:")
    print(f"     总降级: {degradation_stats['total_degradations']}")


async def demo_retry_strategies():
    """演示不同重试策略"""
    print("\n=== 重试策略演示 ===")
    
    retry_manager = get_error_handler().retry_manager
    
    strategies = [
        (RetryStrategy.IMMEDIATE_RETRY, "立即重试"),
        (RetryStrategy.FIXED_INTERVAL, "固定间隔"),
        (RetryStrategy.LINEAR_BACKOFF, "线性退避"),
        (RetryStrategy.EXPONENTIAL_BACKOFF, "指数退避")
    ]
    
    for strategy, name in strategies:
        print(f"\n策略: {name}")
        
        config = RetryConfig(
            max_attempts=3,
            strategy=strategy,
            base_delay=1.0,
            max_delay=10.0
        )
        
        # 显示延迟序列
        print(f"   重试延迟序列:")
        for attempt in range(1, config.max_attempts + 1):
            delay = retry_manager.calculate_delay(attempt, config)
            print(f"     尝试 {attempt}: {delay:.2f}秒")


async def main():
    """主演示函数"""
    print("=" * 60)
    print("msearch 错误处理系统演示")
    print("=" * 60)
    
    try:
        # 设置日志
        setup_logging("INFO")
        
        # 运行各项演示
        await demo_error_classification()
        await demo_retry_mechanism()
        await demo_graceful_degradation()
        await demo_error_handling_decorator()
        await demo_comprehensive_error_handling()
        await demo_retry_strategies()
        
        print("\n" + "=" * 60)
        print("错误处理系统演示完成！")
        print("=" * 60)
        
        print("\n主要功能:")
        print("✓ 智能错误分类: 自动识别错误类型和严重级别")
        print("✓ 多种重试策略: 支持固定间隔、线性退避、指数退避等")
        print("✓ 优雅降级: 系统故障时自动切换到备用方案")
        print("✓ 装饰器支持: 简单的错误处理注解")
        print("✓ 统计监控: 完整的错误和重试统计")
        print("✓ 自定义错误: 支持特定错误类型的特殊处理")
        
    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")
        logging.error(f"错误处理演示失败: {e}")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())
