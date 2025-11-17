"""
人脸模型管理器单元测试
测试FaceModelManager的核心功能
"""
import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import cv2

from src.business.face_model_manager import FaceModelManager, get_face_model_manager


class TestFaceModelManager:
    """人脸模型管理器核心功能测试"""
    
    @pytest.fixture
    def mock_config_manager(self):
        """模拟配置管理器"""
        mock_config = {
            'face_recognition': {
                'detection': {
                    'min_face_size': 20,
                    'confidence_threshold': 0.6
                },
                'feature_extraction': {
                    'normalize': True
                }
            }
        }
        
        mock_config_manager = Mock()
        mock_config_manager.config = mock_config
        mock_config_manager.get = Mock(side_effect=lambda key, default=None: {
            'face_recognition': mock_config['face_recognition'],
            'face_recognition.detection': mock_config['face_recognition']['detection'],
            'face_recognition.feature_extraction': mock_config['face_recognition']['feature_extraction']
        }.get(key, default))
        mock_config_manager.watch = Mock()
        
        return mock_config_manager
    
    @pytest.fixture
    def face_model_manager(self, mock_config_manager):
        """人脸模型管理器实例"""
        with patch('src.business.face_model_manager.get_config_manager', return_value=mock_config_manager), \
             patch('src.business.face_model_manager.MTCNN'), \
             patch('src.business.face_model_manager.InceptionResnetV1'):
            manager = FaceModelManager()
            yield manager
    
    def test_init_success(self, mock_config_manager):
        """测试初始化成功"""
        with patch('src.business.face_model_manager.get_config_manager', return_value=mock_config_manager), \
             patch('src.business.face_model_manager.MTCNN') as mock_mtcnn, \
             patch('src.business.face_model_manager.InceptionResnetV1') as mock_facenet:
            
            # 创建模拟模型实例
            mock_detector = Mock()
            mock_mtcnn.return_value = mock_detector
            
            mock_extractor = Mock()
            mock_extractor.eval = Mock(return_value=mock_extractor)
            mock_facenet.return_value = mock_extractor
            
            manager = FaceModelManager()
            
            # 验证组件是否正确初始化
            assert manager.config_manager == mock_config_manager
            assert manager.face_detector is not None
            assert manager.feature_extractor is not None
            assert manager.detection_config == mock_config_manager.get('face_recognition.detection', {})
            assert manager.feature_config == mock_config_manager.get('face_recognition.feature_extraction', {})
            
            # 验证配置监听
            mock_config_manager.watch.assert_called()
    
    def test_reload_config(self, face_model_manager):
        """测试重新加载配置"""
        # 执行测试
        face_model_manager._reload_config('face_recognition.detection.min_face_size', 30)
        
        # 验证配置已更新
        assert face_model_manager.detection_config == {'min_face_size': 30}
    
    def test_detect_faces_success(self, face_model_manager):
        """测试成功检测人脸"""
        # 设置mock对象
        mock_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        with patch('cv2.imread', return_value=mock_image), \
             patch('cv2.cvtColor', return_value=mock_image):
            
            # 模拟检测结果
            mock_faces = [
                {
                    'box': [100, 100, 200, 200],
                    'keypoints': {'left_eye': [150, 150], 'right_eye': [200, 150]},
                    'confidence': 0.95
                }
            ]
            face_model_manager.face_detector.detect_faces = Mock(return_value=mock_faces)
            
            # 执行测试
            result = face_model_manager.detect_faces('test_image.jpg')
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]['bbox']['x'] == 100
            assert result[0]['bbox']['y'] == 100
            assert result[0]['bbox']['width'] == 200
            assert result[0]['bbox']['height'] == 200
            assert result[0]['confidence'] == 0.95
    
    def test_detect_faces_image_not_found(self, face_model_manager):
        """测试检测人脸时图片不存在"""
        with patch('cv2.imread', return_value=None):
            # 执行测试
            result = face_model_manager.detect_faces('nonexistent_image.jpg')
            
            # 验证结果
            assert result == []
    
    def test_extract_face_features_success(self, face_model_manager):
        """测试成功提取人脸特征"""
        # 设置mock对象
        mock_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        with patch('cv2.imread', return_value=mock_image):
            
            # 模拟特征提取结果
            mock_features = torch.tensor([[0.1, 0.2, 0.3]])
            face_model_manager.feature_extractor = Mock()
            face_model_manager.feature_extractor.return_value = mock_features
            
            # 执行测试
            bbox = {'x': 100, 'y': 100, 'width': 200, 'height': 200}
            result = face_model_manager.extract_face_features('test_image.jpg', bbox)
            
            # 验证结果
            assert result is not None
            assert isinstance(result, np.ndarray)
            assert len(result) == 3
            # 验证L2归一化
            norm = np.linalg.norm(result)
            assert abs(norm - 1.0) < 1e-6  # 归一化后的模长应该接近1
    
    def test_extract_face_features_image_not_found(self, face_model_manager):
        """测试提取人脸特征时图片不存在"""
        with patch('cv2.imread', return_value=None):
            # 执行测试
            bbox = {'x': 100, 'y': 100, 'width': 200, 'height': 200}
            result = face_model_manager.extract_face_features('nonexistent_image.jpg', bbox)
            
            # 验证结果
            assert result is None
    
    def test_detect_and_extract_faces_success(self, face_model_manager):
        """测试成功检测并提取人脸特征"""
        # 设置mock对象
        mock_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        with patch('cv2.imread', return_value=mock_image), \
             patch('cv2.cvtColor', return_value=mock_image):
            
            # 模拟检测结果
            mock_faces = [
                {
                    'box': [100, 100, 200, 200],
                    'keypoints': {'left_eye': [150, 150], 'right_eye': [200, 150]},
                    'confidence': 0.95
                }
            ]
            face_model_manager.face_detector.detect_faces = Mock(return_value=mock_faces)
            
            # 模拟特征提取结果
            mock_features = torch.tensor([[0.1, 0.2, 0.3]])
            face_model_manager.feature_extractor = Mock()
            face_model_manager.feature_extractor.return_value = mock_features
            
            # 执行测试
            result = face_model_manager.detect_and_extract_faces('test_image.jpg')
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 1
            assert 'bbox' in result[0]
            assert 'features' in result[0]
            assert isinstance(result[0]['features'], list)
            assert len(result[0]['features']) == 3
    
    def test_detect_and_extract_faces_detection_failed(self, face_model_manager):
        """测试检测并提取人脸特征时检测失败"""
        # 设置mock对象
        mock_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        with patch('cv2.imread', return_value=mock_image), \
             patch('cv2.cvtColor', return_value=mock_image):
            
            # 模拟检测失败
            face_model_manager.face_detector.detect_faces = Mock(return_value=[])
            
            # 执行测试
            result = face_model_manager.detect_and_extract_faces('test_image.jpg')
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 0
    
    def test_detect_faces_low_confidence_filtered(self, face_model_manager):
        """测试低置信度人脸被过滤"""
        # 设置mock对象
        mock_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        with patch('cv2.imread', return_value=mock_image), \
             patch('cv2.cvtColor', return_value=mock_image):
            
            # 模拟低置信度检测结果
            mock_faces = [
                {
                    'box': [100, 100, 200, 200],
                    'keypoints': {'left_eye': [150, 150], 'right_eye': [200, 150]},
                    'confidence': 0.3  # 低于阈值0.9
                }
            ]
            face_model_manager.face_detector.detect_faces = Mock(return_value=mock_faces)
            
            # 执行测试
            result = face_model_manager.detect_faces('test_image.jpg')
            
            # 验证低置信度人脸被过滤
            assert isinstance(result, list)
            assert len(result) == 0

class TestFaceModelManagerSingleton:
    """人脸模型管理器单例模式测试"""
    
    def test_get_face_model_manager_singleton(self):
        """测试获取全局人脸模型管理器实例"""
        with patch('src.business.face_model_manager.MTCNN'), \
             patch('src.business.face_model_manager.InceptionResnetV1'):
            
            # 重置全局实例
            import src.business.face_model_manager as fmm
            fmm._face_model_manager = None
            
            # 获取第一个实例
            manager1 = get_face_model_manager()
            assert manager1 is not None
            
            # 获取第二个实例，应该与第一个相同
            manager2 = get_face_model_manager()
            assert manager1 is manager2

# 导入torch以避免NameError
import torch

if __name__ == '__main__':
    pytest.main([__file__])