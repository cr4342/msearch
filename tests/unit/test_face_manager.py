"""
FaceManager单元测试
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List
import numpy as np
import cv2

from src.search_service.face_manager import FaceManager


class TestFaceManager:
    """FaceManager单元测试类"""
    
    @pytest.fixture
    def face_manager(self):
        """创建FaceManager实例"""
        return FaceManager()
    
    @pytest.fixture
    def sample_image(self):
        """创建测试用的图像文件"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(b'fake image data')
            return tmp.name
    
    @pytest.fixture
    def sample_video(self):
        """创建测试用的视频文件"""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b'fake video data')
            return tmp.name
    
    def test_initialization(self, face_manager):
        """测试FaceManager初始化"""
        assert face_manager is not None
        assert hasattr(face_manager, 'face_recognition_enabled')
    
    def test_check_face_recognition_availability(self, face_manager):
        """测试人脸功能可用性检查"""
        # 测试人脸功能不可用的情况
        face_manager.detector = None
        face_manager.encoder = None
        face_manager.app = None
        assert not face_manager._check_face_recognition_availability()
    
    @patch('src.search_service.face_manager.cv2.imread')
    def test_detect_faces_no_model(self, mock_imread, face_manager, sample_image):
        """测试无人脸模型时的人脸检测"""
        # 设置无人脸模型
        face_manager.detector = None
        face_manager.encoder = None
        face_manager.app = None
        face_manager.face_recognition_enabled = False
        
        result = face_manager.detect_faces(sample_image)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0
    
    @patch('src.search_service.face_manager.cv2.imread')
    @patch('src.search_service.face_manager.MTCNN')
    @patch('src.search_service.face_manager.InceptionResnetV1')
    def test_detect_faces_facenet(self, 
                                mock_resnet, 
                                mock_mtcnn, 
                                mock_imread, 
                                face_manager, 
                                sample_image):
        """测试使用facenet进行人脸检测"""
        # 模拟依赖
        mock_imread.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 模拟MTCNN检测结果
        mock_detector = MagicMock()
        mock_detector.detect.return_value = (np.array([[100, 100, 200, 200]]), None)
        mock_mtcnn.return_value = mock_detector
        
        # 模拟InceptionResnetV1
        mock_encoder = MagicMock()
        mock_encoder.return_value = np.random.rand(512)
        mock_resnet.return_value.eval.return_value = mock_encoder
        
        # 初始化模型
        face_manager.detector = mock_detector
        face_manager.encoder = mock_encoder
        face_manager.face_recognition_enabled = True
        
        result = face_manager.detect_faces(sample_image)
        
        assert result is not None
        assert isinstance(result, list)
    
    @patch('src.search_service.face_manager.cv2.imread')
    @patch('src.search_service.face_manager.FaceAnalysis')
    def test_detect_faces_insightface(self, 
                                    mock_face_analysis, 
                                    mock_imread, 
                                    face_manager, 
                                    sample_image):
        """测试使用insightface进行人脸检测"""
        # 模拟依赖
        mock_imread.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 模拟InsightFace检测结果
        mock_app = MagicMock()
        mock_app.get.return_value = [{
            'bbox': np.array([100, 100, 200, 200]),
            'det_score': 0.95,
            'embedding': np.random.rand(512)
        }]
        mock_face_analysis.return_value = mock_app
        
        # 初始化模型
        face_manager.app = mock_app
        face_manager.face_recognition_enabled = True
        
        result = face_manager.detect_faces(sample_image)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
    
    @patch('src.search_service.face_manager.cv2.imread')
    @patch('src.search_service.face_manager.DatabaseAdapter')
    def test_register_person(self, mock_db_adapter, mock_imread, face_manager, sample_image):
        """测试人物注册"""
        # 模拟依赖
        mock_imread.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 设置人脸功能可用
        face_manager.face_recognition_enabled = True
        
        # 模拟人脸检测结果
        with patch.object(face_manager, 'detect_faces') as mock_detect_faces:
            mock_detect_faces.return_value = [{"embedding": np.random.rand(512)}]
            
            # 模拟数据库适配器
            mock_db = MagicMock()
            mock_db_adapter.return_value = mock_db
            face_manager.db_adapter = mock_db
            
            result = face_manager.register_person("test_person", sample_image)
            
            assert result is not None
            assert isinstance(result, str)
    
    def test_calculate_similarity(self, face_manager):
        """测试相似度计算"""
        # 创建两个相似向量
        vector1 = np.array([0.5, 0.5, 0.5, 0.5])
        vector2 = np.array([0.5, 0.5, 0.5, 0.5])
        
        similarity = face_manager._calculate_similarity(vector1, vector2)
        assert similarity == 1.0
        
        # 创建两个不同向量
        vector3 = np.array([1.0, 0.0, 0.0, 0.0])
        vector4 = np.array([0.0, 1.0, 0.0, 0.0])
        
        similarity = face_manager._calculate_similarity(vector3, vector4)
        assert similarity == 0.0
        
        # 测试不同形状的向量
        vector5 = np.array([0.5, 0.5, 0.5])
        vector6 = np.array([0.5, 0.5])
        
        similarity = face_manager._calculate_similarity(vector5, vector6)
        assert similarity == 0.0
    
    @patch('src.search_service.face_manager.DatabaseAdapter')
    def test_match_person(self, mock_db_adapter, face_manager):
        """测试人脸匹配"""
        # 设置人脸功能可用
        face_manager.face_recognition_enabled = True
        
        # 模拟数据库适配器
        mock_db = MagicMock()
        mock_db.get_all_face_embeddings.return_value = [
            {
                'person_id': 'person_1',
                'name': 'test_person',
                'embedding': np.array([0.5, 0.5, 0.5, 0.5])
            }
        ]
        mock_db_adapter.return_value = mock_db
        face_manager.db_adapter = mock_db
        
        # 测试匹配成功
        query_vector = np.array([0.5, 0.5, 0.5, 0.5])
        result = face_manager.match_person(query_vector, threshold=0.8)
        
        assert result is not None
        assert isinstance(result, dict)
        assert result['name'] == 'test_person'
        
        # 测试匹配失败
        query_vector = np.array([0.0, 0.0, 0.0, 0.0])
        result = face_manager.match_person(query_vector, threshold=0.8)
        
        assert result is None
    
    @patch('src.search_service.face_manager.DatabaseAdapter')
    def test_search_by_person_name(self, mock_db_adapter, face_manager):
        """测试根据人名搜索"""
        # 模拟数据库适配器
        mock_db = MagicMock()
        mock_db.get_person_by_name.return_value = {"id": "person_1"}
        mock_db.get_files_by_person.return_value = [
            {
                'file_id': 'file_1',
                'file_path': '/test/file1.jpg',
                'file_name': 'file1.jpg',
                'file_type': 'image',
                'timestamp': None,
                'confidence': 0.8
            }
        ]
        mock_db_adapter.return_value = mock_db
        face_manager.db_adapter = mock_db
        
        result = face_manager.search_by_person_name("test_person")
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
    
    @patch('src.search_service.face_manager.cv2.VideoCapture')
    def test_extract_faces_from_video(self, mock_video_capture, face_manager, sample_video):
        """测试从视频中提取人脸"""
        # 设置人脸功能可用
        face_manager.face_recognition_enabled = True
        
        # 模拟视频捕获
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = [30.0, 100, 0]  # fps: 30, frame_count: 100, video_duration: 0
        mock_cap.read.return_value = (False, None)  # 立即结束读取
        mock_video_capture.return_value = mock_cap
        
        result = face_manager.extract_faces_from_video(sample_video)
        
        assert result is not None
        assert isinstance(result, list)
    
    def test_detect_faces_from_frame(self, face_manager):
        """测试从视频帧中检测人脸"""
        # 设置人脸功能不可用
        face_manager.face_recognition_enabled = False
        
        result = face_manager.detect_faces_from_frame(np.zeros((480, 640, 3), dtype=np.uint8))
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0
    
    @patch('src.search_service.face_manager.cv2.cvtColor')
    @patch('src.search_service.face_manager.MTCNN')
    def test_detect_faces_from_frame_facenet(self, 
                                        mock_mtcnn, 
                                        mock_cvt_color, 
                                        face_manager):
        """测试使用facenet从视频帧中检测人脸"""
        # 设置人脸功能可用
        face_manager.face_recognition_enabled = True
        
        # 模拟依赖
        mock_cvt_color.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 模拟MTCNN检测结果
        mock_detector = MagicMock()
        mock_detector.detect.return_value = (np.array([[100, 100, 200, 200]]), None)
        mock_mtcnn.return_value = mock_detector
        
        # 初始化模型
        face_manager.detector = mock_detector
        
        result = face_manager.detect_faces_from_frame(np.zeros((480, 640, 3), dtype=np.uint8))
        
        assert result is not None
        assert isinstance(result, list)
    
    @patch('src.search_service.face_manager.cv2.cvtColor')
    @patch('src.search_service.face_manager.FaceAnalysis')
    def test_detect_faces_from_frame_insightface(self, 
                                            mock_face_analysis, 
                                            mock_cvt_color, 
                                            face_manager):
        """测试使用insightface从视频帧中检测人脸"""
        # 设置人脸功能可用
        face_manager.face_recognition_enabled = True
        
        # 模拟依赖
        mock_cvt_color.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 模拟InsightFace检测结果
        mock_app = MagicMock()
        mock_app.get.return_value = [{
            'bbox': np.array([100, 100, 200, 200]),
            'det_score': 0.95,
            'embedding': np.random.rand(512)
        }]
        mock_face_analysis.return_value = mock_app
        
        # 初始化模型
        face_manager.app = mock_app
        
        result = face_manager.detect_faces_from_frame(np.zeros((480, 640, 3), dtype=np.uint8))
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
    
    @patch('src.search_service.face_manager.FaceAnalysis')
    @patch('src.search_service.face_manager.InceptionResnetV1')
    @patch('src.search_service.face_manager.MTCNN')
    def test_initialization_error(self, 
                                mock_mtcnn, 
                                mock_resnet, 
                                mock_face_analysis, 
                                face_manager):
        """测试初始化错误处理"""
        # 模拟初始化失败
        mock_mtcnn.side_effect = Exception("MTCNN initialization failed")
        mock_face_analysis.side_effect = Exception("InsightFace initialization failed")
        
        # 重新初始化
        face_manager._initialize_models()
        
        # 检查人脸功能是否不可用
        assert not face_manager.face_recognition_enabled
    
    def test_register_person_no_face(self, face_manager, sample_image):
        """测试注册无人脸的图像"""
        # 设置人脸功能可用
        face_manager.face_recognition_enabled = True
        
        # 模拟未检测到人脸
        with patch.object(face_manager, 'detect_faces') as mock_detect_faces:
            mock_detect_faces.return_value = []
            
            result = face_manager.register_person("test_person", sample_image)
            
            assert result is None
    
    @patch('src.search_service.face_manager.cv2.imread')
    def test_detect_faces_invalid_image(self, mock_imread, face_manager, sample_image):
        """测试检测无效图像"""
        # 设置人脸功能可用
        face_manager.face_recognition_enabled = True
        
        # 模拟无法读取图像
        mock_imread.return_value = None
        
        result = face_manager.detect_faces(sample_image)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_get_face_manager(self):
        """测试获取全局人脸管理器实例"""
        from src.search_service.face_manager import get_face_manager
        
        face_manager = get_face_manager()
        assert face_manager is not None
        assert isinstance(face_manager, FaceManager)
        
        # 测试单例模式
        face_manager2 = get_face_manager()
        assert face_manager is face_manager2
    
    def test_preprocess_face(self, face_manager):
        """测试人脸预处理"""
        # 测试无模型时的预处理
        face_manager.encoder = None
        result = face_manager._preprocess_face(np.zeros((224, 224, 3), dtype=np.uint8))
        assert result is None
    
    def test_extract_embedding(self, face_manager):
        """测试人脸特征提取"""
        # 测试无模型时的特征提取
        face_manager.encoder = None
        result = face_manager._extract_embedding(None)
        assert result is None
    
    @patch('src.search_service.face_manager.DatabaseAdapter')
    def test_match_person_no_embeddings(self, mock_db_adapter, face_manager):
        """测试无已注册人脸特征时的匹配"""
        # 设置人脸功能可用
        face_manager.face_recognition_enabled = True
        
        # 模拟数据库适配器
        mock_db = MagicMock()
        mock_db.get_all_face_embeddings.return_value = []
        mock_db_adapter.return_value = mock_db
        face_manager.db_adapter = mock_db
        
        # 测试匹配
        query_vector = np.array([0.5, 0.5, 0.5, 0.5])
        result = face_manager.match_person(query_vector)
        
        assert result is None
    
    @patch('src.search_service.face_manager.DatabaseAdapter')
    def test_search_by_nonexistent_person(self, mock_db_adapter, face_manager):
        """测试搜索不存在的人名"""
        # 模拟数据库适配器
        mock_db = MagicMock()
        mock_db.get_person_by_name.return_value = None
        mock_db_adapter.return_value = mock_db
        face_manager.db_adapter = mock_db
        
        result = face_manager.search_by_person_name("nonexistent_person")
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0
    
    @patch('src.search_service.face_manager.cv2.VideoCapture')
    def test_extract_faces_from_invalid_video(self, mock_video_capture, face_manager, sample_video):
        """测试从无效视频中提取人脸"""
        # 设置人脸功能可用
        face_manager.face_recognition_enabled = True
        
        # 模拟无法打开视频
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap
        
        result = face_manager.extract_faces_from_video(sample_video)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0