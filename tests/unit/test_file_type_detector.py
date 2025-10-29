"""
文件类型检测器单元测试
"""
import unittest
import sys
from unittest.mock import patch, MagicMock
import os
import tempfile

# 添加项目根目录到Python路径
sys.path.insert(0, '..')

from src.core.file_type_detector import FileTypeDetector, get_file_type_detector


class TestFileTypeDetector(unittest.TestCase):
    """文件类型检测器单元测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 配置
        self.config = {
            'file_monitoring.file_extensions': {
                'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'],
                'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
                'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac'],
                'text': ['.txt', '.md', '.csv', '.json', '.xml']
            },
            'file_monitoring.mime_types': {
                'image': ['image/jpeg', 'image/png', 'image/bmp', 'image/gif', 'image/webp'],
                'video': ['video/mp4', 'video/x-msvideo', 'video/quicktime', 'video/x-matroska', 'video/webm'],
                'audio': ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/flac', 'audio/aac'],
                'text': ['text/plain', 'text/markdown', 'text/csv', 'application/json', 'application/xml']
            }
        }
    
    def test_detector_initialization(self):
        """测试检测器初始化"""
        detector = FileTypeDetector(self.config)
        
        # 验证配置是否正确加载
        self.assertEqual(detector.file_extensions, self.config['file_monitoring.file_extensions'])
        self.assertEqual(detector.mime_types, self.config['file_monitoring.mime_types'])
    
    def test_extension_based_detection(self):
        """测试基于扩展名的检测"""
        detector = FileTypeDetector(self.config)
        
        # 测试图片文件
        result = detector._detect_by_extension("test.jpg")
        self.assertEqual(result['type'], 'image')
        self.assertEqual(result['subtype'], 'jpg')
        self.assertEqual(result['extension'], '.jpg')
        self.assertEqual(result['confidence'], 0.7)
        self.assertEqual(result['detect_method'], 'extension')
        
        # 测试视频文件
        result = detector._detect_by_extension("test.mp4")
        self.assertEqual(result['type'], 'video')
        self.assertEqual(result['subtype'], 'mp4')
        self.assertEqual(result['extension'], '.mp4')
        
        # 测试未知文件
        result = detector._detect_by_extension("test.unknown")
        self.assertEqual(result['type'], 'unknown')
        self.assertEqual(result['subtype'], 'unknown')
        self.assertEqual(result['extension'], '.unknown')
        self.assertEqual(result['confidence'], 0.3)
    
    @patch('src.core.file_type_detector.MAGIC_AVAILABLE', False)
    def test_mime_detection_unavailable(self):
        """测试MIME检测不可用的情况"""
        detector = FileTypeDetector(self.config)
        
        result = detector._detect_by_mime("test.jpg")
        self.assertEqual(result['type'], 'unknown')
        self.assertEqual(result['subtype'], 'octet-stream')
        self.assertEqual(result['mime_type'], 'application/octet-stream')
        self.assertEqual(result['detect_method'], 'mime_unavailable')
    
    def test_combined_detection_results(self):
        """测试综合检测结果"""
        detector = FileTypeDetector(self.config)
        
        # 测试结果一致的情况
        extension_result = {
            'type': 'image',
            'subtype': 'jpg',
            'extension': '.jpg',
            'confidence': 0.7,
            'detect_method': 'extension'
        }
        
        mime_result = {
            'type': 'image',
            'subtype': 'jpeg',
            'mime_type': 'image/jpeg',
            'file_description': 'JPEG image',
            'confidence': 0.9,
            'detect_method': 'mime'
        }
        
        combined_result = detector._combine_detection_results(extension_result, mime_result)
        self.assertEqual(combined_result['type'], 'image')
        self.assertEqual(combined_result['subtype'], 'jpg')
        self.assertEqual(combined_result['extension'], '.jpg')
        self.assertEqual(combined_result['mime_type'], 'image/jpeg')
        self.assertEqual(combined_result['detect_method'], 'combined')
        self.assertGreaterEqual(combined_result['confidence'], 0.89)
        
        # 测试结果不一致的情况（优先MIME）
        extension_result['type'] = 'video'
        combined_result = detector._combine_detection_results(extension_result, mime_result)
        self.assertEqual(combined_result['type'], 'image')
        self.assertEqual(combined_result['detect_method'], 'mime_priority')
        self.assertEqual(combined_result['confidence'], 0.9)
        
        # 测试MIME结果未知的情况
        mime_result['type'] = 'unknown'
        combined_result = detector._combine_detection_results(extension_result, mime_result)
        self.assertEqual(combined_result['type'], 'video')
        self.assertEqual(combined_result['detect_method'], 'extension_fallback')
        self.assertEqual(combined_result['confidence'], 0.7)
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        detector1 = get_file_type_detector(self.config)
        detector2 = get_file_type_detector(self.config)
        
        # 验证是同一个实例
        self.assertIs(detector1, detector2)
        
        # 验证配置是否正确
        self.assertEqual(detector1.file_extensions, self.config['file_monitoring.file_extensions'])


if __name__ == '__main__':
    unittest.main()