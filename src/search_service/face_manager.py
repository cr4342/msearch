
"""
人脸管理器
负责人脸识别和基于人名的检索功能
"""

import os
import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np
import cv2
from pathlib import Path

from src.core.retry import async_retry

# 尝试导入人脸检测相关库
try:
    from facenet_pytorch import MTCNN, InceptionResnetV1
    import torch
    FACENET_AVAILABLE = True
except ImportError:
    FACENET_AVAILABLE = False
    logging.warning("facenet_pytorch not available, face recognition will be disabled")

try:
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False
    logging.warning("insightface not available, face recognition will be disabled")

from src.common.storage.database_adapter import DatabaseAdapter
from src.core.config_manager import get_config_manager


logger = logging.getLogger(__name__)


class FaceManager:
    """人脸管理器 - 负责人脸识别和基于人名的检索"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.db_adapter = DatabaseAdapter()
        
        # 初始化人脸检测模型
        self._initialize_models()
        
        # 检查人脸功能是否可用
        self.face_recognition_enabled = self._check_face_recognition_availability()
        
        if self.face_recognition_enabled:
            logger.info("人脸管理器初始化成功")
        else:
            logger.warning("人脸管理器初始化失败，人脸功能不可用")
    
    def _initialize_models(self):
        """初始化人脸检测和识别模型"""
        if not FACENET_AVAILABLE and not INSIGHTFACE_AVAILABLE:
            logger.warning("无人脸识别库可用，人脸功能将被禁用")
            self.detector = None
            self.encoder = None
            return
        
        # 从配置获取模型参数
        face_config = self.config_manager.get('face_recognition', {})
        
        if FACENET_AVAILABLE:
            try:
                # 初始化MTCNN人脸检测器
                self.detector = MTCNN(
                    image_size=face_config.get('detection.min_face_size', 160),
                    margin=0,
                    min_face_size=face_config.get('detection.min_face_size', 40),
                    thresholds=face_config.get('detection.thresholds', [0.6, 0.7, 0.7]),
                    factor=0.709,
                    post_process=True,
                    device=self._get_device(face_config.get('device', 'cpu'))
                )
                
                # 初始化InceptionResnetV1特征提取器
                self.encoder = InceptionResnetV1(
                    pretrained='vggface2',
                    classify=False,
                    num_classes=None
                ).eval()
                
                if face_config.get('device', 'cpu') == 'cuda' and torch.cuda.is_available():
                    self.encoder.cuda()
                
                logger.info("使用facenet_pytorch模型初始化人脸管理器")
            except Exception as e:
                logger.error(f"初始化facenet模型失败: {e}")
                self.detector = None
                self.encoder = None
        elif INSIGHTFACE_AVAILABLE:
            try:
                self.app = FaceAnalysis(name='buffalo_l')
                self.app.prepare(ctx_id=0, det_size=(640, 640))
                logger.info("使用insightface模型初始化人脸管理器")
            except Exception as e:
                logger.error(f"初始化insightface模型失败: {e}")
                self.app = None
        else:
            self.detector = None
            self.encoder = None
    
    def _get_device(self, device_str: str):
        """获取torch设备"""
        if device_str == 'cuda' and torch.cuda.is_available():
            return torch.device('cuda')
        return torch.device('cpu')
    
    def _check_face_recognition_availability(self) -> bool:
        """检查人脸功能是否可用"""
        return (FACENET_AVAILABLE and hasattr(self, 'detector') and self.detector is not None) or \
               (INSIGHTFACE_AVAILABLE and hasattr(self, 'app') and self.app is not None)
    
    @async_retry(max_attempts=3, delay=0.5, backoff=2.0)
    def detect_faces(self, image_path: str) -> List[Dict[str, Any]]:
        """检测图像中的人脸"""
        if not self.face_recognition_enabled:
            logger.error("人脸功能不可用")
            return []
        
        try:
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"无法读取图像: {image_path}")
                return []
            
            # 转换为RGB格式（如果使用facenet_pytorch）
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            faces_info = []
            
            if FACENET_AVAILABLE and self.detector is not None:
                # 使用facenet检测人脸
                boxes, _ = self.detector.detect(image_rgb)
                
                if boxes is not None:
                    for i, box in enumerate(boxes):
                        x1, y1, x2, y2 = [int(coord) for coord in box]
                        
                        # 提取人脸区域
                        face_img = image_rgb[y1:y2, x1:x2]
                        
                        # 提取人脸特征
                        face_tensor = self._preprocess_face(face_img)
                        if face_tensor is not None:
                            embedding = self._extract_embedding(face_tensor)
                            
                            faces_info.append({
                                'bbox': [x1, y1, x2, y2],
                                'embedding': embedding,
                                'confidence': 0.9,  # 暂时使用固定置信度
                                'face_image': face_img
                            })
            elif INSIGHTFACE_AVAILABLE and self.app is not None:
                # 使用insightface检测人脸
                faces = self.app.get(image_rgb)
                
                for face in faces:
                    bbox = face['bbox'].astype(int)
                    x1, y1, x2, y2 = bbox
                    
                    # 提取人脸区域
                    face_img = image_rgb[y1:y2, x1:x2]
                    
                    faces_info.append({
                        'bbox': [x1, y1, x2, y2],
                        'embedding': face['embedding'] if 'embedding' in face else None,
                        'confidence': float(face['det_score']) if 'det_score' in face else 0.9,
                        'face_image': face_img
                    })
            
            return faces_info
            
        except FileNotFoundError as e:
            logger.error(f"文件未找到: {image_path}, 错误: {e}")
            return []
        except PermissionError as e:
            logger.error(f"权限错误: {image_path}, 错误: {e}")
            return []
        except cv2.error as e:
            logger.error(f"OpenCV错误: {image_path}, 错误: {e}")
            return []
        except RuntimeError as e:
            logger.error(f"模型运行时错误: {image_path}, 错误: {e}")
            return []
        except Exception as e:
            logger.error(f"人脸检测失败: {e}")
            return []
    
    def _preprocess_face(self, face_image):
        """预处理人脸图像"""
        if not FACENET_AVAILABLE:
            return None
        
        try:
            # 调整图像大小
            face_image = cv2.resize(face_image, (160, 160))
            
            # 转换为tensor
            face_tensor = torch.tensor(face_image, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0)
            
            # 归一化
            face_tensor = face_tensor / 255.0
            
            return face_tensor
        except Exception as e:
            logger.error(f"人脸预处理失败: {e}")
            return None
    
    def _extract_embedding(self, face_tensor):
        """提取人脸特征向量"""
        if not FACENET_AVAILABLE or self.encoder is None:
            return None
        
        try:
            with torch.no_grad():
                embedding = self.encoder(face_tensor)
                return embedding.squeeze().cpu().numpy()
        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            return None
    
    @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
    def register_person(self, name: str, image_path: str, aliases: Optional[List[str]] = None) -> Optional[str]:
        """注册人脸到人物库"""
        if not self.face_recognition_enabled:
            logger.error("人脸功能不可用")
            return None
        
        try:
            # 检测人脸
            faces_info = self.detect_faces(image_path)
            
            if not faces_info:
                logger.warning(f"在图像中未检测到人脸: {image_path}")
                return None
            
            # 为每个人脸注册信息
            for face_info in faces_info:
                embedding = face_info['embedding']
                if embedding is None:
                    continue
                
                # 生成人物ID
                person_id = str(uuid.uuid4())
                
                # 在数据库中注册人物
                self.db_adapter.add_person(
                    person_id=person_id,
                    name=name,
                    aliases=aliases or [],
                    embedding=embedding,
                    image_path=image_path
                )
                
                logger.info(f"人物注册成功: {name} (ID: {person_id})")
                return person_id
            
            return None
            
        except Exception as e:
            logger.error(f"人物注册失败: {e}")
            return None
    
    def match_person(self, query_embedding: np.ndarray, threshold: float = None) -> Optional[Dict[str, Any]]:
        """匹配人脸到已注册的人物"""
        if not self.face_recognition_enabled:
            logger.error("人脸功能不可用")
            return None
        
        if threshold is None:
            threshold = self.config_manager.get_float('face_recognition.matching.similarity_threshold', 0.6)
        
        try:
            # 从数据库获取所有人脸特征
            stored_embeddings = self.db_adapter.get_all_face_embeddings()
            
            if not stored_embeddings:
                logger.debug("数据库中无人脸特征数据")
                return None
            
            best_match = None
            best_score = 0.0
            
            for person_data in stored_embeddings:
                person_id = person_data['person_id']
                stored_embedding = person_data['embedding']
                
                # 计算余弦相似度
                similarity = self._calculate_similarity(query_embedding, stored_embedding)
                
                if similarity > best_score and similarity >= threshold:
                    best_score = similarity
                    best_match = {
                        'person_id': person_id,
                        'name': person_data['name'],
                        'similarity': similarity,
                        'confidence': similarity
                    }
            
            if best_match:
                logger.debug(f"找到最佳匹配: {best_match['name']} (相似度: {best_match['similarity']:.3f})")
                return best_match
            else:
                logger.debug(f"未找到匹配的人脸 (阈值: {threshold})")
                return None
                
        except Exception as e:
            logger.error(f"人脸匹配失败: {e}")
            return None
    
    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """计算两个特征向量的余弦相似度"""
        try:
            # 确保向量形状一致
            if embedding1.shape != embedding2.shape:
                logger.warning(f"特征向量形状不一致: {embedding1.shape} vs {embedding2.shape}")
                return 0.0
            
            # 归一化向量
            embedding1_norm = embedding1 / np.linalg.norm(embedding1)
            embedding2_norm = embedding2 / np.linalg.norm(embedding2)
            
            # 计算点积（即余弦相似度）
            similarity = np.dot(embedding1_norm, embedding2_norm)
            
            # 确保相似度在合理范围内
            return max(0.0, min(1.0, float(similarity)))
        except Exception as e:
            logger.error(f"相似度计算失败: {e}")
            return 0.0
    
    def search_by_person_name(self, person_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """根据人名搜索包含该人物的媒体文件"""
        try:
            # 从数据库获取人物信息
            person_info = self.db_adapter.get_person_by_name(person_name)
            
            if not person_info:
                logger.debug(f"未找到人物: {person_name}")
                return []
            
            person_id = person_info['id']
            
            # 搜索包含该人物的文件
            file_results = self.db_adapter.get_files_by_person(person_id, limit)
            
            results = []
            for file_record in file_results:
                results.append({
                    'file_id': file_record['file_id'],
                    'file_path': file_record['file_path'],
                    'file_name': file_record['file_name'],
                    'file_type': file_record['file_type'],
                    'timestamp': file_record.get('timestamp'),  # 视频中的时间戳
                    'confidence': file_record.get('confidence', 0.8)
                })
            
            logger.debug(f"找到 {len(results)} 个包含 {person_name} 的文件")
            return results
            
        except Exception as e:
            logger.error(f"人名搜索失败: {e}")
            return []
    
    @async_retry(max_attempts=3, delay=0.5, backoff=2.0)
    def extract_faces_from_video(self, video_path: str, sample_interval: float = 5.0) -> List[Dict[str, Any]]:
        """从视频中提取人脸"""
        if not self.face_recognition_enabled:
            logger.error("人脸功能不可用")
            return []
        
        try:
            import cv2
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"无法打开视频: {video_path}")
                return []
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_duration = frame_count / fps
            
            faces_data = []
            frame_num = 0
            timestamp = 0.0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 根据采样间隔处理帧
                if frame_num % int(fps * sample_interval) == 0:
                    timestamp = frame_num / fps
                    
                    # 检测当前帧中的人脸
                    faces_info = self.detect_faces_from_frame(frame)
                    
                    for face_info in faces_info:
                        faces_data.append({
                            'timestamp': timestamp,
                            'frame_number': frame_num,
                            'embedding': face_info['embedding'],
                            'bbox': face_info['bbox'],
                            'confidence': face_info['confidence'],
                            'video_path': video_path
                        })
                
                frame_num += 1
            
            cap.release()
            logger.info(f"从视频中提取了 {len(faces_data)} 个人脸")
            return faces_data
            
        except FileNotFoundError as e:
            logger.error(f"文件未找到: {video_path}, 错误: {e}")
            return []
        except PermissionError as e:
            logger.error(f"权限错误: {video_path}, 错误: {e}")
            return []
        except cv2.error as e:
            logger.error(f"OpenCV错误: {video_path}, 错误: {e}")
            return []
        except RuntimeError as e:
            logger.error(f"模型运行时错误: {video_path}, 错误: {e}")
            return []
        except Exception as e:
            logger.error(f"从视频提取人脸失败: {e}")
            return []
    
    @async_retry(max_attempts=3, delay=0.5, backoff=2.0)
    def detect_faces_from_frame(self, frame):
        """从视频帧中检测人脸"""
        if not self.face_recognition_enabled:
            return []
        
        try:
            # 转换BGR到RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            faces_info = []
            
            if FACENET_AVAILABLE and self.detector is not None:
                # 使用facenet检测人脸
                boxes, _ = self.detector.detect(frame_rgb)
                
                if boxes is not None:
                    for i, box in enumerate(boxes):
                        x1, y1, x2, y2 = [int(coord) for coord in box]
                        
                        # 提取人脸区域
                        face_img = frame_rgb[y1:y2, x1:x2]
                        
                        # 提取人脸特征
                        face_tensor = self._preprocess_face(face_img)
                        if face_tensor is not None:
                            embedding = self._extract_embedding(face_tensor)
                            
                            faces_info.append({
                                'bbox': [x1, y1, x2, y2],
                                'embedding': embedding,
                                'confidence': 0.9,
                                'face_image': face_img
                            })
            
            elif INSIGHTFACE_AVAILABLE and self.app is not None:
                # 使用insightface检测人脸
                faces = self.app.get(frame_rgb)
                
                for face in faces:
                    bbox = face['bbox'].astype(int)
                    x1, y1, x2, y2 = bbox
                    
                    faces_info.append({
                        'bbox': [x1, y1, x2, y2],
                        'embedding': face['embedding'] if 'embedding' in face else None,
                        'confidence': float(face['det_score']) if 'det_score' in face else 0.9,
                        'face_image': frame_rgb[y1:y2, x1:x2]
                    })
            
            return faces_info
            
        except Exception as e:
            logger.error(f"视频帧人脸检测失败: {e}")
            return []


# 全局人脸管理器实例
_face_manager = None


def get_face_manager() -> Optional[FaceManager]:
    """获取全局人脸管理器实例"""
    global _face_manager
    
    if _face_manager is None:
        try:
            _face_manager = FaceManager()
        except Exception as e:
            logger.error(f"人脸管理器初始化失败: {e}")
            return None
    
    return _face_manager
