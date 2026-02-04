#!/usr/bin/env python3
"""
测试任务管理系统的基本功能
"""

import asyncio
import tempfile
import os
from datetime import datetime
from src.core.task.central_task_manager import CentralTaskManager
from src.core.task.task_scheduler import TaskScheduler
from src.core.task.task_executor import OptimizedTaskExecutor
from src.core.task.task_monitor import OptimizedTaskMonitor
from src.core.task.task_group_manager import TaskGroupManager
from src.core.task.task import Task


def test_priority_calculator():
    """测试优先级计算器"""
    print("Testing PriorityCalculator...")
    from src.core.task.priority_calculator import PriorityCalculator
    
    calculator = PriorityCalculator()
    
    # 创建一个测试任务
    task = Task(
        id="test_task",
        task_type="file_embed_image",
        task_data={"file_path": "/test/image.jpg"},
        file_id="test_file",
        file_path="/test/image.jpg"
    )
    
    # 测试优先级计算
    priority = calculator.calculate_priority(task)
    print(f"Priority for image task: {priority}")
    
    # 测试另一个任务类型
    task.task_type = "file_embed_video"
    priority = calculator.calculate_priority(task)
    print(f"Priority for video task: {priority}")
    
    # 测试音频任务
    task.task_type = "file_embed_audio"
    priority = calculator.calculate_priority(task)
    print(f"Priority for audio task: {priority}")
    
    print("PriorityCalculator test completed successfully!")


def test_task_group_manager():
    """测试任务组管理器"""
    print("Testing TaskGroupManager...")
    config = {"test": True}
    manager = TaskGroupManager(config)
    
    # 测试创建任务组
    group = asyncio.run(manager.create_group("test_file", "/test/file.mp4"))
    print(f"Created group: {group.file_id}, path: {group.file_path}")
    
    # 创建一个测试任务
    task = Task(
        id="test_task",
        task_type="file_embed_video",
        task_data={"file_path": "/test/file.mp4"},
        file_id="test_file",
        file_path="/test/file.mp4"
    )
    
    # 添加任务到组
    asyncio.run(manager.add_task_to_group("test_file", task))
    print("Task added to group successfully")
    
    # 获取组信息
    group_info = asyncio.run(manager.get_group("test_file"))
    print(f"Group has {len(group_info.get_all_tasks())} tasks")
    
    print("TaskGroupManager test completed successfully!")


def test_task_scheduler():
    """测试任务调度器"""
    print("Testing TaskScheduler...")
    config = {
        "wait_time_compensation": True,
        "wait_time_compensation_interval": 60,
        "wait_time_compensation_max": 999,
        "dynamic_priority": True,
        "priority_boost_threshold": 300
    }
    scheduler = TaskScheduler(config)
    
    # 启动调度器
    asyncio.run(scheduler.start())
    
    # 创建一个测试任务
    task = Task(
        id="test_task",
        task_type="file_embed_image",
        task_data={"file_path": "/test/image.jpg"},
        file_id="test_file",
        file_path="/test/image.jpg"
    )
    
    # 计算优先级
    priority = scheduler.calculate_priority(task)
    print(f"Task priority calculated: {priority}")
    
    # 添加任务到队列
    success = asyncio.run(scheduler.enqueue_task(task))
    print(f"Task enqueued: {success}")
    
    # 检查队列大小
    queue_size = asyncio.run(scheduler.get_queue_size())
    print(f"Queue size: {queue_size}")
    
    # 停止调度器
    asyncio.run(scheduler.stop())
    
    print("TaskScheduler test completed successfully!")


def test_simple_integration():
    """简单集成测试"""
    print("Testing simple integration...")
    
    # 配置
    config = {
        "task_manager": {
            "max_workers": 4
        },
        "thread_pools": {
            "task": {"max_workers": 4}
        }
    }
    
    # 创建各组件
    task_scheduler = TaskScheduler({
        "wait_time_compensation": True,
        "wait_time_compensation_interval": 60,
        "wait_time_compensation_max": 999,
        "dynamic_priority": True,
        "priority_boost_threshold": 300
    })
    task_executor = OptimizedTaskExecutor()  # 使用优化的任务执行器
    task_monitor = OptimizedTaskMonitor()  # 使用优化的任务监控器
    task_group_manager = TaskGroupManager(config)
    
    # 启动调度器
    asyncio.run(task_scheduler.start())
    
    # 创建中央任务管理器
    central_manager = CentralTaskManager(
        config=config,
        task_scheduler=task_scheduler,
        task_executor=task_executor,
        task_monitor=task_monitor,
        task_group_manager=task_group_manager,
        device="cpu"
    )
    
    # 创建测试任务
    task_id = central_manager.create_task(
        task_type="file_embed_image",
        task_data={"file_path": "/test/image.jpg"},
        file_id="test_file_1",
        file_path="/test/image.jpg"
    )
    
    print(f"Created task with ID: {task_id}")
    
    # 获取任务状态
    status = central_manager.get_task_status(task_id)
    print(f"Task status: {status}")
    
    # 获取所有任务
    all_tasks = central_manager.get_all_tasks()
    print(f"Total tasks: {len(all_tasks)}")
    
    # 获取统计信息
    stats = central_manager.get_statistics()
    print(f"Statistics: {stats}")
    
    # 获取线程池状态
    pool_status = central_manager.get_thread_pool_status()
    print(f"Thread pool status: {pool_status}")
    
    # 测试获取队列大小（需要异步）
    print("Simple integration test completed successfully!")
    
    print("Simple integration test completed successfully!")


def main():
    print("Starting task system tests...")
    
    test_priority_calculator()
    print()
    
    test_task_group_manager()
    print()
    
    test_task_scheduler()
    print()
    
    test_simple_integration()
    print()
    
    print("All tests completed successfully!")


if __name__ == "__main__":
    main()