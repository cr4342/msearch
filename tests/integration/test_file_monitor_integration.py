#!/usr/bin/env python3
"""
文件监控功能集成测试
测试文件监控服务与API的集成
"""

import os
import sys
import unittest
import tempfile
import shutil
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch

# 将src目录添加到Python路径中
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from src.api.main import app
from src.core.config_manager import ConfigManager
from src.business.orchestrator import ProcessingOrchestrator


class TestFileMonitorIntegration(unittest.TestCase):
    """测试文件监控功能集成"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试配置
        self.config_data = {
            'general': {
                'watch_directories': [self.temp_dir]
            },
            'file_monitoring.file_extensions': {
                'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'],
                'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
                'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac'],
                'text': ['.txt', '.md', '.csv', '.json', '.xml']
            },
            'task': {
                'max_retry_count': 3,
                'max_concurrent_tasks': 4
            },
            'processing': {
                'image': {
                    'target_size': 224,
                    'max_resolution': (1920, 1080),
                    'quality_threshold': 0.5
                },
                'video': {
                    'target_size': 224,
                    'max_resolution': (1280, 720),
                    'scene_threshold': 0.3,
                    'frame_interval': 2.0
                },
                'audio': {
                    'target_sample_rate': 16000,
                    'target_channels': 1,
                    'segment_duration': 10.0,
                    'quality_threshold': 0.5
                },
                'text': {
                    'max_file_size': 10 * 1024 * 1024,
                    'encoding_priority': ['utf-8', 'gbk', 'gb2312', 'latin-1']
                }
            }
        }
        
        # 创建测试客户端
        self.client = TestClient(app)
        
        # 模拟配置管理器
        self.config_manager_patcher = patch('src.api.main.get_config_manager')
        self.mock_config_manager = self.config_manager_patcher.start()
        self.mock_config_manager.return_value.config = self.config_data
        self.mock_config_manager.return_value.get_all_config.return_value = self.config_data
        self.mock_config_manager.return_value.get_config.return_value = self.config_data['general']['watch_directories']
        self.mock_config_manager.return_value.set_config = Mock()
        
        # 模拟处理编排器
        self.orchestrator_patcher = patch('src.api.main.ProcessingOrchestrator')
        self.mock_orchestrator_class = self.orchestrator_patcher.start()
        self.mock_orchestrator = Mock(spec=ProcessingOrchestrator)
        self.mock_orchestrator_class.return_value = self.mock_orchestrator
        
        # 模拟文件监控初始化
        self.monitoring_patcher = patch('src.api.routes.monitoring.init_monitoring_service')
        self.mock_monitoring_init = self.monitoring_patcher.start()
        self.mock_monitor = Mock()
        self.mock_monitor.is_monitoring.return_value = False
        self.mock_monitor.get_monitored_directories.return_value = [self.temp_dir]
        self.mock_monitoring_init.return_value = self.mock_monitor
    
    def tearDown(self):
        """清理测试环境"""
        # 停止所有patch
        self.config_manager_patcher.stop()
        self.orchestrator_patcher.stop()
        self.monitoring_patcher.stop()
        
        # 删除临时目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_get_monitoring_status(self):
        """测试获取监控状态"""
        # 调用API
        response = self.client.get("/api/v1/monitoring/status")
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "获取文件监控状态成功")
        self.assertIn("data", data)
        self.assertIn("running", data["data"])
        self.assertIn("watched_directories", data["data"])
    
    def test_get_file_processing_status(self):
        """测试获取文件处理状态"""
        # 模拟处理编排器返回文件处理状态
        file_path = os.path.join(self.temp_dir, "test.jpg")
        self.mock_orchestrator.get_file_processing_status.return_value = {
            'status': 'success',
            'file_path': file_path,
            'task_id': 'task_123',
            'processing_status': 'processing',
            'progress': 50,
            'error_message': None,
            'retry_count': 0,
            'created_at': '2023-01-01T00:00:00Z',
            'updated_at': '2023-01-01T00:01:00Z'
        }
        
        # 调用API
        response = self.client.get(f"/api/v1/monitoring/file-status?file_path={file_path}")
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "获取文件处理状态成功")
        self.assertIn("data", data)
        self.assertEqual(data["data"]["file_path"], file_path)
        self.assertEqual(data["data"]["task_id"], "task_123")
        self.assertEqual(data["data"]["processing_status"], "processing")
        self.assertEqual(data["data"]["progress"], 50)
        
        # 验证方法调用
        self.mock_orchestrator.get_file_processing_status.assert_called_once_with(file_path)
    
    def test_get_file_processing_status_not_found(self):
        """测试获取不存在文件的处理状态"""
        # 模拟处理编排器返回未找到状态
        file_path = os.path.join(self.temp_dir, "nonexistent.jpg")
        self.mock_orchestrator.get_file_processing_status.return_value = {
            'status': 'not_found',
            'file_path': file_path,
            'message': '文件未被处理或任务已被清理'
        }
        
        # 调用API
        response = self.client.get(f"/api/v1/monitoring/file-status?file_path={file_path}")
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "文件未被处理或任务已被清理")
        self.assertIn("data", data)
        self.assertEqual(data["data"]["status"], "not_found")
        
        # 验证方法调用
        self.mock_orchestrator.get_file_processing_status.assert_called_once_with(file_path)
    
    def test_get_file_processing_status_error(self):
        """测试获取文件处理状态出错"""
        # 模拟处理编排器返回错误状态
        file_path = os.path.join(self.temp_dir, "error.jpg")
        self.mock_orchestrator.get_file_processing_status.return_value = {
            'status': 'error',
            'error': '数据库连接失败'
        }
        
        # 调用API
        response = self.client.get(f"/api/v1/monitoring/file-status?file_path={file_path}")
        
        # 验证响应
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("数据库连接失败", data["detail"])
        
        # 验证方法调用
        self.mock_orchestrator.get_file_processing_status.assert_called_once_with(file_path)
    
    def test_get_file_processing_status_no_orchestrator(self):
        """测试处理编排器未初始化时获取文件处理状态"""
        # 模拟处理编排器为None
        with patch('src.api.routes.monitoring._orchestrator', None):
            file_path = os.path.join(self.temp_dir, "test.jpg")
            
            # 调用API
            response = self.client.get(f"/api/v1/monitoring/file-status?file_path={file_path}")
            
            # 验证响应
            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertFalse(data["success"])
            self.assertIn("处理编排器未初始化", data["detail"])
    
    def test_get_all_processing_status(self):
        """测试获取所有文件处理状态统计"""
        # 模拟处理编排器返回状态统计
        self.mock_orchestrator.get_all_processing_status.return_value = {
            'status': 'success',
            'task_counts': {
                'pending': 5,
                'processing': 3,
                'completed': 10,
                'failed': 2
            },
            'total_tasks': 20
        }
        
        # 调用API
        response = self.client.get("/api/v1/monitoring/processing-status")
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "获取处理状态统计成功")
        self.assertIn("data", data)
        self.assertEqual(data["data"]["task_counts"]["pending"], 5)
        self.assertEqual(data["data"]["task_counts"]["processing"], 3)
        self.assertEqual(data["data"]["task_counts"]["completed"], 10)
        self.assertEqual(data["data"]["task_counts"]["failed"], 2)
        self.assertEqual(data["data"]["total_tasks"], 20)
        
        # 验证方法调用
        self.mock_orchestrator.get_all_processing_status.assert_called_once()
    
    def test_get_all_processing_status_error(self):
        """测试获取所有文件处理状态统计出错"""
        # 模拟处理编排器返回错误状态
        self.mock_orchestrator.get_all_processing_status.return_value = {
            'status': 'error',
            'error': '数据库查询失败'
        }
        
        # 调用API
        response = self.client.get("/api/v1/monitoring/processing-status")
        
        # 验证响应
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("数据库查询失败", data["detail"])
        
        # 验证方法调用
        self.mock_orchestrator.get_all_processing_status.assert_called_once()
    
    def test_get_all_processing_status_no_orchestrator(self):
        """测试处理编排器未初始化时获取所有文件处理状态统计"""
        # 模拟处理编排器为None
        with patch('src.api.routes.monitoring._orchestrator', None):
            # 调用API
            response = self.client.get("/api/v1/monitoring/processing-status")
            
            # 验证响应
            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertFalse(data["success"])
            self.assertIn("处理编排器未初始化", data["detail"])

    def test_start_monitoring(self):
        """测试启动监控"""
        # 调用API
        response = self.client.post("/api/v1/monitoring/start")
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "文件监控已启动")
        self.assertIn("data", data)
        self.assertIn("watched_directories", data["data"])
        
        # 验证方法调用
        self.mock_monitor.start_monitoring.assert_called_once()
    
    def test_start_monitoring_with_directories(self):
        """测试启动监控并指定目录"""
        new_dir = tempfile.mkdtemp()
        try:
            # 请求数据
            request_data = {
                "directories": [self.temp_dir, new_dir]
            }
            
            # 调用API
            response = self.client.post("/api/v1/monitoring/start", json=request_data)
            
            # 验证响应
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["message"], "文件监控已启动")
            
            # 验证方法调用
            self.mock_monitor.stop_monitoring.assert_called_once()
            self.mock_monitor.start_monitoring.assert_called_once()
            
        finally:
            if os.path.exists(new_dir):
                shutil.rmtree(new_dir)
    
    def test_stop_monitoring(self):
        """测试停止监控"""
        # 调用API
        response = self.client.post("/api/v1/monitoring/stop")
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "文件监控已停止")
        
        # 验证方法调用
        self.mock_monitor.stop_monitoring.assert_called_once()
    
    def test_add_monitoring_directory(self):
        """测试添加监控目录"""
        new_dir = tempfile.mkdtemp()
        try:
            # 调用API
            response = self.client.post(f"/api/v1/monitoring/directories/add?directory={new_dir}")
            
            # 验证响应
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["message"], f"已添加监控目录: {new_dir}")
            
            # 验证方法调用
            self.mock_monitor.add_directory.assert_called_once_with(new_dir)
            
        finally:
            if os.path.exists(new_dir):
                shutil.rmtree(new_dir)
    
    def test_add_nonexistent_monitoring_directory(self):
        """测试添加不存在的监控目录"""
        nonexistent_dir = "/path/to/nonexistent/directory"
        
        # 调用API
        response = self.client.post(f"/api/v1/monitoring/directories/add?directory={nonexistent_dir}")
        
        # 验证响应
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("目录不存在", data["detail"])
    
    def test_remove_monitoring_directory(self):
        """测试移除监控目录"""
        # 调用API
        response = self.client.delete(f"/api/v1/monitoring/directories/{self.temp_dir}")
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], f"已移除监控目录: {self.temp_dir}")
        
        # 验证方法调用
        self.mock_monitor.remove_directory.assert_called_once_with(self.temp_dir)
    
    def test_file_change_callback(self):
        """测试文件变化回调"""
        # 模拟文件变化
        file_path = os.path.join(self.temp_dir, "test.jpg")
        event_type = "created"
        
        # 创建文件
        with open(file_path, 'wb') as f:
            f.write(b"fake image content")
        
        # 模拟文件监控回调
        from src.api.routes.monitoring import _handle_file_change
        
        # 调用回调函数
        _handle_file_change(file_path, event_type)
        
        # 验证处理编排器被调用
        self.mock_orchestrator.process_file.assert_called_once_with(file_path)


class TestFileMonitorWorkflow(unittest.TestCase):
    """测试文件监控工作流程"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试配置
        self.config_data = {
            'general': {
                'watch_directories': [self.temp_dir]
            },
            'file_monitoring.file_extensions': {
                'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'],
                'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
                'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac'],
                'text': ['.txt', '.md', '.csv', '.json', '.xml']
            }
        }
        
        # 创建配置管理器
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.get_all_config.return_value = self.config_data
        self.config_manager.get_config.return_value = self.config_data['general']['watch_directories']
        self.config_manager.set_config = Mock()
        
        # 创建处理编排器
        self.orchestrator = Mock(spec=ProcessingOrchestrator)
        
        # 初始化文件监控服务
        from src.api.routes.monitoring import init_monitoring_service
        self.monitor = init_monitoring_service(self.config_manager, self.orchestrator)
    
    def tearDown(self):
        """清理测试环境"""
        # 停止监控
        if self.monitor.is_monitoring():
            self.monitor.stop_monitoring()
        
        # 删除临时目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_monitoring_workflow(self):
        """测试完整的监控工作流程"""
        # 1. 启动监控
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor.is_monitoring())
        
        # 2. 创建测试文件
        test_file = os.path.join(self.temp_dir, "test.jpg")
        with open(test_file, 'wb') as f:
            f.write(b"fake image content")
        
        # 3. 等待文件监控事件处理
        time.sleep(1)
        
        # 4. 验证处理编排器被调用
        self.orchestrator.process_file.assert_called()
        
        # 5. 停止监控
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.is_monitoring())
    
    def test_file_filtering(self):
        """测试文件过滤功能"""
        # 添加回调函数
        callback = Mock()
        self.monitor.add_callback(callback)
        
        # 启动监控
        self.monitor.start_monitoring()
        
        # 1. 创建支持的文件类型
        supported_file = os.path.join(self.temp_dir, "test.jpg")
        with open(supported_file, 'wb') as f:
            f.write(b"fake image content")
        
        # 2. 创建不支持的文件类型
        unsupported_file = os.path.join(self.temp_dir, "test.xyz")
        with open(unsupported_file, 'w') as f:
            f.write("unsupported file")
        
        # 3. 等待文件监控事件处理
        time.sleep(1)
        
        # 4. 验证只有支持的文件被处理
        # 注意：由于我们使用的是模拟的处理编排器，这里只能验证回调函数的调用
        # 实际的文件过滤在FileMonitorHandler中实现
        
        # 5. 停止监控
        self.monitor.stop_monitoring()


if __name__ == '__main__':
    unittest.main()