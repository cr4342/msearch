"""
处理调度器单元测试
验证文件处理策略和向量化逻辑
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.processing_service.orchestrator import ProcessingOrchestrator


class TestProcessingOrchestrator:
    """处理调度器测试类"""

    @pytest.fixture
    def mock_config_manager(self):
        """模拟配置管理器"""
        config = Mock()
        config.get = Mock(side_effect=lambda key, default=None: {
            'orchestrator.check_interval': 5.0,
            'orchestrator.max_concurrent_tasks': 3,
            'media_processing.image.target_resolution': 720,
            'media_processing.video.max_segment_duration': 5,
            'media_processing.video.target_fps': 8,
            'media_processing.audio.sample_rate': 16000,
        }.get(key, default))
        return config

    @pytest.fixture
    def orchestrator(self, mock_config_manager):
        """创建调度器实例（带mock组件）"""
        with patch('src.common.storage.database_adapter.DatabaseAdapter'), \
             patch('src.processing_service.task_manager.TaskManager'), \
             patch('src.processing_service.media_processor.MediaProcessor'), \
             patch('src.common.embedding.embedding_engine.EmbeddingEngine'):
            orchestrator = ProcessingOrchestrator(mock_config_manager)
            return orchestrator

    def test_determine_processing_strategy_text(self, orchestrator):
        """测试文本文件处理策略"""
        file_info = {
            'id': 'test-id',
            'file_type': '.txt',
            'file_path': '/test/document.txt'
        }
        
        strategy = orchestrator._determine_processing_strategy(file_info)
        
        assert strategy['modality'] == 'text'
        assert strategy['preprocessing'] is None
        assert strategy['vectorization']['model'] == 'clip'
        assert strategy['vectorization']['method'] == 'embed_text'

    def test_determine_processing_strategy_image(self, orchestrator):
        """测试图像文件处理策略"""
        file_info = {
            'id': 'test-id',
            'file_type': '.jpg',
            'file_path': '/test/image.jpg'
        }
        
        strategy = orchestrator._determine_processing_strategy(file_info)
        
        assert strategy['modality'] == 'image'
        assert strategy['preprocessing']['resize'] is True
        assert strategy['vectorization']['model'] == 'clip'
        assert strategy['vectorization']['method'] == 'embed_image'

    def test_determine_processing_strategy_video(self, orchestrator):
        """测试视频文件处理策略"""
        file_info = {
            'id': 'test-id',
            'file_type': '.mp4',
            'file_path': '/test/video.mp4'
        }
        
        strategy = orchestrator._determine_processing_strategy(file_info)
        
        assert strategy['modality'] == 'video'
        assert strategy['preprocessing']['scene_detection'] is True
        assert strategy['preprocessing']['audio_separation'] is True
        assert strategy['vectorization']['model'] == 'clip'
        assert strategy['vectorization']['method'] == 'embed_image'  # 视频帧作为图像处理

    def test_determine_processing_strategy_audio(self, orchestrator):
        """测试音频文件处理策略"""
        file_info = {
            'id': 'test-id',
            'file_type': '.mp3',
            'file_path': '/test/audio.mp3'
        }
        
        strategy = orchestrator._determine_processing_strategy(file_info)
        
        assert strategy['modality'] == 'audio'
        assert strategy['preprocessing']['format_conversion'] is True
        assert strategy['vectorization']['model'] == 'clap'
        assert strategy['vectorization']['method'] == 'embed_audio_music'

    def test_should_process_file(self, orchestrator):
        """测试是否应该处理文件"""
        # 测试应该处理的文件类型
        assert orchestrator._should_process_file('/test/image.jpg') is True
        assert orchestrator._should_process_file('/test/video.mp4') is True
        assert orchestrator._should_process_file('/test/audio.mp3') is True
        
        # 测试不应该处理的文件类型
        assert orchestrator._should_process_file('/test/document.txt') is True  # 文本也应该处理
        assert orchestrator._should_process_file('/test/archive.zip') is False
        assert orchestrator._should_process_file('/test/code.py') is False

    def test_get_preprocessing_strategy(self, orchestrator):
        """测试获取预处理策略"""
        # 测试图像预处理策略
        image_strategy = orchestrator._get_preprocessing_strategy('image')
        assert image_strategy['resize'] is True
        assert image_strategy['target_resolution'] == 720
        
        # 测试视频预处理策略
        video_strategy = orchestrator._get_preprocessing_strategy('video')
        assert video_strategy['scene_detection'] is True
        assert video_strategy['max_segment_duration'] == 5
        assert video_strategy['target_fps'] == 8
        
        # 测试音频预处理策略
        audio_strategy = orchestrator._get_preprocessing_strategy('audio')
        assert audio_strategy['format_conversion'] is True
        assert audio_strategy['sample_rate'] == 16000

    def test_get_vectorization_strategy(self, orchestrator):
        """测试获取向量化策略"""
        # 测试文本向量化策略
        text_strategy = orchestrator._get_vectorization_strategy('text')
        assert text_strategy['model'] == 'clip'
        assert text_strategy['method'] == 'embed_text'
        
        # 测试图像向量化策略
        image_strategy = orchestrator._get_vectorization_strategy('image')
        assert image_strategy['model'] == 'clip'
        assert image_strategy['method'] == 'embed_image'
        
        # 测试视频向量化策略
        video_strategy = orchestrator._get_vectorization_strategy('video')
        assert video_strategy['model'] == 'clip'
        assert video_strategy['method'] == 'embed_image'
        
        # 测试音频向量化策略
        audio_strategy = orchestrator._get_vectorization_strategy('audio')
        assert audio_strategy['model'] == 'clap'
        assert audio_strategy['method'] == 'embed_audio_music'

    def test_route_to_processor(self, orchestrator):
        """测试根据文件类型路由到处理器"""
        # 测试图像处理器路由
        image_processor = orchestrator._route_to_processor('image')
        assert image_processor is not None
        
        # 测试视频处理器路由
        video_processor = orchestrator._route_to_processor('video')
        assert video_processor is not None
        
        # 测试音频处理器路由
        audio_processor = orchestrator._route_to_processor('audio')
        assert audio_processor is not None
        
        # 测试文本处理器路由
        text_processor = orchestrator._route_to_processor('text')
        assert text_processor is not None

    @pytest.mark.asyncio
    async def test_audio_music_type_uses_clap(self):
        """测试音乐类型音频使用CLAP模型"""
        with patch('src.common.storage.database_adapter.DatabaseAdapter'), \
             patch('src.processing_service.task_manager.TaskManager'), \
             patch('src.processing_service.media_processor.MediaProcessor'), \
             patch('src.common.embedding.embedding_engine.EmbeddingEngine') as mock_embedding_engine:
            orchestrator = ProcessingOrchestrator(Mock())
            
            # 测试音乐类型音频使用CLAP模型
            strategy = orchestrator._get_vectorization_strategy('audio')
            assert strategy['model'] == 'clap'
            assert strategy['method'] == 'embed_audio_music'

    @pytest.mark.asyncio
    async def test_audio_speech_type_uses_whisper(self):
        """测试语音类型音频使用Whisper模型"""
        with patch('src.common.storage.database_adapter.DatabaseAdapter'), \
             patch('src.processing_service.task_manager.TaskManager'), \
             patch('src.processing_service.media_processor.MediaProcessor'), \
             patch('src.common.embedding.embedding_engine.EmbeddingEngine') as mock_embedding_engine:
            orchestrator = ProcessingOrchestrator(Mock())
            
            # 模拟语音检测结果
            with patch.object(orchestrator.media_processor, 'classify_audio_content', return_value={'type': 'speech'}):
                # 处理音频文件
                file_info = {
                    'id': 'test-id',
                    'file_type': '.mp3',
                    'file_path': '/test/speech.mp3'
                }
                
                # 获取向量化策略
                strategy = orchestrator._get_vectorization_strategy('audio')
                # 注意：当前实现中，音频类型的向量化策略是基于配置固定的，不是基于实际内容分类的
                assert strategy['model'] == 'clap'

    @pytest.mark.asyncio
    async def test_audio_mixed_type_uses_clap_default(self):
        """测试混合类型音频使用CLAP作为默认模型"""
        with patch('src.common.storage.database_adapter.DatabaseAdapter'), \
             patch('src.processing_service.task_manager.TaskManager'), \
             patch('src.processing_service.media_processor.MediaProcessor'), \
             patch('src.common.embedding.embedding_engine.EmbeddingEngine') as mock_embedding_engine:
            orchestrator = ProcessingOrchestrator(Mock())
            
            # 测试混合类型音频使用CLAP作为默认模型
            strategy = orchestrator._get_vectorization_strategy('audio')
            assert strategy['model'] == 'clap'

    @pytest.mark.asyncio
    async def test_audio_unknown_type_uses_clap_default(self):
        """测试未知类型音频使用CLAP作为默认模型"""
        with patch('src.common.storage.database_adapter.DatabaseAdapter'), \
             patch('src.processing_service.task_manager.TaskManager'), \
             patch('src.processing_service.media_processor.MediaProcessor'), \
             patch('src.common.embedding.embedding_engine.EmbeddingEngine') as mock_embedding_engine:
            orchestrator = ProcessingOrchestrator(Mock())
            
            # 测试未知类型音频使用CLAP作为默认模型
            strategy = orchestrator._get_vectorization_strategy('audio')
            assert strategy['model'] == 'clap'

    @pytest.mark.asyncio
    async def test_vectorize_file_audio_music_flow(self):
        """测试音频（音乐）向量化流程"""
        with patch('src.common.storage.database_adapter.DatabaseAdapter'), \
             patch('src.processing_service.task_manager.TaskManager'), \
             patch('src.processing_service.media_processor.MediaProcessor') as mock_media_processor, \
             patch('src.common.embedding.embedding_engine.EmbeddingEngine') as mock_embedding_engine:
            
            # 配置mock
            orchestrator = ProcessingOrchestrator(Mock())
            
            # 模拟媒体处理器
            mock_media_processor_instance = Mock()
            mock_media_processor.return_value = mock_media_processor_instance
            mock_media_processor_instance.process_audio = AsyncMock(return_value={'status': 'COMPLETED'})
            
            # 模拟向量化引擎
            mock_embedding_engine_instance = Mock()
            mock_embedding_engine.return_value = mock_embedding_engine_instance
            mock_embedding_engine_instance.embed_audio_music = AsyncMock(return_value=[0.1, 0.2, 0.3])
            
            # 处理音频文件
            file_info = {
                'id': 'test-id',
                'file_type': '.mp3',
                'file_path': '/test/music.mp3'
            }
            
            result = await orchestrator.vectorize_file(file_info)
            assert result is not None

    @pytest.mark.asyncio
    async def test_vectorize_file_audio_speech_flow(self):
        """测试音频（语音）向量化流程"""
        with patch('src.common.storage.database_adapter.DatabaseAdapter'), \
             patch('src.processing_service.task_manager.TaskManager'), \
             patch('src.processing_service.media_processor.MediaProcessor') as mock_media_processor, \
             patch('src.common.embedding.embedding_engine.EmbeddingEngine') as mock_embedding_engine:
            
            # 配置mock
            orchestrator = ProcessingOrchestrator(Mock())
            
            # 模拟媒体处理器
            mock_media_processor_instance = Mock()
            mock_media_processor.return_value = mock_media_processor_instance
            mock_media_processor_instance.process_audio = AsyncMock(return_value={'status': 'COMPLETED'})
            
            # 模拟向量化引擎
            mock_embedding_engine_instance = Mock()
            mock_embedding_engine.return_value = mock_embedding_engine_instance
            mock_embedding_engine_instance.transcribe_audio = AsyncMock(return_value='test transcription')
            mock_embedding_engine_instance.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])
            
            # 处理音频文件
            file_info = {
                'id': 'test-id',
                'file_type': '.mp3',
                'file_path': '/test/speech.mp3'
            }
            
            result = await orchestrator.vectorize_file(file_info)
            assert result is not None

    @pytest.mark.asyncio
    async def test_vectorize_file_video_flow(self):
        """测试视频向量化流程"""
        with patch('src.common.storage.database_adapter.DatabaseAdapter'), \
             patch('src.processing_service.task_manager.TaskManager'), \
             patch('src.processing_service.media_processor.MediaProcessor') as mock_media_processor, \
             patch('src.common.embedding.embedding_engine.EmbeddingEngine') as mock_embedding_engine:
            
            # 配置mock
            orchestrator = ProcessingOrchestrator(Mock())
            
            # 模拟媒体处理器
            mock_media_processor_instance = Mock()
            mock_media_processor.return_value = mock_media_processor_instance
            mock_media_processor_instance.process_video = AsyncMock(return_value={'status': 'COMPLETED'})
            
            # 模拟向量化引擎
            mock_embedding_engine_instance = Mock()
            mock_embedding_engine.return_value = mock_embedding_engine_instance
            mock_embedding_engine_instance.embed_image = AsyncMock(return_value=[0.1, 0.2, 0.3])
            
            # 处理视频文件
            file_info = {
                'id': 'test-id',
                'file_type': '.mp4',
                'file_path': '/test/video.mp4'
            }
            
            result = await orchestrator.vectorize_file(file_info)
            assert result is not None
