"""
优化后的并发管理器
基于系统负载和可用资源动态调整并发任务数量
"""

import psutil
import threading
import time
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SystemResources:
    """系统资源信息"""

    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    gpu_memory_available_gb: float
    gpu_memory_percent: float
    disk_io_read_mb_per_sec: float
    disk_io_write_mb_per_sec: float
    timestamp: float


@dataclass
class ConcurrencyConfig:
    """并发配置"""

    min_concurrent: int = 1
    max_concurrent: int = 8
    concurrency_mode: str = "dynamic"  # "static" 或 "dynamic"
    base_concurrent_tasks: int = 4  # 基础并发任务数（静态模式使用）
    target_cpu_percent: float = 70.0
    target_memory_percent: float = 70.0
    target_gpu_memory_percent: float = 80.0
    target_disk_io_mb_per_sec: float = 100.0  # 磁盘IO目标阈值（MB/s）
    adjustment_interval: float = 5.0
    adjustment_step: int = 1
    enable_gpu_monitoring: bool = True
    enable_disk_io_monitoring: bool = True


class OptimizedConcurrencyManager:
    """优化后的并发管理器"""

    def __init__(self, config: ConcurrencyConfig, device: str = "cpu"):
        """
        初始化并发管理器

        Args:
            config: 并发配置
            device: 设备类型（cuda/cpu），从配置文件读取
        """
        self.config = config
        self.device = device  # 从配置文件读取

        # 根据并发模式设置初始并发数
        if config.concurrency_mode == "static":
            self.current_concurrent = config.base_concurrent_tasks
            self.target_concurrent = config.base_concurrent_tasks
        else:  # dynamic mode
            self.current_concurrent = config.min_concurrent
            self.target_concurrent = config.min_concurrent

        # 资源监控
        self.last_resources: Optional[SystemResources] = None
        self.resource_history: list[SystemResources] = []
        self.max_history_size = 10

        # 控制线程
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        # GPU监控（根据device参数决定）
        self.has_gpu = device == "cuda"

        logger.info(
            f"优化并发管理器初始化完成: mode={config.concurrency_mode}, "
            f"min={config.min_concurrent}, max={config.max_concurrent}, "
            f"current={self.current_concurrent}, device={self.device}"
        )

    def initialize(self) -> bool:
        """
        初始化并发管理器，启动监控线程

        Returns:
            是否成功启动
        """
        try:
            if self.config.concurrency_mode == "dynamic":
                self.is_running = True
                self.monitor_thread = threading.Thread(
                    target=self._monitor_loop, daemon=True
                )
                self.monitor_thread.start()
                logger.info("并发管理器监控线程启动")

            return True
        except Exception as e:
            logger.error(f"并发管理器初始化失败: {e}")
            return False

    def shutdown(self) -> None:
        """关闭并发管理器"""
        logger.info("正在关闭优化并发管理器...")

        self.is_running = False

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)

        logger.info("优化并发管理器已关闭")

    def _monitor_loop(self) -> None:
        """监控循环"""
        logger.info("并发管理器监控循环启动")

        while self.is_running:
            try:
                # 获取当前系统资源
                resources = self._get_current_resources()

                # 更新资源历史
                self.resource_history.append(resources)
                if len(self.resource_history) > self.max_history_size:
                    self.resource_history.pop(0)

                # 更新最后的资源信息
                self.last_resources = resources

                # 动态调整并发数
                if self.config.concurrency_mode == "dynamic":
                    self._adjust_concurrent_count(resources)

                # 等待下一个调整周期
                time.sleep(self.config.adjustment_interval)

            except Exception as e:
                logger.error(f"并发管理器监控循环错误: {e}")
                time.sleep(1.0)

    def _get_current_resources(self) -> SystemResources:
        """获取当前系统资源信息"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1.0)

        # 内存使用率和可用内存
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)

        # GPU内存信息（如果可用）
        gpu_memory_available_gb = 0.0
        gpu_memory_percent = 0.0

        if self.has_gpu:
            gpu_memory_available_gb, gpu_memory_percent = self._get_gpu_info()

        # 磁盘IO（简化获取）
        disk_io_read_mb_per_sec = 0.0
        disk_io_write_mb_per_sec = 0.0

        if self.config.enable_disk_io_monitoring:
            # 这里可以实现磁盘IO监控，为简化暂时返回0
            pass

        return SystemResources(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            gpu_memory_available_gb=gpu_memory_available_gb,
            gpu_memory_percent=gpu_memory_percent,
            disk_io_read_mb_per_sec=disk_io_read_mb_per_sec,
            disk_io_write_mb_per_sec=disk_io_write_mb_per_sec,
            timestamp=time.time(),
        )

    def _get_gpu_info(self) -> tuple[float, float]:
        """
        获取GPU信息

        Returns:
            (GPU可用内存GB, GPU内存使用率)
        """
        # 只有在device为cuda时才获取GPU信息
        if not self.has_gpu:
            return 0.0, 0.0

        try:
            import torch

            # 获取第一个GPU的信息
            device = torch.cuda.current_device()
            total_memory = torch.cuda.get_device_properties(device).total_memory / (
                1024**3
            )
            allocated_memory = torch.cuda.memory_allocated(device) / (1024**3)
            reserved_memory = torch.cuda.memory_reserved(device) / (1024**3)

            available_memory = total_memory - reserved_memory
            memory_percent = (
                (allocated_memory / total_memory) * 100 if total_memory > 0 else 0.0
            )

            return available_memory, memory_percent
        except ImportError:
            logger.warning("PyTorch未安装，无法获取GPU信息")
            return 0.0, 0.0
        except Exception as e:
            logger.error(f"获取GPU信息失败: {e}")
            return 0.0, 0.0

    def _adjust_concurrent_count(self, resources: SystemResources) -> None:
        """根据资源使用情况调整并发数"""
        with self.lock:
            # 检查各个资源指标
            cpu_too_high = resources.cpu_percent > self.config.target_cpu_percent
            memory_too_high = (
                resources.memory_percent > self.config.target_memory_percent
            )
            gpu_too_high = (
                self.has_gpu
                and resources.gpu_memory_percent > self.config.target_gpu_memory_percent
            )

            current_concurrent = self.current_concurrent

            # 如果资源使用过高，减少并发数
            if cpu_too_high or memory_too_high or gpu_too_high:
                if current_concurrent > self.config.min_concurrent:
                    self.current_concurrent = max(
                        self.config.min_concurrent,
                        current_concurrent - self.config.adjustment_step,
                    )
                    logger.debug(
                        f"资源使用过高，减少并发数: {current_concurrent} -> {self.current_concurrent}"
                    )

            # 如果资源使用适中且有容量，增加并发数
            else:
                cpu_ok = resources.cpu_percent < self.config.target_cpu_percent * 0.8
                memory_ok = (
                    resources.memory_percent < self.config.target_memory_percent * 0.8
                )
                gpu_ok = (
                    not self.has_gpu
                    or resources.gpu_memory_percent
                    < self.config.target_gpu_memory_percent * 0.8
                )

                if cpu_ok and memory_ok and gpu_ok:
                    if current_concurrent < self.config.max_concurrent:
                        self.current_concurrent = min(
                            self.config.max_concurrent,
                            current_concurrent + self.config.adjustment_step,
                        )
                        logger.debug(
                            f"资源使用正常，增加并发数: {current_concurrent} -> {self.current_concurrent}"
                        )

    def get_current_concurrent(self) -> int:
        """
        获取当前并发数

        Returns:
            当前并发数
        """
        with self.lock:
            return self.current_concurrent

    def get_target_concurrent(self) -> int:
        """
        获取目标并发数（考虑动态调整）

        Returns:
            目标并发数
        """
        with self.lock:
            return self.target_concurrent

    def get_resource_usage(self) -> Optional[SystemResources]:
        """
        获取最后的资源使用情况

        Returns:
            系统资源信息或None
        """
        with self.lock:
            return self.last_resources

    def get_resource_history(self) -> list[SystemResources]:
        """
        获取资源使用历史

        Returns:
            资源使用历史列表
        """
        with self.lock:
            return self.resource_history.copy()

    def set_concurrent_count(self, count: int) -> bool:
        """
        设置并发数（主要用于静态模式）

        Args:
            count: 并发数

        Returns:
            是否设置成功
        """
        if count < self.config.min_concurrent or count > self.config.max_concurrent:
            logger.warning(
                f"并发数 {count} 超出配置范围 [{self.config.min_concurrent}, {self.config.max_concurrent}]"
            )
            return False

        with self.lock:
            self.current_concurrent = count
            self.target_concurrent = count
            logger.info(f"设置并发数为 {count}")
            return True

    def get_config(self) -> ConcurrencyConfig:
        """
        获取配置

        Returns:
            并发配置
        """
        return self.config

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        with self.lock:
            resources = self.last_resources
            if resources:
                return {
                    "current_concurrent": self.current_concurrent,
                    "target_concurrent": self.target_concurrent,
                    "cpu_percent": resources.cpu_percent,
                    "memory_percent": resources.memory_percent,
                    "memory_available_gb": resources.memory_available_gb,
                    "gpu_memory_percent": resources.gpu_memory_percent,
                    "gpu_memory_available_gb": resources.gpu_memory_available_gb,
                    "resource_history_count": len(self.resource_history),
                }
            else:
                return {
                    "current_concurrent": self.current_concurrent,
                    "target_concurrent": self.target_concurrent,
                    "resource_history_count": len(self.resource_history),
                }

    def force_adjustment(self) -> None:
        """强制进行一次并发数调整"""
        if self.config.concurrency_mode == "dynamic":
            resources = self._get_current_resources()
            self._adjust_concurrent_count(resources)
            logger.debug("强制调整并发数完成")
