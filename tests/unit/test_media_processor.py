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
        assert 'sample_rate' in result
        assert result['sample_rate'] == 44100
    
    @patch('src.processing_service.media_processor.asyncio.create_subprocess_exec')
    @patch('src.processing_service.media_processor.MediaProcessor._extract_video_metadata')
    async def test_detect_video_scenes(self, mock_extract_metadata, mock_create_subprocess_exec, media_processor, sample_video):
        """测试视频场景检测"""
        # 模拟视频元数据
        mock_extract_metadata.return_value = {"duration": 10.0}
        
        # 模拟ffmpeg调用
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'', b'select:1.000000 pts_time:0.5\nselect:1.000000 pts_time:5.5')
        mock_process.returncode = 0
        mock_create_subprocess_exec.return_value = mock_process
        
        result = await media_processor._detect_video_scenes(sample_video, max_duration=5.0, target_fps=8)
        
        assert result is not None
        assert isinstance(result, list)
    
    @patch('src.processing_service.media_processor.asyncio.create_subprocess_exec')
    async def test_convert_audio_format(self, mock_create_subprocess_exec, media_processor, sample_audio):
        """测试音频格式转换"""
        # 模拟ffmpeg调用
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'', b'')
        mock_process.returncode = 0
        mock_create_subprocess_exec.return_value = mock_process
        
        result = await media_processor._convert_audio_format(sample_audio, sample_rate=16000, channels=1)
        
        assert result is not None
        assert isinstance(result, str)
        assert Path(result).exists()
    
    @patch('src.processing_service.media_processor.InceptionResnetV1')
    @patch('src.processing_service.media_processor.MTCNN')
    @patch('src.processing_service.media_processor.MediaProcessor._extract_video_metadata')
    @patch('src.processing_service.media_processor.MediaProcessor._detect_video_scenes')
    @patch('src.processing_service.media_processor.MediaProcessor._extract_audio_from_video')
    async def test_process_video(self, 
                                mock_extract_audio, 
                                mock_detect_scenes, 
                                mock_extract_metadata, 
                                mock_mtcnn, 
                                mock_resnet, 
                                media_processor, 
                                sample_video):
        """测试视频处理功能"""
        # 模拟依赖
        mock_extract_metadata.return_value = {"duration": 10.0, "has_audio": True}
        mock_detect_scenes.return_value = [{'id': 'test', 'segment_type': 'video_frame'}]
        mock_extract_audio.return_value = '/fake/audio/path.wav'
        
        strategy = {'preprocessing': {'scene_detection': True, 'max_segment_duration': 5, 'target_fps': 8, 'audio_separation': True}}
        result = await media_processor._process_video(sample_video, strategy)
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'segments' in result
        assert len(result['segments']) > 0
    
    @patch('src.processing_service.media_processor.inaSpeechSegmenter')
    @patch('src.processing_service.media_processor.MediaProcessor._extract_audio_metadata')
    async def test_process_audio(self, mock_extract_metadata, mock_ina_segmenter, media_processor, sample_audio):
        """测试音频处理功能"""
        # 模拟依赖
        mock_extract_metadata.return_value = {"duration": 5.0}
        mock_segmenter = MagicMock()
        mock_segmenter.return_value = [('speech', 0.0, 5.0)]
        mock_ina_segmenter.Segmenter.return_value = mock_segmenter
        
        strategy = {'preprocessing': {'format_conversion': True, 'sample_rate': 16000, 'channels': 1}}
        result = await media_processor._process_audio(sample_audio, strategy)
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'segments' in result
        assert len(result['segments']) > 0
    
    @patch('src.processing_service.media_processor.MediaProcessor._extract_video_metadata')
    @patch('src.processing_service.media_processor.MediaProcessor._detect_video_scenes')
    async def test_process_invalid_file(self, mock_detect_scenes, mock_extract_metadata, media_processor):
        """测试处理无效文件"""
        # 创建无效文件
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b'fake text data')
            invalid_file = tmp.name
        
        strategy = {}
        with pytest.raises(ValueError):
            await media_processor.process(invalid_file, strategy)
    
    def test_parse_fps(self, media_processor):
        """测试帧率解析"""
        assert media_processor._parse_fps('30/1') == 30.0
        assert media_processor._parse_fps('60/1') == 60.0
        assert media_processor._parse_fps('0/1') == 0.0
        assert media_processor._parse_fps('29.97') == 29.97
    
    @patch('src.processing_service.media_processor.InceptionResnetV1')
    @patch('src.processing_service.media_processor.MTCNN')
    @patch('src.processing_service.media_processor.asyncio.create_subprocess_exec')
    async def test_resize_image(self, mock_create_subprocess_exec, mock_mtcnn, mock_resnet, media_processor):
        """测试图像缩放功能"""
        # 模拟FFmpeg调用
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'', b'')
        mock_process.returncode = 0
        mock_create_subprocess_exec.return_value = mock_process
        
        # 创建测试图像数据
        test_image = b'fake image data'
        result = await media_processor._resize_image(test_image, 720)
        
        assert result is not None
        assert isinstance(result, bytes)
    
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
            files = asyncio.run(media_processor._get_files_in_directory(tmpdir))
            
            assert len(files) == 3
            assert all(file.endswith(('.jpg', '.mp4', '.mp3')) for file in files)
    
    # 清理测试文件
    def teardown_method(self):
        """测试方法执行后清理临时文件"""
        # 清理可能遗留的临时文件
        for file in Path('.').glob('*.jpg'):
            if 'fake' in str(file):
                file.unlink()
        for file in Path('.').glob('*.mp4'):
            if 'fake' in str(file):
                file.unlink()
        for file in Path('.').glob('*.mp3'):
            if 'fake' in str(file):
                file.unlink()
        for file in Path('.').glob('*.wav'):
            if 'fake' in str(file):
                file.unlink()
    
    @patch('src.processing_service.media_processor.asyncio.create_subprocess_exec')
    async def test_extract_audio_from_video(self, mock_create_subprocess_exec, media_processor, sample_video):
        """测试从视频中提取音频"""
        # 模拟ffmpeg调用
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'', b'')
        mock_process.returncode = 0
        mock_create_subprocess_exec.return_value = mock_process
        
        result = await media_processor._extract_audio_from_video(sample_video)
        
        assert result is not None
        assert isinstance(result, str)
        assert Path(result).exists()
    
    @patch('src.processing_service.media_processor.asyncio.create_subprocess_exec')
    async def test_extract_image_metadata(self, mock_create_subprocess_exec, media_processor, sample_image):
        """测试提取图像元数据"""
        # 模拟PIL库
        with patch('src.processing_service.media_processor.Image') as mock_image:
            mock_img_instance = MagicMock()
            mock_img_instance.width = 1920
            mock_img_instance.height = 1080
            mock_img_instance.format = 'JPEG'
            mock_img_instance.mode = 'RGB'
            mock_img_instance.info = {'author': 'test'}
            mock_image.open.return_value.__enter__.return_value = mock_img_instance
            
            result = await media_processor._extract_image_metadata(sample_image)
            
            assert result is not None
            assert isinstance(result, dict)
            assert result['width'] == 1920
            assert result['height'] == 1080
            assert result['format'] == 'JPEG'
    
    @patch('src.processing_service.media_processor.asyncio.create_subprocess_exec')
    async def test_classify_audio(self, mock_create_subprocess_exec, media_processor, sample_audio):
        """测试音频分类"""
        # 模拟inaSpeechSegmenter
        with patch('src.processing_service.media_processor.Segmenter') as mock_segmenter:
            mock_seg_instance = MagicMock()
            mock_seg_instance.return_value = [('speech', 0.0, 2.0), ('music', 2.0, 5.0)]
            mock_segmenter.return_value = mock_seg_instance
            
            result = await media_processor._classify_audio(sample_audio)
            
            assert result is not None
            assert isinstance(result, str)
    
    async def test_get_files_in_directory_empty(self, media_processor):
        """测试获取空目录中的文件"""
        # 创建临时空目录
        with tempfile.TemporaryDirectory() as tmpdir:
            files = await media_processor._get_files_in_directory(tmpdir)
            
            assert len(files) == 0
    
    @patch('src.processing_service.media_processor.asyncio.create_subprocess_exec')
    async def test_processing_error_handling(self, mock_create_subprocess_exec, media_processor, sample_video):
        """测试处理错误时的异常处理"""
        # 模拟ffmpeg调用失败
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'', b'Error: Invalid input')
        mock_process.returncode = 1
        mock_create_subprocess_exec.return_value = mock_process
        
        with pytest.raises(Exception):
            await media_processor._extract_video_metadata(sample_video)