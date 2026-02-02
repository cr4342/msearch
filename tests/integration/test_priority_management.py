"""
CentralTaskManager优先级管理集成测试
测试文件类型优先级管理功能
"""

import pytest
from typing import Optional, List, Dict, Any
from unittest.mock import Mock, MagicMock
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
        return 11  # Return a high value to allow file type priority to take effect


class MockTaskExecutor(TaskExecutorInterface):
    """Mock任务执行器"""

    def execute_task(self, task: Task) -> bool:
        return True

    def register_handler(self, task_type: str, handler: callable) -> bool:
        return True

    def get_supported_types(self) -> List[str]:
        return [
            "video_embed",
            "audio_embed",
            "image_embed",
            "thumbnail_gen",
            "preview_gen",
        ]


class MockTaskMonitor(TaskMonitorInterface):
    """Mock任务监控器"""

    def __init__(self):
        self.tasks = {}

    def add_task(self, task: Task) -> bool:
        self.tasks[task.id] = task
        return True

    def update_task_status(
        self, task_id: str, status: str, progress: float = 0.0
    ) -> bool:
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


class TestCentralTaskManagerPriority:
    """CentralTaskManager优先级管理测试"""

    @pytest.fixture
    def config(self):
        """测试配置"""
        return {
            "task_manager": {
                "max_workers": 4,
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

    def test_initial_file_type_priority(self, task_manager):
        """测试初始文件类型优先级配置"""
        manager, _ = task_manager

        assert manager.file_type_priority == {
            "video": "medium",
            "audio": "medium",
            "image": "medium",
        }

    def test_priority_mapping(self, task_manager):
        """测试优先级映射配置"""
        manager, _ = task_manager

        assert manager.priority_mapping == {"high": 2, "medium": 5, "low": 9}

    def test_set_file_type_priority_valid(self, task_manager):
        """测试设置有效的文件类型优先级"""
        manager, _ = task_manager

        result = manager.set_file_type_priority("video", "high")

        assert result is True
        assert manager.file_type_priority["video"] == "high"

    def test_set_file_type_priority_invalid_type(self, task_manager):
        """测试设置无效的文件类型"""
        manager, _ = task_manager

        result = manager.set_file_type_priority("unknown", "high")

        assert result is False
        assert "unknown" not in manager.file_type_priority

    def test_set_file_type_priority_invalid_level(self, task_manager):
        """测试设置无效的优先级级别"""
        manager, _ = task_manager

        result = manager.set_file_type_priority("video", "invalid")

        assert result is False
        assert manager.file_type_priority["video"] == "medium"

    def test_get_file_type_priority_default(self, task_manager):
        """测试获取默认文件类型优先级"""
        manager, _ = task_manager

        priority = manager.get_file_type_priority("video")

        assert priority == 5  # medium maps to 5

    def test_get_file_type_priority_high(self, task_manager):
        """测试获取高优先级"""
        manager, _ = task_manager
        manager.set_file_type_priority("video", "high")

        priority = manager.get_file_type_priority("video")

        assert priority == 2  # high maps to 2

    def test_get_file_type_priority_low(self, task_manager):
        """测试获取低优先级"""
        manager, _ = task_manager
        manager.set_file_type_priority("audio", "low")

        priority = manager.get_file_type_priority("audio")

        assert priority == 9  # low maps to 9

    def test_get_file_type_priority_unknown_type(self, task_manager):
        """测试获取未知文件类型的优先级"""
        manager, _ = task_manager

        priority = manager.get_file_type_priority("unknown")

        assert priority == 5  # defaults to medium

    def test_set_priority_settings_valid(self, task_manager):
        """测试批量设置有效的优先级设置"""
        manager, _ = task_manager

        settings = {"video": "high", "audio": "medium", "image": "low"}

        result = manager.set_priority_settings(settings)

        assert result is True
        assert manager.file_type_priority["video"] == "high"
        assert manager.file_type_priority["audio"] == "medium"
        assert manager.file_type_priority["image"] == "low"

    def test_set_priority_settings_mixed(self, task_manager):
        """测试批量设置混合的优先级设置（部分有效、部分无效）"""
        manager, _ = task_manager

        settings = {"video": "high", "unknown": "medium", "image": "low"}  # invalid

        result = manager.set_priority_settings(settings)

        assert result is True  # should still return True
        assert manager.file_type_priority["video"] == "high"
        assert manager.file_type_priority["image"] == "low"
        assert "unknown" not in manager.file_type_priority

    def test_get_priority_settings(self, task_manager):
        """测试获取优先级设置"""
        manager, _ = task_manager
        manager.set_file_type_priority("video", "high")

        settings = manager.get_priority_settings()

        assert settings["video"] == "high"
        assert settings["audio"] == "medium"
        assert settings["image"] == "medium"

    def test_task_type_to_file_type_mapping(self, task_manager):
        """测试任务类型到文件类型的映射"""
        manager, _ = task_manager

        assert manager.task_type_to_file_type["video_embed"] == "video"
        assert manager.task_type_to_file_type["audio_embed"] == "audio"
        assert manager.task_type_to_file_type["image_embed"] == "image"
        assert manager.task_type_to_file_type["thumbnail_gen"] == "image"
        assert manager.task_type_to_file_type["preview_gen"] == "video"

    def test_get_task_priority_by_type_video_embed(self, task_manager):
        """测试video_embed任务类型获取优先级"""
        manager, _ = task_manager
        manager.set_file_type_priority("video", "high")

        priority = manager.get_task_priority_by_type("video_embed")

        assert priority == 2  # high priority

    def test_get_task_priority_by_type_audio_embed(self, task_manager):
        """测试audio_embed任务类型获取优先级"""
        manager, _ = task_manager
        manager.set_file_type_priority("audio", "low")

        priority = manager.get_task_priority_by_type("audio_embed")

        assert priority == 9  # low priority

    def test_get_task_priority_by_type_image_embed(self, task_manager):
        """测试image_embed任务类型获取优先级"""
        manager, _ = task_manager
        manager.set_file_type_priority("image", "medium")

        priority = manager.get_task_priority_by_type("image_embed")

        assert priority == 5  # medium priority

    def test_get_task_priority_by_type_unknown_type(self, task_manager):
        """测试未知任务类型获取优先级"""
        manager, _ = task_manager

        priority = manager.get_task_priority_by_type(
            "unknown_task_type", base_priority=3
        )

        assert priority == 3  # returns base priority

    def test_create_task_with_priority_mapping(self, task_manager):
        """测试创建任务时应用优先级映射"""
        manager, monitor = task_manager
        manager.set_file_type_priority("video", "high")

        task_id = manager.create_task(
            task_type="video_embed",
            task_data={"file_path": "/path/to/video.mp4"},
            file_id="test_file_id",
        )

        task = monitor.tasks.get(task_id)
        assert task is not None
        assert task.priority == 2  # high priority

    def test_create_task_with_different_priorities(self, task_manager):
        """测试创建不同优先级的任务"""
        manager, monitor = task_manager

        manager.set_file_type_priority("video", "high")
        manager.set_file_type_priority("audio", "low")

        video_task_id = manager.create_task(
            task_type="video_embed",
            task_data={"file_path": "/path/to/video.mp4"},
        )

        audio_task_id = manager.create_task(
            task_type="audio_embed",
            task_data={"file_path": "/path/to/audio.mp3"},
        )

        video_task = monitor.tasks.get(video_task_id)
        audio_task = monitor.tasks.get(audio_task_id)

        assert video_task.priority == 2  # high
        assert audio_task.priority == 9  # low

    def test_update_all_task_priorities(self, task_manager):
        """测试更新所有任务的优先级"""
        manager, monitor = task_manager

        task1_id = manager.create_task(
            task_type="video_embed",
            task_data={"file_path": "/path/to/video1.mp4"},
        )

        task2_id = manager.create_task(
            task_type="audio_embed",
            task_data={"file_path": "/path/to/audio1.mp3"},
        )

        task3_id = manager.create_task(
            task_type="image_embed",
            task_data={"file_path": "/path/to/image1.jpg"},
        )

        # Change priorities
        manager.set_file_type_priority("video", "high")
        manager.set_file_type_priority("audio", "low")
        manager.set_file_type_priority("image", "medium")

        # Update all task priorities
        result = manager.update_all_task_priorities()

        assert result is True

        task1 = monitor.tasks.get(task1_id)
        task2 = monitor.tasks.get(task2_id)
        task3 = monitor.tasks.get(task3_id)

        assert task1.priority == 2  # high
        assert task2.priority == 9  # low
        assert task3.priority == 5  # medium

    def test_update_all_task_priorities_no_change_needed(self, task_manager):
        """测试更新任务优先级时没有需要更改的"""
        manager, monitor = task_manager

        task_id = manager.create_task(
            task_type="video_embed",
            task_data={"file_path": "/path/to/video.mp4"},
        )

        # Get initial priority
        initial_priority = monitor.tasks.get(task_id).priority

        # Update without changing settings
        result = manager.update_all_task_priorities()

        assert result is True
        assert monitor.tasks.get(task_id).priority == initial_priority

    def test_thumbnail_gen_task_priority(self, task_manager):
        """测试thumbnail_gen任务类型的优先级（应映射到image类型）"""
        manager, monitor = task_manager
        manager.set_file_type_priority("image", "high")

        task_id = manager.create_task(
            task_type="thumbnail_gen",
            task_data={"file_path": "/path/to/image.jpg"},
        )

        task = monitor.tasks.get(task_id)
        assert task.priority == 2  # high priority (image -> high)

    def test_preview_gen_task_priority(self, task_manager):
        """测试preview_gen任务类型的优先级（应映射到video类型）"""
        manager, monitor = task_manager
        manager.set_file_type_priority("video", "low")

        task_id = manager.create_task(
            task_type="preview_gen",
            task_data={"file_path": "/path/to/video.mp4"},
        )

        task = monitor.tasks.get(task_id)
        assert task.priority == 9  # low priority (video -> low)

    def test_priority_levels_boundary(self, task_manager):
        """测试优先级级别边界值"""
        manager, _ = task_manager

        # Test high boundary
        manager.set_file_type_priority("video", "high")
        assert manager.get_file_type_priority("video") == 2

        # Test low boundary
        manager.set_file_type_priority("audio", "low")
        assert manager.get_file_type_priority("audio") == 9

        # Test medium
        manager.set_file_type_priority("image", "medium")
        assert manager.get_file_type_priority("image") == 5

    def test_all_priority_levels(self, task_manager):
        """测试所有优先级级别"""
        manager, _ = task_manager

        manager.set_file_type_priority("video", "high")
        manager.set_file_type_priority("audio", "medium")
        manager.set_file_type_priority("image", "low")

        assert manager.get_file_type_priority("video") == 2
        assert manager.get_file_type_priority("audio") == 5
        assert manager.get_file_type_priority("image") == 9
