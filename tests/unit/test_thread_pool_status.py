"""
CentralTaskManager线程池状态功能测试
"""

import pytest
from typing import List, Dict, Any, Optional
from src.core.task.central_task_manager import CentralTaskManager
from src.core.task.task import Task
from src.interfaces.task_interface import (
    TaskSchedulerInterface,
    TaskExecutorInterface,
    TaskMonitorInterface,
    TaskGroupManagerInterface,
)


class MockTaskScheduler(TaskSchedulerInterface):
    """Mock任务调度器"""

    def __init__(self):
        self.tasks = []

    def enqueue_task(self, task: Task) -> bool:
        self.tasks.append(task)
        return True

    def dequeue_task(self) -> Optional[Task]:
        if self.tasks:
            return self.tasks.pop(0)
        return None

    def get_queue_size(self) -> int:
        return len(self.tasks)

    def calculate_priority(self, task: Task) -> int:
        return 11


class MockTaskExecutor(TaskExecutorInterface):
    """Mock任务执行器"""

    def execute_task(self, task: Task) -> bool:
        return True

    def register_handler(self, task_type: str, handler: callable) -> bool:
        return True

    def get_supported_types(self) -> List[str]:
        return ["video_embed", "audio_embed", "image_embed"]


class MockTaskMonitor(TaskMonitorInterface):
    """Mock任务监控器"""

    def __init__(self):
        self.tasks = {}

    def add_task(self, task: Task) -> bool:
        self.tasks[task.id] = task
        return True

    def update_task_status(self, task_id: str, status: str, progress: float = 0.0) -> bool:
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            self.tasks[task_id].progress = progress
            return True
        return False

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        task = self.tasks.get(task_id)
        if task:
            return {
                "id": task.id,
                "task_type": task.task_type,
                "status": task.status,
                "priority": task.priority,
                "progress": getattr(task, "progress", 0.0),
            }
        return None

    def get_all_tasks(self, status: Optional[str] = None) -> Dict[str, Any]:
        if status:
            return {
                task_id: task
                for task_id, task in self.tasks.items()
                if task.status == status
            }
        return self.tasks


class MockTaskGroupManager(TaskGroupManagerInterface):
    """Mock任务组管理器"""

    def __init__(self):
        self.groups = {}
        self.locks = {}

    def create_group(self, file_id: str, file_path: str) -> bool:
        if file_id not in self.groups:
            self.groups[file_id] = {"file_path": file_path, "tasks": []}
            self.locks[file_id] = False
            return True
        return False

    def add_task_to_group(self, file_id: str, task: Task) -> bool:
        if file_id in self.groups:
            self.groups[file_id]["tasks"].append(task.id)
            return True
        return False

    def add_task_to_group_sync(self, group_id: str, task: Task):
        self.add_task_to_group(group_id, task)

    def is_pipeline_locked(self, file_id: str) -> bool:
        return self.locks.get(file_id, False)

    def acquire_pipeline_lock(self, file_id: str, task_id: str) -> bool:
        if file_id in self.locks and not self.locks[file_id]:
            self.locks[file_id] = True
            return True
        return False

    def release_pipeline_lock(self, file_id: str, task_id: str) -> bool:
        if file_id in self.locks and self.locks[file_id]:
            self.locks[file_id] = False
            return True
        return False

    def get_group_progress(self, file_id: str) -> float:
        return 1.0 if file_id in self.groups else 0.0


