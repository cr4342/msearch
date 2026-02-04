"""
API Client for msearch FastAPI server
Handles HTTP requests to the backend API
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class APIClient:
    """API客户端，用于调用FastAPI服务器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化API客户端

        Args:
            base_url: API服务器基础URL
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = 30  # 30秒超时

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        发送HTTP请求

        Args:
            method: 请求方法 (GET, POST, PUT, DELETE)
            endpoint: API端点
            **kwargs: 其他参数

        Returns:
            API响应数据

        Raises:
            Exception: 请求失败时抛出异常
        """
        url = f"{self.base_url}{endpoint}"

        try:
            logger.debug(f"发送{method}请求到: {url}")

            response = self.session.request(
                method=method, url=url, timeout=self.timeout, **kwargs
            )

            response.raise_for_status()  # 检查HTTP状态码

            # 解析响应
            if response.headers.get("Content-Type") == "application/json":
                return response.json()
            else:
                return {"text": response.text}

        except requests.RequestException as e:
            logger.error(f"API请求失败: {e}")
            raise Exception(f"API请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            raise Exception(f"响应格式错误: {str(e)}")

    # ==================== 搜索相关 ====================

    def search_text(
        self, query: str, top_k: int = 20, threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        文本搜索

        Args:
            query: 搜索查询
            top_k: 返回结果数量
            threshold: 相似度阈值

        Returns:
            搜索结果
        """
        endpoint = "/api/v1/search/text"
        data = {"query": query, "top_k": top_k}
        if threshold is not None:
            data["threshold"] = threshold

        return self._make_request("POST", endpoint, json=data)

    def search_image(self, image_path: str, top_k: int = 20) -> Dict[str, Any]:
        """
        图像搜索

        Args:
            image_path: 图像路径
            top_k: 返回结果数量

        Returns:
            搜索结果
        """
        endpoint = "/api/v1/search/image"

        # 使用 FormData 上传文件
        files = {
            "file": (os.path.basename(image_path), open(image_path, "rb"), "image/jpeg")
        }
        data = {"top_k": str(top_k)}

        try:
            response = self._make_request("POST", endpoint, files=files, data=data)
            return response
        finally:
            # 关闭文件
            files["file"][1].close()

    def search_audio(self, audio_path: str, top_k: int = 20) -> Dict[str, Any]:
        """
        音频搜索

        Args:
            audio_path: 音频路径
            top_k: 返回结果数量

        Returns:
            搜索结果
        """
        endpoint = "/api/v1/search/audio"

        # 使用 FormData 上传文件
        files = {
            "file": (os.path.basename(audio_path), open(audio_path, "rb"), "audio/wav")
        }
        data = {"top_k": str(top_k)}

        try:
            response = self._make_request("POST", endpoint, files=files, data=data)
            return response
        finally:
            # 关闭文件
            files["file"][1].close()

    # ==================== 任务管理相关 ====================

    def get_all_tasks(
        self, status: Optional[str] = None, task_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取所有任务

        Args:
            status: 任务状态过滤
            task_type: 任务类型过滤

        Returns:
            任务列表
        """
        endpoint = "/api/v1/tasks"
        params = {}
        if status:
            params["status"] = status
        if task_type:
            params["task_type"] = task_type

        return self._make_request("GET", endpoint, params=params)

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态
        """
        endpoint = f"/api/v1/tasks/{task_id}"
        return self._make_request("GET", endpoint)

    def set_task_priority(self, task_id: str, priority: int) -> Dict[str, Any]:
        """
        设置任务优先级

        Args:
            task_id: 任务ID
            priority: 优先级

        Returns:
            操作结果
        """
        endpoint = f"/api/v1/tasks/{task_id}/priority"
        data = {"priority": priority}
        return self._make_request("POST", endpoint, json=data)

    def pause_task(self, task_id: str) -> Dict[str, Any]:
        """
        暂停任务

        Args:
            task_id: 任务ID

        Returns:
            操作结果
        """
        endpoint = f"/api/v1/tasks/{task_id}/pause"
        return self._make_request("POST", endpoint)

    def resume_task(self, task_id: str) -> Dict[str, Any]:
        """
        恢复任务

        Args:
            task_id: 任务ID

        Returns:
            操作结果
        """
        endpoint = f"/api/v1/tasks/{task_id}/resume"
        return self._make_request("POST", endpoint)

    def retry_task(self, task_id: str) -> Dict[str, Any]:
        """
        重试任务

        Args:
            task_id: 任务ID

        Returns:
            操作结果
        """
        endpoint = f"/api/v1/tasks/{task_id}/retry"
        return self._make_request("POST", endpoint)

    def archive_task(self, task_id: str) -> Dict[str, Any]:
        """
        归档任务

        Args:
            task_id: 任务ID

        Returns:
            操作结果
        """
        endpoint = f"/api/v1/tasks/{task_id}/archive"
        return self._make_request("POST", endpoint)

    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            操作结果
        """
        endpoint = f"/api/v1/tasks/{task_id}"
        return self._make_request("DELETE", endpoint)

    def cancel_all_tasks(self, cancel_running: bool = False) -> Dict[str, Any]:
        """
        取消所有任务

        Args:
            cancel_running: 是否取消运行中的任务

        Returns:
            操作结果
        """
        endpoint = "/api/v1/tasks/cancel-all"
        data = {"cancel_running": cancel_running}
        return self._make_request("POST", endpoint, json=data)

    def cancel_tasks_by_type(
        self, task_type: str, cancel_running: bool = False
    ) -> Dict[str, Any]:
        """
        按类型取消任务

        Args:
            task_type: 任务类型
            cancel_running: 是否取消运行中的任务

        Returns:
            操作结果
        """
        endpoint = "/api/v1/tasks/cancel-by-type"
        data = {"task_type": task_type, "cancel_running": cancel_running}
        return self._make_request("POST", endpoint, json=data)

    def get_task_stats(self) -> Dict[str, Any]:
        """
        获取任务统计

        Returns:
            任务统计数据
        """
        endpoint = "/api/v1/tasks/stats"
        return self._make_request("GET", endpoint)

    # ==================== 系统相关 ====================

    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息

        Returns:
            系统信息
        """
        endpoint = "/api/v1/system/info"
        return self._make_request("GET", endpoint)

    # ==================== 索引相关 ====================

    def index_file(self, file_path: str) -> Dict[str, Any]:
        """
        索引文件

        Args:
            file_path: 文件路径

        Returns:
            操作结果
        """
        endpoint = "/api/v1/index/file"
        data = {"file_path": file_path}
        return self._make_request("POST", endpoint, data=data)

    def index_directory(self, directory: str, recursive: bool = True) -> Dict[str, Any]:
        """
        索引目录

        Args:
            directory: 目录路径
            recursive: 是否递归索引

        Returns:
            操作结果
        """
        endpoint = "/api/v1/index/directory"
        data = {"directory": directory, "recursive": str(recursive).lower()}
        return self._make_request("POST", endpoint, data=data)

    def get_index_status(self) -> Dict[str, Any]:
        """
        获取索引状态

        Returns:
            索引状态
        """
        endpoint = "/api/v1/index/status"
        return self._make_request("GET", endpoint)
