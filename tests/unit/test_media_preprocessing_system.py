"""
媒体预处理系统单元测试
"""
import os
import unittest
import asyncio
import tempfile
import shutil
from unittest.mock import MagicMock, patch, AsyncMock

from src.processors.media_preprocessing_system import MediaPreprocessingSystem, get_media_preprocessing_system
from src.core.config_manager import get_config_manager


class TestMediaPreprocessingSystem(unittest.TestCase):
    """媒体预处理系统测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试文件
        self.test_files = {
            'image': os.path.join(self.temp_dir, 'test.jpg'),
            'video': os.path.join(self.temp_dir, 'test.mp4'),
            'audio': os.path.join(self.temp_dir, 'test.mp3'),
            'text': os.path.join(self.temp_dir, 'test.txt')
        }
        
        # 创建空文件
        for file_path in self.test_files.values():
            with open(file_path, 'wb') as f:
                f.write(b'')
        
        # 创建媒体预处理系统实例
        self.system = MediaPreprocessingSystem()
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_detect_file_type(self):
        """测试文件类型检测"""
        # 测试图像文件
        self.assertEqual(self.system._detect_file_type(self.test_files['image']), 'image')
        
        # 测试视频文件
        self.assertEqual(self.system._detect_file_type(self.test_files['video']), 'video')
        
        # 测试音频文件
        self.assertEqual(self.system._detect_file_type(self.test_files['audio']), 'audio')
        
        # 测试文本文件
        self.assertEqual(self.system._detect_file_type(self.test_files['text']), 'text')
        
        # 测试未知文件类型
        unknown_file = os.path.join(self.temp_dir, 'test.xyz')
        with open(unknown_file, 'wb') as f:
            f.write(b'')
        self.assertEqual(self.system._detect_file_type(unknown_file), 'unknown')
    
    def test_validate_file(self):
        """测试文件验证"""
        # 测试有效文件
        result = self.system.validate_file(self.test_files['image'])
        self.assertTrue(result['valid'])
        self.assertEqual(result['file_type'], 'image')
        self.assertEqual(len(result['errors']), 0)
        
        # 测试不存在的文件
        non_existent_file = os.path.join(self.temp_dir, 'non_existent.jpg')
        result = self.system.validate_file(non_existent_file)
        self.assertFalse(result['valid'])
        self.assertIn("文件不存在", result['errors'][0])
        
        # 测试未知文件类型
        unknown_file = os.path.join(self.temp_dir, 'test.xyz')
        with open(unknown_file, 'wb') as f:
            f.write(b'')
        result = self.system.validate_file(unknown_file)
        self.assertFalse(result['valid'])
        self.assertIn("不支持的文件类型", result['errors'][0])
    
    def test_get_supported_formats(self):
        """测试获取支持的格式"""
        formats = self.system.get_supported_formats()
        
        # 检查是否包含所有媒体类型
        self.assertIn('image', formats)
        self.assertIn('video', formats)
        self.assertIn('audio', formats)
        self.assertIn('text', formats)
        
        # 检查图像格式
        self.assertIn('.jpg', formats['image'])
        self.assertIn('.png', formats['image'])
        
        # 检查视频格式
        self.assertIn('.mp4', formats['video'])
        self.assertIn('.avi', formats['video'])
        
        # 检查音频格式
        self.assertIn('.mp3', formats['audio'])
        self.assertIn('.wav', formats['audio'])
        
        # 检查文本格式
        self.assertIn('.txt', formats['text'])
        self.assertIn('.md', formats['text'])
    
    @patch('src.processors.image_processor.ImageProcessor.process_image')
    async def test_process_image(self, mock_process_image):
        """测试图像处理"""
        # 设置模拟返回值
        mock_result = {
            'status': 'success',
            'data': {'image_data': 'test'},
            'width': 1920,
            'height': 1080
        }
        mock_process_image.return_value = mock_result
        
        # 处理图像
        result = await self.system.process_file(self.test_files['image'], 'image')
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['file_path'], self.test_files['image'])
        self.assertEqual(result['file_type'], 'image')
        self.assertIn('data', result)
        self.assertIn('metadata', result)
        
        # 验证调用
        mock_process_image.assert_called_once_with(self.test_files['image'])
    
    @patch('src.processors.video_processor.VideoProcessor.process_video')
    @patch('src.processors.media_processor.MediaProcessor.process_video')
    async def test_process_video(self, mock_ffmpeg_process, mock_process_video):
        """测试视频处理"""
        # 设置模拟返回值
        mock_result = {
            'status': 'success',
            'data': {'video_data': 'test'},
            'duration': 120.5,
            'fps': 30.0
        }
        mock_process_video.return_value = mock_result
        mock_ffmpeg_result = {
            'status': 'success',
            'chunks': [{'start_time': 0, 'end_time': 60}],
            'keyframes': ['keyframe1.jpg']
        }
        mock_ffmpeg_process.return_value = mock_ffmpeg_result
        
        # 处理视频
        result = await self.system.process_file(self.test_files['video'], 'video')
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['file_path'], self.test_files['video'])
        self.assertEqual(result['file_type'], 'video')
        self.assertIn('data', result)
        self.assertIn('chunks', result)
        self.assertIn('keyframes', result)
        self.assertIn('metadata', result)
        
        # 验证调用
        mock_process_video.assert_called_once_with(self.test_files['video'])
        mock_ffmpeg_process.assert_called_once_with(self.test_files['video'])
    
    @patch('src.processors.audio_processor.AudioProcessor.process_audio')
    @patch('src.processors.media_processor.MediaProcessor.process_audio')
    async def test_process_audio(self, mock_ffmpeg_process, mock_process_audio):
        """测试音频处理"""
        # 设置模拟返回值
        mock_result = {
            'status': 'success',
            'data': {'audio_data': 'test'},
            'duration': 180.2,
            'sample_rate': 44100
        }
        mock_process_audio.return_value = mock_result
        mock_ffmpeg_result = {
            'status': 'success',
            'segments': [{'type': 'music', 'start_time': 0, 'end_time': 60}]
        }
        mock_ffmpeg_process.return_value = mock_ffmpeg_result
        
        # 处理音频
        result = await self.system.process_file(self.test_files['audio'], 'audio')
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['file_path'], self.test_files['audio'])
        self.assertEqual(result['file_type'], 'audio')
        self.assertIn('data', result)
        self.assertIn('segments', result)
        self.assertIn('metadata', result)
        
        # 验证调用
        mock_process_audio.assert_called_once_with(self.test_files['audio'])
        mock_ffmpeg_process.assert_called_once_with(self.test_files['audio'])
    
    @patch('src.processors.text_processor.TextProcessor.process_text')
    async def test_process_text(self, mock_process_text):
        """测试文本处理"""
        # 设置模拟返回值
        mock_result = {
            'status': 'success',
            'data': {'text_data': 'test'},
            'content': 'This is a test text file.',
            'encoding': 'utf-8'
        }
        mock_process_text.return_value = mock_result
        
        # 处理文本
        result = await self.system.process_file(self.test_files['text'], 'text')
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['file_path'], self.test_files['text'])
        self.assertEqual(result['file_type'], 'text')
        self.assertIn('data', result)
        self.assertIn('metadata', result)
        
        # 验证调用
        mock_process_text.assert_called_once_with(self.test_files['text'])
    
    async def test_process_file_error(self):
        """测试文件处理错误"""
        # 测试不存在的文件
        non_existent_file = os.path.join(self.temp_dir, 'non_existent.jpg')
        result = await self.system.process_file(non_existent_file, 'image')
        
        # 验证结果
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
        self.assertEqual(result['file_path'], non_existent_file)
        self.assertEqual(result['file_type'], 'image')
    
    async def test_process_file_unsupported_type(self):
        """测试不支持的文件类型"""
        # 创建未知类型的文件
        unknown_file = os.path.join(self.temp_dir, 'test.xyz')
        with open(unknown_file, 'wb') as f:
            f.write(b'')
        
        # 处理未知类型文件
        result = await self.system.process_file(unknown_file, 'unknown')
        
        # 验证结果
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
        self.assertEqual(result['file_path'], unknown_file)
        self.assertEqual(result['file_type'], 'unknown')
    
    @patch('src.processors.media_preprocessing_system.MediaPreprocessingSystem.process_file')
    async def test_batch_process_files(self, mock_process_file):
        """测试批量处理文件"""
        # 设置模拟返回值
        mock_process_file.side_effect = [
            {'status': 'success', 'file_path': self.test_files['image']},
            {'status': 'success', 'file_path': self.test_files['video']},
            {'status': 'error', 'error': 'Processing failed', 'file_path': self.test_files['audio']}
        ]
        
        # 批量处理文件
        file_paths = list(self.test_files.values())
        results = await self.system.batch_process_files(file_paths)
        
        # 验证结果
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0]['status'], 'success')
        self.assertEqual(results[1]['status'], 'success')
        self.assertEqual(results[2]['status'], 'error')
        self.assertEqual(results[3]['status'], 'success')
        
        # 验证调用次数
        self.assertEqual(mock_process_file.call_count, 4)


class TestGlobalMediaPreprocessingSystem(unittest.TestCase):
    """全局媒体预处理系统测试类"""
    
    def test_get_media_preprocessing_system(self):
        """测试获取全局媒体预处理系统实例"""
        # 获取实例
        system1 = get_media_preprocessing_system()
        system2 = get_media_preprocessing_system()
        
        # 验证是同一个实例
        self.assertIs(system1, system2)
        self.assertIsInstance(system1, MediaPreprocessingSystem)


class TestMediaPreprocessingSystemIntegration(unittest.TestCase):
    """媒体预处理系统集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建媒体预处理系统实例
        self.system = MediaPreprocessingSystem()
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.processors.image_processor.ImageProcessor._extract_metadata')
    async def test_extract_metadata(self, mock_extract_metadata):
        """测试元数据提取"""
        # 创建测试图像文件
        image_file = os.path.join(self.temp_dir, 'test.jpg')
        with open(image_file, 'wb') as f:
            f.write(b'fake image data')
        
        # 设置模拟返回值
        mock_metadata = {
            'width': 1920,
            'height': 1080,
            'format': 'JPEG'
        }
        mock_extract_metadata.return_value = mock_metadata
        
        # 提取元数据
        metadata = await self.system._extract_metadata(image_file, 'image')
        
        # 验证结果
        self.assertEqual(metadata['file_path'], image_file)
        self.assertEqual(metadata['file_type'], 'image')
        self.assertIn('file_size', metadata)
        self.assertIn('width', metadata)
        self.assertIn('height', metadata)
        self.assertIn('format', metadata)
        
        # 验证调用
        mock_extract_metadata.assert_called_once_with(image_file)


# 运行测试
if __name__ == '__main__':
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTest(unittest.makeSuite(TestMediaPreprocessingSystem))
    suite.addTest(unittest.makeSuite(TestGlobalMediaPreprocessingSystem))
    suite.addTest(unittest.makeSuite(TestMediaPreprocessingSystemIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果
    if result.wasSuccessful():
        print("所有测试通过!")
    else:
        print(f"测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        for test, traceback in result.failures + result.errors:
            print(f"失败测试: {test}")
            print(traceback)