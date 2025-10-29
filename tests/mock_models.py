"""
模型Mock接口
为测试环境提供轻量级模型模拟
"""

import numpy as np
from typing import List, Dict, Any
import asyncio


class MockInfinityEngine:
    """Mock Infinity引擎"""
    
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.vector_dim = 512  # 标准向量维度
        
    async def embed(self, texts: List[str]) -> tuple:
        """Mock文本嵌入"""
        embeddings = [np.random.rand(self.vector_dim).astype(np.float32) for _ in texts]
        return embeddings, {}
    
    async def image_embed(self, images: List[str]) -> tuple:
        """Mock图像嵌入"""
        embeddings = [np.random.rand(self.vector_dim).astype(np.float32) for _ in images]
        return embeddings, {}
    
    async def audio_embed(self, audio_files: List[str]) -> tuple:
        """Mock音频嵌入"""
        embeddings = [np.random.rand(self.vector_dim).astype(np.float32) for _ in audio_files]
        return embeddings, {}
    
    async def transcribe(self, audio_files: List[str]) -> tuple:
        """Mock语音转文本"""
        # 返回mock文本和嵌入
        texts = [f"mock transcription for {file}" for file in audio_files]
        embeddings = [np.random.rand(self.vector_dim).astype(np.float32) for _ in audio_files]
        return embeddings, {"texts": texts}


class MockFaceDetector:
    """Mock人脸检测器"""
    
    def detect_faces(self, image):
        """Mock人脸检测"""
        # 返回空的人脸检测结果
        return []
    
    def extract_features(self, image, face_locations):
        """Mock特征提取"""
        return []


class MockAudioClassifier:
    """Mock音频分类器"""
    
    def classify_segments(self, audio_file):
        """Mock音频片段分类"""
        # 返回mock分类结果
        return [
            {
                "label": "music",
                "start": 0.0,
                "end": 10.0,
                "confidence": 0.8
            }
        ]


class MockMediaProcessor:
    """Mock媒体处理器"""
    
    def __init__(self):
        self.face_detector = MockFaceDetector()
        self.audio_classifier = MockAudioClassifier()
    
    def process_image(self, image_path):
        """Mock图像处理"""
        return {
            "faces": [],
            "features": [],
            "metadata": {"width": 640, "height": 480, "format": "jpeg"}
        }
    
    def process_video(self, video_path):
        """Mock视频处理"""
        return {
            "frames": [],
            "scenes": [],
            "audio_segments": [],
            "metadata": {"duration": 60.0, "fps": 30, "resolution": "640x480"}
        }
    
    def process_audio(self, audio_path):
        """Mock音频处理"""
        return {
            "segments": self.audio_classifier.classify_segments(audio_path),
            "transcription": "mock transcription",
            "metadata": {"duration": 30.0, "sample_rate": 16000, "channels": 1}
        }


def create_mock_embedding_engine(config):
    """创建Mock嵌入引擎"""
    from unittest.mock import Mock, AsyncMock
    
    mock_engine = Mock()
    mock_engine.embed = AsyncMock(return_value=([np.random.rand(512).astype(np.float32)], {}))
    mock_engine.image_embed = AsyncMock(return_value=([np.random.rand(512).astype(np.float32)], {}))
    mock_engine.audio_embed = AsyncMock(return_value=([np.random.rand(512).astype(np.float32)], {}))
    mock_engine.transcribe = AsyncMock(return_value=([np.random.rand(512).astype(np.float32)], {"texts": ["mock text"]}))
    
    return mock_engine


def patch_models_for_testing():
    """为测试环境设置模型mock"""
    patches = []
    
    # Mock Infinity导入 - 完全禁用真实导入
    patches.append(patch('src.business.embedding_engine.INFINITY_AVAILABLE', False))
    patches.append(patch('src.business.embedding_engine.AsyncEngineArray', MockInfinityEngine))
    patches.append(patch('src.business.embedding_engine.EngineArgs', MockInfinityEngine))
    
    # Mock 人脸检测器
    patches.append(patch('src.business.face_model_manager.MTCNN', MockFaceDetector))
    patches.append(patch('src.business.face_model_manager.FaceNet', MockFaceDetector))
    patches.append(patch('src.business.face_model_manager.InsightFace', MockFaceDetector))
    
    # Mock 音频分类器
    patches.append(patch('src.processors.audio_classifier.inaSpeechSegmenter', MockAudioClassifier))
    
    return patches


def setup_test_environment():
    """设置测试环境"""
    import os
    
    # 设置测试环境变量
    os.environ["MSEARCH_TEST_MODE"] = "true"
    os.environ["MSEARCH_MOCK_MODELS"] = "true"
    os.environ["MSEARCH_DEVICE"] = "cpu"
    
    # 确保测试目录存在
    os.makedirs("./tests/test_data", exist_ok=True)
    os.makedirs("./tests/temp", exist_ok=True)
    
    print("✅ 测试环境设置完成")