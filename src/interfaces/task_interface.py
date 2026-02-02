# -*- coding: utf-8 -*-
"""
任务管理抽象接口定义

定义任务管理相关组件的抽象接口，实现业务逻辑与具体实现的解耦。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable


class TaskManagerInterface(ABC):
    """
    任务管理器接口

    负责任务生命周期管理、任务调度、任务状态跟踪的抽象接口。
    """

    @abstractmethod
    def create_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        priority: int = 5,
        file_id: Optional[str] = None,
        file_path: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        group_id: Optional[str] = None,
    ) -> str:
        """
        创建任务

        Args:
            task_type: 任务类型
            task_data: 任务数据
            priority: 优先级
            file_id: 关联的文件ID
            file_path: 关联的文件路径
            depends_on: 依赖的任务ID列表
            group_id: 任务组ID

        Returns:
            任务ID
        """
        pass

    @abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        pass

    @abstractmethod
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态字典
        """
        pass

    @abstractmethod
    def get_all_tasks(
        self, status: Optional[str] = None, task_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取所有任务

        Args:
            status: 状态过滤
            task_type: 任务类型过滤

        Returns:
            任务列表
        """
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """启动任务管理器"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """停止任务管理器"""
        pass


class TaskSchedulerInterface(ABC):
    """
    任务调度器接口

    负责任务优先级计算、任务队列管理、任务排序和选择的抽象接口。
    """

    @abstractmethod
    def enqueue_task(self, task: Any) -> bool:
        """
        将任务加入队列

        Args:
            task: 任务对象

        Returns:
            是否成功入队
        """
        pass

    @abstractmethod
    def dequeue_task(self) -> Optional[Any]:
        """
        从队列取出任务

        Returns:
            任务对象，如果队列为空返回None
        """
        pass

    @abstractmethod
    def get_queue_size(self) -> int:
        """
        获取队列大小

        Returns:
            队列中的任务数量
        """
        pass

    @abstractmethod
    def calculate_priority(self, task: Any) -> int:
        """
        计算任务优先级

        Args:
            task: 任务对象

        Returns:
            计算后的优先级
        """
        pass


class TaskExecutorInterface(ABC):
    """
    任务执行器接口

    负责任务执行、错误处理和重试、进度更新的抽象接口。
    """

    @abstractmethod
    def execute_task(self, task: Any) -> bool:
        """
        执行任务

        Args:
            task: 任务对象

        Returns:
            是否执行成功
        """
        pass

    @abstractmethod
    def register_handler(self, task_type: str, handler: Callable) -> bool:
        """
        注册任务处理器

        Args:
            task_type: 任务类型
            handler: 处理函数

        Returns:
            是否注册成功
        """
        pass

    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """
        获取支持的任务类型

        Returns:
            任务类型列表
        """
        pass


class TaskMonitorInterface(ABC):
    """
    任务监控器接口

    负责任务状态跟踪、任务统计、历史记录的抽象接口。
    """

    @abstractmethod
    def add_task(self, task: Any) -> bool:
        """
        添加任务到监控

        Args:
            task: 任务对象

        Returns:
            是否添加成功
        """
        pass

    @abstractmethod
    def update_task_status(
        self, task_id: str, status: str, progress: float = 0.0
    ) -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            progress: 进度(0-1)

        Returns:
            是否更新成功
        """
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典
        """
        pass

    @abstractmethod
    def get_all_tasks(self, status: Optional[str] = None) -> Dict[str, Any]:
        """
        获取所有任务

        Args:
            status: 状态过滤

        Returns:
            任务字典
        """
        pass


class TaskGroupManagerInterface(ABC):
    """
    任务组管理器接口

    负责任务组管理、任务流水线锁管理、文件级任务组织的抽象接口。
    """

    @abstractmethod
    def create_group(self, file_id: str, file_path: str) -> bool:
        """
        创建任务组

        Args:
            file_id: 文件ID
            file_path: 文件路径

        Returns:
            是否创建成功
        """
        pass

    @abstractmethod
    def add_task_to_group(self, file_id: str, task: Any) -> bool:
        """
        添加任务到任务组

        Args:
            file_id: 文件ID
            task: 任务对象

        Returns:
            是否添加成功
        """
        pass

    @abstractmethod
    def is_pipeline_locked(self, file_id: str) -> bool:
        """
        检查流水线锁状态

        Args:
            file_id: 文件ID

        Returns:
            是否被锁定
        """
        pass

    @abstractmethod
    def acquire_pipeline_lock(self, file_id: str, task_id: str) -> bool:
        """
        获取流水线锁

        Args:
            file_id: 文件ID
            task_id: 任务ID

        Returns:
            是否获取成功
        """
        pass

    @abstractmethod
    def release_pipeline_lock(self, file_id: str, task_id: str) -> bool:
        """
        释放流水线锁

        Args:
            file_id: 文件ID
            task_id: 任务ID

        Returns:
            是否释放成功
        """
        pass

    @abstractmethod
    def get_group_progress(self, file_id: str) -> float:
        """
        获取任务组进度

        Args:
            file_id: 文件ID

        Returns:
            进度(0-1)
        """
        pass
