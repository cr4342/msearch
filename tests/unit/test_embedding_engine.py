"""
EmbeddingEngine单元测试
测试michaelfeil/infinity Python-native模式集成
"""
import pytest
import numpy as np
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import torch

from src.business.embedding_engine import EmbeddingEngine
from src.core.config_manager import ConfigManager


class TestEmbeddingEngine:
    """EmbeddingEngine核心功能测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        config = Mock(spec=ConfigManager)
        config.get.side_effect = lambda key, default=None: {
            'embedding.models_dir': './data/models',
            'embedding.models.clip': 'clip',
            'embedding.models.clap': 'clap', 
            'embedding.models.whisper': 'whisper',
            'processing.batch_size': 16,
            'device': 'cpu'
        }.get(key, default)
        return config
    
    @pytest.fixture
    def mock_infinity_engine(self):
        """模拟infinity引擎"""
        with patch('src.business.embedding_engine.AsyncEngineArray') as mock_engine_array:
            mock_engine = AsyncMock()
            mock_engine_array.from_args.return_value = mock_engine
            yield mock_engine
    
    def test_embedding_engine_initialization(self, mock_config, mock_infinity_engine):
        """测试EmbeddingEngine初始化"""
        engine = EmbeddingEngine(config=mock_config)
        
        # 验证初始化
        assert engine.config == mock_config
        assert engine.engine_array == mock_infinity_engine
        
        # 验证模型路径配置
        mock_config.get.assert_any_call('embedding.models_dir', './data/models')
        mock_config.get.assert_any_call('embedding.models.clip', 'clip')
    
    @pytest.mark.asyncio
    async def test_embed_image(self, mock_config, mock_infinity_engine):
        """测试图片向量化"""
        # 设置mock返回值
        mock_infinity_engine.embed.return_value = [np.random.rand(512).tolist()]
        
        engine = EmbeddingEngine(config=mock_config)
        
        # 测试图片向量化
        test_image_data = np.random.rand(224, 224, 3)
        result = await engine.embed_image(test_image_data)
        
        # 验证结果
        assert len(result) == 1
        assert len(result[0]) == 512
        mock_infinity_engine.embed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_embed_audio(self, mock_config, mock_infinity_engine):
        """测试音频向量化"""
        # 设置mock返回值
        mock_infinity_engine.embed.return_value = [np.random.rand(512).tolist()]
        
        engine = EmbeddingEngine(config=mock_config)
        
        # 测试音频向量化
        test_audio_data = np.random.rand(16000)  # 1秒16kHz音频
        result = await engine.embed_audio(test_audio_data)
        
        # 验证结果
        assert len(result) == 1
        assert len(result[0]) == 512
        mock_infinity_engine.embed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_embed_text(self, mock_config, mock_infinity_engine):
        """测试文本向量化"""
        # 设置mock返回值
        mock_infinity_engine.embed.return_value = [np.random.rand(512).tolist()]
        
        engine = EmbeddingEngine(config=mock_config)
        
        # 测试文本向量化
        test_text = "测试文本内容"
        result = await engine.embed_text(test_text)
        
        # 验证结果
        assert len(result) == 1
        assert len(result[0]) == 512
        mock_infinity_engine.embed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, mock_config, mock_infinity_engine):
        """测试批处理功能"""
        # 设置mock返回值 - 批量处理
        batch_size = 4
        mock_infinity_engine.embed.return_value = [
            np.random.rand(512).tolist() for _ in range(batch_size)
        ]
        
        engine = EmbeddingEngine(config=mock_config)
        
        # 测试批量文本向量化
        test_texts = [f"测试文本 {i}" for i in range(batch_size)]
        result = await engine.embed_text_batch(test_texts)
        
        # 验证结果
        assert len(result) == batch_size
        for vector in result:
            assert len(vector) == 512
        mock_infinity_engine.embed.assert_called_once()
    
    def test_model_routing(self, mock_config, mock_infinity_engine):
        """测试模型路由功能"""
        engine = EmbeddingEngine(config=mock_config)
        
        # 测试内容类型到模型的映射
        assert engine._get_model_for_content_type('image') == 'clip'
        assert engine._get_model_for_content_type('text') == 'clip'
        assert engine._get_model_for_content_type('audio_music') == 'clap'
        assert engine._get_model_for_content_type('audio_speech') == 'whisper'
    
    @pytest.mark.asyncio
    async def test_vector_quality_validation(self, mock_config, mock_infinity_engine):
        """测试向量质量验证"""
        # 设置mock返回值 - 包含无效向量
        mock_infinity_engine.embed.return_value = [
            np.random.rand(512).tolist(),  # 正常向量
            [0] * 512,  # 零向量
            np.random.rand(256).tolist(),  # 错误维度
        ]
        
        engine = EmbeddingEngine(config=mock_config)
        
        # 测试向量质量验证
        test_texts = ["正常文本", "零向量文本", "错误维度文本"]
        result = await engine.embed_text_batch(test_texts)
        
        # 验证只返回有效向量
        valid_vectors = engine._validate_vectors(result)
        assert len(valid_vectors) == 1  # 只有一个有效向量
        assert len(valid_vectors[0]) == 512
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_config, mock_infinity_engine):
        """测试错误处理"""
        # 设置mock抛出异常
        mock_infinity_engine.embed.side_effect = Exception("模型调用失败")
        
        engine = EmbeddingEngine(config=mock_config)
        
        # 测试异常处理
        with pytest.raises(Exception) as exc_info:
            await engine.embed_text("测试文本")
        
        assert "模型调用失败" in str(exc_info.value)


class TestEmbeddingEngineIntegration:
    """EmbeddingEngine集成测试"""
    
    @pytest.fixture
    def integration_config(self):
        """集成测试配置"""
        return {
            'embedding': {
                'models_dir': './data/models',
                'models': {
                    'clip': 'clip',
                    'clap': 'clap',
                    'whisper': 'whisper'
                }
            },
            'processing': {
                'batch_size': 8,
                'max_concurrent_tasks': 2
            },
            'device': 'cpu'
        }
    
    @pytest.mark.asyncio
    async def test_multimodal_processing(self, integration_config):
        """测试多模态处理集成"""
        with patch('src.business.embedding_engine.AsyncEngineArray') as mock_engine_array:
            mock_engine = AsyncMock()
            mock_engine_array.from_args.return_value = mock_engine
            
            # 设置不同模态的mock返回值
            def mock_embed_side_effect(*args, **kwargs):
                model = kwargs.get('model', 'clip')
                if model == 'clip':
                    return [np.random.rand(512).tolist()]
                elif model == 'clap':
                    return [np.random.rand(512).tolist()]
                elif model == 'whisper':
                    return [np.random.rand(512).tolist()]
                else:
                    return [np.random.rand(512).tolist()]
            
            mock_engine.embed.side_effect = mock_embed_side_effect
            
            # 创建配置管理器
            config_manager = Mock(spec=ConfigManager)
            config_manager.get.side_effect = lambda key, default=None: {
                'embedding.models_dir': integration_config['embedding']['models_dir'],
                'embedding.models.clip': integration_config['embedding']['models']['clip'],
                'embedding.models.clap': integration_config['embedding']['models']['clap'],
                'embedding.models.whisper': integration_config['embedding']['models']['whisper'],
                'processing.batch_size': integration_config['processing']['batch_size'],
                'device': integration_config['device']
            }.get(key, default)
            
            engine = EmbeddingEngine(config=config_manager)
            
            # 测试多模态内容处理
            image_result = await engine.embed_content(np.random.rand(224, 224, 3), 'image')
            audio_result = await engine.embed_content(np.random.rand(16000), 'audio_music')
            text_result = await engine.embed_content("测试文本", 'text')
            
            # 验证所有模态都返回512维向量
            assert len(image_result[0]) == 512
            assert len(audio_result[0]) == 512
            assert len(text_result[0]) == 512
    
    @pytest.mark.asyncio
    async def test_python_native_performance(self, integration_config):
        """测试Python-native模式性能"""
        with patch('src.business.embedding_engine.AsyncEngineArray') as mock_engine_array:
            mock_engine = AsyncMock()
            mock_engine_array.from_args.return_value = mock_engine
            
            # 模拟快速响应
            mock_engine.embed.return_value = [np.random.rand(512).tolist()]
            
            config_manager = Mock(spec=ConfigManager)
            config_manager.get.side_effect = lambda key, default=None: {
                'embedding.models_dir': integration_config['embedding']['models_dir'],
                'embedding.models.clip': integration_config['embedding']['models']['clip'],
                'device': integration_config['device']
            }.get(key, default)
            
            engine = EmbeddingEngine(config=config_manager)
            
            # 测试响应时间
            import time
            start_time = time.time()
            
            result = await engine.embed_text("性能测试文本")
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            # Python-native模式应该有更快的响应时间（无HTTP开销）
            assert response_time < 100  # 应该小于100ms
            assert len(result[0]) == 512
    
    @pytest.mark.asyncio
    async def test_memory_management(self, integration_config):
        """测试内存管理"""
        with patch('src.business.embedding_engine.AsyncEngineArray') as mock_engine_array:
            mock_engine = AsyncMock()
            mock_engine_array.from_args.return_value = mock_engine
            
            # 模拟大批量处理
            batch_size = 100
            mock_engine.embed.return_value = [
                np.random.rand(512).tolist() for _ in range(batch_size)
            ]
            
            config_manager = Mock(spec=ConfigManager)
            config_manager.get.side_effect = lambda key, default=None: {
                'embedding.models_dir': integration_config['embedding']['models_dir'],
                'embedding.models.clip': integration_config['embedding']['models']['clip'],
                'processing.batch_size': batch_size,
                'device': integration_config['device']
            }.get(key, default)
            
            engine = EmbeddingEngine(config=config_manager)
            
            # 测试大批量处理
            test_texts = [f"测试文本 {i}" for i in range(batch_size)]
            result = await engine.embed_text_batch(test_texts)
            
            # 验证结果
            assert len(result) == batch_size
            for vector in result:
                assert len(vector) == 512
                assert not np.allclose(vector, 0)  # 确保不是零向量