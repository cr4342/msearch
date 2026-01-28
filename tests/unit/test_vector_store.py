import pytest
import numpy as np
from pathlib import Path
import tempfile
from src.core.vector.vector_store import VectorStore, create_vector_store


@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def vector_store_config(temp_data_dir):
    return {
        'data_dir': str(temp_data_dir),
        'collection_name': 'test_vectors',
        'index_type': 'ivf_flat',
        'num_partitions': 10,
        'vector_dimension': 512
    }


@pytest.fixture
def vector_store(vector_store_config):
    store = VectorStore(vector_store_config)
    yield store
    # 清理
    store.close()


class TestVectorStore:
    """测试向量存储功能"""
    
    def test_create_vector_store(self, vector_store_config):
        """测试创建向量存储"""
        store = create_vector_store(vector_store_config)
        assert store is not None
        assert isinstance(store, VectorStore)
        store.close()
    
    def test_add_vector(self, vector_store):
        """测试添加向量"""
        vector = np.random.rand(512).tolist()
        vector_data = {
            'id': 'test_vector_1',
            'vector': vector,
            'metadata': {
                'type': 'image',
                'path': '/path/to/image.jpg',
                'tags': ['test', 'image']
            },
            'timestamp': '2023-01-01T00:00:00'
        }
        
        # 使用 insert_vectors 方法（VectorStore 的实际 API）
        vector_store.insert_vectors([vector_data])
        # 验证向量是否添加成功
        result = vector_store.get_vector('test_vector_1')
        assert result is not None
    
    def test_add_vectors(self, vector_store):
        """测试批量添加向量"""
        vectors = []
        for i in range(5):
            vector = np.random.rand(512).tolist()
            vectors.append({
                'id': f'test_vector_{i}',
                'vector': vector,
                'metadata': {
                    'type': 'image',
                    'path': f'/path/to/image_{i}.jpg',
                    'tags': ['test', 'image']
                },
                'timestamp': '2023-01-01T00:00:00'
            })
        
        # 使用 insert_vectors 方法（VectorStore 的实际 API）
        vector_store.insert_vectors(vectors)
        # 验证向量是否添加成功
        stats = vector_store.get_collection_stats()
        # 注意：创建表时会添加一个默认的空向量，所以总向量数是5+1=6
        assert stats['total_vectors'] == 6
    
    def test_search_vectors(self, vector_store):
        """测试搜索向量"""
        # 添加测试向量
        vectors = []
        target_vector = np.random.rand(512).tolist()
        vectors.append({
            'id': 'target_vector',
            'vector': target_vector,
            'metadata': {'type': 'target'},
            'timestamp': '2023-01-01T00:00:00'
        })
        
        for i in range(10):
            vector = np.random.rand(512).tolist()
            vectors.append({
                'id': f'random_vector_{i}',
                'vector': vector,
                'metadata': {'type': 'random'},
                'timestamp': '2023-01-01T00:00:00'
            })
        
        # 使用 insert_vectors 方法（VectorStore 的实际 API）
        vector_store.insert_vectors(vectors)
        
        # 搜索目标向量
        results = vector_store.search_vectors(target_vector, limit=5)
        assert len(results) > 0
        assert results[0]['id'] == 'target_vector'
    
    def test_get_vector(self, vector_store):
        """测试获取单个向量"""
        vector = np.random.rand(512).tolist()
        vector_data = {
            'id': 'test_vector_1',
            'vector': vector,
            'metadata': {'type': 'image'},
            'timestamp': '2023-01-01T00:00:00'
        }
        
        # 使用 insert_vectors 方法（VectorStore 的实际 API）
        vector_store.insert_vectors([vector_data])
        result = vector_store.get_vector('test_vector_1')
        
        assert result is not None
        assert result['id'] == 'test_vector_1'
    
    def test_delete_vector(self, vector_store):
        """测试删除向量"""
        vector = np.random.rand(512).tolist()
        vector_data = {
            'id': 'test_vector_1',
            'vector': vector,
            'metadata': {'type': 'image'},
            'timestamp': '2023-01-01T00:00:00'
        }
        
        vector_store.add_vector(vector_data)
        result = vector_store.delete_vectors(['test_vector_1'])
        
        # delete_vectors没有返回值，直接检查删除结果
        assert vector_store.get_vector('test_vector_1') is None
    
    def test_update_vector(self, vector_store):
        """测试更新向量"""
        vector = np.random.rand(512).tolist()
        vector_data = {
            'id': 'test_vector_1',
            'vector': vector,
            'metadata': {'type': 'image', 'status': 'old'},
            'timestamp': '2023-01-01T00:00:00'
        }
        
        vector_store.add_vector(vector_data)
        
        # 更新向量
        new_vector = np.random.rand(512).tolist()
        update_data = {
            'vector': new_vector,
            'metadata': {'type': 'image', 'status': 'updated'}
        }
        
        result = vector_store.update_vector('test_vector_1', update_data)
        assert result is True
        
        # 验证更新
        updated_vector = vector_store.get_vector('test_vector_1')
        assert updated_vector['metadata']['status'] == 'updated'
    
    def test_get_collection_stats(self, vector_store):
        """测试获取集合统计信息"""
        stats = vector_store.get_collection_stats()
        assert isinstance(stats, dict)
        assert 'vector_count' in stats
        assert 'vector_dimension' in stats
    
    def test_create_index(self, vector_store):
        """测试创建索引"""
        result = vector_store.create_index()
        assert result is True
    
    def test_create_different_index_types(self, vector_store_config, temp_data_dir):
        """测试创建不同类型的索引"""
        # 测试IVF-Flat索引
        vector_store_config['index_type'] = 'ivf_flat'
        vector_store_config['collection_name'] = 'test_vectors_ivf_flat'
        vector_store_config['data_dir'] = str(temp_data_dir)
        store1 = VectorStore(vector_store_config)
        result1 = store1.create_index()
        assert result1 is True
        store1.close()
        
        # 测试IVF-PQ索引
        vector_store_config['index_type'] = 'ivf_pq'
        vector_store_config['collection_name'] = 'test_vectors_ivf_pq'
        vector_store_config['data_dir'] = str(temp_data_dir)
        store2 = VectorStore(vector_store_config)
        result2 = store2.create_index()
        assert result2 is True
        store2.close()
        
        # 测试Brute force索引
        vector_store_config['index_type'] = 'brute'
        vector_store_config['collection_name'] = 'test_vectors_brute'
        vector_store_config['data_dir'] = str(temp_data_dir)
        store3 = VectorStore(vector_store_config)
        result3 = store3.create_index()
        assert result3 is True
        store3.close()
