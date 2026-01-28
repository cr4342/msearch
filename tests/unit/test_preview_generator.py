"""
测试预览生成器
"""

import pytest
import tempfile
from pathlib import Path
from src.data.generators.preview_generator import PreviewGenerator, PreviewType


@pytest.fixture
def temp_cache_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def preview_generator_config(temp_cache_dir):
    return {
        'cache_dir': str(temp_cache_dir)
    }


@pytest.fixture
def preview_generator(preview_generator_config):
    generator = PreviewGenerator(preview_generator_config)
    yield generator
    # 清理
    generator.clear_preview_cache()


class TestPreviewGenerator:
    """测试预览生成器功能"""
    
    def test_initialize(self, preview_generator_config):
        """测试初始化"""
        generator = PreviewGenerator(preview_generator_config)
        assert generator is not None
        assert isinstance(generator, PreviewGenerator)
    
    def test_get_preview_filename(self, preview_generator):
        """测试获取预览文件名"""
        file_id = "test-file-id"
        
        # 测试不同预览类型
        assert preview_generator.get_preview_filename(file_id, PreviewType.THUMBNAIL) == "test-file-id.jpg"
        assert preview_generator.get_preview_filename(file_id, PreviewType.VIDEO_PREVIEW) == "test-file-id.mp4"
        assert preview_generator.get_preview_filename(file_id, PreviewType.GIF_PREVIEW) == "test-file-id.gif"
        assert preview_generator.get_preview_filename(file_id, PreviewType.AUDIO_WAVEFORM) == "test-file-id.png"
    
    def test_get_preview_path(self, preview_generator):
        """测试获取预览路径"""
        file_id = "test-file-id"
        
        # 测试获取预览路径
        path = preview_generator.get_preview_path(file_id, PreviewType.THUMBNAIL)
        assert file_id in path
        assert PreviewType.THUMBNAIL in path
    
    def test_has_preview(self, preview_generator):
        """测试检查预览是否存在"""
        file_id = "test-file-id"
        
        # 不存在的预览
        assert not preview_generator.has_preview(file_id, PreviewType.THUMBNAIL)
    
    def test_get_cache_usage(self, preview_generator):
        """测试获取缓存使用情况"""
        usage = preview_generator.get_cache_usage()
        assert 'total_size' in usage
        assert 'file_count' in usage
        assert usage['total_size'] >= 0
        assert usage['file_count'] >= 0


class TestPreviewType:
    """测试预览类型定义"""
    
    def test_preview_type_constants(self):
        """测试预览类型常量"""
        assert PreviewType.THUMBNAIL == "thumbnail"
        assert PreviewType.SMALL_PREVIEW == "small"
        assert PreviewType.MEDIUM_PREVIEW == "medium"
        assert PreviewType.LARGE_PREVIEW == "large"
        assert PreviewType.GIF_PREVIEW == "gif"
        assert PreviewType.VIDEO_PREVIEW == "video"
        assert PreviewType.AUDIO_WAVEFORM == "waveform"