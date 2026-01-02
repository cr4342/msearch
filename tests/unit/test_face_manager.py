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
    @patch('src.search_service.face_manager.insightface.app.FaceAnalysis')
    def test_detect_faces_insightface(self, 
                                    mock_face_analysis, 
                                    mock_imread, 
                                    face_manager, 
                                    sample_image):
        """测试使用insightface进行人脸检测"""
        # 模拟依赖
        mock_imread.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 模拟insightface检测结果
        mock_app = MagicMock()
        mock_app.get.return_value = [{"bbox": [100, 100, 200, 200], "embedding": np.random.rand(512)}]
        mock_face_analysis.return_value = mock_app
        
        # 初始化模型
        face_manager.app = mock_app
        face_manager.face_recognition_enabled = True
        
        result = face_manager.detect_faces(sample_image)
        
        assert result is not None
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_register_person(self, face_manager, sample_image):
        """测试注册人��"""
        # 设置无人脸模型
        face_manager.detector = None
        face_manager.encoder = None
        face_manager.app = None
        face_manager.face_recognition_enabled = False
        
        result = await face_manager.register_person(sample_image, "test_person")
        
        assert result is not None
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_match_person(self, face_manager, sample_image):
        """测试匹配人��"""
        # 设置无人脸模型
        face_manager.detector = None
        face_manager.encoder = None
        face_manager.app = None
        face_manager.face_recognition_enabled = False
        
        result = await face_manager.match_person(np.random.rand(512))
        
        assert result is not None
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_extract_faces_from_video(self, face_manager, sample_video):
        """测试从视频中提取人脸"""
        # 设置无人脸模型
        face_manager.detector = None
        face_manager.encoder = None
        face_manager.app = None
        face_manager.face_recognition_enabled = False
        
        result = await face_manager.extract_faces_from_video(sample_video)
        
        assert result is not None
        assert isinstance(result, list)
    
    @patch('src.search_service.face_manager.cv2.imread')
    @patch('src.search_service.face_manager.MTCNN')
    @patch('src.search_service.face_manager.InceptionResnetV1')
    def test_detect_faces_from_frame_facenet(self, 
                                            mock_resnet, 
                                            mock_mtcnn, 
                                            mock_imread, 
                                            face_manager, 
                                            sample_image):
        """测试使用facenet从单帧图像检测人脸"""
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
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = face_manager._detect_faces_from_frame(frame)
        
        assert result is not None
        assert isinstance(result, list)
    
    @patch('src.search_service.face_manager.cv2.imread')
    @patch('src.search_service.face_manager.insightface.app.FaceAnalysis')
    def test_detect_faces_from_frame_insightface(self, 
                                            mock_face_analysis, 
                                            mock_imread, 
                                            face_manager, 
                                            sample_image):
        """测试使用insightface从单帧图像检测人脸"""
        # 模拟依赖
        mock_imread.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 模拟insightface检测结果
        mock_app = MagicMock()
        mock_app.get.return_value = [{"bbox": [100, 100, 200, 200], "embedding": np.random.rand(512)}]
        mock_face_analysis.return_value = mock_app
        
        # 初始化模型
        face_manager.app = mock_app
        face_manager.face_recognition_enabled = True
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = face_manager._detect_faces_from_frame(frame)
        
        assert result is not None
        assert isinstance(result, list)
    
    def test_initialization_error(self, face_manager):
        """测试初始化错误处理"""
        # 模拟初始化错误
        with patch('src.search_service.face_manager.insightface.app.FaceAnalysis', side_effect=Exception("Insightface initialization error")):
            face_manager._init_face_models()
            assert not face_manager.face_recognition_enabled
    
    @pytest.mark.asyncio
    async def test_register_person_no_face(self, face_manager, sample_image):
        """测试注册无人脸的图像"""
        # 设置无人脸模型
        face_manager.detector = None
        face_manager.encoder = None
        face_manager.app = None
        face_manager.face_recognition_enabled = False
        
        result = await face_manager.register_person(sample_image, "test_person")
        
        assert result is not None
        assert isinstance(result, dict)
    
    @patch('src.search_service.face_manager.cv2.imread')
    def test_detect_faces_invalid_image(self, mock_imread, face_manager, sample_image):
        """测试检测无效图像的人脸"""
        # 模拟无效图像
        mock_imread.return_value = None
        
        result = face_manager.detect_faces(sample_image)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_match_person_no_embeddings(self, face_manager):
        """测试无嵌入向量时的人脸匹配"""
        # 设置无人脸模型
        face_manager.detector = None
        face_manager.encoder = None
        face_manager.app = None
        face_manager.face_recognition_enabled = False
        
        # 清空人脸特征库
        face_manager.face_embeddings = {}
        
        result = await face_manager.match_person(np.random.rand(512))
        
        assert result is not None
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_extract_faces_from_invalid_video(self, face_manager):
        """测试从无效视频中提取人脸"""
        # 设置无人脸模型
        face_manager.detector = None
        face_manager.encoder = None
        face_manager.app = None
        face_manager.face_recognition_enabled = False
        
        result = await face_manager.extract_faces_from_video("invalid_video_path")
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_calculate_similarity(self, face_manager):
        """测试计算人脸相似度"""
        # 测试相同向量的相似度
        embedding1 = np.ones(512)
        embedding2 = np.ones(512)
        similarity = face_manager._calculate_similarity(embedding1, embedding2)
        assert similarity == 1.0
        
        # 测试不同向量的相似度
        embedding2 = np.zeros(512)
        similarity = face_manager._calculate_similarity(embedding1, embedding2)
        assert similarity < 1.0
    
    def test_generate_face_id(self, face_manager):
        """测试生成人脸ID"""
        face_id = face_manager._generate_face_id("test_person")
        assert isinstance(face_id, str)
        assert len(face_id) > 0
    
    @pytest.mark.asyncio
    async def test_get_all_registered_persons(self, face_manager):
        """测试获取所有注册人"""
        # 设置无人脸模型
        face_manager.detector = None
        face_manager.encoder = None
        face_manager.app = None
        face_manager.face_recognition_enabled = False
        
        result = await face_manager.get_all_registered_persons()
        
        assert result is not None
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_delete_registered_person(self, face_manager):
        """测试删除注册人"""
        # 设置无人脸模型
        face_manager.detector = None
        face_manager.encoder = None
        face_manager.app = None
        face_manager.face_recognition_enabled = False
        
        result = await face_manager.delete_registered_person("test_person_id")
        
        assert result is not None
        assert isinstance(result, dict)
