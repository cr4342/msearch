import pytest
import tempfile
import os
from pathlib import Path

@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def temp_file():
    """创建临时文件"""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        yield tmp.name
    os.unlink(tmp.name)

@pytest.fixture
def sample_config():
    """提供示例配置"""
    return {
        'database': {
            'sqlite': {
                'path': ':memory:'
            }
        },
        'vector_store': {
            'lancedb': {
                'directory': ':memory:'
            }
        },
        'embedding_engine': {
            'model': 'OFA-Sys/chinese-clip-vit-base-patch16',
            'device': 'cpu'
        },
        'cache': {
            'preprocessing': {
                'directory': '/tmp/msearch/preprocessing_cache',
                'max_size': 1073741824,  # 1GB
                'ttl': 86400  # 24小时
            }
        }
    }

@pytest.fixture
def sample_video_info():
    """提供示例视频信息"""
    return {
        'duration': 120.5,
        'width': 1920,
        'height': 1080,
        'fps': 30.0,
        'codec': 'h264',
        'is_short_video': False,
        'total_segments': 4
    }

@pytest.fixture
def sample_segment_info():
    """提供示例视频片段信息"""
    return {
        'segment_index': 0,
        'start_time': 0.0,
        'end_time': 30.0,
        'duration': 30.0,
        'is_full_video': False,
        'frame_count': 900,
        'key_frames': [0, 300, 600, 899]
    }
