"""
人脸管理器单元测试
测试FaceManager的核心功能
"""
import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.business.face_manager import FaceManager


class TestFaceManager:
    """人脸管理器核心功能测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            'face.similarity_threshold': 0.7
        }
    
    @pytest.fixture
    def face_manager(self, mock_config):
        """人脸管理器实例"""
        # 创建mock对象
        mock_face_database = AsyncMock()
        mock_embedding_engine = AsyncMock()
        
        manager = FaceManager(mock_config, mock_face_database, mock_embedding_engine)
        return manager
    
    def test_init_success(self, mock_config):
        """测试初始化成功"""
        # 创建mock对象
        mock_face_database = AsyncMock()
        mock_embedding_engine = AsyncMock()
        
        manager = FaceManager(mock_config, mock_face_database, mock_embedding_engine)
        
        # 验证组件是否正确初始化
        assert manager.config == mock_config
        assert manager.face_database == mock_face_database
        assert manager.embedding_engine == mock_embedding_engine
        assert manager.similarity_threshold == 0.7
        assert manager.cluster_manager is not None
    
    @pytest.mark.asyncio
    async def test_register_face_success(self, face_manager):
        """测试成功注册人脸"""
        # 设置mock对象
        face_manager._extract_face_features = AsyncMock(return_value=np.array([0.1, 0.2, 0.3]))
        face_manager.face_database.add_person = AsyncMock(return_value='person_123')
        face_manager.face_database.store_face_vector = AsyncMock()
        
        # 执行测试
        result = await face_manager.register_face('face.jpg', '张三', ['小张', '三儿'])
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['person_name'] == '张三'
        assert 'person_id' in result
        assert 'vector_id' in result
        
        # 验证调用了正确的数据库方法
        face_manager.face_database.add_person.assert_called_once_with(
            name='张三',
            aliases=['小张', '三儿']
        )
        face_manager.face_database.store_face_vector.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_face_with_extraction_error(self, face_manager):
        """测试人脸注册时特征提取错误"""
        # 设置mock对象，模拟特征提取失败
        face_manager._extract_face_features = AsyncMock(return_value=None)
        
        # 执行测试
        result = await face_manager.register_face('face.jpg', '张三')
        
        # 验证结果
        assert result['status'] == 'error'
        assert '无法提取人脸特征' in result['error']
        assert result['person_name'] == '张三'
    
    @pytest.mark.asyncio
    async def test_cluster_faces_success(self, face_manager):
        """测试成功聚类人脸"""
        # 设置mock对象
        face_manager.cluster_manager.cluster_faces = AsyncMock(return_value={
            'status': 'success',
            'clusters': [{'cluster_id': 'cluster_1'}],
            'total_faces': 2
        })
        
        # 执行测试
        face_images = ['face1.jpg', 'face2.jpg']
        result = await face_manager.cluster_faces(face_images)
        
        # 验证结果
        assert result['status'] == 'success'
        assert 'clusters' in result
        assert result['total_faces'] == 2
        
        # 验证调用了聚类管理器的方法
        face_manager.cluster_manager.cluster_faces.assert_called_once_with(face_images, True)
    
    @pytest.mark.asyncio
    async def test_get_cluster_suggestions_success(self, face_manager):
        """测试成功获取聚类建议名称"""
        # 设置mock对象
        face_manager.cluster_manager.suggest_cluster_names = AsyncMock(return_value={
            'status': 'success',
            'cluster_id': 'cluster_1',
            'suggested_names': ['张三', '李四']
        })
        
        # 执行测试
        name_suggestions = ['张三', '李四']
        result = await face_manager.get_cluster_suggestions('cluster_1', name_suggestions)
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['cluster_id'] == 'cluster_1'
        
        # 验证调用了聚类管理器的方法
        face_manager.cluster_manager.suggest_cluster_names.assert_called_once_with('cluster_1', name_suggestions)
    
    @pytest.mark.asyncio
    async def test_merge_clusters_success(self, face_manager):
        """测试成功合并聚类"""
        # 设置mock对象
        face_manager.cluster_manager.merge_clusters = AsyncMock(return_value={
            'status': 'success',
            'merged_cluster_id': 'merged_123',
            'original_clusters': ['cluster_1', 'cluster_2']
        })
        
        # 执行测试
        cluster_ids = ['cluster_1', 'cluster_2']
        new_name = '合并聚类'
        result = await face_manager.merge_clusters(cluster_ids, new_name)
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['merged_cluster_id'] == 'merged_123'
        
        # 验证调用了聚类管理器的方法
        face_manager.cluster_manager.merge_clusters.assert_called_once_with(cluster_ids, new_name)
    
    @pytest.mark.asyncio
    async def test_split_cluster_success(self, face_manager):
        """测试成功拆分聚类"""
        # 设置mock对象
        face_manager.cluster_manager.split_cluster = AsyncMock(return_value={
            'status': 'success',
            'original_cluster_id': 'cluster_1',
            'new_cluster_id': 'new_cluster_123'
        })
        
        # 执行测试
        cluster_id = 'cluster_1'
        face_ids_to_move = ['face_1']
        new_cluster_name = '新聚类'
        result = await face_manager.split_cluster(cluster_id, face_ids_to_move, new_cluster_name)
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['original_cluster_id'] == cluster_id
        assert result['new_cluster_id'] == 'new_cluster_123'
        
        # 验证调用了聚类管理器的方法
        face_manager.cluster_manager.split_cluster.assert_called_once_with(
            cluster_id, face_ids_to_move, new_cluster_name
        )
    
    @pytest.mark.asyncio
    async def test_recognize_face_success(self, face_manager):
        """测试成功识别人脸"""
        # 设置mock对象
        face_manager._extract_face_features = AsyncMock(return_value=np.array([0.1, 0.2, 0.3]))
        face_manager.face_database.search_similar_faces = AsyncMock(return_value=[
            {'person_name': '张三', 'confidence': 0.9, 'person_id': 'person_123'}
        ])
        
        # 执行测试
        result = await face_manager.recognize_face('unknown_face.jpg')
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['match'] is not None
        assert result['match']['person_name'] == '张三'
        assert result['match']['confidence'] == 0.9
        
        # 验证调用了正确的处理步骤
        face_manager._extract_face_features.assert_called_once_with('unknown_face.jpg')
        face_manager.face_database.search_similar_faces.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_recognize_face_with_extraction_error(self, face_manager):
        """测试人脸识别时特征提取错误"""
        # 设置mock对象，模拟特征提取失败
        face_manager._extract_face_features = AsyncMock(return_value=None)
        
        # 执行测试
        result = await face_manager.recognize_face('unknown_face.jpg')
        
        # 验证结果
        assert result['status'] == 'error'
        assert '无法提取人脸特征' in result['error']
        assert result['image_path'] == 'unknown_face.jpg'
    
    @pytest.mark.asyncio
    async def test_search_by_person_name_success(self, face_manager):
        """测试成功按人名搜索"""
        # 设置mock对象
        face_manager.face_database.get_person_by_name = AsyncMock(return_value={
            'id': 'person_123',
            'name': '张三',
            'aliases': ['小张']
        })
        face_manager.face_database.get_files_by_person = AsyncMock(return_value=[
            {'file_id': 'file_1', 'file_path': 'face1.jpg'},
            {'file_id': 'file_2', 'file_path': 'face2.jpg'}
        ])
        
        # 执行测试
        result = await face_manager.search_by_person_name('张三')
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['person_info'] is not None
        assert result['person_info']['name'] == '张三'
        assert len(result['files']) == 2
        
        # 验证调用了正确的数据库方法
        face_manager.face_database.get_person_by_name.assert_called_once_with('张三')
        face_manager.face_database.get_files_by_person.assert_called_once_with('person_123')
    
    @pytest.mark.asyncio
    async def test_search_by_person_name_not_found(self, face_manager):
        """测试按人名搜索但未找到人物"""
        # 设置mock对象
        face_manager.face_database.get_person_by_name = AsyncMock(return_value=None)
        
        # 执行测试
        result = await face_manager.search_by_person_name('不存在的人')
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['person_info'] is None
        assert len(result['files']) == 0
        
        # 验证调用了正确的数据库方法
        face_manager.face_database.get_person_by_name.assert_called_once_with('不存在的人')
        face_manager.face_database.get_files_by_person.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_extract_face_features_success(self, face_manager):
        """测试成功提取人脸特征"""
        # 设置mock对象
        face_manager.embedding_engine.embed_image = AsyncMock(return_value=np.array([0.1, 0.2, 0.3]))
        
        # 执行测试
        result = await face_manager._extract_face_features('face.jpg')
        
        # 验证结果
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_update_person_aliases_success(self, face_manager):
        """测试成功更新人物别名"""
        # 设置mock对象
        face_manager.face_database.get_person_by_name = AsyncMock(return_value={
            'id': 'person_123',
            'name': '张三'
        })
        face_manager.face_database.update_person_aliases = AsyncMock()
        
        # 执行测试
        aliases = ['小张', '三儿', '张先生']
        result = await face_manager.update_person_aliases('张三', aliases)
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['person_name'] == '张三'
        assert result['aliases'] == aliases
        
        # 验证调用了正确的数据库方法
        face_manager.face_database.get_person_by_name.assert_called_once_with('张三')
        face_manager.face_database.update_person_aliases.assert_called_once_with(
            person_id='person_123',
            aliases=aliases
        )
    
    @pytest.mark.asyncio
    async def test_update_person_aliases_person_not_found(self, face_manager):
        """测试更新人物别名但人物不存在"""
        # 设置mock对象
        face_manager.face_database.get_person_by_name = AsyncMock(return_value=None)
        
        # 执行测试
        aliases = ['小张', '三儿']
        result = await face_manager.update_person_aliases('不存在的人', aliases)
        
        # 验证结果
        assert result['status'] == 'error'
        assert '未找到人物' in result['error']
        assert result['person_name'] == '不存在的人'
        
        # 验证调用了正确的数据库方法
        face_manager.face_database.get_person_by_name.assert_called_once_with('不存在的人')
        face_manager.face_database.update_person_aliases.assert_not_called()


if __name__ == '__main__':
    pytest.main([__file__])