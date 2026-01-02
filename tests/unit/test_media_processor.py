"""
MediaProcessor单元测试
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

from src.processing_service.media_processor import MediaProcessor


class TestMediaProcessor:
    """MediaProcessor单元测试类"""
    
    @pytest.fixture
    def media_processor(self):
        """创建MediaProcessor实例"""
        return MediaProcessor()
    
    @pytest.fixture
    def sample_image(self):
        """创建测试用的图像文件"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(b'fake image data')
            return tmp.name
    
    @pytest.fixture
    def sample_video(self):
        """创建测试用的视频文件"""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b'fake video data')
            return tmp.name
    
    @pytest.fixture
    def sample_audio(self):
        """创建测试用的音频文件"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp.write(b'fake audio data')
            return tmp.name
    
    def test_initialization(self, media_processor):
        """测试MediaProcessor初始化"""
        assert media_processor is not None
        assert hasattr(media_processor, 'image_extensions')
        assert hasattr(media_processor, 'video_extensions')
        assert hasattr(media_processor, 'audio_extensions')
    
    @pytest.mark.asyncio
    @patch('src.processing_service.media_processor.asyncio.create_subprocess_exec')
    async def test_process_image(self, mock_create_subprocess_exec, media_processor, sample_image):
        """测试图像处理功能"""
        # 模拟FFmpeg调用
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'', b'')
        mock_process.returncode = 0
        mock_create_subprocess_exec.return_value = mock_process
        
        # 测试图像类型
        strategy = {'preprocessing': {'resize': True, 'target_resolution': 720}}
        result = await media_processor._process_image(sample_image, strategy)
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'segments' in result
        assert len(result['segments']) > 0
    
    @pytest.mark.asyncio
    @patch('src.processing_service.media_processor.asyncio.create_subprocess_exec')
    async def test_extract_video_metadata(self, mock_create_subprocess_exec, media_processor, sample_video):
        """测试提取视频元数据"""
        # 模拟ffprobe调用
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'{"format": {"duration": "10.0", "size": "1000"}, "streams": [{"codec_type": "video", "width": "1920", "height": "1080", "r_frame_rate": "30/1"}]}', b'')
        mock_process.returncode = 0
        mock_create_subprocess_exec.return_value = mock_process
        
        result = await media_processor._extract_video_metadata(sample_video)
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'duration' in result
        assert result['duration'] == 10.0
        assert 'width' in result
        assert result['width'] == 1920
        assert 'height' in result
        assert result['height'] == 1080
    
    @pytest.mark.asyncio
    @patch('src.processing_service.media_processor.asyncio.create_subprocess_exec')
    async def test_extract_audio_metadata(self, mock_create_subprocess_exec, media_processor, sample_audio):
        """测试提取音频元数据"""
        # 模拟ffprobe调用
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'{"format": {"duration": "5.0", "size": "500"}, "streams": [{"codec_type": "audio", "sample_rate": "44100", "channels": "2", "codec_name": "mp3", "bit_rate": "128000"}]}', b'')
        mock_process.returncode = 0
        mock_create_subprocess_exec.return_value = mock_process
        
        result = await media_processor._extract_audio_metadata(sample_audio)
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'duration' in result
        assert result['duration'] == 5.0
    
    @pytest.mark.asyncio
    @patch('src.processing_service.media_processor.asyncio.create_subprocess_exec')
    async def test_detect_video_scenes(self, mock_create_subprocess_exec, media_processor, sample_video):
        """测试视频场景检测"""
        # 模拟FFmpeg调用
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'', b'')
        mock_process.returncode = 0
        mock_create_subprocess_exec.return_value = mock_process
        
        result = await media_processor._detect_video_scenes(sample_video)
        
        assert result is not None
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    @patch('src.processing_service.media_processor.asyncio.create_subprocess_exec')
    async def test_convert_audio_format(self, mock_create_subprocess_exec, media_processor, sample_audio):
        """测试音频格式转换"""
        # 模拟FFmpeg调用
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'', b'')
        mock_process.returncode = 0
        mock_create_subprocess_exec.return_value = mock_process
        
        result = await media_processor._convert_audio_format(sample_audio, target_format='wav')
        
        assert result is not None
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    @patch('src.processing_service.media_processor.MediaProcessor._process_image')
    @patch('src.processing_service.media_processor.MediaProcessor._process_video')
    async def test_process_video(self, mock_process_video, mock_process_image, media_processor, sample_video):
        """测试视频处理"""
        # 模拟_process_video方法
        mock_process_video.return_value = {'status': 'COMPLETED'}
        
        result = await media_processor.process_video(sample_video)
        
        assert result is not None
        assert result['status'] == 'COMPLETED'
    
    @pytest.mark.asyncio
    @patch('src.processing_service.media_processor.MediaProcessor._process_image')
    @patch('src.processing_service.media_processor.MediaProcessor._process_audio')
    async def test_process_audio(self, mock_process_audio, mock_process_image, media_processor, sample_audio):
        """测试音频处理"""
        # 模拟_process_audio方法
        mock_process_audio.return_value = {'status': 'COMPLETED'}
        
        result = await media_processor.process_audio(sample_audio)
        
        assert result is not None
        assert result['status'] == 'COMPLETED'
    
    @pytest.mark.asyncio
    @patch('src.processing_service.media_processor.MediaProcessor._process_image')
    async def test_process_invalid_file(self, mock_process_image, media_processor):
        """测试处理无效文件"""
        # 模拟_process_image方法抛出异常
        mock_process_image.side_effect = Exception("Invalid file format")
        
        result = await media_processor.process_image("invalid_file.txt")
        
        assert result is not None
        assert result['status'] == 'FAILED'
    
    @pytest.mark.asyncio
    async def test_resize_image(self, media_processor):
        """测试图像缩放"""
        # 这个测试需要FFmpeg，所以我们模拟调用
        with patch('src.processing_service.media_processor.asyncio.create_subprocess_exec') as mock_create_subprocess_exec:
            mock_process = MagicMock()
            mock_process.communicate.return_value = (b'', b'')
            mock_process.returncode = 0
            mock_create_subprocess_exec.return_value = mock_process
            
            result = await media_processor._resize_image("fake_image.jpg", 720)
            
            assert result is not None
    
    def test_get_files_in_directory(self, media_processor):
        """测试获取目录中的文件"""
        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            with open(os.path.join(tmpdir, 'test.jpg'), 'w') as f:
                f.write('test')
            with open(os.path.join(tmpdir, 'test.mp4'), 'w') as f:
                f.write('test')
            with open(os.path.join(tmpdir, 'test.mp3'), 'w') as f:
                f.write('test')
            with open(os.path.join(tmpdir, 'test.txt'), 'w') as f:
                f.write('test')

            # 测试获取文件
            files = media_processor._get_files_in_directory(tmpdir)
            
            assert len(files) == 3  # 只应该返回媒体文件
    
    @pytest.mark.asyncio
    @patch('src.processing_service.media_processor.asyncio.create_subprocess_exec')
    async def test_extract_audio_from_video(self, mock_create_subprocess_exec, media_processor, sample_video):
        """测试从视频中提取音频"""
        # 模拟FFmpeg调用
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'', b'')
        mock_process.returncode = 0
        mock_create_subprocess_exec.return_value = mock_process
        
        result = await media_processor._extract_audio_from_video(sample_video)
        
        assert result is not None
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    @patch('src.processing_service.media_processor.asyncio.create_subprocess_exec')
    async def test_extract_image_metadata(self, mock_create_subprocess_exec, media_processor, sample_image):
        """测试提取图像元数据"""
        # 模拟ffprobe调用
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'{"format": {"duration": "0.0"}, "streams": [{"codec_type": "video", "width": "1920", "height": "1080"}]}', b'')
        mock_process.returncode = 0
        mock_create_subprocess_exec.return_value = mock_process
        
        result = await media_processor._extract_image_metadata(sample_image)
        
        assert result is not None
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    @patch('src.processing_service.media_processor.asyncio.create_subprocess_exec')
    async def test_classify_audio(self, mock_create_subprocess_exec, media_processor, sample_audio):
        """测试音频分类"""
        # 模拟FFmpeg调用
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'', b'')
        mock_process.returncode = 0
        mock_create_subprocess_exec.return_value = mock_process
        
        result = await media_processor._classify_audio(sample_audio)
        
        assert result is not None
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_get_files_in_directory_empty(self, media_processor):
        """测试获取空目录中的文件"""
        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            # 测试获取文件
            files = media_processor._get_files_in_directory(tmpdir)
            
            assert len(files) == 0
    
    @pytest.mark.asyncio
    @patch('src.processing_service.media_processor.MediaProcessor._process_image')
    async def test_processing_error_handling(self, mock_process_image, media_processor, sample_image):
        """测试错误处理"""
        # 模拟_process_image方法抛出异常
        mock_process_image.return_value = {'status': 'FAILED', 'error': 'Test error'}
        
        result = await media_processor.process_image(sample_image)
        
        assert result is not None
        assert result['status'] == 'FAILED'
        assert 'error' in result
