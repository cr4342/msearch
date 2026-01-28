"""
噪音过滤器单元测试
"""

import pytest
from src.data.extractors.noise_filter import (
    NoiseFilterManager,
    ImageNoiseFilter,
    VideoNoiseFilter,
    AudioNoiseFilter,
    TextNoiseFilter
)


class TestImageNoiseFilter:
    """图像噪音过滤器测试"""
    
    @pytest.fixture
    def image_filter(self):
        """创建图像过滤器实例"""
        config = {
            "min_dimension": 32,
            "min_file_size": 1024,
            "allowed_formats": ["jpg", "jpeg", "png", "bmp", "gif", "webp"],
            "min_quality": 0.1
        }
        return ImageNoiseFilter(config)
    
    def test_filter_valid_image(self, image_filter):
        """测试有效图像过滤"""
        media_info = {
            "width": 1920,
            "height": 1080,
            "file_size": 1024000,
            "file_ext": "jpg"
        }
        should_keep, reason = image_filter.filter(media_info)
        assert should_keep is True
        assert "符合要求" in reason
    
    def test_filter_small_dimension(self, image_filter):
        """测试尺寸过小的图像"""
        media_info = {
            "width": 16,
            "height": 16,
            "file_size": 1024000,
            "file_ext": "jpg"
        }
        should_keep, reason = image_filter.filter(media_info)
        assert should_keep is False
        assert "尺寸过小" in reason
    
    def test_filter_small_file_size(self, image_filter):
        """测试文件大小过小的图像"""
        media_info = {
            "width": 1920,
            "height": 1080,
            "file_size": 512,
            "file_ext": "jpg"
        }
        should_keep, reason = image_filter.filter(media_info)
        assert should_keep is False
        assert "文件大小过小" in reason
    
    def test_filter_unsupported_format(self, image_filter):
        """测试不支持的图像格式"""
        media_info = {
            "width": 1920,
            "height": 1080,
            "file_size": 1024000,
            "file_ext": "tiff"
        }
        should_keep, reason = image_filter.filter(media_info)
        assert should_keep is False
        assert "不支持的图像格式" in reason
    
    def test_filter_low_quality(self, image_filter):
        """测试质量过低的图像"""
        media_info = {
            "width": 1920,
            "height": 1080,
            "file_size": 1024000,
            "file_ext": "jpg",
            "quality_score": 0.05
        }
        should_keep, reason = image_filter.filter(media_info)
        assert should_keep is False
        assert "图像质量过低" in reason
    
    def test_get_stats(self, image_filter):
        """测试获取统计信息"""
        # 过滤一些图像
        image_filter.filter({"width": 1920, "height": 1080, "file_size": 1024000, "file_ext": "jpg"})
        image_filter.filter({"width": 16, "height": 16, "file_size": 1024000, "file_ext": "jpg"})
        
        stats = image_filter.get_stats()
        assert stats["total_processed"] == 2
        assert stats["passed"] == 1
        assert stats["filtered_out"] == 1
        assert "small_dimension" in stats["filter_reasons"]


class TestVideoNoiseFilter:
    """视频噪音过滤器测试"""
    
    @pytest.fixture
    def video_filter(self):
        """创建视频过滤器实例"""
        config = {
            "min_duration": 0.5,
            "min_file_size": 10240,
            "allowed_formats": ["mp4", "avi", "mov", "wmv", "flv", "mkv"],
            "min_resolution": 160
        }
        return VideoNoiseFilter(config)
    
    def test_filter_valid_video(self, video_filter):
        """测试有效视频过滤"""
        media_info = {
            "duration": 10.0,
            "file_size": 10240000,
            "width": 1920,
            "height": 1080,
            "file_ext": "mp4"
        }
        should_keep, reason = video_filter.filter(media_info)
        assert should_keep is True
        assert "符合要求" in reason
    
    def test_filter_short_duration(self, video_filter):
        """测试时长过短的视频"""
        media_info = {
            "duration": 0.3,
            "file_size": 10240000,
            "width": 1920,
            "height": 1080,
            "file_ext": "mp4"
        }
        should_keep, reason = video_filter.filter(media_info)
        assert should_keep is False
        assert "时长过短" in reason
    
    def test_filter_small_file_size(self, video_filter):
        """测试文件大小过小的视频"""
        media_info = {
            "duration": 10.0,
            "file_size": 5120,
            "width": 1920,
            "height": 1080,
            "file_ext": "mp4"
        }
        should_keep, reason = video_filter.filter(media_info)
        assert should_keep is False
        assert "文件大小过小" in reason
    
    def test_filter_low_resolution(self, video_filter):
        """测试分辨率过低的视频"""
        media_info = {
            "duration": 10.0,
            "file_size": 10240000,
            "width": 120,
            "height": 80,
            "file_ext": "mp4"
        }
        should_keep, reason = video_filter.filter(media_info)
        assert should_keep is False
        assert "分辨率过低" in reason


