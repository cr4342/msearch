import pytest
from src.core.file_type_detector import FileTypeDetector, get_file_type_detector


class TestFileTypeDetectorFixed:
    """测试修复后的FileTypeDetector类"""
    
    def test_file_type_detector_initialization(self):
        """测试文件类型检测器初始化"""
        detector = FileTypeDetector({})
        assert detector is not None
        assert isinstance(detector, FileTypeDetector)
    
    def test_file_type_detector_with_default_config(self):
        """测试文件类型检测器使用默认配置"""
        detector = FileTypeDetector()
        assert detector is not None
        assert isinstance(detector, FileTypeDetector)
    
    def test_is_supported_file_type(self):
        """测试文件类型支持检查"""
        detector = FileTypeDetector()
        # 测试支持的文件类型
        assert detector.is_supported_file_type('test.jpg')
        assert detector.is_supported_file_type('test.mp3')
        assert detector.is_supported_file_type('test.txt')
        # 测试未知文件类型
        assert not detector.is_supported_file_type('test.unknown')
    
    def test_get_file_type_detector_singleton(self):
        """测试文件类型检测器单例模式"""
        detector1 = get_file_type_detector()
        detector2 = get_file_type_detector()
        assert detector1 is detector2
    
    def test_detect_file_type(self):
        """测试文件类型检测"""
        detector = FileTypeDetector()
        result = detector.detect_file_type('test.jpg')
        assert result is not None
        assert 'type' in result
    
    def test_detect_file_type_with_default_config_function(self):
        """测试使用默认配置的get_file_type_detector函数"""
        detector = get_file_type_detector()
        result = detector.detect_file_type('test.mp4')
        assert result is not None
        assert result['success'] == True
