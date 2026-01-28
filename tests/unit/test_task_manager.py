"""
任务管理器单元测试
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock

import sys
sys.path.insert(0, '/data/project/msearch/src')

from src.core.task.task_types import Task, TaskStatus, TaskType
from src.core.task.task_manager import TaskManager
from src.core.task.task_scheduler import TaskScheduler
from src.core.task.task_executor import OptimizedTaskExecutor
from src.core.task.task_group_manager import TaskGroupManager
from src.core.task.resource_manager import OptimizedResourceManager
from src.core.task.task_monitor import OptimizedTaskMonitor


@pytest.fixture
def task_manager():
    """创建任务管理器实例"""
    config = {
        "task_manager": {
            "concurrency_mode": "dynamic",
            "min_concurrent_tasks": 1,
            "max_concurrent_tasks": 8,
            "base_concurrent_tasks": 4
        }
    }
    return TaskManager(config, device='cpu')


@pytest.mark.asyncio
async def test_task_manager_initialization(task_manager):
    """测试任务管理器初始化"""
    assert task_manager.is_running is False
    assert task_manager.task_queue is not None
    assert task_manager.task_executor is not None
    assert task_manager.group_manager is not None
    assert task_manager.resource_manager is not None
    assert task_manager.task_monitor is not None


@pytest.mark.asyncio
async def test_task_creation(task_manager):
    """测试任务创建"""
    # 初始化任务管理器
    success = task_manager.initialize()
    assert success is True
    
    try:
        # 注册任务处理器
        def mock_handler(task):
            return {"status": "success"}
        
        task_manager.register_handler("image_preprocess", mock_handler)
        
        # 创建任务
        task_id = task_manager.create_task(
            task_type="image_preprocess",
            task_data={"file_path": "/test/image.jpg"},
            priority=5,
            file_id="file_001"
        )
        
        # 验证任务创建
        assert task_id is not None
        assert isinstance(task_id, str)
        
        # 获取任务状态
        task_info = task_manager.get_task_status(task_id)
        assert task_info is not None
        
    finally:
        task_manager.shutdown()


@pytest.mark.asyncio
async def test_task_priority_calculation():
    """测试任务优先级计算"""
    scheduler = TaskScheduler({})
    
    # 测试基础优先级计算
    priority = scheduler.calculate_priority(
        task_type=TaskType.IMAGE_PREPROCESS,
        file_priority=5
    )
    
    # 验证优先级是数值
    assert isinstance(priority, int)
    assert priority > 0
    
    # 测试不同任务类型的优先级
    priority_image = scheduler.calculate_priority(TaskType.IMAGE_PREPROCESS, 5)
    priority_thumbnail = scheduler.calculate_priority(TaskType.THUMBNAIL_GENERATE, 5)
    
    # 图像预处理应该比缩略图生成优先级高（数值更小）
    assert priority_image < priority_thumbnail


@pytest.mark.asyncio
async def test_task_group_manager():
    """测试任务组管理器"""
    config = {}
    group_manager = TaskGroupManager(config)
    
    # 启动
    await group_manager.start()
    
    try:
        # 创建任务组
        group = await group_manager.create_group("file_001", "/test/file.jpg")
        assert group is not None
        assert group.file_id == "file_001"
        
        # 测试流水线锁
        assert group_manager.is_pipeline_locked("file_001") is False
        
        # 获取锁
        result = group_manager.acquire_pipeline_lock("file_001", "task_001")
        assert result is True
        assert group_manager.is_pipeline_locked("file_001") is True
        
        # 释放锁
        result = group_manager.release_pipeline_lock("file_001", "task_001")
        assert result is True
        assert group_manager.is_pipeline_locked("file_001") is False
        
    finally:
        await group_manager.stop()


@pytest.mark.asyncio
async def test_resource_manager():
    """测试资源管理器"""
    config = {
        'memory_warning_threshold': 85.0,
        'memory_pause_threshold': 95.0
    }
    resource_manager = OptimizedResourceManager(config)
    
    try:
        # 获取当前内存使用
        memory_usage = resource_manager.get_memory_usage()
        assert isinstance(memory_usage, dict)
        assert 'percent' in memory_usage
        
        # 获取资源统计
        stats = resource_manager.get_resource_usage()
        assert "memory" in stats
        
        # 检查OOM状态
        oom_state = resource_manager.check_oom_status()
        assert oom_state in ["normal", "warning", "critical"]
        
    finally:
        resource_manager.cleanup()


@pytest.mark.asyncio
async def test_task_scheduler_queue():
    """测试任务调度器队列"""
    scheduler = TaskScheduler({})
    await scheduler.start()
    
    try:
        # 创建测试任务
        task = Task(
            id="test_task_001",
            type=TaskType.IMAGE_PREPROCESS,
            file_id="file_001",
            file_path="/test/image.jpg",
            priority=100
        )
        
        # 入队
        result = await scheduler.enqueue_task(task)
        assert result is True
        
        # 检查队列大小
        queue_size = await scheduler.get_queue_size()
        assert queue_size == 1
        
        # 出队
        dequeued_task = await scheduler.dequeue_task()
        assert dequeued_task is not None
        assert dequeued_task.id == task.id
        
    finally:
        await scheduler.stop()


@pytest.mark.asyncio
async def test_task_executor():
    """测试任务执行器"""
    executor = OptimizedTaskExecutor()
    
    try:
        # 注册处理器
        def mock_handler(task):
            return {"status": "success", "task_id": task.id}
        
        executor.register_handler("image_preprocess", mock_handler)
        
        # 创建测试任务
        from src.core.task.task import Task as OldTask
        task = OldTask(
            id="test_task_002",
            task_type="image_preprocess",
            task_data={"file_path": "/test/image.jpg"},
            priority=100
        )
        
        # 执行任务
        result = executor.execute_task(task)
        assert result is not None
        assert result["status"] == "success"
        
    finally:
        executor.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
