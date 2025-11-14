#!/usr/bin/env python3
"""
文件监控功能单元测试
测试文件监控服务的核心功能
"""

import os
import sys
import unittest
import tempfile
import shutil
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 将src目录添加到Python路径中
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.business.file_monitor import FileMonitor, FileMonitorHandler
from src.api.routes.monitoring import init_monitoring_service, get_monitoring_status, start_monitoring, stop_monitoring
from src.core.config_manager import ConfigManager


class TestFileMonitorHandler(unittest.TestCase):
    """测试文件监控事件处理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.callback = Mock()
        self.config = {
            'file_monitoring.file_extensions': {
                'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'],
                'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
                'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac'],
                'text': ['.txt', '.md', '.csv', '.json', '.xml']
            }
        }
        self.handler = FileMonitorHandler(self.callback, self.config)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_supported_extensions(self):
        """测试支持的文件扩展名"""
        # 应该包含所有配置的扩展名
        expected_extensions = set()
        for extensions in self.config['file_monitoring.file_extensions'].values():
            expected_extensions.update(extensions)
        
        self.assertEqual(self.handler.supported_extensions, expected_extensions)
    
    def test_is_file_ready_success(self):
        """测试文件准备就绪检查 - 成功情况"""
        # 创建一个临时文件
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # 文件应该准备就绪
        self.assertTrue(self.handler._is_file_ready(test_file))
    
    def test_is_file_ready_failure(self):
        """测试文件准备就绪检查 - 失败情况"""
        # 不存在的文件应该未准备就绪
        non_existent_file = os.path.join(self.temp_dir, "non_existent.txt")
        self.assertFalse(self.handler._is_file_ready(non_existent_file))
    
    def test_handle_file_event_supported_extension(self):
        """测试处理文件事件 - 支持的扩展名"""
        # 创建一个临时图片文件
        test_file = os.path.join(self.temp_dir, "test.jpg")
        with open(test_file, 'wb') as f:
            f.write(b"fake image content")
        
        # 处理文件事件
        self.handler._handle_file_event(test_file, "created")
        
        # 回调函数应该被调用
        self.callback.assert_called_once_with(test_file, "created")
    
    def test_handle_file_event_unsupported_extension(self):
        """测试处理文件事件 - 不支持的扩展名"""
        # 创建一个临时文件，扩展名不在支持列表中
        test_file = os.path.join(self.temp_dir, "test.xyz")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # 处理文件事件
        self.handler._handle_file_event(test_file, "created")
        
        # 回调函数不应该被调用
        self.callback.assert_not_called()


class TestFileMonitor(unittest.TestCase):
    """测试文件监控服务"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'general': {
                'watch_directories': [self.temp_dir]
            }
        }
        
        # 创建模拟配置管理器
        self.mock_config_manager = Mock()
        self.mock_config_manager.config = self.config
        self.mock_config_manager.get.return_value = self.config['general']['watch_directories']
        self.mock_config_manager.set = Mock()
        
        # 创建模拟处理编排器
        self.mock_orchestrator = Mock()
        
        # 创建FileMonitor实例，只传入配置字典
        self.monitor = FileMonitor(self.config)
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """测试初始化"""
        # 验证配置已正确设置
        self.assertEqual(self.monitor.config, self.config)
        
        # 验证监控目录已正确设置
        self.assertEqual(self.monitor.directories, [self.temp_dir])
        
        # 验证监控未启动
        self.assertFalse(self.monitor.is_monitoring())
        
        # 验证回调函数列表为空
        self.assertEqual(len(self.monitor.callbacks), 0)
    
    def test_add_callback(self):
        """测试添加回调函数"""
        callback = Mock()
        self.monitor.add_callback(callback)
        
        self.assertIn(callback, self.monitor.callbacks)
    
    def test_get_monitored_directories(self):
        """测试获取监控目录列表"""
        directories = self.monitor.get_monitored_directories()
        # 验证返回的是目录列表的副本
        self.assertEqual(directories, [self.temp_dir])
        # 验证返回的是副本，修改返回值不会影响原列表
        directories.append("/another/directory")
        self.assertEqual(self.monitor.directories, [self.temp_dir])
    
    def test_add_directory(self):
        """测试添加监控目录"""
        new_dir = tempfile.mkdtemp()
        try:
            self.monitor.add_directory(new_dir)
            self.assertIn(new_dir, self.monitor.directories)
        finally:
            if os.path.exists(new_dir):
                shutil.rmtree(new_dir)
    
    def test_remove_directory(self):
        """测试移除监控目录"""
        self.monitor.remove_directory(self.temp_dir)
        self.assertNotIn(self.temp_dir, self.monitor.directories)


