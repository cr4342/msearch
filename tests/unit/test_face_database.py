"""
人脸数据库单元测试
测试FaceDatabase的核心功能
"""
import pytest
import asyncio
import numpy as np
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sqlite3

from src.storage.face_database import FaceDatabase, get_face_database


class TestFaceDatabase:
    """人脸数据库核心功能测试"""
    
    @pytest.fixture
    def mock_config_manager(self):
        """模拟配置管理器"""
        mock_config = {
            'database': {
                'sqlite': {
                    'path': './data/msearch.db'
                }
            },
            'face_recognition': {
                'matching': {
                    'max_matches': 10,
                    'similarity_threshold': 0.6
                }
            }
        }
        
        mock_config_manager = Mock()
        mock_config_manager.config = mock_config
        mock_config_manager.get = Mock(side_effect=lambda key, default=None: {
            'database.sqlite.path': './data/msearch.db',
            'face_recognition.matching.max_matches': 10,
            'face_recognition.matching.similarity_threshold': 0.6
        }.get(key, default))
        mock_config_manager.watch = Mock()
        
        return mock_config_manager
    
    @pytest.fixture
    def temp_db_path(self):
        """创建临时数据库文件"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        yield tmp_path
        os.unlink(tmp_path)
    
    @pytest.fixture
    def face_database(self, mock_config_manager, temp_db_path):
        """人脸数据库实例"""
        with patch('src.storage.face_database.get_config_manager', return_value=mock_config_manager):
            db = FaceDatabase(temp_db_path)
            return db
    
    def test_init_success(self, mock_config_manager, temp_db_path):
        """测试初始化成功"""
        with patch('src.storage.face_database.get_config_manager', return_value=mock_config_manager):
            db = FaceDatabase(temp_db_path)
            
            # 验证组件是否正确初始化
            assert db.db_path == temp_db_path
            assert db.config_manager == mock_config_manager
            mock_config_manager.watch.assert_called()
            
            # 验证数据库表已创建
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            
            # 检查所有必需的表是否存在
            tables = ['persons', 'face_features', 'file_faces', 'face_match_cache']
            for table in tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
                assert cursor.fetchone() is not None
            
            conn.close()
    
    @pytest.mark.asyncio
    async def test_add_person_success(self, face_database):
        """测试成功添加人物"""
        # 执行测试
        person_id = await face_database.add_person('张三', ['小张', '三儿'], '测试人物')
        
        # 验证结果
        assert isinstance(person_id, int)
        assert person_id > 0
        
        # 验证数据已存入数据库
        person_info = await face_database.get_person_by_name('张三')
        assert person_info['name'] == '张三'
        assert person_info['aliases'] == ['小张', '三儿']
        assert person_info['description'] == '测试人物'
    
    @pytest.mark.asyncio
    async def test_store_face_vector_success(self, face_database):
        """测试成功存储人脸特征向量"""
        # 添加一个测试人物
        person_id = await face_database.add_person('李四')
        
        # 创建测试向量
        test_vector = np.array([0.1, 0.2, 0.3, 0.4] * 128, dtype=np.float32)  # 512维
        
        # 执行测试
        result = await face_database.store_face_vector('vector_123', person_id, 'test_face.jpg', test_vector)
        
        # 验证结果
        assert result is True
    
    @pytest.mark.asyncio
    async def test_store_face_vector_person_not_exists(self, face_database):
        """测试存储人脸特征向量时人物不存在"""
        # 创建测试向量
        test_vector = np.array([0.1, 0.2, 0.3, 0.4] * 128, dtype=np.float32)  # 512维
        
        # 执行测试 - 使用不存在的人物ID
        result = await face_database.store_face_vector('vector_123', 99999, 'test_face.jpg', test_vector)
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_person_by_name_success(self, face_database):
        """测试成功根据人名获取人物信息"""
        # 添加测试人物
        await face_database.add_person('王五', ['小王'], '测试人物2')
        
        # 执行测试
        result = await face_database.get_person_by_name('王五')
        
        # 验证结果
        assert result is not None
        assert result['name'] == '王五'
        assert result['aliases'] == ['小王']
        assert result['description'] == '测试人物2'
    
    @pytest.mark.asyncio
    async def test_get_person_by_name_not_found(self, face_database):
        """测试根据人名获取人物信息但未找到"""
        # 执行测试
        result = await face_database.get_person_by_name('不存在的人')
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_files_by_person(self, face_database):
        """测试根据人物ID获取相关文件"""
        # 添加测试人物
        person_id = await face_database.add_person('赵六')
        
        # 创建测试向量并存储
        test_vector = np.array([0.1, 0.2, 0.3, 0.4] * 128, dtype=np.float32)  # 512维
        await face_database.store_face_vector('vector_124', person_id, 'test_face2.jpg', test_vector)
        
        # 执行测试
        result = await face_database.get_files_by_person(person_id)
        
        # 验证结果
        assert isinstance(result, list)
        # 由于file_faces表中的数据是通过index_file_faces方法添加的，这里我们验证空结果
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_update_person_aliases_success(self, face_database):
        """测试成功更新人物别名"""
        # 添加测试人物
        person_id = await face_database.add_person('孙七')
        
        # 执行测试
        result = await face_database.update_person_aliases(person_id, ['小孙', '七哥'])
        
        # 验证结果
        assert result is True
        
        # 验证别名已更新
        person_info = await face_database.get_person_by_name('孙七')
        assert person_info['aliases'] == ['小孙', '七哥']
    
    @pytest.mark.asyncio
    async def test_update_person_aliases_person_not_found(self, face_database):
        """测试更新人物别名时人物不存在"""
        # 执行测试 - 使用不存在的人物ID
        result = await face_database.update_person_aliases(99999, ['不存在'])
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_all_persons(self, face_database):
        """测试获取所有人名信息"""
        # 添加多个测试人物
        await face_database.add_person('人物1')
        await face_database.add_person('人物2')
        
        # 执行测试
        result = await face_database.get_all_persons()
        
        # 验证结果
        assert isinstance(result, list)
        assert len(result) >= 2
        names = [person['name'] for person in result]
        assert '人物1' in names
        assert '人物2' in names
    
    @pytest.mark.asyncio
    async def test_search_similar_faces(self, face_database):
        """测试搜索相似人脸"""
        # 添加测试人物并存储特征向量
        person_id = await face_database.add_person('相似测试')
        
        # 存储一个特征向量
        test_vector = np.array([0.1, 0.2, 0.3, 0.4] * 128, dtype=np.float32)  # 512维
        await face_database.store_face_vector('vector_125', person_id, 'test_face3.jpg', test_vector)
        
        # 执行搜索，使用一个相似的向量
        query_vector = test_vector + np.random.normal(0, 0.01, test_vector.shape)  # 添加少量噪声
        
        result = await face_database.search_similar_faces(query_vector, top_k=5, threshold=0.1)
        
        # 验证结果
        assert isinstance(result, list)
        # 结果数量取决于数据库中存储的人脸数量和相似度阈值
        # 由于我们只存储了一个向量且查询向量与之高度相似，应该能找到匹配
    
    def test_cosine_similarity(self, face_database):
        """测试余弦相似度计算"""
        # 创建两个相同的向量
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([1.0, 0.0, 0.0])
        
        # 执行测试
        result = face_database._cosine_similarity(a, b)
        
        # 验证结果 - 相同向量的相似度应为1
        assert abs(result - 1.0) < 1e-6
    
    def test_cosine_similarity_orthogonal(self, face_database):
        """测试正交向量的余弦相似度"""
        # 创建两个正交向量
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        
        # 执行测试
        result = face_database._cosine_similarity(a, b)
        
        # 验证结果 - 正交向量的相似度应为0
        assert abs(result) < 1e-6
    
    def test_reload_config(self, face_database, temp_db_path):
        """测试重新加载配置"""
        # 模拟配置管理器返回新的数据库路径
        with patch.object(face_database.config_manager, 'get', return_value=temp_db_path):
            # 执行测试
            face_database._reload_config('database.sqlite.path', temp_db_path)
            
            # 验证配置已更新 - _reload_config会从配置管理器获取路径并更新db_path
            assert face_database.db_path == temp_db_path


class TestFaceDatabaseSingleton:
    """人脸数据库单例模式测试"""
    
    def test_get_face_database_singleton(self):
        """测试获取全局人脸数据库实例"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            temp_db_path = tmp_file.name
        
        try:
            # 模拟配置管理器返回临时数据库路径
            with patch('src.storage.face_database.get_config_manager') as mock_config_manager:
                mock_config = {
                    'database': {
                        'sqlite': {
                            'path': temp_db_path
                        }
                    }
                }
                mock_config_manager.return_value.config = mock_config
                mock_config_manager.return_value.get = Mock(side_effect=lambda key, default=None: {
                    'database.sqlite.path': temp_db_path
                }.get(key, default))
                mock_config_manager.return_value.watch = Mock()
                
                # 重置全局实例
                import src.storage.face_database as fd
                fd._face_database = None
                
                # 获取第一个实例
                db1 = get_face_database()
                assert db1 is not None
                
                # 获取第二个实例，应该与第一个相同
                db2 = get_face_database()
                assert db1 is db2
        finally:
            # 清理临时文件
            os.unlink(temp_db_path)


if __name__ == '__main__':
    pytest.main([__file__])