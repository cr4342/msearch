"""
文件类型识别器单元测试
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.core.file_type_detector import FileTypeDetector, get_file_type_detector
from src.core.config_manager import ConfigManager


class TestFileTypeDetector(unittest.TestCase):
    """文件类型识别器单元测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建临时文件用于测试
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # 创建测试文件
        self.test_files = {
            'image.jpg': os.path.join(self.temp_dir.name, 'test_image.jpg'),
            'video.mp4': os.path.join(self.temp_dir.name, 'test_video.mp4'),
            'audio.mp3': os.path.join(self.temp_dir.name, 'test_audio.mp3'),
            'text.txt': os.path.join(self.temp_dir.name, 'test_text.txt'),
            'unknown.xyz': os.path.join(self.temp_dir.name, 'test_unknown.xyz')
        }
        
        # 创建空文件
        for file_path in self.test_files.values():
            open(file_path, 'w').close()
        
        # 模拟配置管理器
        self.mock_config_manager = MagicMock(spec=ConfigManager)
        self.mock_config_manager.get.side_effect = self._mock_get_config
        
        # 模拟magic库
        self.magic_mock = MagicMock()
        self.magic_mock.from_file.side_effect = self._mock_magic_from_file
    
    def tearDown(self):
        """测试后的清理工作"""
        self.temp_dir.cleanup()
    
    def _mock_get_config(self, key, default=None):
        """模拟配置获取"""
        config_map = {
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
        return config_map.get(key, default)
    
    def _mock_magic_from_file(self, file_path):
        """模拟magic.from_file方法"""
        if file_path.endswith('.jpg'):
            return 'image/jpeg'
        elif file_path.endswith('.mp4'):
            return 'video/mp4'
        elif file_path.endswith('.mp3'):
            return 'audio/mpeg'
        elif file_path.endswith('.txt'):
            return 'text/plain'
        else:
            return 'application/octet-stream'
    
    @patch('src.core.file_type_detector.get_config_manager')
    @patch('src.core.file_type_detector.magic.Magic')
    def test_detect_by_extension(self, mock_magic_class, mock_get_config_manager):
        """测试基于文件扩展名的类型检测"""
        # 设置模拟
        mock_get_config_manager.return_value = self.mock_config_manager
        mock_magic_class.return_value = self.magic_mock
        
        # 创建文件类型检测器
        detector = FileTypeDetector()
        
        # 测试不同类型文件
        result = detector._detect_by_extension(self.test_files['image.jpg'])
        self.assertEqual(result['type'], 'image')
        self.assertEqual(result['subtype'], 'jpg')
        self.assertEqual(result['extension'], '.jpg')
        self.assertEqual(result['confidence'], 0.7)
        
        result = detector._detect_by_extension(self.test_files['unknown.xyz'])
        self.assertEqual(result['type'], 'unknown')
        self.assertEqual(result['subtype'], 'unknown')
        self.assertEqual(result['extension'], '.xyz')
        self.assertEqual(result['confidence'], 0.3)
    
    @patch('src.core.file_type_detector.get_config_manager')
    @patch('src.core.file_type_detector.magic.Magic')
    def test_detect_by_mime(self, mock_magic_class, mock_get_config_manager):
        """测试基于MIME类型的文件类型检测"""
        # 设置模拟
        mock_get_config_manager.return_value = self.mock_config_manager
        
        # 创建两个不同的magic实例模拟
        mock_mime_magic = MagicMock()
        mock_file_magic = MagicMock()
        mock_mime_magic.from_file.side_effect = self._mock_magic_from_file
        mock_file_magic.from_file.return_value = "Mock file description"
        
        # 模拟多次调用返回不同实例
        mock_magic_class.side_effect = [mock_mime_magic, mock_file_magic]
        
        # 创建文件类型检测器
        detector = FileTypeDetector()
        
        # 测试不同类型文件
        result = detector._detect_by_mime(self.test_files['video.mp4'])
        self.assertEqual(result['type'], 'video')
        self.assertEqual(result['subtype'], 'mp4')
        self.assertEqual(result['mime_type'], 'video/mp4')
        self.assertEqual(result['file_description'], "Mock file description")
        self.assertEqual(result['confidence'], 0.9)
        
        result = detector._detect_by_mime(self.test_files['unknown.xyz'])
        self.assertEqual(result['type'], 'unknown')
        self.assertEqual(result['subtype'], 'octet-stream')
        self.assertEqual(result['mime_type'], 'application/octet-stream')
        self.assertEqual(result['file_description'], "Mock file description")
        self.assertEqual(result['confidence'], 0.9)
    
    @patch('src.core.file_type_detector.get_config_manager')
    @patch('src.core.file_type_detector.magic.Magic')
    def test_combine_detection_results(self, mock_magic_class, mock_get_config_manager):
        """测试综合检测结果"""
        # 设置模拟
        mock_get_config_manager.return_value = self.mock_config_manager
        mock_magic_class.return_value = self.magic_mock
        
        # 创建文件类型检测器
        detector = FileTypeDetector()
        
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
        self.assertAlmostEqual(combined_result['confidence'], 0.97, places=2)
        
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
    
    @patch('src.core.file_type_detector.get_config_manager')
    @patch('src.core.file_type_detector.magic.Magic')
    def test_get_processing_strategy(self, mock_magic_class, mock_get_config_manager):
        """测试获取处理策略"""
        # 设置模拟
        mock_get_config_manager.return_value = self.mock_config_manager
        mock_magic_class.return_value = self.magic_mock
        
        # 创建文件类型检测器
        detector = FileTypeDetector()
        
        # 测试不同文件类型对应的处理策略
        self.assertEqual(detector.get_processing_strategy('image'), 'image_processing')
        self.assertEqual(detector.get_processing_strategy('video'), 'video_processing')
        self.assertEqual(detector.get_processing_strategy('audio'), 'audio_processing')
        self.assertEqual(detector.get_processing_strategy('text'), 'text_processing')
        self.assertEqual(detector.get_processing_strategy('unknown'), 'default_processing')
    
    @patch('src.core.file_type_detector.get_config_manager')
    @patch('src.core.file_type_detector.magic.Magic')
    def test_is_supported_file_type(self, mock_magic_class, mock_get_config_manager):
        """测试文件类型是否受支持"""
        # 设置模拟
        mock_get_config_manager.return_value = self.mock_config_manager
        
        # 创建两个不同的magic实例模拟
        mock_mime_magic = MagicMock()
        mock_file_magic = MagicMock()
        mock_mime_magic.from_file.side_effect = self._mock_magic_from_file
        mock_file_magic.from_file.return_value = "Mock file description"
        
        # 模拟多次调用返回不同实例
        mock_magic_class.side_effect = [mock_mime_magic, mock_file_magic]
        
        # 创建文件类型检测器
        detector = FileTypeDetector()
        
        # 测试受支持和不受支持的文件类型
        self.assertTrue(detector.is_supported_file_type(self.test_files['image.jpg']))
        self.assertTrue(detector.is_supported_file_type(self.test_files['video.mp4']))
        
        # 修改MIME检测结果为unknown
        mock_mime_magic.from_file.return_value = 'application/octet-stream'
        self.assertFalse(detector.is_supported_file_type(self.test_files['unknown.xyz']))
    
    def test_get_file_type_detector_singleton(self):
        """测试获取文件类型检测器的单例模式"""
        # 由于无法轻松地模拟单例的初始化，这里只测试获取实例的功能
        try:
            detector1 = get_file_type_detector()
            detector2 = get_file_type_detector()
            # 验证是同一个实例
            self.assertIs(detector1, detector2)
        except Exception as e:
            # 如果初始化失败（可能是因为缺少依赖），至少确保函数可以被调用
            self.fail(f"get_file_type_detector() raised Exception {type(e).__name__}: {e}")


if __name__ == '__main__':
    unittest.main()