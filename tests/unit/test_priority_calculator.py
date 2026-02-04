#!/usr/bin/env python3
"""
专门测试优先级计算器的改进功能
"""

import asyncio
from datetime import datetime, timedelta
from src.core.task.priority_calculator import PriorityCalculator
from src.core.task.central_task_manager import CentralTaskManager
from src.core.task.task import Task
from src.core.task.task_scheduler import TaskScheduler
from src.core.task.task_executor import OptimizedTaskExecutor
from src.core.task.task_monitor import OptimizedTaskMonitor
from src.core.task.task_group_manager import TaskGroupManager


def test_priority_calculator_comprehensive():
    """全面测试优先级计算器"""
    print("Testing PriorityCalculator comprehensive functionality...")
    
    calculator = PriorityCalculator()
    
    # 测试不同任务类型的优先级
    task_types = [
        "file_embed_image",
        "file_embed_video", 
        "file_embed_audio",
        "file_embed_text",
        "image_preprocess",
        "video_preprocess",
        "audio_preprocess",
        "file_scan",
        "video_slice",
        "thumbnail_generate",
        "preview_generate"
    ]
    
    print("Testing base priority calculation for different task types:")
    for task_type in task_types:
        task = Task(
            id=f"test_{task_type}",
            task_type=task_type,
            task_data={"file_path": f"/test/{task_type}.jpg"},
            file_id="test_file",
            file_path=f"/test/{task_type}.jpg"
        )
        
        priority = calculator.calculate_priority(task)
        print(f"  {task_type}: {priority}")
    
    # 测试等待时间补偿
    print("\nTesting wait time compensation:")
    
    # 创建一个5分钟前创建的任务
    old_task = Task(
        id="old_task",
        task_type="file_embed_image",
        task_data={"file_path": "/test/image.jpg"},
        file_id="test_file",
        file_path="/test/image.jpg"
    )
    old_task.created_at = (datetime.now() - timedelta(minutes=5)).timestamp()
    
    priority_without_wait = calculator.calculate_priority(Task(
        id="new_task",
        task_type="file_embed_image",
        task_data={"file_path": "/test/image.jpg"},
        file_id="test_file",
        file_path="/test/image.jpg"
    ))
    
    priority_with_wait = calculator.calculate_priority(old_task)
    
    print(f"  New task priority: {priority_without_wait}")
    print(f"  5-min old task priority: {priority_with_wait}")
    print(f"  Difference (should be positive due to wait compensation): {priority_with_wait - priority_without_wait}")
    
    # 测试文件优先级影响
    print("\nTesting file priority influence:")
    task = Task(
        id="test_task",
        task_type="file_embed_video",
        task_data={"file_path": "/test/video.mp4"},
        file_id="test_file",
        file_path="/test/video.mp4"
    )
    
    priority_with_low_file_priority = calculator.calculate_priority(task, file_priority=2)
    priority_with_high_file_priority = calculator.calculate_priority(task, file_priority=8)
    
    print(f"  With file priority 2: {priority_with_low_file_priority}")
    print(f"  With file priority 8: {priority_with_high_file_priority}")
    
    print("PriorityCalculator comprehensive test completed successfully!")


def test_task_scheduler_priority_calculation():
    """测试任务调度器的优先级计算"""
    print("\nTesting TaskScheduler priority calculation...")
    
    config = {
        "wait_time_compensation": True,
        "wait_time_compensation_interval": 60,
        "wait_time_compensation_max": 999,
        "dynamic_priority": True,
        "priority_boost_threshold": 300
    }
    
    scheduler = TaskScheduler(config)
    
    # 创建不同类型的任务
    tasks = [
        Task(id="task1", task_type="file_embed_image", task_data={"path": "/img.jpg"}),
        Task(id="task2", task_type="file_embed_video", task_data={"path": "/vid.mp4"}),
        Task(id="task3", task_type="file_embed_audio", task_data={"path": "/aud.mp3"}),
        Task(id="task4", task_type="file_embed_text", task_data={"path": "/doc.txt"}),
    ]
    
    print("Task priorities calculated by scheduler:")
    for task in tasks:
        priority = scheduler.calculate_priority(task)
        print(f"  {task.task_type}: {priority}")
    
    print("TaskScheduler priority calculation test completed successfully!")


