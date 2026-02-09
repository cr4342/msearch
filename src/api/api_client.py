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
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        logger.info(f"API客户端初始化完成: {base_url}")

    # ==================== 搜索相关API ====================

    def search_text(self, query: str, top_k: int = 20, threshold: float = None) -> Dict[str, Any]:
        """
        文本搜索

        Args:
            query: 搜索查询
            top_k: 返回结果数量
            threshold: 相似度阈值

        Returns:
            搜索结果
        """
        try:
            data = {"query": query, "top_k": top_k}
            if threshold is not None:
                data["threshold"] = threshold

            response = self.session.post(f"{self.base_url}/search/text", json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"文本搜索失败: {e}")
            return {"status": "error", "error": str(e), "results": []}
        except Exception as e:
            logger.error(f"文本搜索失败: {e}")
            return {"status": "error", "error": str(e), "results": []}

    def search_image(self, image_path: str, top_k: int = 20) -> Dict[str, Any]:
        """
        图像搜索

        Args:
            image_path: 图像文件路径
            top_k: 返回结果数量

        Returns:
            搜索结果
        """
        try:
            from pathlib import Path

            # 使用文件上传方式
            with open(image_path, "rb") as f:
                files = {"file": (Path(image_path).name, f)}
                data = {"top_k": str(top_k)}
                response = self.session.post(
                    f"{self.base_url}/search/image", files=files, data=data
                )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"图像搜索失败: {e}")
            return {"status": "error", "error": str(e), "results": []}
        except Exception as e:
            logger.error(f"图像搜索失败: {e}")
            return {"status": "error", "error": str(e), "results": []}

    def search_audio(self, audio_path: str, top_k: int = 20) -> Dict[str, Any]:
        """
        音频搜索

        Args:
            audio_path: 音频文件路径
            top_k: 返回结果数量

        Returns:
            搜索结果
        """
        try:
            from pathlib import Path

            with open(audio_path, "rb") as f:
                files = {"file": (Path(audio_path).name, f)}
                data = {"top_k": str(top_k)}
                response = self.session.post(
                    f"{self.base_url}/search/audio", files=files, data=data
                )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"音频搜索失败: {e}")
            return {"status": "error", "error": str(e), "results": []}
        except Exception as e:
            logger.error(f"音频搜索失败: {e}")
            return {"status": "error", "error": str(e), "results": []}

    # ==================== 索引相关API ====================

    def index_file(self, file_path: str) -> bool:
        """
        索引单个文件

        Args:
            file_path: 文件路径

        Returns:
            是否成功
        """
        try:
            response = self.session.post(
                f"{self.base_url}/index/file", data={"file_path": file_path}
            )
            response.raise_for_status()
            logger.info(f"已提交索引任务: {file_path}")
            return True
        except requests.RequestException as e:
            logger.error(f"索引文件失败 {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"索引文件失败 {file_path}: {e}")
            return False

    def index_directory(self, directory: str, recursive: bool = True) -> bool:
        """
        索引目录

        Args:
            directory: 目录路径
            recursive: 是否递归

        Returns:
            是否成功
        """
        try:
            response = self.session.post(
                f"{self.base_url}/index/directory",
                data={"directory": directory, "recursive": str(recursive).lower()},
            )
            response.raise_for_status()
            logger.info(f"已提交目录索引任务: {directory}")
            return True
        except requests.RequestException as e:
            logger.error(f"索引目录失败 {directory}: {e}")
            return False
        except Exception as e:
            logger.error(f"索引目录失败 {directory}: {e}")
            return False

    def reindex_all(self) -> bool:
        """
        重新索引所有文件

        Returns:
            是否成功
        """
        try:
            response = self.session.post(f"{self.base_url}/index/reindex-all")
            response.raise_for_status()
            logger.info("已启动全量重新索引")
            return True
        except requests.RequestException as e:
            logger.error(f"重新索引失败: {e}")
            return False
        except Exception as e:
            logger.error(f"重新索引失败: {e}")
            return False

    def get_index_status(self) -> Dict[str, Any]:
        """
        获取索引状态

        Returns:
            索引状态信息
        """
        try:
            response = self.session.get(f"{self.base_url}/index/status")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"获取索引状态失败: {e}")
            return {}
        except Exception as e:
            logger.error(f"获取索引状态失败: {e}")
            return {}

    # ==================== 文件相关API ====================

    def get_files_list(
        self, file_type: str = None, indexed_only: bool = False, limit: int = 100, offset: int = 0
    ) -> Dict[str, Any]:
        """
        获取文件列表

        Args:
            file_type: 文件类型过滤
            indexed_only: 仅已索引文件
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            文件列表
        """
        try:
            params = {"indexed_only": indexed_only, "limit": limit, "offset": offset}
            if file_type:
                params["file_type"] = file_type

            response = self.session.get(f"{self.base_url}/files/list", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"获取文件列表失败: {e}")
            return {"files": [], "total_files": 0}
        except Exception as e:
            logger.error(f"获取文件列表失败: {e}")
            return {"files": [], "total_files": 0}

    def get_file_info(self, file_uuid: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息

        Args:
            file_uuid: 文件UUID

        Returns:
            文件信息或None
        """
        try:
            response = self.session.get(f"{self.base_url}/files/{file_uuid}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"获取文件信息失败 {file_uuid}: {e}")
            return None
        except Exception as e:
            logger.error(f"获取文件信息失败 {file_uuid}: {e}")
            return None

    def upload_file(self, file_path: str) -> Optional[str]:
        """
        上传文件

        Args:
            file_path: 文件路径

        Returns:
            上传后的文件路径或None
        """
        try:
            from pathlib import Path

            with open(file_path, "rb") as f:
                files = {"file": (Path(file_path).name, f)}
                response = self.session.post(f"{self.base_url}/files/upload", files=files)
            response.raise_for_status()
            data = response.json()
            return data.get("file_path")
        except requests.RequestException as e:
            logger.error(f"上传文件失败 {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"上传文件失败 {file_path}: {e}")
            return None

    def get_file_preview(self, file_path: str) -> Optional[bytes]:
        """
        获取文件预览

        Args:
            file_path: 文件路径

        Returns:
            预览数据或None
        """
        try:
            response = self.session.get(
                f"{self.base_url}/files/preview", params={"path": file_path}
            )
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            logger.error(f"获取文件预览失败 {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"获取文件预览失败 {file_path}: {e}")
            return None

    def get_file_thumbnail(self, thumbnail_path: str) -> Optional[bytes]:
        """
        获取文件缩略图

        Args:
            thumbnail_path: 缩略图路径

        Returns:
            缩略图数据或None
        """
        try:
            response = self.session.get(
                f"{self.base_url}/files/thumbnail", params={"path": thumbnail_path}
            )
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            logger.error(f"获取缩略图失败 {thumbnail_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"获取缩略图失败 {thumbnail_path}: {e}")
            return None

    # ==================== 任务管理相关API ====================

    def get_tasks(
        self, status: str = None, task_type: str = None, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取任务列表

        Args:
            status: 状态过滤
            task_type: 任务类型过滤
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            任务列表
        """
        try:
            params = {"limit": limit, "offset": offset}
            if status:
                params["status"] = status
            if task_type:
                params["task_type"] = task_type

            response = self.session.get(f"{self.base_url}/tasks", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("tasks", [])
        except requests.RequestException as e:
            logger.error(f"获取任务列表失败: {e}")
            return []
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return []

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个任务

        Args:
            task_id: 任务ID

        Returns:
            任务信息或None
        """
        try:
            response = self.session.get(f"{self.base_url}/tasks/{task_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"获取任务失败 {task_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"获取任务失败 {task_id}: {e}")
            return None

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        try:
            response = self.session.delete(f"{self.base_url}/tasks/{task_id}")
            response.raise_for_status()
            logger.info(f"已取消任务: {task_id}")
            return True
        except requests.RequestException as e:
            logger.error(f"取消任务失败 {task_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"取消任务失败 {task_id}: {e}")
            return False

    def update_task_priority(self, task_id: str, priority: int) -> bool:
        """
        更新任务优先级

        Args:
            task_id: 任务ID
            priority: 优先级（1-10）

        Returns:
            是否成功
        """
        try:
            response = self.session.post(
                f"{self.base_url}/tasks/{task_id}/priority", data={"priority": str(priority)}
            )
            response.raise_for_status()
            logger.info(f"已更新任务优先级: {task_id} -> {priority}")
            return True
        except requests.RequestException as e:
            logger.error(f"更新任务优先级失败 {task_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"更新任务优先级失败 {task_id}: {e}")
            return False

    def pause_task(self, task_id: str) -> bool:
        """
        暂停任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        try:
            response = self.session.post(f"{self.base_url}/tasks/{task_id}/pause")
            response.raise_for_status()
            logger.info(f"已暂停任务: {task_id}")
            return True
        except requests.RequestException as e:
            logger.error(f"暂停任务失败 {task_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"暂停任务失败 {task_id}: {e}")
            return False

    def resume_task(self, task_id: str) -> bool:
        """
        恢复任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        try:
            response = self.session.post(f"{self.base_url}/tasks/{task_id}/resume")
            response.raise_for_status()
            logger.info(f"已恢复任务: {task_id}")
            return True
        except requests.RequestException as e:
            logger.error(f"恢复任务失败 {task_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"恢复任务失败 {task_id}: {e}")
            return False

    def retry_task(self, task_id: str) -> bool:
        """
        重试任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        try:
            response = self.session.post(f"{self.base_url}/tasks/{task_id}/retry")
            response.raise_for_status()
            logger.info(f"已重试任务: {task_id}")
            return True
        except requests.RequestException as e:
            logger.error(f"重试任务失败 {task_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"重试任务失败 {task_id}: {e}")
            return False

    def archive_task(self, task_id: str) -> bool:
        """
        归档任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        try:
            response = self.session.post(f"{self.base_url}/tasks/{task_id}/archive")
            response.raise_for_status()
            logger.info(f"已归档任务: {task_id}")
            return True
        except requests.RequestException as e:
            logger.error(f"归档任务失败 {task_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"归档任务失败 {task_id}: {e}")
            return False

    def get_task_stats(self) -> Dict[str, Any]:
        """
        获取任务统计

        Returns:
            任务统计信息
        """
        try:
            response = self.session.get(f"{self.base_url}/tasks/stats")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"获取任务统计失败: {e}")
            return {}
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {}

    def cancel_all_tasks(self, cancel_running: bool = False) -> bool:
        """
        取消所有任务

        Args:
            cancel_running: 是否取消运行中的任务

        Returns:
            是否成功
        """
        try:
            response = self.session.post(
                f"{self.base_url}/tasks/cancel-all", data={"cancel_running": str(cancel_running).lower()}
            )
            response.raise_for_status()
            logger.info("已取消所有任务")
            return True
        except requests.RequestException as e:
            logger.error(f"取消所有任务失败: {e}")
            return False
        except Exception as e:
            logger.error(f"取消所有任务失败: {e}")
            return False

    def cancel_tasks_by_type(self, task_type: str, cancel_running: bool = False) -> bool:
        """
        按类型取消任务

        Args:
            task_type: 任务类型
            cancel_running: 是否取消运行中的任务

        Returns:
            是否成功
        """
        try:
            response = self.session.post(
                f"{self.base_url}/tasks/cancel-by-type",
                data={"task_type": task_type, "cancel_running": str(cancel_running).lower()},
            )
            response.raise_for_status()
            logger.info(f"已取消类型为 {task_type} 的所有任务")
            return True
        except requests.RequestException as e:
            logger.error(f"按类型取消任务失败: {e}")
            return False
        except Exception as e:
            logger.error(f"按类型取消任务失败: {e}")
            return False

    def get_thread_pool_status(self) -> Dict[str, Any]:
        """
        获取线程池状态

        Returns:
            线程池状态
        """
        try:
            response = self.session.get(f"{self.base_url}/tasks/thread-pool/status")
            response.raise_for_status()
            data = response.json()
            return data.get("thread_pool", {})
        except requests.RequestException as e:
            logger.error(f"获取线程池状态失败: {e}")
            return {"max_workers": 8, "active_threads": 0, "idle_threads": 8, "load_percentage": 0}
        except Exception as e:
            logger.error(f"获取线程池状态失败: {e}")
            return {"max_workers": 8, "active_threads": 0, "idle_threads": 8, "load_percentage": 0}

    # ==================== 系统相关API ====================

    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息

        Returns:
            系统信息
        """
        try:
            response = self.session.get(f"{self.base_url}/system/info")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"获取系统信息失败: {e}")
            return {}
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return {}

    def get_system_stats(self) -> Dict[str, Any]:
        """
        获取系统统计

        Returns:
            系统统计信息
        """
        try:
            response = self.session.get(f"{self.base_url}/system/stats")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"获取系统统计失败: {e}")
            return {}
        except Exception as e:
            logger.error(f"获取系统统计失败: {e}")
            return {}

    def check_health(self) -> bool:
        """
        检查API健康状态

        Returns:
            是否健康
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get("status") == "healthy"
        except requests.RequestException:
            return False
        except Exception:
            return False

    # ==================== 向量存储相关API ====================

    def get_vector_stats(self) -> Dict[str, Any]:
        """
        获取向量存储统计

        Returns:
            向量统计信息
        """
        try:
            response = self.session.get(f"{self.base_url}/vector/stats")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"获取向量统计失败: {e}")
            return {}
        except Exception as e:
            logger.error(f"获取向量统计失败: {e}")
            return {}


# 全局API客户端实例
_api_client: Optional[APIClient] = None


def get_api_client(base_url: str = "http://localhost:8000/api/v1") -> APIClient:
    """
    获取全局API客户端实例

    Args:
        base_url: API基础URL

    Returns:
        API客户端实例
    """
    global _api_client
    if _api_client is None:
        _api_client = APIClient(base_url)
    return _api_client
