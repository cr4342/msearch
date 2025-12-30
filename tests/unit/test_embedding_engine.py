"""
EmbeddingEngine单元测试
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List
import numpy as np

from src.common.embedding.embedding_engine import EmbeddingEngine


class TestEmbeddingEngine:
    """EmbeddingEngine单元测试类"""
    
    @pytest.fixture
    def embedding_engine(self):
        """创建EmbeddingEngine实例"""
        return EmbeddingEngine()
    
    @pytest.fixture
    def sample_image_data(self):
        """创建测试用的图像数据"""
        return b'fake image data'
    
    @pytest.fixture
    def sample_audio_data(self):
        """创建测试用的音频数据"""
        return b'fake audio data'
    
    def test_initialization(self, embedding_engine):
        """测试EmbeddingEngine初始化"""
        assert embedding_engine is not None
        assert hasattr(embedding_engine, 'engines')
        assert hasattr(embedding_engine, 'engine_initialized')
    
    def test_get_available_models(self, embedding_engine):
        """测试获取可用模型列表"""
        models = embedding_engine.get_available_models()
        assert isinstance(models, list)
    
    def test_is_model_available(self, embedding_engine):
        """测试模型可用性检查"""
        assert not embedding_engine.is_model_available('clip')
        assert not embedding_engine.is_model_available('clap')
        assert not embedding_engine.is_model_available('whisper')
    
    @patch('src.common.embedding.embedding_engine.AsyncEngineArray')
    async def test_embed_image(self, mock_async_engine_array, embedding_engine, sample_image_data):
        """测试图像向量化"""
        # 模拟AsyncEngineArray
        mock_engine = MagicMock()
        mock_engine.astart.return_value = None
        mock_engine.image_embed.return_value = ([np.random.rand(512).tolist()], None)
        
        mock_async_engine_array.from_args.return_value = mock_engine
        
        # 手动初始化模型
        embedding_engine.engines['clip'] = mock_engine
        embedding_engine.engine_initialized['clip'] = True
        
        result = await embedding_engine.embed_image(sample_image_data)
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (512,)
    
    @patch('src.common.embedding.embedding_engine.AsyncEngineArray')
    async def test_embed_text_for_visual(self, mock_async_engine_array, embedding_engine):
        """测试文本向量化（用于图像/视频检索）"""
        # 模拟AsyncEngineArray
        mock_engine = MagicMock()
        mock_engine.astart.return_value = None
        mock_engine.embed.return_value = ([np.random.rand(512).tolist()], None)
        
        mock_async_engine_array.from_args.return_value = mock_engine
        
        # 手动初始化模型
        embedding_engine.engines['clip'] = mock_engine
        embedding_engine.engine_initialized['clip'] = True
        
        result = await embedding_engine.embed_text_for_visual("test image")
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (512,)
    
    @patch('src.common.embedding.embedding_engine.AsyncEngineArray')
    async def test_embed_text_for_music(self, mock_async_engine_array, embedding_engine):
        """测试文本向量化（用于音乐检索）"""
        # 模拟AsyncEngineArray
        mock_engine = MagicMock()
        mock_engine.astart.return_value = None
        mock_engine.embed.return_value = ([np.random.rand(512).tolist()], None)
        
        mock_async_engine_array.from_args.return_value = mock_engine
        
        # 手动初始化模型
        embedding_engine.engines['clap'] = mock_engine
        embedding_engine.engine_initialized['clap'] = True
        
        result = await embedding_engine.embed_text_for_music("test music")
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (512,)
    
    @patch('src.common.embedding.embedding_engine.AsyncEngineArray')
    @patch('src.common.embedding.embedding_engine.librosa.resample')
    @patch('src.common.embedding.embedding_engine.soundfile.read')
    @patch('src.common.embedding.embedding_engine.soundfile.write')
    async def test_embed_audio_music(self, 
                                   mock_soundfile_write, 
                                   mock_soundfile_read, 
                                   mock_librosa_resample, 
                                   mock_async_engine_array, 
                                   embedding_engine, 
                                   sample_audio_data):
        """测试音频向量化（音乐）"""
        # 模拟依赖
        mock_soundfile_read.return_value = (np.random.rand(48000), 48000)
        mock_librosa_resample.return_value = np.random.rand(48000)
        
        # 模拟AsyncEngineArray
        mock_engine = MagicMock()
        mock_engine.astart.return_value = None
        mock_engine.audio_embed.return_value = ([np.random.rand(512).tolist()], None)
        
        mock_async_engine_array.from_args.return_value = mock_engine
        
        # 手动初始化模型
        embedding_engine.engines['clap'] = mock_engine
        embedding_engine.engine_initialized['clap'] = True
        
        result = await embedding_engine.embed_audio_music(sample_audio_data)
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (512,)
    
    @patch('src.common.embedding.embedding_engine.AsyncEngineArray')
    async def test_transcribe_audio(self, mock_async_engine_array, embedding_engine, sample_audio_data):
        """测试语音转文本"""
        # 模拟AsyncEngineArray
        mock_engine = MagicMock()
        mock_engine.astart.return_value = None
        mock_engine.audio_embed.return_value = (["test transcription"], None)
        
        mock_async_engine_array.from_args.return_value = mock_engine
        
        # 手动初始化模型
        embedding_engine.engines['whisper'] = mock_engine
        embedding_engine.engine_initialized['whisper'] = True
        
        result = await embedding_engine.transcribe_audio(sample_audio_data)
        
        assert result is not None
        assert isinstance(result, str)
    
    @patch('src.common.embedding.embedding_engine.AsyncEngineArray')
    async def test_transcribe_and_embed(self, mock_async_engine_array, embedding_engine, sample_audio_data):
        """测试转录并向量化语音"""
        # 模拟AsyncEngineArray
        mock_whisper_engine = MagicMock()
        mock_whisper_engine.astart.return_value = None
        mock_whisper_engine.audio_embed.return_value = (["test transcription"], None)
        
        mock_clip_engine = MagicMock()
        mock_clip_engine.astart.return_value = None
        mock_clip_engine.embed.return_value = ([np.random.rand(512).tolist()], None)
        
        mock_async_engine_array.from_args.return_value = mock_whisper_engine
        
        # 手动初始化模型
        embedding_engine.engines['whisper'] = mock_whisper_engine
        embedding_engine.engines['clip'] = mock_clip_engine
        embedding_engine.engine_initialized['whisper'] = True
        embedding_engine.engine_initialized['clip'] = True
        
        result = await embedding_engine.transcribe_and_embed(sample_audio_data)
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (512,)
    
    @patch('src.common.embedding.embedding_engine.AsyncEngineArray')
    async def test_batch_embed_images(self, mock_async_engine_array, embedding_engine):
        """测试批量图像向量化"""
        # 模拟AsyncEngineArray
        mock_engine = MagicMock()
        mock_engine.astart.return_value = None
        mock_engine.image_embed.return_value = ([np.random.rand(512).tolist()], None)
        
        mock_async_engine_array.from_args.return_value = mock_engine
        
        # 手动初始化模型
        embedding_engine.engines['clip'] = mock_engine
        embedding_engine.engine_initialized['clip'] = True
        
        sample_images = [b'fake image 1', b'fake image 2', b'fake image 3']
        results = await embedding_engine.batch_embed_images(sample_images)
        
        assert results is not None
        assert isinstance(results, list)
        assert len(results) == 3
        assert all(isinstance(result, np.ndarray) for result in results)
    
    @patch('src.common.embedding.embedding_engine.AsyncEngineArray')
    async def test_batch_embed_texts(self, mock_async_engine_array, embedding_engine):
        """测试批量文本向量化"""
        # 模拟AsyncEngineArray
        mock_engine = MagicMock()
        mock_engine.astart.return_value = None
        mock_engine.embed.return_value = ([np.random.rand(512).tolist()], None)
        
        mock_async_engine_array.from_args.return_value = mock_engine
        
        # 手动初始化模型
        embedding_engine.engines['clip'] = mock_engine
        embedding_engine.engine_initialized['clip'] = True
        
        sample_texts = ["test 1", "test 2", "test 3"]
        results = await embedding_engine.batch_embed_texts(sample_texts, modality="visual")
        
        assert results is not None
        assert isinstance(results, list)
        assert len(results) == 3
        assert all(isinstance(result, np.ndarray) for result in results)
    
    async def test_safe_embed(self, embedding_engine):
        """测试安全嵌入方法"""
        # 测试模型未初始化时的处理
        async def mock_embed():
            raise RuntimeError("模型未初始化")
        
        result = await embedding_engine._safe_embed('clip', mock_embed)
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (512,)
        assert np.all(result == 0)
    
    @patch('src.common.embedding.embedding_engine.AsyncEngineArray')
    async def test_embed_text(self, mock_async_engine_array, embedding_engine):
        """测试通用文本向量化"""
        # 模拟AsyncEngineArray
        mock_engine = MagicMock()
        mock_engine.astart.return_value = None
        mock_engine.embed.return_value = ([np.random.rand(512).tolist()], None)
        
        mock_async_engine_array.from_args.return_value = mock_engine
        
        # 手动初始化模型
        embedding_engine.engines['clip'] = mock_engine
        embedding_engine.engines['clap'] = mock_engine
        embedding_engine.engine_initialized['clip'] = True
        embedding_engine.engine_initialized['clap'] = True
        
        # 测试视觉模态
        result_visual = await embedding_engine.embed_text("test", modality="visual")
        assert result_visual is not None
        
        # 测试音乐模态
        result_music = await embedding_engine.embed_text("test", modality="music")
        assert result_music is not None
        
        # 测试无效模态
        with pytest.raises(ValueError):
            await embedding_engine.embed_text("test", modality="invalid")
    
    async def test_embed_face(self, embedding_engine, sample_image_data):
        """测试人脸向量化"""
        # 人脸向量化默认使用图像向量化
        with patch.object(embedding_engine, 'embed_image') as mock_embed_image:
            mock_embed_image.return_value = np.random.rand(512)
            
            result = await embedding_engine.embed_face(sample_image_data)
            
            assert result is not None
            assert isinstance(result, np.ndarray)
            assert result.shape == (512,)
    
    @patch('src.common.embedding.embedding_engine.MilvusAdapter')
    async def test_search_vector(self, mock_milvus_adapter, embedding_engine):
        """测试向量搜索"""
        # 模拟MilvusAdapter
        mock_milvus = MagicMock()
        mock_milvus.search_vectors.return_value = []
        
        embedding_engine.milvus_adapter = mock_milvus
        
        query_vector = np.random.rand(512)
        result = await embedding_engine.search_vector('visual', query_vector)
        
        assert result is not None
        assert isinstance(result, list)
    
    @patch('src.common.embedding.embedding_engine.MilvusAdapter')
    async def test_store_vector(self, mock_milvus_adapter, embedding_engine):
        """测试向量存储"""
        # 模拟MilvusAdapter
        mock_milvus = MagicMock()
        mock_milvus.store_vector.return_value = "vector_id_123"
        
        embedding_engine.milvus_adapter = mock_milvus
        
        vector_data = np.random.rand(512)
        result = await embedding_engine.store_vector('visual', vector_data, 'file_id_123')
        
        assert result is not None
        assert isinstance(result, str)
        assert result == "vector_id_123"
    
    async def test_health_check(self, embedding_engine):
        """测试健康检查"""
        result = await embedding_engine.health_check()
        
        assert result is not None
        assert isinstance(result, dict)
    
    async def test_model_initialization_error(self, embedding_engine):
        """测试模型初始化错误处理"""
        # 测试模型未初始化时的向量化
        result = await embedding_engine.embed_image(b'fake image')
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert np.all(result == 0)
    
    @patch('src.common.embedding.embedding_engine.torch.cuda.is_available')
    def test_check_cuda_availability(self, mock_cuda_available, embedding_engine):
        """测试CUDA可用性检查"""
        mock_cuda_available.return_value = True
        assert embedding_engine._check_cuda_availability() == True
        
        mock_cuda_available.return_value = False
        assert embedding_engine._check_cuda_availability() == False
    
    def test_check_model_path(self, embedding_engine):
        """测试模型路径检查"""
        # 测试不存在的路径
        assert not embedding_engine._check_model_path("/non/existent/path")
        
        # 测试存在的路径
        with tempfile.TemporaryDirectory() as tmpdir:
            assert embedding_engine._check_model_path(tmpdir)
    
    def test_get_model_info(self, embedding_engine):
        """测试获取模型信息"""
        # 测试不存在的模型
        info = embedding_engine.get_model_info("non_existent_model")
        assert info is not None
        assert info["status"] == "unavailable"
        
        # 测试存在的模型（但未初始化）
        embedding_engine.engines["clip"] = MagicMock()
        info = embedding_engine.get_model_info("clip")
        assert info is not None
        assert info["name"] == "clip"
    
    async def test_milvus_health_check(self, embedding_engine):
        """测试Milvus健康检查"""
        # 模拟MilvusAdapter
        with patch.object(embedding_engine.milvus_adapter, 'health_check') as mock_health_check:
            mock_health_check.return_value = {"status": "healthy"}
            
            result = await embedding_engine.milvus_health_check()
            
            assert result is not None
            assert result["status"] == "healthy"