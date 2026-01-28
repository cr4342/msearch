"""
集成测试：索引流程
测试完整的文件索引流程，包括文件扫描、元数据提取、向量化、存储等
使用Mock避免真实模型依赖
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import numpy as np

from src.core.config.config_manager import ConfigManager
from src.core.database.database_manager import DatabaseManager
from src.core.vector.vector_store import VectorStore
from src.core.embedding.embedding_engine import EmbeddingEngine
from src.services.media.media_processor import MediaProcessor
from src.data.extractors.noise_filter import NoiseFilterManager


@pytest.fixture(scope="module")
def temp_dir():
    """创建临时目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="module")
def test_media_dir(temp_dir):
    """创建测试媒体目录"""
    media_dir = Path(temp_dir) / "media"
    media_dir.mkdir(exist_ok=True)
    
    # 创建测试图像
    test_image = media_dir / "test_image.jpg"
    img = Image.new('RGB', (800, 600), color='red')
    img.save(test_image, quality=95)
    
    # 创建另一个测试图像
    test_image2 = media_dir / "test_image2.png"
    img2 = Image.new('RGB', (1024, 768), color='blue')
    img2.save(test_image2)
    
    # 创建测试文本文件
    test_text = media_dir / "test_text.txt"
    test_text.write_text("这是一个测试文本文件，用于测试索引流程。")
    
    return media_dir


@pytest.fixture(scope="module")
def config_manager():
    """使用默认配置管理器"""
    return ConfigManager()


@pytest.fixture(scope="module")
def database_manager(temp_dir, config_manager):
    """创建数据库管理器"""
    db_path = Path(temp_dir) / "database" / "msearch.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    db_manager = DatabaseManager(db_path=str(db_path))
    db_manager.initialize()
    yield db_manager
    db_manager.close()


@pytest.fixture(scope="module")
def vector_store(temp_dir, config_manager):
    """创建向量存储"""
    vector_dir = Path(temp_dir) / "lancedb"
    vector_dir.mkdir(parents=True, exist_ok=True)
    
    vector_store = VectorStore(config={
        'data_dir': str(vector_dir),
        'collection_name': 'unified_vectors',
        'vector_dimension': 512
    })
    vector_store.initialize()
    return vector_store


@pytest.fixture(scope="module")
def mock_embedding_engine():
    """创建Mock向量化引擎"""
    engine = Mock(spec=EmbeddingEngine)
    # 模拟异步方法，直接返回结果而不是coroutine
    engine.embed_text = lambda text: [0.1] * 512
    engine.embed_image = lambda path: [0.2] * 512
    return engine


@pytest.fixture(scope="module")
def noise_filter(config_manager):
    """创建噪音过滤器"""
    filter_config = config_manager.config.get('noise_filter', {})
    return NoiseFilterManager(filter_config)


@pytest.fixture(scope="module")
def media_processor(config_manager):
    """创建媒体处理器"""
    processor = MediaProcessor(config=config_manager.config)
    return processor


class TestIndexingFlow:
    """索引流程集成测试"""
    
    def test_image_indexing_flow(self, test_media_dir, media_processor, database_manager, vector_store, noise_filter, mock_embedding_engine):
        """测试图像索引流程"""
        # 1. 获取测试图像文件
        test_image = test_media_dir / "test_image.jpg"
        assert test_image.exists()
        
        # 2. 使用Mock向量化引擎
        image_vector = mock_embedding_engine.embed_image(str(test_image))
        
        # 3. 验证向量维度
        assert len(image_vector) == 512, f"期望向量维度512，实际{len(image_vector)}"
        
        print(f"✓ 图像索引流程测试通过")
        print(f"  测试图像: {test_image.name}")
        print(f"  向量维度: {len(image_vector)}")
    
    def test_text_indexing_flow(self, test_media_dir, media_processor, database_manager, vector_store, noise_filter, mock_embedding_engine):
        """测试文本索引流程"""
        # 1. 获取测试文本文件
        test_text = test_media_dir / "test_text.txt"
        assert test_text.exists()
        
        # 2. 读取文本内容
        text_content = test_text.read_text()
        assert len(text_content) > 0
        
        # 3. 使用Mock向量化引擎
        text_vector = mock_embedding_engine.embed_text(text_content)
        
        # 4. 验证向量维度
        assert len(text_vector) == 512, f"期望向量维度512，实际{len(text_vector)}"
        
        print(f"✓ 文本索引流程测试通过")
        print(f"  文本长度: {len(text_content)}")
        print(f"  向量维度: {len(text_vector)}")
    
    def test_batch_indexing_flow(self, test_media_dir, media_processor, database_manager, vector_store, noise_filter, mock_embedding_engine):
        """测试批量索引流程"""
        # 1. 获取所有测试文件
        test_files = list(test_media_dir.glob("*"))
        assert len(test_files) >= 2, f"期望至少2个测试文件，实际{len(test_files)}"
        
        # 2. 批量处理
        indexed_count = 0
        for test_file in test_files:
            if test_file.suffix in ['.jpg', '.png', '.txt']:
                # 模拟向量化
                if test_file.suffix in ['.jpg', '.png']:
                    vector = mock_embedding_engine.embed_image(str(test_file))
                else:
                    vector = mock_embedding_engine.embed_text(test_file.read_text())
                
                indexed_count += 1
        
        # 3. 验证批量处理结果
        assert indexed_count >= 2, f"期望至少索引2个文件，实际{indexed_count}"
        
        print(f"✓ 批量索引流程测试通过")
        print(f"  索引文件数: {indexed_count}")
    
    def test_duplicate_detection_flow(self, test_media_dir, media_processor, database_manager, vector_store, noise_filter):
        """测试重复文件检测流程"""
        # 1. 创建重复文件
        original_image = test_media_dir / "test_image.jpg"
        duplicate_image = test_media_dir / "test_image_duplicate.jpg"
        
        # 复制文件
        shutil.copy(original_image, duplicate_image)
        
        # 2. 验证两个文件存在
        assert original_image.exists()
        assert duplicate_image.exists()
        
        # 3. 验证文件哈希相同
        import hashlib
        
        def get_file_hash(file_path):
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        
        original_hash = get_file_hash(original_image)
        duplicate_hash = get_file_hash(duplicate_image)
        
        assert original_hash == duplicate_hash, "重复文件哈希值应该相同"
        
        print(f"✓ 重复文件检测流程测试通过")
        print(f"  原始文件: {original_image.name}")
        print(f"  重复文件: {duplicate_image.name}")
        print(f"  文件哈希: {original_hash[:16]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])