class TestAudioNoiseFilter:
    """音频噪音过滤器测试"""
    
    @pytest.fixture
    def audio_filter(self):
        """创建音频过滤器实例"""
        config = {
            "min_duration": 3.0,
            "min_file_size": 5120,
            "allowed_formats": ["mp3", "wav", "aac", "ogg", "flac", "wma"],
            "min_bitrate": 32
        }
        return AudioNoiseFilter(config)
    
    def test_filter_valid_audio(self, audio_filter):
        """测试有效音频过滤"""
        media_info = {
            "duration": 10.0,
            "file_size": 1024000,
            "file_ext": "mp3",
            "bitrate": 128
        }
        should_keep, reason = audio_filter.filter(media_info)
        assert should_keep is True
        assert "符合要求" in reason
    
    def test_filter_short_duration(self, audio_filter):
        """测试时长过短的音频"""
        media_info = {
            "duration": 2.0,
            "file_size": 1024000,
            "file_ext": "mp3",
            "bitrate": 128
        }
        should_keep, reason = audio_filter.filter(media_info)
        assert should_keep is False
        assert "时长过短" in reason
    
    def test_filter_low_bitrate(self, audio_filter):
        """测试比特率过低的音频"""
        media_info = {
            "duration": 10.0,
            "file_size": 1024000,
            "file_ext": "mp3",
            "bitrate": 16
        }
        should_keep, reason = audio_filter.filter(media_info)
        assert should_keep is False
        assert "比特率过低" in reason


class TestTextNoiseFilter:
    """文本噪音过滤器测试"""
    
    @pytest.fixture
    def text_filter(self):
        """创建文本过滤器实例"""
        config = {
            "min_length": 5,
            "min_file_size": 10,
            "allowed_formats": ["txt", "md", "pdf", "docx", "xlsx", "csv"],
            "min_quality": 0.1
        }
        return TextNoiseFilter(config)
    
    def test_filter_valid_text(self, text_filter):
        """测试有效文本过滤"""
        media_info = {
            "text_length": 100,
            "file_size": 1024,
            "file_ext": "txt"
        }
        should_keep, reason = text_filter.filter(media_info)
        assert should_keep is True
        assert "符合要求" in reason
    
    def test_filter_short_text(self, text_filter):
        """测试文本长度过短"""
        media_info = {
            "text_length": 3,
            "file_size": 1024,
            "file_ext": "txt"
        }
        should_keep, reason = text_filter.filter(media_info)
        assert should_keep is False
        assert "文本长度过短" in reason


