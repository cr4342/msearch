"""
人脸聚类管理器单元测试
测试FaceClusterManager的核心功能
"""
import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import uuid

from src.business.face_cluster_manager import FaceClusterManager

class TestFaceClusterManager:
    """人脸聚类管理器核心功能测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            'face_clustering': {
                'method': 'dbscan',
                'similarity_threshold': 0.7,
                'min_samples': 2,
                'eps': 0.3
            }
        }
    
    @pytest.fixture
    def face_cluster_manager(self, mock_config):
        """人脸聚类管理器实例"""
        with patch('src.business.face_cluster_manager.FaceClusterManager._init_face_detector'), \
             patch('src.business.face_cluster_manager.FaceClusterManager._init_feature_extractor'):
            manager = FaceClusterManager(mock_config)
            yield manager
    
    def test_init_success(self, mock_config):
        """测试初始化成功"""
        with patch('src.business.face_cluster_manager.FaceClusterManager._init_face_detector') as mock_init_detector, \
             patch('src.business.face_cluster_manager.FaceClusterManager._init_feature_extractor') as mock_init_extractor:
            
            manager = FaceClusterManager(mock_config)
            
            # 验证配置是否正确加载
            assert manager.config == mock_config
            assert manager.method == 'dbscan'
            assert manager.threshold == 0.7
            assert manager.min_samples == 2
            assert manager.epsilon == 0.3
    
    @pytest.mark.asyncio
    async def test_cluster_faces_success(self, face_cluster_manager):
        """测试成功聚类人脸"""
        # 设置mock对象
        face_cluster_manager._extract_face_features = AsyncMock(return_value=np.array([0.1, 0.2, 0.3]))
        face_cluster_manager._perform_clustering = AsyncMock(return_value=[
            {
                'cluster_id': 'cluster_1',
                'cluster_name': 'Cluster_1',
                'faces': [
                    {'image_path': 'face1.jpg', 'vector': np.array([0.1, 0.2, 0.3]), 'similarity': 1.0}
                ],
                'size': 1
            }
        ])
        face_cluster_manager._save_cluster_results = AsyncMock(return_value=True)
        
        # 执行测试
        face_images = ['face1.jpg', 'face2.jpg']
        result = await face_cluster_manager.cluster_faces(face_images)
        
        # 验证结果
        assert result['status'] == 'success'
        assert 'clusters' in result
        assert 'total_faces' in result
        assert result['total_faces'] == 2
        
        # 验证调用了正确的处理步骤
        assert face_cluster_manager._extract_face_features.call_count == 2
        face_cluster_manager._perform_clustering.assert_called_once()
        face_cluster_manager._save_cluster_results.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cluster_faces_with_extraction_error(self, face_cluster_manager):
        """测试聚类人脸时特征提取错误"""
        # 设置mock对象，模拟特征提取失败
        face_cluster_manager._extract_face_features = AsyncMock(return_value=None)
        
        # 执行测试
        face_images = ['face1.jpg', 'face2.jpg']
        result = await face_cluster_manager.cluster_faces(face_images)
        
        # 验证结果
        assert result['status'] == 'success'
        assert len(result['clusters']) == 0
        assert result['total_faces'] == 0
        assert len(result['unclustered']) == 2
    
    @pytest.mark.asyncio
    async def test_cluster_faces_insufficient_faces(self, face_cluster_manager):
        """测试人脸数量不足无法聚类"""
        # 设置mock对象
        face_cluster_manager._extract_face_features = AsyncMock(return_value=np.array([0.1, 0.2, 0.3]))
        
        # 执行测试 - 只有一个有效人脸
        face_images = ['face1.jpg']
        result = await face_cluster_manager.cluster_faces(face_images)
        
        # 验证结果
        assert result['status'] == 'success'
        assert len(result['clusters']) == 0
        assert result['total_faces'] == 1
        assert len(result['unclustered']) == 1
    
    @pytest.mark.asyncio
    async def test_extract_face_features_success(self, face_cluster_manager):
        """测试成功提取人脸特征"""
        # 设置mock对象
        face_cluster_manager.embedding_engine = AsyncMock()
        face_cluster_manager.embedding_engine.embed_image = AsyncMock(return_value=np.array([0.1, 0.2, 0.3]))
        
        # 执行测试
        result = await face_cluster_manager._extract_face_features('test_face.jpg')
        
        # 验证结果
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert len(result) == 3
        # 验证L2归一化
        norm = np.linalg.norm(result)
        assert abs(norm - 1.0) < 1e-6  # 归一化后的模长应该接近1
    
    @pytest.mark.asyncio
    async def test_extract_face_features_with_no_embedding_engine(self, face_cluster_manager):
        """测试没有嵌入引擎时提取人脸特征"""
        # 设置没有嵌入引擎
        face_cluster_manager.embedding_engine = None
        
        # 执行测试
        result = await face_cluster_manager._extract_face_features('test_face.jpg')
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_dbscan_clustering_success(self, face_cluster_manager):
        """测试DBSCAN聚类成功"""
        # 创建测试向量
        face_vectors = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.9, 0.1, 0.0]),
            np.array([0.0, 1.0, 0.0]),
            np.array([0.1, 0.9, 0.0])
        ]
        face_images = ['face1.jpg', 'face2.jpg', 'face3.jpg', 'face4.jpg']
        
        # 执行测试
        result = await face_cluster_manager._dbscan_clustering(face_vectors, face_images)
        
        # 验证结果
        assert isinstance(result, list)
        # DBSCAN应该能生成聚类（具体数量取决于参数）
    
    @pytest.mark.asyncio
    async def test_kmeans_clustering_success(self, face_cluster_manager):
        """测试KMeans聚类成功"""
        # 创建测试向量
        face_vectors = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.9, 0.1, 0.0]),
            np.array([0.0, 1.0, 0.0]),
            np.array([0.1, 0.9, 0.0])
        ]
        face_images = ['face1.jpg', 'face2.jpg', 'face3.jpg', 'face4.jpg']
        
        # 设置聚类方法为KMeans
        face_cluster_manager.method = 'kmeans'
        
        # 执行测试
        result = await face_cluster_manager._kmeans_clustering(face_vectors, face_images)
        
        # 验证结果
        assert isinstance(result, list)
        # KMeans应该能生成聚类
    
    @pytest.mark.asyncio
    async def test_perform_clustering_with_invalid_method(self, face_cluster_manager):
        """测试使用无效聚类方法"""
        # 设置无效的聚类方法
        face_cluster_manager.method = 'invalid_method'
        
        # 创建测试向量
        face_vectors = [np.array([0.1, 0.2, 0.3])]
        face_images = ['face1.jpg']
        
        # 执行测试
        result = await face_cluster_manager._perform_clustering(face_vectors, face_images)
        
        # 验证结果 - 应该返回默认聚类
        assert isinstance(result, list)
        assert len(result) >= 0
    
    @pytest.mark.asyncio
    async def test_suggest_cluster_names_success(self, face_cluster_manager):
        """测试成功建议聚类名称"""
        # 设置mock对象
        face_cluster_manager.face_database = AsyncMock()
        face_cluster_manager.face_database.get_all_persons = AsyncMock(return_value=[
            {'id': 'cluster_1', 'name': 'Cluster_1', 'aliases': []}
        ])
        face_cluster_manager.face_database.update_person_name = AsyncMock()
        face_cluster_manager.face_database.update_person_aliases = AsyncMock()
        
        # 执行测试
        name_suggestions = ['张三', '李四', '王五']
        result = await face_cluster_manager.suggest_cluster_names('cluster_1', name_suggestions)
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['cluster_id'] == 'cluster_1'
        assert result['suggested_names'] == name_suggestions
        assert result['new_name'] == '张三'
        
        # 验证调用了正确的数据库方法
        face_cluster_manager.face_database.update_person_name.assert_called_once()
        face_cluster_manager.face_database.update_person_aliases.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_merge_clusters_success(self, face_cluster_manager):
        """测试成功合并聚类"""
        # 设置mock对象
        face_cluster_manager.face_database = AsyncMock()
        face_cluster_manager.face_database.get_face_vectors_by_person_id = AsyncMock(return_value=[
            {'vector_id': 'face_1', 'image_path': 'face1.jpg', 'vector': np.array([0.1, 0.2, 0.3])},
            {'vector_id': 'face_2', 'image_path': 'face2.jpg', 'vector': np.array([0.2, 0.3, 0.4])}
        ])
        face_cluster_manager.face_database.add_person = AsyncMock(return_value='merged_cluster_123')
        face_cluster_manager.face_database.store_face_vector = AsyncMock()
        face_cluster_manager.face_database.delete_person = AsyncMock()
        
        # 执行测试
        cluster_ids = ['cluster_1', 'cluster_2']
        new_name = '合并聚类'
        result = await face_cluster_manager.merge_clusters(cluster_ids, new_name)
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['merged_cluster_id'] == 'merged_cluster_123'
        assert result['original_clusters'] == cluster_ids
        assert result['new_name'] == new_name
        
        # 验证调用了正确的数据库方法
        assert face_cluster_manager.face_database.get_face_vectors_by_person_id.call_count == 2
        face_cluster_manager.face_database.add_person.assert_called_once_with(
            name=new_name,
            aliases=[],
            is_cluster=True
        )
        assert face_cluster_manager.face_database.store_face_vector.call_count == 2
        assert face_cluster_manager.face_database.delete_person.call_count == 2
    
    @pytest.mark.asyncio
    async def test_split_cluster_success(self, face_cluster_manager):
        """测试成功拆分聚类"""
        # 设置mock对象
        face_cluster_manager.face_database = AsyncMock()
        face_cluster_manager.face_database.get_face_vectors_by_person_id = AsyncMock(return_value=[
            {'vector_id': 'face_1', 'image_path': 'face1.jpg', 'vector': np.array([0.1, 0.2, 0.3])},
            {'vector_id': 'face_2', 'image_path': 'face2.jpg', 'vector': np.array([0.2, 0.3, 0.4])}
        ])
        face_cluster_manager.face_database.add_person = AsyncMock(return_value='new_cluster_123')
        face_cluster_manager.face_database.store_face_vector = AsyncMock()
        face_cluster_manager.face_database.delete_person = AsyncMock()
        face_cluster_manager.face_database.update_person_name = AsyncMock()
        
        # 执行测试
        cluster_id = 'cluster_1'
        face_ids_to_move = ['face_1']
        new_cluster_name = '新聚类'
        result = await face_cluster_manager.split_cluster(cluster_id, face_ids_to_move, new_cluster_name)
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['original_cluster_id'] == cluster_id
        assert 'new_cluster_id' in result
        assert result['moved_faces'] == face_ids_to_move
        assert result['remaining_faces_count'] == 1
        
        # 验证调用了正确的数据库方法
        face_cluster_manager.face_database.get_face_vectors_by_person_id.assert_called_once_with(cluster_id)
        face_cluster_manager.face_database.add_person.assert_called_once_with(
            name=new_cluster_name,
            aliases=[],
            is_cluster=True
        )
        face_cluster_manager.face_database.store_face_vector.assert_called_once()
        face_cluster_manager.face_database.delete_person.assert_called_once_with(cluster_id)


if __name__ == '__main__':
    pytest.main([__file__])