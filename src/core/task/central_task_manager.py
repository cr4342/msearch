"""
中央任务管理器

统一协调所有任务管理功能，解决职责边界模糊问题。
严格遵循依赖注入原则，所有依赖通过构造函数参数传递。
"""

import uuid
import threading
import time
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from datetime import datetime
import logging

from src.interfaces.task_interface import (
    TaskManagerInterface,
    TaskSchedulerInterface,
    TaskExecutorInterface,
    TaskMonitorInterface,
    TaskGroupManagerInterface,
)

from .task import Task


logger = logging.getLogger(__name__)


class CentralTaskManager(TaskManagerInterface):
    """
    中央任务管理器：统一协调所有任务管理功能

    职责：
    - 任务生命周期管理（创建、执行、取消）
    - 组件协调和集成（orchestrator 角色）
    - 对外提供统一的任务管理接口
    - 调度循环控制

    明确边界：
    - ✅ 负责任务的创建、取消、状态查询
    - ✅ 协调各组件完成调度流程
    - ✅ 维护调度循环，触发任务调度
    - ❌ 不直接计算优先级（委托给TaskScheduler）
    - ❌ 不直接执行任务（委托给TaskExecutor）
    - ❌ 不直接管理任务组锁（委托给TaskGroupManager）
    """

    def __init__(
        self,
        config: Dict[str, Any],
        task_scheduler: TaskSchedulerInterface,
        task_executor: TaskExecutorInterface,
        task_monitor: TaskMonitorInterface,
        task_group_manager: TaskGroupManagerInterface,
        device: str = "cpu",
    ):
        """
        初始化中央任务管理器

        Args:
            config: 配置字典
            task_scheduler: 任务调度器
            task_executor: 任务执行器
            task_monitor: 任务监控器
            task_group_manager: 任务组管理器
            device: 设备类型（cuda/cpu）
        """
        self.config = config
        self.device = device

        # 任务配置
        self.task_config = config.get("task_manager", {})

        # 依赖注入：通过构造函数参数接收组件
        self.task_scheduler = task_scheduler
        self.task_executor = task_executor
        self.task_monitor = task_monitor
        self.group_manager = task_group_manager

        # 任务处理器
        self.task_handlers: Dict[str, Callable] = {}

        # 线程控制
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
            "retried_tasks": 0,
        }

        # 文件类型优先级配置
        self.file_type_priority = {
            "video": "medium",
            "audio": "medium",
            "image": "medium",
        }

        # 优先级映射（高/中/低 → 1-11级）
        self.priority_mapping = {"high": 2, "medium": 5, "low": 9}

        # 任务类型到文件类型的映射
        self.task_type_to_file_type = {
            "video_embed": "video",
            "audio_embed": "audio",
            "image_embed": "image",
            "thumbnail_gen": "image",
            "preview_gen": "video",
        }

        logger.info("中央任务管理器初始化完成（依赖注入模式）")

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
        task_id = str(uuid.uuid4())

        # 创建任务对象
        task = Task(
            id=task_id,
            task_type=task_type,
            task_data=task_data,
            priority=priority,
            file_id=file_id,
            file_path=file_path,
            depends_on=depends_on or [],
            group_id=group_id,
        )

        # 根据任务类型获取优先级（使用文件类型优先级配置）
        optimized_priority = self.get_task_priority_by_type(task_type, priority)

        # 如果调度器有额外的优先级计算逻辑，也应用它
        try:
            scheduler_priority = self.task_scheduler.calculate_priority(task)
            # 取较小的优先级（更高的优先级）
            task.priority = min(optimized_priority, scheduler_priority)
        except Exception as e:
            logger.warning(f"调度器优先级计算失败，使用文件类型优先级: {e}")
            task.priority = optimized_priority

        # 添加到任务组
        if file_id:
            self.group_manager.add_task_to_group_sync(file_id, task)

        # 添加到调度器队列
        self.task_scheduler.enqueue_task(task)

        # 添加到监控器
        self.task_monitor.add_task(task)

        # 更新统计
        with self.lock:
            self.stats["total_tasks"] += 1

        logger.info(
            f"任务创建成功: {task_id}, 类型: {task_type}, 优先级: {optimized_priority}"
        )

        return task_id

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        try:
            # 更新任务状态
            self.task_monitor.update_task_status(task_id, "cancelled")

            # 更新统计
            with self.lock:
                self.stats["cancelled_tasks"] += 1

            logger.info(f"任务已取消: {task_id}")
            return True
        except Exception as e:
            logger.error(f"取消任务失败 {task_id}: {e}")
            return False

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态字典
        """
        task = self.task_monitor.get_task(task_id)

        if task is None:
            return None

        # 如果任务对象有 to_dict 方法，使用它
        if hasattr(task, "to_dict"):
            return task.to_dict()

        # 否则，手动构建字典
        return {
            "id": getattr(task, "id", task_id),
            "task_type": getattr(task, "task_type", "unknown"),
            "status": getattr(task, "status", "unknown"),
            "priority": getattr(task, "priority", 5),
            "file_id": getattr(task, "file_id", None),
            "file_path": getattr(task, "file_path", None),
            "created_at": getattr(task, "created_at", None),
            "started_at": getattr(task, "started_at", None),
            "completed_at": getattr(task, "completed_at", None),
            "progress": getattr(task, "progress", 0.0),
            "error": getattr(task, "error", None),
            "result": getattr(task, "result", None),
            "depends_on": getattr(task, "depends_on", []),
            "group_id": getattr(task, "group_id", None),
        }

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
        tasks_dict = self.task_monitor.get_all_tasks(status=status)
        # 将Task对象转换为字典列表
        return [task.to_dict() for task in tasks_dict.values()]

    def list_tasks(
        self, status: Optional[str] = None, task_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取所有任务（别名方法，兼容API路由）

        Args:
            status: 状态过滤（pending/running/completed/failed）
            task_type: 任务类型过滤

        Returns:
            任务列表
        """
        return self.get_all_tasks(status=status, task_type=task_type)

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        with self.lock:
            stats = self.stats.copy()

        # 添加各组件的统计
        stats["scheduler"] = {"queue_size": self.task_scheduler.get_queue_size()}

        return stats

    def start(self) -> None:
        """启动任务管理器"""
        if self.is_running:
            logger.warning("任务管理器已经在运行")
            return

        self.is_running = True

        # 启动工作线程
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

        logger.info("中央任务管理器已启动")

    def stop(self) -> None:
        """停止任务管理器"""
        if not self.is_running:
            return

        self.is_running = False

        # 等待工作线程结束
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)

        logger.info("中央任务管理器已停止")

    def _worker_loop(self) -> None:
        """工作线程主循环"""
        logger.info("任务调度工作线程已启动")

        import asyncio

        while self.is_running:
            try:
                # 从调度器获取任务（同步调用异步方法）
                task = asyncio.run(self.task_scheduler.dequeue_task())

                if task:
                    # 执行任务
                    self._execute_task(task)
                else:
                    # 没有任务，短暂休眠
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"工作线程出错: {e}")
                time.sleep(1)

    def _execute_task(self, task: Task) -> None:
        """
        执行任务

        Args:
            task: 任务对象
        """
        try:
            logger.debug(f"执行任务: {task.id}, 类型: {task.task_type}")

            # 更新任务状态
            self.task_monitor.update_task_status(task.id, "running")

            # 委托给执行器
            success = self.task_executor.execute_task(task)

            if success:
                self.task_monitor.update_task_status(task.id, "completed", progress=1.0)
                with self.lock:
                    self.stats["completed_tasks"] += 1
            else:
                self.task_monitor.update_task_status(task.id, "failed")
                with self.lock:
                    self.stats["failed_tasks"] += 1

        except Exception as e:
            logger.error(f"执行任务失败 {task.id}: {e}")
            self.task_monitor.update_task_status(task.id, "failed")
            with self.lock:
                self.stats["failed_tasks"] += 1

    def register_task_handler(self, task_type: str, handler: Callable) -> bool:
        """
        注册任务处理器

        Args:
            task_type: 任务类型
            handler: 处理函数

        Returns:
            是否注册成功
        """
        self.task_handlers[task_type] = handler
        return self.task_executor.register_handler(task_type, handler)

    def cancel_all_tasks(self, cancel_running: bool = False) -> Dict[str, Any]:
        """
        取消所有任务

        Args:
            cancel_running: 是否取消运行中的任务

        Returns:
            取消结果统计
        """
        try:
            all_tasks = self.task_monitor.get_all_tasks()

            cancelled = 0
            failed = 0

            for task_id, task in all_tasks.items():
                status = task.status if hasattr(task, "status") else "pending"

                # 只取消待处理和运行中的任务，除非指定 cancel_running
                if status == "pending" or (cancel_running and status == "running"):
                    try:
                        success = self.cancel_task(task_id)
                        if success:
                            cancelled += 1
                        else:
                            failed += 1
                    except Exception as e:
                        logger.error(f"取消任务失败 {task_id}: {e}")
                        failed += 1

            logger.info(f"取消所有任务完成: 成功={cancelled}, 失败={failed}")

            return {
                "cancelled": cancelled,
                "failed": failed,
                "total": cancelled + failed,
            }

        except Exception as e:
            logger.error(f"取消所有任务失败: {e}")
            return {"cancelled": 0, "failed": 0, "error": str(e)}

    def cancel_tasks_by_type(
        self, task_type: str, cancel_running: bool = False
    ) -> Dict[str, Any]:
        """
        按类型取消任务

        Args:
            task_type: 任务类型
            cancel_running: 是否取消运行中的任务

        Returns:
            取消结果统计
        """
        try:
            all_tasks = self.task_monitor.get_all_tasks()

            cancelled = 0
            failed = 0

            for task_id, task in all_tasks.items():
                # 检查任务类型
                current_task_type = (
                    task.task_type if hasattr(task, "task_type") else "unknown"
                )
                if current_task_type != task_type:
                    continue

                status = task.status if hasattr(task, "status") else "pending"

                # 只取消待处理和运行中的任务，除非指定 cancel_running
                if status == "pending" or (cancel_running and status == "running"):
                    try:
                        success = self.cancel_task(task_id)
                        if success:
                            cancelled += 1
                        else:
                            failed += 1
                    except Exception as e:
                        logger.error(f"取消任务失败 {task_id}: {e}")
                        failed += 1

            logger.info(
                f"按类型取消任务完成 ({task_type}): 成功={cancelled}, 失败={failed}"
            )

            return {
                "cancelled": cancelled,
                "failed": failed,
                "total": cancelled + failed,
                "task_type": task_type,
            }

        except Exception as e:
            logger.error(f"按类型取消任务失败 ({task_type}): {e}")
            return {
                "cancelled": 0,
                "failed": 0,
                "task_type": task_type,
                "error": str(e),
            }

    def update_task_priority(self, task_id: str, new_priority: int) -> bool:
        """
        更新任务优先级

        Args:
            task_id: 任务ID
            new_priority: 新优先级

        Returns:
            是否成功更新
        """
        try:
            # 从监控器获取任务
            task = self.task_monitor.get_task(task_id)
            if not task:
                logger.warning(f"任务不存在: {task_id}")
                return False

            # 只能更新待处理任务的优先级
            if hasattr(task, "status") and task.status != "pending":
                logger.warning(
                    f"只能更新待处理任务的优先级: {task_id} (当前状态: {task.status})"
                )
                return False

            # 更新任务优先级
            if hasattr(task, "priority"):
                task.priority = new_priority
                logger.info(f"任务优先级已更新: {task_id} -> {new_priority}")
                return True
            else:
                logger.warning(f"任务对象不支持优先级更新: {task_id}")
                return False

        except Exception as e:
            logger.error(f"更新任务优先级失败 {task_id}: {e}")
            return False

    def batch_update_priority(
        self, task_ids: List[str], new_priority: int
    ) -> Dict[str, Any]:
        """
        批量更新任务优先级

        Args:
            task_ids: 任务ID列表
            new_priority: 新优先级

        Returns:
            更新结果统计
        """
        try:
            updated = 0
            failed = 0

            for task_id in task_ids:
                if self.update_task_priority(task_id, new_priority):
                    updated += 1
                else:
                    failed += 1

            logger.info(f"批量更新优先级完成: 成功={updated}, 失败={failed}")

            return {"updated": updated, "failed": failed, "total": updated + failed}

        except Exception as e:
            logger.error(f"批量更新优先级失败: {e}")
            return {"updated": 0, "failed": len(task_ids), "error": str(e)}

    def batch_cancel_tasks(
        self, task_ids: List[str], cancel_running: bool = False
    ) -> Dict[str, Any]:
        """
        批量取消任务

        Args:
            task_ids: 任务ID列表
            cancel_running: 是否取消运行中的任务

        Returns:
            取消结果统计
        """
        try:
            cancelled = 0
            failed = 0

            for task_id in task_ids:
                task = self.task_monitor.get_task(task_id)
                if not task:
                    failed += 1
                    continue

                status = task.status if hasattr(task, "status") else "pending"

                if status == "pending" or (cancel_running and status == "running"):
                    if self.cancel_task(task_id):
                        cancelled += 1
                    else:
                        failed += 1
                else:
                    failed += 1

            logger.info(f"批量取消任务完成: 成功={cancelled}, 失败={failed}")

            return {
                "cancelled": cancelled,
                "failed": failed,
                "total": cancelled + failed,
            }

        except Exception as e:
            logger.error(f"批量取消任务失败: {e}")
            return {"cancelled": 0, "failed": len(task_ids), "error": str(e)}

    def get_task_dependencies(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务依赖信息

        Args:
            task_id: 任务ID

        Returns:
            依赖信息字典
        """
        try:
            task = self.task_monitor.get_task(task_id)
            if not task:
                return {
                    "task_id": task_id,
                    "exists": False,
                    "depends_on": [],
                    "dependent_tasks": [],
                }

            depends_on = getattr(task, "depends_on", [])

            # 查找依赖此任务的其他任务
            all_tasks = self.task_monitor.get_all_tasks()
            dependent_tasks = []

            for other_task_id, other_task in all_tasks.items():
                other_depends_on = getattr(other_task, "depends_on", [])
                if task_id in other_depends_on:
                    dependent_tasks.append(other_task_id)

            return {
                "task_id": task_id,
                "exists": True,
                "depends_on": depends_on,
                "dependent_tasks": dependent_tasks,
                "dependency_count": len(depends_on),
                "dependent_count": len(dependent_tasks),
            }

        except Exception as e:
            logger.error(f"获取任务依赖信息失败 {task_id}: {e}")
            return {"task_id": task_id, "exists": False, "error": str(e)}

    def check_task_dependencies(self, task_id: str) -> bool:
        """
        检查任务依赖是否都已满足

        Args:
            task_id: 任务ID

        Returns:
            是否所有依赖都已满足
        """
        try:
            task = self.task_monitor.get_task(task_id)
            if not task:
                return False

            depends_on = getattr(task, "depends_on", [])

            if not depends_on:
                return True

            # 检查所有依赖任务是否已完成
            for dep_task_id in depends_on:
                dep_task = self.task_monitor.get_task(dep_task_id)
                if not dep_task:
                    return False

                dep_status = getattr(dep_task, "status", "pending")
                if dep_status != "completed":
                    return False

            return True

        except Exception as e:
            logger.error(f"检查任务依赖失败 {task_id}: {e}")
            return False

    def set_file_type_priority(self, file_type: str, priority_level: str) -> bool:
        """
        设置文件类型优先级

        Args:
            file_type: 文件类型（video/audio/image）
            priority_level: 优先级级别（high/medium/low）

        Returns:
            是否成功设置
        """
        try:
            if file_type not in self.file_type_priority:
                logger.warning(f"不支持的文件类型: {file_type}")
                return False

            if priority_level not in self.priority_mapping:
                logger.warning(f"不支持的优先级级别: {priority_level}")
                return False

            self.file_type_priority[file_type] = priority_level
            logger.info(f"文件类型优先级已更新: {file_type} -> {priority_level}")
            return True

        except Exception as e:
            logger.error(f"设置文件类型优先级失败: {e}")
            return False

    def get_file_type_priority(self, file_type: str) -> int:
        """
        获取文件类型优先级

        Args:
            file_type: 文件类型（video/audio/image）

        Returns:
            优先级（1-11）
        """
        try:
            priority_level = self.file_type_priority.get(file_type, "medium")
            return self.priority_mapping.get(priority_level, 5)

        except Exception as e:
            logger.error(f"获取文件类型优先级失败: {e}")
            return 5

    def set_priority_settings(self, settings: Dict[str, str]) -> bool:
        """
        批量设置优先级配置

        Args:
            settings: 优先级设置字典，例如 {'video': 'high', 'audio': 'medium', 'image': 'low'}

        Returns:
            是否成功设置
        """
        try:
            for file_type, priority_level in settings.items():
                if not self.set_file_type_priority(file_type, priority_level):
                    logger.warning(
                        f"设置文件类型优先级失败: {file_type} -> {priority_level}"
                    )

            logger.info(f"优先级设置已批量更新: {settings}")
            return True

        except Exception as e:
            logger.error(f"批量设置优先级失败: {e}")
            return False

    def get_priority_settings(self) -> Dict[str, str]:
        """
        获取当前优先级设置

        Returns:
            优先级设置字典
        """
        return self.file_type_priority.copy()

    def get_task_priority_by_type(self, task_type: str, base_priority: int = 5) -> int:
        """
        根据任务类型获取优先级

        Args:
            task_type: 任务类型（例如 video_embed, audio_embed, image_embed）
            base_priority: 基础优先级

        Returns:
            优化后的优先级
        """
        try:
            file_type = self.task_type_to_file_type.get(task_type)

            if file_type:
                return self.get_file_type_priority(file_type)

            return base_priority

        except Exception as e:
            logger.error(f"获取任务类型优先级失败: {e}")
            return base_priority

    def update_all_task_priorities(self) -> bool:
        """
        更新所有任务的优先级（当优先级配置变更时调用）

        Returns:
            是否成功更新
        """
        try:
            all_tasks = self.task_monitor.get_all_tasks()
            updated_count = 0

            for task_id, task in all_tasks.items():
                task_type = getattr(task, "task_type", "unknown")
                base_priority = getattr(task, "priority", 5)

                new_priority = self.get_task_priority_by_type(task_type, base_priority)

                if new_priority != base_priority:
                    task.priority = new_priority
                    updated_count += 1

            logger.info(f"已更新 {updated_count} 个任务的优先级")
            return True

        except Exception as e:
            logger.error(f"更新任务优先级失败: {e}")
            return False

        except Exception as e:
            logger.error(f"检查任务依赖失败 {task_id}: {e}")
            return False

    def get_tasks_by_file(self, file_id: str) -> List[Dict[str, Any]]:
        """
        获取文件的所有任务

        Args:
            file_id: 文件ID

        Returns:
            任务列表
        """
        try:
            all_tasks = self.task_monitor.get_all_tasks()
            file_tasks = []

            for task_id, task in all_tasks.items():
                task_file_id = getattr(task, "file_id", None)
                if task_file_id == file_id:
                    if hasattr(task, "to_dict"):
                        file_tasks.append(task.to_dict())
                    else:
                        file_tasks.append(
                            {
                                "id": getattr(task, "id", task_id),
                                "task_type": getattr(task, "task_type", "unknown"),
                                "status": getattr(task, "status", "unknown"),
                                "priority": getattr(task, "priority", 5),
                            }
                        )

            return file_tasks

        except Exception as e:
            logger.error(f"获取文件任务失败 {file_id}: {e}")
            return []

    def get_file_task_summary(self, file_id: str) -> Dict[str, Any]:
        """
        获取文件任务摘要

        Args:
            file_id: 文件ID

        Returns:
            任务摘要
        """
        try:
            tasks = self.get_tasks_by_file(file_id)

            summary = {
                "file_id": file_id,
                "total_tasks": len(tasks),
                "pending": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
            }

            for task in tasks:
                status = task.get("status", "unknown")
                if status in summary:
                    summary[status] += 1

            # 计算进度
            if summary["total_tasks"] > 0:
                summary["progress"] = summary["completed"] / summary["total_tasks"]
            else:
                summary["progress"] = 0.0

            return summary

        except Exception as e:
            logger.error(f"获取文件任务摘要失败 {file_id}: {e}")
            return {"file_id": file_id, "error": str(e)}

    def get_thread_pool_status(self) -> Dict[str, Any]:
        """
        获取线程池状态

        Returns:
            线程池状态字典，包含：
            - max_workers: 最大线程数
            - active_threads: 活跃线程数（运行中的任务）
            - idle_threads: 空闲线程数
            - load_percentage: 负载百分比
        """
        try:
            all_tasks = self.task_monitor.get_all_tasks()

            active_threads = 0
            for task_id, task in all_tasks.items():
                if task.status == "running":
                    active_threads += 1

            max_workers = self.task_config.get("max_workers", 8)
            idle_threads = max(0, max_workers - active_threads)
            load_percentage = (
                int((active_threads / max_workers * 100)) if max_workers > 0 else 0
            )

            return {
                "max_workers": max_workers,
                "active_threads": active_threads,
                "idle_threads": idle_threads,
                "load_percentage": load_percentage,
            }

        except Exception as e:
            logger.error(f"获取线程池状态失败: {e}")
            return {
                "max_workers": 8,
                "active_threads": 0,
                "idle_threads": 8,
                "load_percentage": 0,
            }
