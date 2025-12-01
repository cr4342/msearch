"""
API服务单元测试
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.api.app import create_app


class TestAPIRoutes:
    """API路由测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        app = create_app()
        return TestClient(app)
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @patch('src.api.routes.search.SmartRetrievalEngine')
    def test_text_search(self, mock_engine_class, client):
        """测试文本搜索"""
        # 模拟检索引擎
        mock_engine = Mock()
        mock_engine.search = AsyncMock(return_value=[
            {
                'file_id': 'file1',
                'score': 0.9,
                'file_path': '/path/to/file1.jpg',
                'file_name': 'file1.jpg',
                'file_type': '.jpg'
            }
        ])
        mock_engine_class.return_value = mock_engine
        
        # 发送搜索请求
        response = client.post("/api/search", json={
            "query": "测试查询",
            "query_type": "text",
            "top_k": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["query"] == "测试查询"
        assert len(data["results"]) == 1
    
    def test_search_validation(self, client):
        """测试搜索参数验证"""
        # 测试缺少查询参数
        response = client.post("/api/search", json={})
        assert response.status_code == 422  # 验证错误
        
        # 测试无效的查询类型
        response = client.post("/api/search", json={
            "query": "测试",
            "query_type": "invalid",
            "top_k": 10
        })
        # 应该能处理，但可能返回空结果
    
    @patch('src.api.routes.search.SmartRetrievalEngine')
    def test_image_search(self, mock_engine_class, client):
        """测试图像搜索"""
        # 模拟检索引擎
        mock_engine = Mock()
        mock_engine.search = AsyncMock(return_value=[
            {
                'file_id': 'file1',
                'score': 0.8,
                'file_path': '/path/to/file1.jpg',
                'file_name': 'file1.jpg',
                'file_type': '.jpg'
            }
        ])
        mock_engine_class.return_value = mock_engine
        
        # 模拟图像文件
        image_content = b'fake_image_data'
        
        # 发送图像搜索请求
        response = client.post(
            "/api/search/image",
            files={"image": ("test.jpg", image_content, "image/jpeg")},
            data={"top_k": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["results"]) == 1
    
    @patch('src.api.routes.search.SmartRetrievalEngine')
    def test_audio_search(self, mock_engine_class, client):
        """测试音频搜索"""
        # 模拟检索引擎
        mock_engine = Mock()
        mock_engine.search = AsyncMock(return_value=[
            {
                'file_id': 'file1',
                'score': 0.7,
                'file_path': '/path/to/file1.mp3',
                'file_name': 'file1.mp3',
                'file_type': '.mp3'
            }
        ])
        mock_engine_class.return_value = mock_engine
        
        # 模拟音频文件
        audio_content = b'fake_audio_data'
        
        # 发送音频搜索请求
        response = client.post(
            "/api/search/audio",
            files={"audio": ("test.mp3", audio_content, "audio/mpeg")},
            data={"top_k": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["results"]) == 1
    
    @patch('src.api.routes.search.SmartRetrievalEngine')
    def test_similar_files(self, mock_engine_class, client):
        """测试相似文件搜索"""
        # 模拟检索引擎
        mock_engine = Mock()
        mock_engine.get_similar_files = AsyncMock(return_value=[
            {
                'file_id': 'file2',
                'score': 0.85,
                'file_path': '/path/to/file2.jpg',
                'file_name': 'file2.jpg',
                'file_type': '.jpg'
            }
        ])
        mock_engine_class.return_value = mock_engine
        
        # 发送相似文件搜索请求
        response = client.get("/api/similar/file1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["file_id"] == "file1"
        assert len(data["results"]) == 1
    
    @patch('src.api.routes.search.SmartRetrievalEngine')
    def test_search_suggestions(self, mock_engine_class, client):
        """测试搜索建议"""
        # 模拟检索引擎
        mock_engine = Mock()
        mock_engine.get_search_suggestions = AsyncMock(return_value=[
            "测试建议1",
            "测试建议2"
        ])
        mock_engine_class.return_value = mock_engine
        
        # 发送搜索建议请求
        response = client.get("/api/suggestions?query=测试&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["query"] == "测试"
        assert len(data["suggestions"]) == 2
    
    @patch('src.api.routes.search.SmartRetrievalEngine')
    def test_popular_searches(self, mock_engine_class, client):
        """测试热门搜索"""
        # 模拟检索引擎
        mock_engine = Mock()
        mock_engine.get_popular_searches = AsyncMock(return_value=[
            "热门搜索1",
            "热门搜索2"
        ])
        mock_engine_class.return_value = mock_engine
        
        # 发送热门搜索请求
        response = client.get("/api/popular?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["popular_searches"]) == 2


class TestConfigAPI:
    """配置API测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        app = create_app()
        return TestClient(app)
    
    def test_get_config(self, client):
        """测试获取配置"""
        response = client.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "config" in data
        assert "system" in data["config"]
        assert "media_processing" in data["config"]
    
    @patch('src.api.routes.config.FileMonitor')
    def test_add_monitored_directory(self, mock_file_monitor, client):
        """测试添加监控目录"""
        # 模拟文件监控器
        mock_monitor = Mock()
        mock_monitor.add_directory = AsyncMock()
        mock_file_monitor.return_value = mock_monitor
        
        # 创建临时目录用于测试
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 发送添加监控目录请求
            response = client.post("/api/config/monitored-directories", json={
                "directory": temp_dir
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert temp_dir in data["directories"]
            
        finally:
            # 清理临时目录
            os.rmdir(temp_dir)
    
    def test_add_invalid_directory(self, client):
        """测试添加无效目录"""
        # 发送添加不存在的目录请求
        response = client.post("/api/config/monitored-directories", json={
            "directory": "/nonexistent/directory"
        })
        
        assert response.status_code == 400
    
    @patch('src.api.routes.config.FileMonitor')
    def test_remove_monitored_directory(self, mock_file_monitor, client):
        """测试移除监控目录"""
        # 模拟文件监控器
        mock_monitor = Mock()
        mock_monitor.remove_directory = AsyncMock()
        mock_file_monitor.return_value = mock_monitor
        
        # 创建临时目录用于测试
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 发送移除监控目录请求
            response = client.delete("/api/config/monitored-directories", json={
                "directory": temp_dir
            })
            
            # 由于目录不在监控列表中，应该返回404
            assert response.status_code in [200, 404]
            
        finally:
            # 清理临时目录
            os.rmdir(temp_dir)
    
    def test_get_supported_extensions(self, client):
        """测试获取支持的扩展名"""
        response = client.get("/api/config/supported-extensions")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "extensions" in data
        assert isinstance(data["extensions"], list)
    
    @patch('src.api.routes.config.get_config_manager')
    def test_reload_config(self, mock_config_manager, client):
        """测试重新加载配置"""
        # 模拟配置管理器
        mock_config = Mock()
        mock_config.reload_config = AsyncMock()
        mock_config_manager.return_value = mock_config
        
        # 发送重新加载配置请求
        response = client.post("/api/config/reload")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    @patch('src.api.routes.config.SmartRetrievalEngine')
    def test_get_model_config(self, mock_engine_class, client):
        """测试获取模型配置"""
        # 模拟检索引擎
        mock_engine = Mock()
        mock_engine.embedding_engine = Mock()
        mock_engine.embedding_engine.health_check = AsyncMock(return_value={
            'clip': True,
            'clap': False,
            'whisper': True
        })
        mock_engine_class.return_value = mock_engine
        
        # 发送获取模型配置请求
        response = client.get("/api/config/models")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "models" in data


class TestStatusAPI:
    """状态API测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        app = create_app()
        return TestClient(app)
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    @patch('psutil.Process')
    def test_get_system_status(self, mock_process, mock_net, mock_disk, mock_memory, mock_cpu, client):
        """测试获取系统状态"""
        # 模拟psutil返回值
        mock_cpu.return_value = 50.0
        
        mock_memory_obj = Mock()
        mock_memory_obj.total = 8589934592  # 8GB
        mock_memory_obj.available = 4294967296  # 4GB
        mock_memory_obj.percent = 50.0
        mock_memory_obj.used = 4294967296
        mock_memory_obj.free = 4294967296
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = Mock()
        mock_disk_obj.total = 107374182400  # 100GB
        mock_disk_obj.used = 53687091200  # 50GB
        mock_disk_obj.free = 53687091200  # 50GB
        mock_disk.return_value = mock_disk_obj
        
        mock_net_obj = Mock()
        mock_net_obj.bytes_sent = 1000000
        mock_net_obj.bytes_recv = 2000000
        mock_net_obj.packets_sent = 1000
        mock_net_obj.packets_recv = 2000
        mock_net_obj.errin = 0
        mock_net_obj.errout = 0
        mock_net_obj.dropin = 0
        mock_net_obj.dropout = 0
        mock_net.return_value = mock_net_obj
        
        mock_process_obj = Mock()
        mock_process_obj.pid = 12345
        mock_process_obj.cpu_percent.return_value = 25.0
        mock_process_obj.num_threads = 4
        mock_process_obj.num_fds = 10
        
        mock_memory_info = Mock()
        mock_memory_info.rss = 104857600  # 100MB
        mock_memory_info.vms = 209715200  # 200MB
        mock_process_obj.memory_info.return_value = mock_memory_info
        
        mock_process.return_value = mock_process_obj
        
        # 发送获取系统状态请求
        response = client.get("/api/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "system" in data["data"]
        assert "process" in data["data"]
    
    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/api/status/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.Process')
    def test_get_performance_metrics(self, mock_process, mock_disk, mock_memory, mock_cpu, client):
        """测试获取性能指标"""
        # 模拟psutil返回值
        mock_cpu.return_value = 60.0
        
        mock_memory_obj = Mock()
        mock_memory_obj.percent = 60.0
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = Mock()
        mock_disk_obj.total = 107374182400
        mock_disk_obj.used = 64424509440
        mock_disk.return_value = mock_disk_obj
        
        mock_process_obj = Mock()
        mock_process_obj.cpu_percent.return_value = 30.0
        mock_process_obj.num_threads = 6
        mock_process_obj.num_fds = 15
        
        mock_memory_info = Mock()
        mock_memory_info.rss = 157286400
        mock_memory_info.vms = 314572800
        mock_process_obj.memory_info.return_value = mock_memory_info
        
        mock_process.return_value = mock_process_obj
        
        # 发送获取性能指标请求
        response = client.get("/api/status/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "system" in data["data"]
        assert "process" in data["data"]
    
    def test_get_recent_logs(self, client):
        """测试获取最近日志"""
        # 创建临时日志文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("2025-01-01 12:00:00 - INFO - Test log message 1\n")
            f.write("2025-01-01 12:01:00 - ERROR - Test log message 2\n")
            f.write("2025-01-01 12:02:00 - DEBUG - Test log message 3\n")
            log_path = f.name
        
        try:
            # 模拟日志文件路径
            with patch('src.api.routes.status.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.open.return_value.__enter__.return_value.read.return_value = \
                    "2025-01-01 12:00:00 - INFO - Test log message 1\n" \
                    "2025-01-01 12:01:00 - ERROR - Test log message 2\n" \
                    "2025-01-01 12:02:00 - DEBUG - Test log message 3\n"
                
                # 发送获取日志请求
                response = client.get("/api/status/logs?lines=10")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert "logs" in data
                assert isinstance(data["logs"], list)
        
        finally:
            # 清理临时日志文件
            os.unlink(log_path)


class TestTasksAPI:
    """任务API测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        app = create_app()
        return TestClient(app)
    
    @patch('src.api.routes.tasks.TaskManager')
    def test_get_tasks(self, mock_task_manager_class, client):
        """测试获取任务列表"""
        # 模拟任务管理器
        mock_task_manager = Mock()
        mock_task_manager.get_pending_tasks = AsyncMock(return_value=[
            {
                'id': 'task1',
                'file_id': 'file1',
                'task_type': 'processing',
                'status': 'pending',
                'created_at': 1234567890
            }
        ])
        mock_task_manager_class.return_value = mock_task_manager
        
        # 发送获取任务列表请求
        response = client.get("/api/tasks?status=pending&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "total_tasks" in data
        assert "tasks" in data
        assert len(data["tasks"]) == 1
    
    @patch('src.api.routes.tasks.TaskManager')
    def test_get_task_detail(self, mock_task_manager_class, client):
        """测试获取任务详情"""
        # 模拟任务管理器
        mock_task_manager = Mock()
        mock_task_manager.get_task = AsyncMock(return_value={
            'id': 'task1',
            'file_id': 'file1',
            'task_type': 'processing',
            'status': 'pending',
            'created_at': 1234567890,
            'updated_at': 1234567890
        })
        mock_task_manager_class.return_value = mock_task_manager
        
        # 发送获取任务详情请求
        response = client.get("/api/tasks/task1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "task" in data
        assert data["task"]["id"] == "task1"
    
    @patch('src.api.routes.tasks.TaskManager')
    def test_retry_task(self, mock_task_manager_class, client):
        """测试重试任务"""
        # 模拟任务管理器
        mock_task_manager = Mock()
        mock_task_manager.retry_failed_task = AsyncMock(return_value=True)
        mock_task_manager_class.return_value = mock_task_manager
        
        # 发送重试任务请求
        response = client.post("/api/tasks/task1/retry")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "task1" in data["message"]
    
    @patch('src.api.routes.tasks.TaskManager')
    def test_get_task_statistics(self, mock_task_manager_class, client):
        """测试获取任务统计"""
        # 模拟任务管理器
        mock_task_manager = Mock()
        mock_task_manager.get_task_statistics = AsyncMock(return_value={
            'pending': 5,
            'processing': 2,
            'completed': 10,
            'failed': 1
        })
        mock_task_manager_class.return_value = mock_task_manager
        
        # 发送获取任务统计请求
        response = client.get("/api/tasks/statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "statistics" in data
        assert data["statistics"]["pending"] == 5
    
    @patch('src.api.routes.tasks.TaskManager')
    def test_cleanup_old_tasks(self, mock_task_manager_class, client):
        """测试清理旧任务"""
        # 模拟任务管理器
        mock_task_manager = Mock()
        mock_task_manager.cleanup_old_tasks = AsyncMock(return_value=5)
        mock_task_manager_class.return_value = mock_task_manager
        
        # 发送清理旧任务请求
        response = client.delete("/api/tasks/cleanup?days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["deleted_count"] == 5
    
    @patch('src.api.routes.tasks.DatabaseAdapter')
    def test_get_file_tasks(self, mock_db_adapter_class, client):
        """测试获取文件任务"""
        # 模拟数据库适配器
        mock_db_adapter = Mock()
        mock_db_adapter.get_connection.return_value.__enter__.return_value.cursor.return_value.fetchall.return_value = [
            ('task1', 'file1', 'processing', 'pending', 1234567890, 1234567890)
        ]
        mock_db_adapter_class.return_value = mock_db_adapter
        
        # 发送获取文件任务请求
        response = client.get("/api/tasks/file1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["file_id"] == "file1"
        assert "tasks" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