class TestThreadPoolStatus:
    """线程池状态测试"""

    @pytest.fixture
    def config(self):
        """测试配置"""
        return {
            "task_manager": {
                "max_workers": 8,
                "default_priority": 5,
            }
        }

    @pytest.fixture
    def task_manager(self, config):
        """创建CentralTaskManager实例"""
        scheduler = MockTaskScheduler()
        executor = MockTaskExecutor()
        monitor = MockTaskMonitor()
        group_manager = MockTaskGroupManager()

        manager = CentralTaskManager(
            config=config,
            task_scheduler=scheduler,
            task_executor=executor,
            task_monitor=monitor,
            task_group_manager=group_manager,
        )
        return manager, monitor

    def test_thread_pool_status_no_tasks(self, task_manager):
        """测试无任务时的线程池状态"""
        manager, _ = task_manager

        status = manager.get_thread_pool_status()

        assert status["max_workers"] == 8
        assert status["active_threads"] == 0
        assert status["idle_threads"] == 8
        assert status["load_percentage"] == 0

    def test_thread_pool_status_with_running_tasks(self, task_manager):
        """测试有运行中任务时的线程池状态"""
        manager, monitor = task_manager

        task_id = manager.create_task(
            task_type="video_embed",
            task_data={"file_path": "/path/to/video.mp4"},
        )

        monitor.tasks[task_id].status = "running"

        status = manager.get_thread_pool_status()

        assert status["max_workers"] == 8
        assert status["active_threads"] == 1
        assert status["idle_threads"] == 7
        assert status["load_percentage"] == 12

    def test_thread_pool_status_multiple_running_tasks(self, task_manager):
        """测试多个运行中任务时的线程池状态"""
        manager, monitor = task_manager

        task_ids = []
        for i in range(5):
            task_id = manager.create_task(
                task_type="video_embed",
                task_data={"file_path": f"/path/to/video{i}.mp4"},
            )
            task_ids.append(task_id)
            monitor.tasks[task_id].status = "running"

        status = manager.get_thread_pool_status()

        assert status["max_workers"] == 8
        assert status["active_threads"] == 5
        assert status["idle_threads"] == 3
        assert status["load_percentage"] == 62

    def test_thread_pool_status_full_load(self, task_manager):
        """测试线程池满载时的状态"""
        manager, monitor = task_manager

        task_ids = []
        for i in range(8):
            task_id = manager.create_task(
                task_type="video_embed",
                task_data={"file_path": f"/path/to/video{i}.mp4"},
            )
            task_ids.append(task_id)
            monitor.tasks[task_id].status = "running"

        status = manager.get_thread_pool_status()

        assert status["max_workers"] == 8
        assert status["active_threads"] == 8
        assert status["idle_threads"] == 0
        assert status["load_percentage"] == 100

    def test_thread_pool_status_mixed_statuses(self, task_manager):
        """测试混合状态任务时的线程池状态"""
        manager, monitor = task_manager

        task_ids = []
        for i in range(10):
            task_id = manager.create_task(
                task_type="video_embed",
                task_data={"file_path": f"/path/to/video{i}.mp4"},
            )
            task_ids.append(task_id)

        monitor.tasks[task_ids[0]].status = "running"
        monitor.tasks[task_ids[1]].status = "running"
        monitor.tasks[task_ids[2]].status = "running"
        monitor.tasks[task_ids[3]].status = "completed"
        monitor.tasks[task_ids[4]].status = "completed"
        monitor.tasks[task_ids[5]].status = "pending"
        monitor.tasks[task_ids[6]].status = "pending"
        monitor.tasks[task_ids[7]].status = "failed"
        monitor.tasks[task_ids[8]].status = "pending"
        monitor.tasks[task_ids[9]].status = "completed"

        status = manager.get_thread_pool_status()

        assert status["max_workers"] == 8
        assert status["active_threads"] == 3
        assert status["idle_threads"] == 5
        assert status["load_percentage"] == 37

    def test_thread_pool_status_custom_max_workers(self, task_manager):
        """测试自定义最大线程数时的线程池状态"""
        manager, monitor = task_manager

        manager.task_config["max_workers"] = 16

        task_ids = []
        for i in range(4):
            task_id = manager.create_task(
                task_type="video_embed",
                task_data={"file_path": f"/path/to/video{i}.mp4"},
            )
            task_ids.append(task_id)
            monitor.tasks[task_id].status = "running"

        status = manager.get_thread_pool_status()

        assert status["max_workers"] == 16
        assert status["active_threads"] == 4
        assert status["idle_threads"] == 12
        assert status["load_percentage"] == 25

    def test_thread_pool_status_load_percentage_calculation(self, task_manager):
        """测试负载百分比计算"""
        manager, monitor = task_manager

        test_cases = [
            (1, 12),
            (2, 25),
            (3, 37),
            (4, 50),
            (5, 62),
            (6, 75),
            (7, 87),
            (8, 100),
        ]

        for running, expected_percentage in test_cases:
            monitor.tasks.clear()

            task_ids = []
            for i in range(running):
                task_id = manager.create_task(
                    task_type="video_embed",
                    task_data={"file_path": f"/path/to/video{i}.mp4"},
                )
                task_ids.append(task_id)
                monitor.tasks[task_id].status = "running"

            status = manager.get_thread_pool_status()
            assert status["load_percentage"] == expected_percentage

    def test_thread_pool_status_idle_threads_calculation(self, task_manager):
        """测试空闲线程数计算"""
        manager, monitor = task_manager

        test_cases = [
            (0, 8),
            (1, 7),
            (2, 6),
            (3, 5),
            (4, 4),
            (5, 3),
            (6, 2),
            (7, 1),
            (8, 0),
        ]

        for running, expected_idle in test_cases:
            monitor.tasks.clear()

            task_ids = []
            for i in range(running):
                task_id = manager.create_task(
                    task_type="video_embed",
                    task_data={"file_path": f"/path/to/video{i}.mp4"},
                )
                task_ids.append(task_id)
                monitor.tasks[task_id].status = "running"

            status = manager.get_thread_pool_status()
            assert status["idle_threads"] == expected_idle
