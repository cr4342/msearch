"""
API客户端
用于UI与后端API之间的通信
"""

import requests
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """API客户端"""

    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        """
        初始化API客户端

        Args:
            base_url: API基础URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        logger.info(f"API客户端初始化完成: {base_url}")

    def get_monitored_directories(self) -> List[Dict[str, Any]]:
        """
        获取监控目录列表

        Returns:
            监控目录列表
        """
        try:
            response = self.session.get(f"{self.base_url}/directories")
            response.raise_for_status()

            data = response.json()
            return data.get("directories", [])

        except requests.RequestException as e:
            logger.error(f"获取监控目录失败: {e}")
            return []
        except Exception as e:
            logger.error(f"解析监控目录响应失败: {e}")
            return []

    def add_monitored_directory(self, directory: str) -> bool:
        """
        添加监控目录

        Args:
            directory: 目录路径

        Returns:
            是否成功添加
        """
        try:
            response = self.session.post(
                f"{self.base_url}/directories", json={"path": directory}
            )
            response.raise_for_status()

            logger.info(f"已添加监控目录: {directory}")
            return True

        except requests.RequestException as e:
            logger.error(f"添加监控目录失败 {directory}: {e}")
            return False
        except Exception as e:
            logger.error(f"添加监控目录失败 {directory}: {e}")
            return False

    def remove_monitored_directory(self, directory: str) -> bool:
        """
        移除监控目录

        Args:
            directory: 目录路径

        Returns:
            是否成功移除
        """
        try:
            response = self.session.delete(
                f"{self.base_url}/directories", params={"path": directory}
            )
            response.raise_for_status()

            logger.info(f"已移除监控目录: {directory}")
            return True

        except requests.RequestException as e:
            logger.error(f"移除监控目录失败 {directory}: {e}")
            return False
        except Exception as e:
            logger.error(f"移除监控目录失败 {directory}: {e}")
            return False

    def pause_directory(self, directory: str) -> bool:
        """
        暂停监控目录

        Args:
            directory: 目录路径

        Returns:
            是否成功暂停
        """
        try:
            response = self.session.post(
                f"{self.base_url}/directories/pause", json={"path": directory}
            )
            response.raise_for_status()

            logger.info(f"已暂停监控目录: {directory}")
            return True

        except requests.RequestException as e:
            logger.error(f"暂停监控目录失败 {directory}: {e}")
            return False
        except Exception as e:
            logger.error(f"暂停监控目录失败 {directory}: {e}")
            return False

    def resume_directory(self, directory: str) -> bool:
        """
        恢复监控目录

        Args:
            directory: 目录路径

        Returns:
            是否成功恢复
        """
        try:
            response = self.session.post(
                f"{self.base_url}/directories/resume", json={"path": directory}
            )
            response.raise_for_status()

            logger.info(f"已恢复监控目录: {directory}")
            return True

        except requests.RequestException as e:
            logger.error(f"恢复监控目录失败 {directory}: {e}")
            return False
        except Exception as e:
            logger.error(f"恢复监控目录失败 {directory}: {e}")
            return False

    def get_file_stats(self) -> Dict[str, int]:
        """
        获取文件统计

        Returns:
            文件统计字典
        """
        try:
            response = self.session.get(f"{self.base_url}/stats/files")
            response.raise_for_status()

            data = response.json()
            return data.get("stats", {"total": 0, "image": 0, "video": 0, "audio": 0})

        except requests.RequestException as e:
            logger.error(f"获取文件统计失败: {e}")
            return {"total": 0, "image": 0, "video": 0, "audio": 0}
        except Exception as e:
            logger.error(f"解析文件统计响应失败: {e}")
            return {"total": 0, "image": 0, "video": 0, "audio": 0}

    def set_priority_settings(self, settings: Dict[str, str]) -> bool:
        """
        设置优先级配置

        Args:
            settings: 优先级设置字典，例如 {'video': 'high', 'audio': 'medium', 'image': 'low'}

        Returns:
            是否成功设置
        """
        try:
            response = self.session.put(
                f"{self.base_url}/tasks/priority", json=settings
            )
            response.raise_for_status()

            logger.info(f"优先级设置已更新: {settings}")
            return True

        except requests.RequestException as e:
            logger.error(f"设置优先级失败: {e}")
            return False
        except Exception as e:
            logger.error(f"设置优先级失败: {e}")
            return False

    def get_priority_settings(self) -> Dict[str, str]:
        """
        获取优先级配置

        Returns:
            优先级设置字典
        """
        try:
            response = self.session.get(f"{self.base_url}/tasks/priority")
            response.raise_for_status()

            data = response.json()
            return data.get(
                "settings", {"video": "medium", "audio": "medium", "image": "medium"}
            )

        except requests.RequestException as e:
            logger.error(f"获取优先级设置失败: {e}")
            return {"video": "medium", "audio": "medium", "image": "medium"}
        except Exception as e:
            logger.error(f"解析优先级设置响应失败: {e}")
            return {"video": "medium", "audio": "medium", "image": "medium"}

    def pause_tasks(self) -> bool:
        """
        暂停所有任务

        Returns:
            是否成功暂停
        """
        try:
            response = self.session.post(f"{self.base_url}/tasks/pause")
            response.raise_for_status()

            logger.info("已暂停所有任务")
            return True

        except requests.RequestException as e:
            logger.error(f"暂停任务失败: {e}")
            return False
        except Exception as e:
            logger.error(f"暂停任务失败: {e}")
            return False

    def resume_tasks(self) -> bool:
        """
        恢复所有任务

        Returns:
            是否成功恢复
        """
        try:
            response = self.session.post(f"{self.base_url}/tasks/resume")
            response.raise_for_status()

            logger.info("已恢复所有任务")
            return True

        except requests.RequestException as e:
            logger.error(f"恢复任务失败: {e}")
            return False
        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
            return False

    def cancel_tasks(self) -> bool:
        """
        取消所有任务

        Returns:
            是否成功取消
        """
        try:
            response = self.session.delete(f"{self.base_url}/tasks")
            response.raise_for_status()

            logger.info("已取消所有任务")
            return True

        except requests.RequestException as e:
            logger.error(f"取消任务失败: {e}")
            return False
        except Exception as e:
            logger.error(f"取消任务失败: {e}")
            return False

    def trigger_full_scan(self) -> bool:
        """
        触发全量扫描

        Returns:
            是否成功触发
        """
        try:
            response = self.session.post(f"{self.base_url}/scan/full")
            response.raise_for_status()

            logger.info("已启动全量扫描")
            return True

        except requests.RequestException as e:
            logger.error(f"触发全量扫描失败: {e}")
            return False
        except Exception as e:
            logger.error(f"触发全量扫描失败: {e}")
            return False

    def trigger_directory_scan(self, directory: str) -> bool:
        """
        触发目录扫描

        Args:
            directory: 目录路径

        Returns:
            是否成功触发
        """
        try:
            response = self.session.post(
                f"{self.base_url}/scan/directory", json={"path": directory}
            )
            response.raise_for_status()

            logger.info(f"已启动目录扫描: {directory}")
            return True

        except requests.RequestException as e:
            logger.error(f"触发目录扫描失败 {directory}: {e}")
            return False
        except Exception as e:
            logger.error(f"触发目录扫描失败 {directory}: {e}")
            return False

    def trigger_vectorization(
        self,
        file_type: Optional[str] = None,
        concurrent: int = 4,
        use_gpu: bool = False,
    ) -> bool:
        """
        触发向量化

        Args:
            file_type: 文件类型（image/video/audio）
            concurrent: 并发数
            use_gpu: 是否使用GPU

        Returns:
            是否成功触发
        """
        try:
            response = self.session.post(
                f"{self.base_url}/vectorize",
                json={
                    "file_type": file_type,
                    "concurrent": concurrent,
                    "use_gpu": use_gpu,
                },
            )
            response.raise_for_status()

            logger.info(f"已启动向量化: {file_type}")
            return True

        except requests.RequestException as e:
            logger.error(f"触导向量化失败: {e}")
            return False
        except Exception as e:
            logger.error(f"触导向量化失败: {e}")
            return False

    def get_tasks(self) -> List[Dict[str, Any]]:
        """
        获取任务列表

        Returns:
            任务列表
        """
        try:
            response = self.session.get(f"{self.base_url}/tasks")
            response.raise_for_status()

            data = response.json()
            return data.get("tasks", [])

        except requests.RequestException as e:
            logger.error(f"获取任务列表失败: {e}")
            return []
        except Exception as e:
            logger.error(f"解析任务列表响应失败: {e}")
            return []

    def get_task_stats(self) -> Dict[str, int]:
        """
        获取任务统计

        Returns:
            任务统计字典
        """
        try:
            response = self.session.get(f"{self.base_url}/tasks/stats")
            response.raise_for_status()

            data = response.json()
            return data.get(
                "stats", {"pending": 0, "running": 0, "completed": 0, "failed": 0}
            )

        except requests.RequestException as e:
            logger.error(f"获取任务统计失败: {e}")
            return {"pending": 0, "running": 0, "completed": 0, "failed": 0}
        except Exception as e:
            logger.error(f"解析任务统计响应失败: {e}")
            return {"pending": 0, "running": 0, "completed": 0, "failed": 0}

    def get_thread_pool_status(self) -> Dict[str, int]:
        """
        获取线程池状态

        Returns:
            线程池状态字典，包含：
            - max_workers: 最大线程数
            - active_threads: 活跃线程数
            - idle_threads: 空闲线程数
            - load_percentage: 负载百分比
        """
        try:
            response = self.session.get(f"{self.base_url}/tasks/thread-pool/status")
            response.raise_for_status()

            data = response.json()
            return data.get(
                "thread_pool",
                {
                    "max_workers": 8,
                    "active_threads": 0,
                    "idle_threads": 8,
                    "load_percentage": 0,
                },
            )

        except requests.RequestException as e:
            logger.error(f"获取线程池状态失败: {e}")
            return {
                "max_workers": 8,
                "active_threads": 0,
                "idle_threads": 8,
                "load_percentage": 0,
            }
        except Exception as e:
            logger.error(f"解析线程池状态响应失败: {e}")
            return {
                "max_workers": 8,
                "active_threads": 0,
                "idle_threads": 8,
                "load_percentage": 0,
            }

    def update_resource_config(self, concurrent: int, use_gpu: bool) -> bool:
        """
        更新资源配置

        Args:
            concurrent: 并发数
            use_gpu: 是否使用GPU

        Returns:
            是否成功更新
        """
        try:
            response = self.session.put(
                f"{self.base_url}/config/resources",
                json={"concurrent": concurrent, "use_gpu": use_gpu},
            )
            response.raise_for_status()

            logger.info(
                f"资源配置已更新: 并发={concurrent}, GPU={'启用' if use_gpu else '禁用'}"
            )
            return True

        except requests.RequestException as e:
            logger.error(f"更新资源配置失败: {e}")
            return False
        except Exception as e:
            logger.error(f"更新资源配置失败: {e}")
            return False