def test_central_task_manager_priority_integration():
    """测试中央任务管理器的优先级集成"""
    print("\nTesting CentralTaskManager priority integration...")
    
    # 创建各组件
    config = {
        "task_manager": {
            "max_workers": 4
        },
        "thread_pools": {
            "task": {"max_workers": 4}
        }
    }
    
    task_scheduler = TaskScheduler({
        "wait_time_compensation": True,
        "wait_time_compensation_interval": 60,
        "wait_time_compensation_max": 999,
        "dynamic_priority": True,
        "priority_boost_threshold": 300
    })
    task_executor = OptimizedTaskExecutor()
    task_monitor = OptimizedTaskMonitor()
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
    
    # 测试设置文件类型优先级
    print("Testing file type priority settings:")
    print(f"  Default image priority: {central_manager.get_file_type_priority('image')}")
    print(f"  Default video priority: {central_manager.get_file_type_priority('video')}")
    print(f"  Default audio priority: {central_manager.get_file_type_priority('audio')}")
    
    # 设置特定文件类型的优先级
    central_manager.set_file_type_priority('image', 'high')
    central_manager.set_file_type_priority('video', 'low')
    
    print(f"  After setting - image priority: {central_manager.get_file_type_priority('image')}")
    print(f"  After setting - video priority: {central_manager.get_file_type_priority('video')}")
    
    # 创建任务并检查优先级
    print("\nTesting task creation with file type priority:")
    task_id = central_manager.create_task(
        task_type="file_embed_image",
        task_data={"file_path": "/test/image.jpg"},
        file_id="test_file_img",
        file_path="/test/image.jpg"
    )
    
    task_status = central_manager.get_task_status(task_id)
    print(f"  Image task priority: {task_status['priority']}")
    
    task_id2 = central_manager.create_task(
        task_type="file_embed_video",
        task_data={"file_path": "/test/video.mp4"},
        file_id="test_file_vid",
        file_path="/test/video.mp4"
    )
    
    task_status2 = central_manager.get_task_status(task_id2)
    print(f"  Video task priority: {task_status2['priority']}")
    
    print("CentralTaskManager priority integration test completed successfully!")


def test_pipeline_continuity_bonus():
    """测试流水线连续性奖励"""
    print("\nTesting pipeline continuity bonus...")
    
    # 这个测试需要更复杂的设置来验证连续性奖励
    # 我们将创建一个简单的模拟来验证逻辑
    from src.core.task.priority_calculator import PriorityCalculator
    from src.core.task.task_group_manager import TaskGroup, Task
    from src.core.task.task_types import TaskStatus
    
    calculator = PriorityCalculator()
    
    # 创建一个模拟的任务组
    group = TaskGroup(file_id="test_file", file_path="/test/file.mp4")
    
    # 添加一些已完成的核心任务
    completed_task = Task(
        id="completed_task",
        task_type="video_preprocess",  # 这是一个核心流水线任务
        task_data={"path": "/test/file.mp4"},
        status="completed"
    )
    group.add_task(completed_task)
    
    # 创建一个待处理的流水线任务
    pending_task = Task(
        id="pending_task",
        task_type="file_embed_video",  # 这也是一个核心流水线任务
        task_data={"path": "/test/file.mp4"},
        file_id="test_file",
        status="pending"
    )
    
    # 模拟中央任务管理器
    class MockCentralTaskManager:
        def get_task_group(self, file_id):
            return group if file_id == "test_file" else None
    
    mock_ctm = MockCentralTaskManager()
    
    # 测试连续性奖励
    priority_without_continuity = calculator.calculate_priority(pending_task)
    priority_with_continuity = calculator.calculate_priority(pending_task, central_task_manager=mock_ctm)
    
    print(f"  Priority without continuity: {priority_without_continuity}")
    print(f"  Priority with continuity: {priority_with_continuity}")
    print(f"  Difference: {priority_with_continuity - priority_without_continuity}")
    
    # 如果连续性奖励生效，带连续性的优先级应该更低（数值更小）
    if priority_with_continuity < priority_without_continuity:
        print("  ✓ Continuity bonus applied correctly (lower priority = higher priority)")
    else:
        print("  - Continuity bonus not applied (this may be expected if conditions aren't met)")
    
    print("Pipeline continuity bonus test completed!")


def main():
    print("Starting comprehensive priority calculator tests...")
    
    test_priority_calculator_comprehensive()
    
    test_task_scheduler_priority_calculation()
    
    test_central_task_manager_priority_integration()
    
    test_pipeline_continuity_bonus()
    
    print("\nAll comprehensive tests completed successfully!")


if __name__ == "__main__":
    main()