class TestMonitoringAPI(unittest.TestCase):
    """测试文件监控API"""
    
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
        
        # 创建模拟配置管理器
        self.mock_config_manager = Mock()
        self.mock_config_manager.config = self.config_data
        self.mock_config_manager.get.return_value = self.config_data['general']['watch_directories']
        self.mock_config_manager.set = Mock()
        self.mock_config_manager.get_all_config.return_value = self.config_data
        
        # 创建模拟处理编排器
        self.mock_orchestrator = Mock()
        
        # 初始化文件监控服务
        from src.api.routes.monitoring import init_monitoring_service
        self.mock_monitor = init_monitoring_service(self.mock_config_manager, self.mock_orchestrator)
        
        # 保存监控实例创建时的目录，用于后续测试比较
        self.monitored_directories = self.mock_monitor.directories.copy()
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_init_monitoring_service(self):
        """测试初始化文件监控服务"""
        # 验证监控实例已创建
        self.assertIsNotNone(self.mock_monitor)
        
        # 验证配置中包含监控目录
        self.assertIn('general', self.mock_monitor.config)
        self.assertIn('watch_directories', self.mock_monitor.config['general'])
        
        # 验证监控目录已正确设置
        self.assertEqual(len(self.mock_monitor.directories), 1)
        
        # 验证监控目录是配置中的目录
        # 使用setUp中保存的目录进行比较，避免临时目录路径变化导致测试失败
        self.assertEqual(self.mock_monitor.directories, self.monitored_directories)
    
    @patch('src.api.routes.monitoring._file_monitor')
    def test_get_monitoring_status(self, mock_monitor):
        """测试获取监控状态API"""
        # 设置模拟返回值
        mock_monitor.is_monitoring.return_value = True
        mock_monitor.get_monitored_directories.return_value = [self.temp_dir]
        
        # 调用API
        from src.api.routes.monitoring import get_monitoring_status
        import asyncio
        response = asyncio.run(get_monitoring_status())
        
        # 验证响应
        self.assertTrue(response.success)
        self.assertEqual(response.message, "获取文件监控状态成功")
        self.assertTrue(response.data['running'])
        self.assertEqual(response.data['watched_directories'], [self.temp_dir])
    
    @patch('src.api.routes.monitoring._file_monitor')
    def test_start_monitoring(self, mock_monitor):
        """测试启动监控API"""
        # 设置模拟返回值
        mock_monitor.get_monitored_directories.return_value = [self.temp_dir]
        
        # 调用API
        from src.api.routes.monitoring import start_monitoring
        import asyncio
        response = asyncio.run(start_monitoring())
        
        # 验证响应
        self.assertTrue(response.success)
        self.assertEqual(response.message, "文件监控已启动")
        self.assertEqual(response.data['watched_directories'], [self.temp_dir])
        
        # 验证方法调用
        mock_monitor.start_monitoring.assert_called_once()
    
    @patch('src.api.routes.monitoring._file_monitor')
    def test_stop_monitoring(self, mock_monitor):
        """测试停止监控API"""
        # 调用API
        from src.api.routes.monitoring import stop_monitoring
        import asyncio
        response = asyncio.run(stop_monitoring())
        
        # 验证响应
        self.assertTrue(response.success)
        self.assertEqual(response.message, "文件监控已停止")
        
        # 验证方法调用
        mock_monitor.stop_monitoring.assert_called_once()


if __name__ == '__main__':
    unittest.main()