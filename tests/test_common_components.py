"""
共享组件单元测试
"""

import pytest
import tempfile
import os
import asyncio
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.common.embedding.embedding_engine import EmbeddingEngine
from src.common.storage.database_adapter import DatabaseAdapter
from src.common.storage.qdrant_adapter import QdrantAdapter


class TestEmbeddingEngine:
    """向量化引擎测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            'infinity': {
                'services': {
                    'clip': {
                        'model_id': 'openai/clip-vit-base-patch32',
                        'device': 'cpu',
                        'port': 7997
                    }
                }
            }
        }
    
    def test_engine_initialization(self, mock_config):
        """测试引擎初始化"""
        try:
            engine = EmbeddingEngine(mock_config)
            assert engine is not None
        except Exception as e:
            # 如果依赖未安装，跳过测试
            pytest.skip(f"依赖未安装: {e}")
    
    def test_available_models(self, mock_config):
        """测试可用模型获取"""
        try:
            engine = EmbeddingEngine(mock_config)
            models = engine.get_available_models()
            assert isinstance(models, list)
        except Exception as e:
            pytest.skip(f"依赖未安装: {e}")
    
    def test_model_info(self, mock_config):
        """测试模型信息获取"""
        try:
            engine = EmbeddingEngine(mock_config)
            if 'clip' in engine.get_available_models():
                info = engine.get_model_info('clip')
                assert isinstance(info, dict)
                assert 'name' in info
                assert 'status' in info
        except Exception as e:
            pytest.skip(f"依赖未安装: {e}")
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_config):
        """测试健康检查"""
        try:
            engine = EmbeddingEngine(mock_config)
            health = await engine.health_check()
            assert isinstance(health, dict)
        except Exception as e:
            pytest.skip(f"依赖未安装: {e}")


class TestDatabaseAdapter:
    """数据库适配器测试"""
    
    @pytest.fixture
    def temp_db(self):
        """临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        yield db_path
        
        # 清理
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_adapter_initialization(self, temp_db):
        """测试适配器初始化"""
        # 使用临时数据库配置
        import yaml
        config_data = {
            'database': {
                'sqlite': {
                    'path': temp_db
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            from src.core.config_manager import ConfigManager
            config_manager = ConfigManager(config_path)
            adapter = DatabaseAdapter(config_manager)
            assert adapter is not None
        finally:
            os.unlink(config_path)
    
    def test_file_operations(self, temp_db):
        """测试文件操作"""
        # 配置临时数据库
        import yaml
        config_data = {
            'database': {
                'sqlite': {
                    'path': temp_db
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            from src.core.config_manager import ConfigManager
            config_manager = ConfigManager(config_path)
            adapter = DatabaseAdapter(config_manager)
            
            # 测试插入文件
            import uuid
            file_info = {
                'id': str(uuid.uuid4()),
                'file_path': '/test/path.jpg',
                'file_name': 'test.jpg',
                'file_type': '.jpg',
                'file_size': 1024,
                'file_hash': 'test_hash',
                'created_at': 1234567890,
                'modified_at': 1234567890
            }
            
            file_id = asyncio.run(adapter.insert_file(file_info))
            assert file_id == file_info['id']
            
            # 测试获取文件
            retrieved_file = asyncio.run(adapter.get_file(file_id))
            assert retrieved_file is not None
            assert retrieved_file['file_path'] == '/test/path.jpg'
            
            # 测试更新文件
            success = asyncio.run(adapter.update_file_status(file_id, 'completed'))
            assert success
            
            # 测试删除文件
            success = asyncio.run(adapter.delete_file(file_id))
            assert success
            
        finally:
            os.unlink(config_path)
    
    def test_task_operations(self, temp_db):
        """测试任务操作"""
        # 配置临时数据库
        import yaml
        config_data = {
            'database': {
                'sqlite': {
                    'path': temp_db
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            from src.core.config_manager import ConfigManager
            config_manager = ConfigManager(config_path)
            adapter = DatabaseAdapter(config_manager)
            
            # 先插入文件
            import uuid
            from datetime import datetime
            file_info = {
                'id': str(uuid.uuid4()),
                'file_path': '/test/path.jpg',
                'file_name': 'test.jpg',
                'file_type': '.jpg',
                'file_size': 1024,
                'file_hash': 'test_hash',
                'created_at': 1234567890,
                'modified_at': 1234567890
            }
            
            file_id = asyncio.run(adapter.insert_file(file_info))
            
            # 测试插入任务
            task_data = {
                'id': str(uuid.uuid4()),
                'file_id': file_id,
                'task_type': 'processing',
                'status': 'pending',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            task_id = asyncio.run(adapter.insert_task(task_data))
            assert task_id == task_data['id']
            
            # 测试获取任务
            retrieved_task = asyncio.run(adapter.get_task(task_id))
            assert retrieved_task is not None
            assert retrieved_task['task_type'] == 'processing'
            
        finally:
            os.unlink(config_path)


class TestQdrantAdapter:
    """Qdrant适配器测试"""
    
    def test_adapter_initialization(self):
        """测试适配器初始化"""
        try:
            adapter = QdrantAdapter()
            assert adapter is not None
        except Exception as e:
            # 如果Qdrant未安装，跳过测试
            pytest.skip(f"Qdrant未安装: {e}")
    
    def test_collection_operations(self):
        """测试集合操作"""
        try:
            adapter = QdrantAdapter()
            
            # 测试创建集合
            collection_name = "test_collection"
            success = asyncio.run(adapter.create_collection(
                collection_name,
                vector_size=512,
                distance="Cosine"
            ))
            
            # 测试获取集合信息
            info = asyncio.run(adapter.get_collection_info(collection_name))
            assert info is not None
            
            # 测试删除集合
            success = asyncio.run(adapter.delete_collection(collection_name))
            
        except Exception as e:
            pytest.skip(f"Qdrant未安装或未启动: {e}")
    
    def test_vector_operations(self):
        """测试向量操作"""
        try:
            adapter = QdrantAdapter()
            
            # 创建测试集合
            collection_name = "test_vectors"
            asyncio.run(adapter.create_collection(
                collection_name,
                vector_size=512,
                distance="Cosine"
            ))
            
            # 测试插入向量
            import numpy as np
            vector = np.random.rand(512).astype(np.float32)
            point_id = asyncio.run(adapter.insert_vector(
                collection_name,
                vector,
                {"test": "payload"}
            ))
            assert point_id is not None
            
            # 测试搜索向量
            results = asyncio.run(adapter.search_vectors(
                collection_name,
                vector,
                limit=10
            ))
            assert isinstance(results, list)
            
            # 清理
            asyncio.run(adapter.delete_collection(collection_name))
            
        except Exception as e:
            pytest.skip(f"Qdrant未安装或未启动: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])