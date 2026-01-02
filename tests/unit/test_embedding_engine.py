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
    
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio
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
        
        # 准备测试数据
        image_data_list = [b'image1', b'image2', b'image3']
        
        result = await embedding_engine.batch_embed_images(image_data_list)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == len(image_data_list)
        assert all(isinstance(item, np.ndarray) for item in result)
        assert all(item.shape == (512,) for item in result)
    
    @pytest.mark.asyncio
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
        
        # 准备测试数据
        texts = ["text1", "text2", "text3"]
        
        result = await embedding_engine.batch_embed_texts(texts, model_type="clip")
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == len(texts)
        assert all(isinstance(item, np.ndarray) for item in result)
        assert all(item.shape == (512,) for item in result)
    
    @pytest.mark.asyncio
    async def test_safe_embed(self, embedding_engine):
        """测试安全向量化（异常处理）"""
        # 测试未初始化模型的情况
        result = await embedding_engine._safe_embed(embedding_engine.embed_image, b'fake image data')
        assert result is None
    
    @pytest.mark.asyncio
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
        embedding_engine.engine_initialized['clip'] = True
        
        # 测试直接调用embed_text方法
        result = await embedding_engine.embed_text("test text")
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (512,)
    
    @pytest.mark.asyncio
    async def test_embed_face(self, embedding_engine, sample_image_data):
        """测试人脸向量化"""
        # 测试未初始化模型的情况
        result = await embedding_engine.embed_face(sample_image_data)
        assert result is None
    
    @pytest.mark.asyncio
    @patch('src.common.embedding.embedding_engine.MilvusAdapter')
    async def test_search_vector(self, mock_milvus_adapter, embedding_engine):
        """测试向量搜索"""
        # 模拟MilvusAdapter
        mock_adapter = MagicMock()
        mock_adapter.search.return_value = [
            ("file1.jpg", 0.9),
            ("file2.jpg", 0.8),
            ("file3.jpg", 0.7)
        ]
        
        mock_milvus_adapter.return_value = mock_adapter
        
        # 手动初始化
        embedding_engine.milvus_adapter = mock_adapter
        
        # 测试搜索
        result = await embedding_engine.search_vector(np.random.rand(512), top_k=3)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 3
    
    @pytest.mark.asyncio
    @patch('src.common.embedding.embedding_engine.MilvusAdapter')
    async def test_store_vector(self, mock_milvus_adapter, embedding_engine):
        """测试向量存储"""
        # 模拟MilvusAdapter
        mock_adapter = MagicMock()
        mock_adapter.insert.return_value = True
        
        mock_milvus_adapter.return_value = mock_adapter
        
        # 手动初始化
        embedding_engine.milvus_adapter = mock_adapter
        
        # 测试存储
        result = await embedding_engine.store_vector(
            vector=np.random.rand(512),
            file_uuid="test-uuid",
            file_path="test.jpg",
            timestamp=1234567890.0
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check(self, embedding_engine):
        """测试健康检查"""
        # 测试健康检查
        result = await embedding_engine.health_check()
        
        assert isinstance(result, dict)
        assert "status" in result
        assert "models" in result
    
    @pytest.mark.asyncio
    async def test_model_initialization_error(self, embedding_engine):
        """测试模型初始化错误处理"""
        # 测试模型初始化错误
        with patch.object(embedding_engine, '_get_model_config') as mock_get_model_config:
            # 模拟返回无效配置
            mock_get_model_config.return_value = {}
            
            result = await embedding_engine._init_model('invalid_model')
            assert result is False
    
    @patch('src.common.embedding.embedding_engine.torch.cuda.is_available')
    def test_check_cuda_availability(self, mock_cuda_available, embedding_engine):
        """测试CUDA可用性检查"""
        # 测试CUDA可用情况
        mock_cuda_available.return_value = True
        result = embedding_engine.check_cuda_availability()
        assert result is True
        
        # 测试CUDA不可用情况
        mock_cuda_available.return_value = False
        result = embedding_engine.check_cuda_availability()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_milvus_health_check(self, embedding_engine):
        """测试Milvus健康检查"""
        # 测试Milvus健康检查
        with patch.object(embedding_engine, '_init_milvus') as mock_init_milvus:
            mock_init_milvus.return_value = False
            result = await embedding_engine._check_milvus_health()
            assert result is False
    
    @pytest.mark.asyncio
    @patch('src.common.embedding.embedding_engine.AsyncEngineArray')
    async def test_load_model(self, mock_async_engine_array, embedding_engine):
        """测试加载模型"""
        # 模拟AsyncEngineArray
        mock_engine = MagicMock()
        mock_engine.astart.return_value = None
        
        mock_async_engine_array.from_args.return_value = mock_engine
        
        # 测试加载模型
        result = await embedding_engine.load_model('clip')
        
        assert result is True
        assert 'clip' in embedding_engine.engines
        assert embedding_engine.engine_initialized['clip'] is True
    
    @pytest.mark.asyncio
    async def test_unload_model(self, embedding_engine):
        """测试卸载模型"""
        # 手动添加一个模型
        embedding_engine.engines['clip'] = MagicMock()
        embedding_engine.engine_initialized['clip'] = True
        
        # 测试卸载模型
        result = await embedding_engine.unload_model('clip')
        
        assert result is True
        assert 'clip' not in embedding_engine.engines
        assert 'clip' not in embedding_engine.engine_initialized
    
    @pytest.mark.asyncio
    @patch('src.common.embedding.embedding_engine.AsyncEngineArray')
    async def test_reload_model(self, mock_async_engine_array, embedding_engine):
        """测试重新加载模型"""
        # 模拟AsyncEngineArray
        mock_engine = MagicMock()
        mock_engine.astart.return_value = None
        
        mock_async_engine_array.from_args.return_value = mock_engine
        
        # 先加载模型
        await embedding_engine.load_model('clip')
        
        # 测试重新加载模型
        result = await embedding_engine.reload_model('clip')
        
        assert result is True
        assert 'clip' in embedding_engine.engines
        assert embedding_engine.engine_initialized['clip'] is True
    
    @pytest.mark.asyncio
    async def test_get_model_status(self, embedding_engine):
        """测试获取模型状态"""
        # 手动添加一个模型
        embedding_engine.engines['clip'] = MagicMock()
        embedding_engine.engine_initialized['clip'] = True
        
        # 测试获取模型状态
        status = await embedding_engine.get_model_status('clip')
        
        assert isinstance(status, dict)
        assert "loaded" in status
        assert status["loaded"] is True
    
    @pytest.mark.asyncio
    async def test_get_all_model_status(self, embedding_engine):
        """测试获取所有模型状态"""
        # 手动添加一个模型
        embedding_engine.engines['clip'] = MagicMock()
        embedding_engine.engine_initialized['clip'] = True
        
        # 测试获取所有模型状态
        status = await embedding_engine.get_all_model_status()
        
        assert isinstance(status, dict)
        assert "clip" in status
        assert "status" in status["clip"]
