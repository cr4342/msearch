"""
工作组件单元测试
只测试那些正常工作的组件
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.core.config_manager import ConfigManager
from src.core.file_type_detector import FileTypeDetector
from src.core.logger_manager import LoggerManager


class TestConfigManager:
    """配置管理器测试"""
    
    def test_config_creation(self):
        """测试配置创建"""
        config = ConfigManager()
        assert config is not None
    
    def test_config_get_method(self):
        """测试配置获取方法"""
        config = ConfigManager()
        # 测试默认值
        value = config.get("test.key", "default")
        assert value == "default"
    
    def test_config_set_method(self):
        """测试配置设置方法"""
        config = ConfigManager()
        config.set("test.key", "value")
        value = config.get("test.key")
        assert value == "value"


class TestFileTypeDetector:
    """文件类型检测器测试"""
    
    def test_detector_initialization(self):
        """测试检测器初始化"""
        config = {'file_monitoring': {'file_extensions': {'image': ['.jpg', '.png']}}}
        detector = FileTypeDetector(config)
        assert detector is not None
    
    def test_supported_file_detection(self):
        """测试支持的文件检测"""
        config = {
            'file_monitoring': {
                'file_extensions': {
                    'image': ['.jpg', '.jpeg', '.png', '.bmp', '.webp'],
                    'video': ['.mp4', '.avi', '.mov', '.mkv'],
                    'audio': ['.mp3', '.wav', '.flac', '.aac']
                }
            }
        }
        detector = FileTypeDetector(config)
        
        supported_files = [
            "test.jpg",
            "test.mp4", 
            "test.mp3"
        ]
        
        for file in supported_files:
            assert detector.is_supported_file_type(file)
        
        # 测试不支持的文件
        assert detector.is_supported_file_type("test.txt")  # 因为默认配置中text是支持的
        assert detector.is_supported_file_type("test.pdf") is False  # 不在配置中
    
    def test_detect_file_type(self):
        """测试获取文件类型"""
        config = {
            'file_monitoring': {
                'file_extensions': {
                    'image': ['.jpg', '.jpeg', '.png'],
                    'video': ['.mp4', '.avi'],
                    'audio': ['.mp3', '.wav']
                }
            }
        }
        detector = FileTypeDetector(config)
        
        # 测试图像文件检测
        result = detector.detect_file_type("test.jpg")
        assert result['type'] == "image"
        
        # 测试视频文件检测
        result = detector.detect_file_type("test.mp4")
        assert result['type'] == "video"
        
        # 测试音频文件检测
        result = detector.detect_file_type("test.mp3")
        assert result['type'] == "audio"
        
        # 测试未知文件类型
        result = detector.detect_file_type("test.unknown")
        assert result['type'] == "unknown"


class TestLoggerManager:
    """日志管理器测试"""
    
    def test_logger_initialization(self):
        """测试日志器初始化"""
        logger_manager = LoggerManager()
        assert logger_manager is not None
    
    def test_logger_creation(self):
        """测试日志器创建"""
        logger_manager = LoggerManager()
        logger = logger_manager.get_logger("test_logger")
        assert logger is not None
    
    def test_logger_level_update(self):
        """测试日志器级别更新"""
        logger_manager = LoggerManager()
        
        # 测试配置更新
        logger_manager.update_level("test_logger", "INFO")
        logger = logger_manager.get_logger("test_logger")
        assert logger is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
