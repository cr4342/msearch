"""
任务管理器单元测试
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock

import sys
sys.path.insert(0, '/data/project/msearch/src')

from src.core.task.task import Task
from src.core.task.task_types import TaskStatus, TaskType
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
    from src.core.task.priority_calculator import PriorityCalculator
    from src.core.task.task import Task
    
    calculator = PriorityCalculator()
    
    # 创建测试任务
    task = Task(
        task_type="image_preprocess",
        task_data={"file_path": "/test/image.jpg"},
        file_id="file_001",
        file_path="/test/image.jpg",
        priority=5
    )
    
    # 测试基础优先级计算
    priority = calculator.calculate_priority(task, file_priority=5)
    
    # 验证优先级是数值
    assert isinstance(priority, int)
    assert priority > 0
    
    # 测试不同任务类型的优先级
    task_image = Task(
        task_type="image_preprocess",
        task_data={"file_path": "/test/image.jpg"},
        file_id="file_001",
        file_path="/test/image.jpg",
        priority=5
    )
    task_thumbnail = Task(
        task_type="thumbnail_generate",
        task_data={"file_path": "/test/image.jpg"},
        file_id="file_001",
        file_path="/test/image.jpg",
        priority=5
    )
    
    priority_image = calculator.calculate_priority(task_image, file_priority=5)
    priority_thumbnail = calculator.calculate_priority(task_thumbnail, file_priority=5)
    
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
        'memory_pause_threshold': 95.0,
        'gpu_memory_warning_threshold': 85.0,
        'gpu_memory_pause_threshold': 95.0
    }
    resource_manager = OptimizedResourceManager(config)
    
    try:
        # 获取当前资源使用
        resource_usage = resource_manager.get_resource_usage()
        assert isinstance(resource_usage, dict)
        assert 'memory_percent' in resource_usage
        
        # 检查OOM状态
        oom_state = resource_manager.get_current_state()
        assert oom_state in ["normal", "warning", "pause"]
        
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
            id="task_001",
            task_type="image_preprocess",
            task_data={"file_path": "/test/image.jpg"},
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
        def mock_handler(task_data):
            # task_data是task.task_data，不是task对象
            return {"status": "success"}
        
        executor.register_handler("image_preprocess", mock_handler)
        
        # 创建测试任务
        task = Task(
            id="test_task_002",
            task_type="image_preprocess",
            task_data={"file_path": "/test/image.jpg"},
            file_id="file_001",
            file_path="/test/image.jpg",
            priority=100
        )
        
        # 执行任务
        result = executor.execute_task(task)
        assert result is True  # execute_task返回bool
        
    finally:
        executor.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
