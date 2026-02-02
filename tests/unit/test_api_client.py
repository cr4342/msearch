"""
APIClient单元测试
测试API客户端的所有方法
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from src.api.api_client import APIClient


class TestAPIClient:
    """APIClient测试类"""

    @pytest.fixture
    def api_client(self):
        """创建APIClient实例并mock session"""
        with patch("src.api.api_client.requests.Session") as mock_session_class:
            session = MagicMock()
            mock_session_class.return_value = session
            client = APIClient(base_url="http://test.com/api/v1")
            client.session = session
            yield client, session

    def test_init(self):
        """测试初始化"""
        client = APIClient(base_url="http://test.com/api/v1")
        assert client.base_url == "http://test.com/api/v1"
        assert client.session is not None

    def test_get_monitored_directories_success(self, api_client):
        """测试成功获取监控目录"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_response.json.return_value = {
            "directories": [
                {"path": "/path/to/dir1", "status": "monitoring"},
                {"path": "/path/to/dir2", "status": "paused"},
            ]
        }
        mock_session.get.return_value = mock_response

        directories = client.get_monitored_directories()

        assert len(directories) == 2
        assert directories[0]["path"] == "/path/to/dir1"
        assert directories[1]["status"] == "paused"

    def test_get_monitored_directories_empty(self, api_client):
        """测试获取空监控目录列表"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_response.json.return_value = {"directories": []}
        mock_session.get.return_value = mock_response

        directories = client.get_monitored_directories()

        assert directories == []

    def test_get_monitored_directories_error(self, api_client):
        """测试获取监控目录时的错误"""
        client, mock_session = api_client
        mock_session.get.side_effect = requests.RequestException("Connection error")

        directories = client.get_monitored_directories()

        assert directories == []

    def test_add_monitored_directory_success(self, api_client):
        """测试成功添加监控目录"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_session.post.return_value = mock_response

        result = client.add_monitored_directory("/new/path")

        assert result is True

    def test_add_monitored_directory_failure(self, api_client):
        """测试添加监控目录失败"""
        client, mock_session = api_client
        mock_session.post.side_effect = requests.RequestException("Network error")

        result = client.add_monitored_directory("/new/path")

        assert result is False

    def test_remove_monitored_directory_success(self, api_client):
        """测试成功移除监控目录"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_session.delete.return_value = mock_response

        result = client.remove_monitored_directory("/path/to/remove")

        assert result is True

    def test_pause_directory_success(self, api_client):
        """测试成功暂停监控目录"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_session.post.return_value = mock_response

        result = client.pause_directory("/path/to/pause")

        assert result is True

    def test_resume_directory_success(self, api_client):
        """测试成功恢复监控目录"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_session.post.return_value = mock_response

        result = client.resume_directory("/path/to/resume")

        assert result is True

    def test_get_file_stats_success(self, api_client):
        """测试成功获取文件统计"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_response.json.return_value = {
            "stats": {"total": 100, "image": 50, "video": 30, "audio": 20}
        }
        mock_session.get.return_value = mock_response

        stats = client.get_file_stats()

        assert stats["total"] == 100
        assert stats["image"] == 50
        assert stats["video"] == 30
        assert stats["audio"] == 20

    def test_set_priority_settings_success(self, api_client):
        """测试成功设置优先级设置"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_session.put.return_value = mock_response

        settings = {"video": "high", "audio": "medium", "image": "low"}

        result = client.set_priority_settings(settings)

        assert result is True

    def test_get_priority_settings_success(self, api_client):
        """测试成功获取优先级设置"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_response.json.return_value = {
            "settings": {"video": "high", "audio": "medium", "image": "low"}
        }
        mock_session.get.return_value = mock_response

        settings = client.get_priority_settings()

        assert settings["video"] == "high"
        assert settings["audio"] == "medium"
        assert settings["image"] == "low"

    def test_pause_tasks_success(self, api_client):
        """测试成功暂停任务"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_session.post.return_value = mock_response

        result = client.pause_tasks()

        assert result is True

    def test_resume_tasks_success(self, api_client):
        """测试成功恢复任务"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_session.post.return_value = mock_response

        result = client.resume_tasks()

        assert result is True

    def test_cancel_tasks_success(self, api_client):
        """测试成功取消任务"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_session.delete.return_value = mock_response

        result = client.cancel_tasks()

        assert result is True

    def test_trigger_full_scan_success(self, api_client):
        """测试成功触发全量扫描"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_session.post.return_value = mock_response

        result = client.trigger_full_scan()

        assert result is True

    def test_trigger_directory_scan_success(self, api_client):
        """测试成功触发目录扫描"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_session.post.return_value = mock_response

        result = client.trigger_directory_scan("/path/to/scan")

        assert result is True

    def test_trigger_vectorization_success(self, api_client):
        """测试成功触导向量化"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_session.post.return_value = mock_response

        result = client.trigger_vectorization(
            file_type="image", concurrent=4, use_gpu=False
        )

        assert result is True

    def test_update_resource_config_success(self, api_client):
        """测试成功更新资源配置"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_session.put.return_value = mock_response

        result = client.update_resource_config(concurrent=4, use_gpu=True)

        assert result is True

    def test_get_tasks_success(self, api_client):
        """测试成功获取任务列表"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_response.json.return_value = {
            "tasks": [
                {"id": "task1", "status": "pending", "priority": 5},
                {"id": "task2", "status": "running", "priority": 3},
            ]
        }
        mock_session.get.return_value = mock_response

        tasks = client.get_tasks()

        assert len(tasks) == 2
        assert tasks[0]["id"] == "task1"

    def test_get_task_stats_success(self, api_client):
        """测试成功获取任务统计"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_response.json.return_value = {
            "stats": {"pending": 30, "running": 5, "completed": 60, "failed": 5}
        }
        mock_session.get.return_value = mock_response

        stats = client.get_task_stats()

        assert stats["running"] == 5
        assert stats["completed"] == 60

    def test_json_parse_error(self, api_client):
        """测试JSON解析错误"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_session.get.return_value = mock_response

        directories = client.get_monitored_directories()

        assert directories == []

    def test_http_error_with_404(self, api_client):
        """测试HTTP 404错误"""
        client, mock_session = api_client
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_session.get.return_value = mock_response

        directories = client.get_monitored_directories()

        assert directories == []
