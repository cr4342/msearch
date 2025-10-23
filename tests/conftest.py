"""
pytest配置文件
提供全局测试配置和共享fixture
"""
import pytest
import tempfile
import os
import shutil
import asyncio
from unittest.mock import Mock, patch
import yaml

from src.core.config_manager import ConfigManager


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data_dir():
    """创建临时测试数据目录"""
    temp_dir = tempfile.mkdtemp(prefix="msearch_test_")
    
    # 创建子目录结构
    os.makedirs(os.path.join(temp_dir, "models"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "database"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "logs"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "temp"), exist_ok=True)
    
    yield temp_dir
    
    # 清理临时目录
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def test_config_file(test_data_dir):
    """创建测试配置文件"""
    config_data = {
        'general': {
            'log_level': 'DEBUG',
            'data_dir': test_data_dir
        },
        'features': {
            'enable_face_recognition': True,
            'enable_audio_processing': True,
            'enable_video_processing': True
        },
        'models': {
            'clip_model': 'openai/clip-vit-base-patch32',
            'clap_model': 'laion/clap-htsat-fused',
            'whisper_model': 'openai/whisper-base'
        },
        'processing': {
            'batch_size': 8,  # 测试环境使用较小的批处理大小
            'max_concurrent_tasks': 2,
            'video': {
                'max_resolution': [720, 480],  # 测试环境使用较低分辨率
                'frame_interval': 2
            },
            'audio': {
                'sample_rate': 16000,
                'segment_duration': 5  # 测试环境使用较短的片段
            },
            'timestamp': {
                'accuracy_requirement': 2.0,
                'overlap_buffer': 1.0
            }
        },
        'storage': {
            'qdrant': {
                'host': 'localhost',
                'port': 6333,
                'collection_prefix': 'test_'
            },
            'sqlite': {
                'path': os.path.join(test_data_dir, 'test_msearch.db')
            }
        },
        'embedding': {
            'models_dir': os.path.join(test_data_dir, 'models'),
            'models': {
                'clip': 'clip',
                'clap': 'clap',
                'whisper': 'whisper'
            }
        },
        'device': 'cpu'  # 测试环境强制使用CPU
    }
    
    config_file = os.path.join(test_data_dir, 'test_config.yml')
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
    
    return config_file


@pytest.fixture
def test_config(test_config_file):
    """测试配置管理器实例"""
    return ConfigManager(test_config_file)


@pytest.fixture
def mock_infinity_engines():
    """模拟infinity引擎的全局fixture"""
    with patch('src.business.embedding_engine.AsyncEngineArray') as mock_engine_array:
        import numpy as np
        from unittest.mock import AsyncMock
        
        # 创建模拟引擎
        mock_engine = AsyncMock()
        mock_engine_array.from_args.return_value = mock_engine
        
        # 设置默认返回值
        mock_engine.embed.return_value = [np.random.rand(512).tolist()]
        
        yield mock_engine


@pytest.fixture
def mock_qdrant_client():
    """模拟Qdrant客户端"""
    with patch('src.storage.qdrant_client.QdrantClient') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        # 设置默认返回值
        mock_instance.search_vectors.return_value = [
            {'id': 'test_vector_1', 'score': 0.95, 'payload': {'file_id': 'test_file_1'}},
            {'id': 'test_vector_2', 'score': 0.88, 'payload': {'file_id': 'test_file_2'}},
        ]
        mock_instance.insert_vectors.return_value = True
        mock_instance.create_collection.return_value = True
        mock_instance.collection_exists.return_value = True
        
        yield mock_instance


@pytest.fixture
def mock_sqlite_manager():
    """模拟SQLite管理器"""
    with patch('src.storage.sqlite_manager.SQLiteManager') as mock_manager:
        mock_instance = Mock()
        mock_manager.return_value = mock_instance
        
        # 设置默认返回值
        mock_instance.get_file_metadata.return_value = {
            'file_id': 'test_file_1',
            'file_path': '/test/path/file.mp4',
            'file_type': 'video',
            'file_size': 1024000,
            'created_at': '2024-01-01T00:00:00Z'
        }
        mock_instance.insert_file_metadata.return_value = True
        mock_instance.update_file_metadata.return_value = True
        mock_instance.delete_file_metadata.return_value = True
        
        yield mock_instance