class TestNoiseFilterManager:
    """噪音过滤管理器测试"""
    
    @pytest.fixture
    def manager(self):
        """创建噪音过滤管理器实例"""
        config = {
            "enable": True,
            "image_filter": {
                "enable": True,
                "min_dimension": 32,
                "min_file_size": 1024,
                "allowed_formats": ["jpg", "jpeg", "png", "bmp", "gif", "webp"],
                "min_quality": 0.1
            },
            "video_filter": {
                "enable": True,
                "min_duration": 0.5,
                "min_file_size": 10240,
                "allowed_formats": ["mp4", "avi", "mov", "wmv", "flv", "mkv"],
                "min_resolution": 160
            },
            "audio_filter": {
                "enable": True,
                "min_duration": 3.0,
                "min_file_size": 5120,
                "allowed_formats": ["mp3", "wav", "aac", "ogg", "flac", "wma"],
                "min_bitrate": 32
            },
            "text_filter": {
                "enable": True,
                "min_length": 5,
                "min_file_size": 10,
                "allowed_formats": ["txt", "md", "pdf", "docx", "xlsx", "csv"],
                "min_quality": 0.1
            }
        }
        return NoiseFilterManager(config)
    
    def test_filter_image(self, manager):
        """测试过滤图像"""
        media_info = {
            "width": 1920,
            "height": 1080,
            "file_size": 1024000,
            "file_ext": "jpg"
        }
        should_keep, reason = manager.filter("image", media_info)
        assert should_keep is True
    
    def test_filter_video(self, manager):
        """测试过滤视频"""
        media_info = {
            "duration": 10.0,
            "file_size": 10240000,
            "width": 1920,
            "height": 1080,
            "file_ext": "mp4"
        }
        should_keep, reason = manager.filter("video", media_info)
        assert should_keep is True
    
    def test_filter_audio(self, manager):
        """测试过滤音频"""
        media_info = {
            "duration": 10.0,
            "file_size": 1024000,
            "file_ext": "mp3",
            "bitrate": 128
        }
        should_keep, reason = manager.filter("audio", media_info)
        assert should_keep is True
    
    def test_filter_text(self, manager):
        """测试过滤文本"""
        media_info = {
            "text_length": 100,
            "file_size": 1024,
            "file_ext": "txt"
        }
        should_keep, reason = manager.filter("text", media_info)
        assert should_keep is True
    
    def test_filter_unsupported_media_type(self, manager):
        """测试不支持的媒体类型"""
        media_info = {"file_size": 1024}
        should_keep, reason = manager.filter("unknown", media_info)
        assert should_keep is True
        assert "不支持过滤" in reason
    
    def test_get_filter_stats(self, manager):
        """测试获取过滤统计信息"""
        # 过滤一些媒体
        manager.filter("image", {"width": 1920, "height": 1080, "file_size": 1024000, "file_ext": "jpg"})
        manager.filter("image", {"width": 16, "height": 16, "file_size": 1024000, "file_ext": "jpg"})
        
        stats = manager.get_filter_stats()
        assert "image" in stats
        assert stats["image"]["total_processed"] == 2
        assert stats["image"]["passed"] == 1
        assert stats["image"]["filtered_out"] == 1
    
    def test_update_filter_config(self, manager):
        """测试更新过滤器配置"""
        new_config = {"min_dimension": 64}
        result = manager.update_filter_config("image", new_config)
        assert result is True
    
    def test_reset_stats(self, manager):
        """测试重置统计信息"""
        # 过滤一些媒体
        manager.filter("image", {"width": 1920, "height": 1080, "file_size": 1024000, "file_ext": "jpg"})
        
        # 重置统计信息
        manager.reset_stats()
        
        # 检查统计信息已重置
        stats = manager.get_filter_stats()
        assert stats["image"]["total_processed"] == 0
    
    def test_is_enabled(self, manager):
        """测试检查是否启用"""
        assert manager.is_enabled() is True
    
    def test_get_supported_media_types(self, manager):
        """测试获取支持的媒体类型"""
        types = manager.get_supported_media_types()
        assert "image" in types
        assert "video" in types
        assert "audio" in types
        assert "text" in types
    
    def test_disabled_manager(self):
        """测试禁用的管理器"""
        config = {"enable": False}
        manager = NoiseFilterManager(config)
        
        media_info = {"width": 16, "height": 16, "file_size": 1024000, "file_ext": "jpg"}
        should_keep, reason = manager.filter("image", media_info)
        assert should_keep is True
        assert "未启用" in reason
    
    def test_default_config(self):
        """测试默认配置"""
        manager = NoiseFilterManager()
        assert manager.is_enabled() is True
        assert len(manager.get_supported_media_types()) == 4