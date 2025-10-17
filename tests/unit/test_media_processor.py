"""
媒体预处理器单元测试
"""
import unittest
import sys
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(0, '..')

from src.business.media_processor import MediaProcessor


class TestMediaProcessor(unittest.TestCase):
    """媒体预处理器单元测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 配置
        self.config = {
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
    
    @patch('src.business.media_processor.ImageProcessor')
    @patch('src.business.media_processor.VideoProcessor')
    @patch('src.business.media_processor.AudioProcessor')
    @patch('src.business.media_processor.TextProcessor')
    @patch('src.business.media_processor.AudioClassifier')
    def test_media_processor_initialization(self, mock_audio_classifier, mock_text_processor, 
                                          mock_audio_processor, mock_video_processor, 
                                          mock_image_processor):
        """测试媒体预处理器初始化"""
        # 创建模拟对象
        mock_image_processor_instance = Mock()
        mock_image_processor.return_value = mock_image_processor_instance
        
        mock_video_processor_instance = Mock()
        mock_video_processor.return_value = mock_video_processor_instance
        
        mock_audio_processor_instance = Mock()
        mock_audio_processor.return_value = mock_audio_processor_instance
        
        mock_text_processor_instance = Mock()
        mock_text_processor.return_value = mock_text_processor_instance
        
        mock_audio_classifier_instance = Mock()
        mock_audio_classifier.return_value = mock_audio_classifier_instance
        
        # 创建媒体预处理器实例
        processor = MediaProcessor(self.config)
        
        # 验证各处理器是否正确初始化
        self.assertIsNotNone(processor.image_processor)
        self.assertIsNotNone(processor.video_processor)
        self.assertIsNotNone(processor.audio_processor)
        self.assertIsNotNone(processor.text_processor)
        self.assertIsNotNone(processor.audio_classifier)
    
    @patch('src.business.media_processor.ImageProcessor')
    @patch('src.business.media_processor.VideoProcessor')
    @patch('src.business.media_processor.AudioProcessor')
    @patch('src.business.media_processor.TextProcessor')
    @patch('src.business.media_processor.AudioClassifier')
    def test_image_processing(self, mock_audio_classifier, mock_text_processor, 
                            mock_audio_processor, mock_video_processor, 
                            mock_image_processor):
        """测试图片处理"""
        # 创建模拟对象
        mock_image_processor_instance = Mock()
        mock_image_processor.return_value = mock_image_processor_instance
        
        # 模拟图片处理结果
        mock_image_processor_instance.process_image.return_value = {
            'status': 'success',
            'image_data': np.random.rand(224, 224, 3).astype(np.float32),
            'quality_score': 0.85
        }
        
        mock_video_processor_instance = Mock()
        mock_video_processor.return_value = mock_video_processor_instance
        
        mock_audio_processor_instance = Mock()
        mock_audio_processor.return_value = mock_audio_processor_instance
        
        mock_text_processor_instance = Mock()
        mock_text_processor.return_value = mock_text_processor_instance
        
        mock_audio_classifier_instance = Mock()
        mock_audio_classifier.return_value = mock_audio_classifier_instance
        
        # 创建媒体预处理器实例
        processor = MediaProcessor(self.config)
        
        # 运行异步处理函数
        import asyncio
        async def run_test():
            result = await processor.process_file("test.jpg", "image")
            return result
        
        # 执行测试
        result = asyncio.run(run_test())
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['file_type'], 'image')
        self.assertEqual(result['file_path'], 'test.jpg')
        
        # 验证图片处理器是否被正确调用
        mock_image_processor_instance.process_image.assert_called_once_with("test.jpg")
    
    @patch('src.business.media_processor.ImageProcessor')
    @patch('src.business.media_processor.VideoProcessor')
    @patch('src.business.media_processor.AudioProcessor')
    @patch('src.business.media_processor.TextProcessor')
    @patch('src.business.media_processor.AudioClassifier')
    def test_unsupported_file_type(self, mock_audio_classifier, mock_text_processor, 
                                 mock_audio_processor, mock_video_processor, 
                                 mock_image_processor):
        """测试不支持的文件类型"""
        # 创建模拟对象
        mock_image_processor_instance = Mock()
        mock_image_processor.return_value = mock_image_processor_instance
        
        mock_video_processor_instance = Mock()
        mock_video_processor.return_value = mock_video_processor_instance
        
        mock_audio_processor_instance = Mock()
        mock_audio_processor.return_value = mock_audio_processor_instance
        
        mock_text_processor_instance = Mock()
        mock_text_processor.return_value = mock_text_processor_instance
        
        mock_audio_classifier_instance = Mock()
        mock_audio_classifier.return_value = mock_audio_classifier_instance
        
        # 创建媒体预处理器实例
        processor = MediaProcessor(self.config)
        
        # 运行异步处理函数
        import asyncio
        async def run_test():
            result = await processor.process_file("test.unsupported", "unsupported")
            return result
        
        # 执行测试
        result = asyncio.run(run_test())
        
        # 验证结果
        self.assertEqual(result['status'], 'error')
        self.assertIn('不支持的文件类型', result['error'])


if __name__ == '__main__':
    unittest.main()