@pytest.fixture
def sample_test_data():
    """提供测试数据样本"""
    import numpy as np
    
    return {
        'image_data': np.random.rand(224, 224, 3).astype(np.float32),
        'audio_data': np.random.rand(16000).astype(np.float32),  # 1秒16kHz音频
        'text_data': "这是一个测试文本内容",
        'vector_data': np.random.rand(512).astype(np.float32),
        'video_metadata': {
            'duration': 60.0,
            'fps': 30.0,
            'resolution': '1280x720',
            'format': 'mp4'
        },
        'audio_metadata': {
            'duration': 30.0,
            'sample_rate': 16000,
            'channels': 1,
            'format': 'wav'
        }
    }


@pytest.fixture
def performance_benchmarks():
    """性能基准测试数据"""
    return {
        'cpu_mode': {
            'text_search_response_time_ms': 500,
            'image_processing_time_s': 2.0,
            'video_processing_fps': 0.5,  # 实时处理的0.5倍
            'memory_usage_mb': 2048,
            'timestamp_accuracy_s': 2.0
        },
        'gpu_mode': {
            'text_search_response_time_ms': 100,
            'image_processing_time_s': 0.5,
            'video_processing_fps': 2.0,  # 实时处理的2倍
            'memory_usage_mb': 4096,
            'gpu_memory_usage_mb': 6144,
            'timestamp_accuracy_s': 2.0
        }
    }


@pytest.fixture
def mock_media_files(test_data_dir):
    """创建模拟媒体文件"""
    import numpy as np
    from PIL import Image
    
    # 创建测试图片
    test_image = Image.fromarray((np.random.rand(224, 224, 3) * 255).astype(np.uint8))
    image_path = os.path.join(test_data_dir, 'test_image.jpg')
    test_image.save(image_path)
    
    # 创建模拟视频文件（空文件，仅用于路径测试）
    video_path = os.path.join(test_data_dir, 'test_video.mp4')
    with open(video_path, 'wb') as f:
        f.write(b'fake_video_data')
    
    # 创建模拟音频文件
    audio_path = os.path.join(test_data_dir, 'test_audio.wav')
    with open(audio_path, 'wb') as f:
        f.write(b'fake_audio_data')
    
    return {
        'image': image_path,
        'video': video_path,
        'audio': audio_path
    }


@pytest.fixture(autouse=True)
def setup_test_logging():
    """设置测试日志"""
    import logging
    
    # 配置测试日志
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # 设置特定模块的日志级别
    logging.getLogger('src.business').setLevel(logging.INFO)
    logging.getLogger('src.storage').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)


@pytest.fixture
def mock_system_resources():
    """模拟系统资源信息"""
    with patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.cpu_count') as mock_cpu_count, \
         patch('torch.cuda.is_available') as mock_cuda_available, \
         patch('torch.cuda.get_device_properties') as mock_gpu_props:
        
        # 设置系统资源mock
        mock_memory.return_value.total = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory.return_value.available = 4 * 1024 * 1024 * 1024  # 4GB可用
        mock_cpu_count.return_value = 8
        mock_cuda_available.return_value = False  # 测试环境默认无GPU
        
        yield {
            'total_memory_gb': 8,
            'available_memory_gb': 4,
            'cpu_cores': 8,
            'gpu_available': False
        }


# 测试标记定义
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "unit: 单元测试标记"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试标记"
    )
    config.addinivalue_line(
        "markers", "performance: 性能测试标记"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试标记"
    )
    config.addinivalue_line(
        "markers", "gpu: 需要GPU的测试标记"
    )
    config.addinivalue_line(
        "markers", "timestamp: 时间戳精度测试标记"
    )


# 测试收集钩子
def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 为慢速测试添加标记
    for item in items:
        if "test_large" in item.name or "test_performance" in item.name:
            item.add_marker(pytest.mark.slow)
        
        if "test_gpu" in item.name or "gpu" in str(item.fspath):
            item.add_marker(pytest.mark.gpu)
        
        if "timestamp" in item.name or "time_accuracy" in item.name:
            item.add_marker(pytest.mark.timestamp)


# 测试会话钩子
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """设置测试环境"""
    # 设置环境变量
    os.environ['MSEARCH_TEST_MODE'] = '1'
    os.environ['MSEARCH_LOG_LEVEL'] = 'DEBUG'
    
    yield
    
    # 清理环境变量
    os.environ.pop('MSEARCH_TEST_MODE', None)
    os.environ.pop('MSEARCH_LOG_LEVEL', None)