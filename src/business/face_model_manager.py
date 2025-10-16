"""
人脸模型管理器模块
负责管理人脸检测和特征提取模型
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from mtcnn import MTCNN
from facenet_pytorch import InceptionResnetV1
import torch
from PIL import Image
import os

from src.core.config_manager import get_config_manager
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class FaceModelManager:
    """人脸模型管理器 - 负责人脸检测和特征提取"""
    
    def __init__(self):
        """初始化人脸模型管理器"""
        self.config_manager = get_config_manager()
        self.config = self.config_manager.config
        
        # 从配置获取参数
        self.face_config = self.config_manager.get('face_recognition', {})
        self.detection_config = self.face_config.get('detection', {})
        self.feature_config = self.face_config.get('feature_extraction', {})
        
        # 初始化人脸检测器
        self.face_detector = None
        self._init_face_detector()
        
        # 初始化特征提取器
        self.feature_extractor = None
        self._init_feature_extractor()
        
        # 监听配置变更
        self.config_manager.watch('face_recognition', self._reload_config)
        
        logger.info("人脸模型管理器初始化完成")
    
    def _reload_config(self, key: str, value: Any) -> None:
        """重新加载配置"""
        if 'detection' in key:
            self.detection_config = self.config_manager.get('face_recognition.detection', {})
        elif 'feature_extraction' in key:
            self.feature_config = self.config_manager.get('face_recognition.feature_extraction', {})
        
        logger.info(f"人脸模型管理器配置已更新: {key}")
    
    def _init_face_detector(self) -> None:
        """初始化人脸检测器"""
        try:
            # 使用MTCNN进行人脸检测
            self.face_detector = MTCNN(
                min_face_size=self.detection_config.get('min_face_size', 40),
                thresholds=[
                    self.detection_config.get('confidence_threshold', 0.9),
                    0.8,
                    0.7
                ]
            )
            logger.info("人脸检测器初始化完成")
        except Exception as e:
            logger.error(f"人脸检测器初始化失败: {e}")
            raise
    
    def _init_feature_extractor(self) -> None:
        """初始化特征提取器"""
        try:
            # 使用FaceNet进行特征提取
            self.feature_extractor = InceptionResnetV1(pretrained='vggface2').eval()
            logger.info("人脸特征提取器初始化完成")
        except Exception as e:
            logger.error(f"人脸特征提取器初始化失败: {e}")
            raise
    
    def detect_faces(self, image_path: str) -> List[Dict[str, Any]]:
        """
        检测图像中的人脸
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            检测到的人脸列表，包含边界框、关键点和置信度
        """
        try:
            logger.info(f"检测图像中的人脸: {image_path}")
            
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"无法读取图像: {image_path}")
            
            # 转换为RGB格式
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 检测人脸
            faces = self.face_detector.detect_faces(image_rgb)
            
            # 转换结果格式
            detected_faces = []
            for face in faces:
                # 获取边界框
                x, y, width, height = face['box']
                
                # 获取关键点
                keypoints = face['keypoints']
                
                # 获取置信度
                confidence = face['confidence']
                
                # 只保留置信度高于阈值的人脸
                if confidence >= self.detection_config.get('confidence_threshold', 0.9):
                    detected_faces.append({
                        'bbox': {
                            'x': x,
                            'y': y,
                            'width': width,
                            'height': height
                        },
                        'keypoints': keypoints,
                        'confidence': confidence,
                        'image_path': image_path
                    })
            
            logger.info(f"检测到 {len(detected_faces)} 个人脸")
            return detected_faces
            
        except Exception as e:
            logger.error(f"人脸检测失败: {e}")
            return []
    
    def extract_face_features(self, image_path: str, bbox: Dict[str, int]) -> Optional[np.ndarray]:
        """
        提取人脸特征向量
        
        Args:
            image_path: 图像文件路径
            bbox: 人脸边界框 {x, y, width, height}
            
        Returns:
            512维人脸特征向量
        """
        try:
            logger.info(f"提取人脸特征: {image_path}")
            
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"无法读取图像: {image_path}")
            
            # 裁剪人脸区域
            x, y, width, height = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            face_image = image[y:y+height, x:x+width]
            
            # 转换为PIL图像并调整大小
            face_pil = Image.fromarray(cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB))
            face_pil = face_pil.resize((160, 160))
            
            # 转换为tensor
            face_tensor = torch.tensor(np.array(face_pil)).permute(2, 0, 1).float()
            face_tensor = face_tensor.unsqueeze(0)
            
            # 归一化
            face_tensor = (face_tensor - 127.5) / 128.0
            
            # 提取特征
            with torch.no_grad():
                features = self.feature_extractor(face_tensor)
            
            # 转换为numpy数组
            features_np = features.squeeze().numpy()
            
            # L2归一化
            if self.feature_config.get('normalize', True):
                features_np = features_np / np.linalg.norm(features_np)
            
            logger.info(f"人脸特征提取完成，维度: {len(features_np)}")
            return features_np
            
        except Exception as e:
            logger.error(f"人脸特征提取失败: {e}")
            return None
    
    def detect_and_extract_faces(self, image_path: str) -> List[Dict[str, Any]]:
        """
        检测并提取图像中所有人脸的特征
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            包含人脸信息和特征向量的列表
        """
        try:
            logger.info(f"检测并提取图像中的人脸特征: {image_path}")
            
            # 检测人脸
            faces = self.detect_faces(image_path)
            
            # 提取特征
            face_features = []
            for face in faces:
                bbox = face['bbox']
                features = self.extract_face_features(image_path, bbox)
                
                if features is not None:
                    face_features.append({
                        **face,
                        'features': features.tolist()  # 转换为列表以便序列化
                    })
            
            logger.info(f"检测并提取了 {len(face_features)} 个人脸特征")
            return face_features
            
        except Exception as e:
            logger.error(f"人脸检测和特征提取失败: {e}")
            return []


# 全局人脸模型管理器实例
_face_model_manager = None


def get_face_model_manager() -> FaceModelManager:
    """
    获取全局人脸模型管理器实例
    
    Returns:
        人脸模型管理器实例
    """
    global _face_model_manager
    if _face_model_manager is None:
        _face_model_manager = FaceModelManager()
    return _face_model_manager