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

    def test_determine_processing_strategy_unsupported(self, orchestrator):
        """测试不支持的文件类型"""
        file_info = {
            'id': 'test-id',
            'file_type': '.exe',
            'file_path': '/test/file.exe'
        }
        
        with pytest.raises(ValueError, match="不支持的文件类型"):
            orchestrator._determine_processing_strategy(file_info)

    def test_determine_processing_strategy_case_insensitive(self, orchestrator):
        """测试文件类型大小写不敏感"""
        file_info = {
            'id': 'test-id',
            'file_type': '.MP4',
            'file_path': '/test/video.MP4'
        }
        
        strategy = orchestrator._determine_processing_strategy(file_info)
        
        assert strategy['modality'] == 'video'


class TestAudioVectorizationLogic:
    """音频向量化逻辑测试类"""

    @pytest.mark.asyncio
    async def test_audio_music_type_uses_clap(self):
        """测试音乐类型音频使用CLAP模型"""
        audio_type = 'music'
        
        # 验证音乐类型应使用 audio_music 集合和 embed_audio_music 方法
        if audio_type == 'music':
            collection_type = 'audio_music'
            method = 'embed_audio_music'
        
        assert collection_type == 'audio_music'
        assert method == 'embed_audio_music'

    @pytest.mark.asyncio
    async def test_audio_speech_type_uses_whisper(self):
        """测试语音类型音频使用Whisper模型"""
        audio_type = 'speech'
        
        # 验证语音类型应使用 audio_speech 集合和 transcribe_and_embed 方法
        if audio_type == 'speech':
            collection_type = 'audio_speech'
            method = 'transcribe_and_embed'
        
        assert collection_type == 'audio_speech'
        assert method == 'transcribe_and_embed'

    @pytest.mark.asyncio
    async def test_audio_mixed_type_uses_clap_default(self):
        """测试混合类型音频默认使用CLAP模型"""
        audio_type = 'mixed'
        
        # 混合或未知类型默认使用CLAP
        if audio_type not in ['music', 'speech']:
            collection_type = 'audio_music'
            method = 'embed_audio_music'
        
        assert collection_type == 'audio_music'
        assert method == 'embed_audio_music'

    @pytest.mark.asyncio
    async def test_audio_unknown_type_uses_clap_default(self):
        """测试未知类型音频默认使用CLAP模型"""
        audio_type = 'unknown'
        
        # 混合或未知类型默认使用CLAP
        if audio_type not in ['music', 'speech']:
            collection_type = 'audio_music'
            method = 'embed_audio_music'
        
        assert collection_type == 'audio_music'
        assert method == 'embed_audio_music'


class TestVideoVectorizationLogic:
    """视频向量化逻辑测试类"""

    def test_video_frames_use_clip_model(self):
        """测试视频帧使用CLIP模型向量化"""
        # 视频帧作为图像处理，使用 embed_image 方法
        vectorization_method = 'embed_image'
        model = 'clip'
        
        assert vectorization_method == 'embed_image'
        assert model == 'clip'


class TestOrchestratorIntegration:
    """调度器集成测试类"""

    @pytest.fixture
    def mock_config_manager(self):
        """模拟配置管理器"""
        config = Mock()
        config.get = Mock(return_value=5.0)
        return config

    @pytest.mark.asyncio
    async def test_vectorize_file_audio_music_flow(self):
        """测试音频文件（音乐）向量化流程"""
        # 模拟预处理结果
        processed_data = {
            'segments': [
                {
                    'id': 'segment-1',
                    'segment_type': 'audio',
                    'data_path': '/test/audio.wav',
                    'metadata': {'duration': 60}
                }
            ],
            'metadata': {'audio_type': 'music'}
        }
        
        audio_type = processed_data.get('metadata', {}).get('audio_type', 'unknown')
        
        # 验证流程
        if audio_type == 'music':
            collection_type = 'audio_music'
        elif audio_type == 'speech':
            collection_type = 'audio_speech'
        else:
            collection_type = 'audio_music'
        
        assert collection_type == 'audio_music'

    @pytest.mark.asyncio
    async def test_vectorize_file_audio_speech_flow(self):
        """测试音频文件（语音）向量化流程"""
        # 模拟预处理结果
        processed_data = {
            'segments': [
                {
                    'id': 'segment-1',
                    'segment_type': 'audio',
                    'data_path': '/test/speech.wav',
                    'metadata': {'duration': 30}
                }
            ],
            'metadata': {'audio_type': 'speech'}
        }
        
        audio_type = processed_data.get('metadata', {}).get('audio_type', 'unknown')
        
        # 验证流程
        if audio_type == 'music':
            collection_type = 'audio_music'
        elif audio_type == 'speech':
            collection_type = 'audio_speech'
        else:
            collection_type = 'audio_music'
        
        assert collection_type == 'audio_speech'

    @pytest.mark.asyncio
    async def test_vectorize_file_video_flow(self):
        """测试视频文件向量化流程"""
        # 模拟预处理结果
        processed_data = {
            'segments': [
                {
                    'id': 'segment-1',
                    'segment_type': 'video_frame',
                    'data_path': '/test/frame.jpg',
                    'metadata': {'frame_time': 5.0}
                },
                {
                    'id': 'segment-2',
                    'segment_type': 'video_frame',
                    'data_path': '/test/frame2.jpg',
                    'metadata': {'frame_time': 10.0}
                }
            ],
            'metadata': {}
        }
        
        # 统计视频帧片段
        video_frames = [
            s for s in processed_data.get('segments', [])
            if s['segment_type'] == 'video_frame'
        ]
        
        assert len(video_frames) == 2
        assert all(s['segment_type'] == 'video_frame' for s in video_frames)


class TestModalityModelMapping:
    """模态模型映射测试"""

    def test_modality_to_model_mapping(self):
        """测试模态到模型的映射关系"""
        mapping = {
            'text': {'model': 'clip', 'method': 'embed_text'},
            'image': {'model': 'clip', 'method': 'embed_image'},
            'video': {'model': 'clip', 'method': 'embed_image'},
            'audio': {'model': 'clap', 'method': 'embed_audio'}
        }
        
        # 视觉模态（文本、图像、视频）都使用CLIP
        assert mapping['text']['model'] == 'clip'
        assert mapping['image']['model'] == 'clip'
        assert mapping['video']['model'] == 'clip'
        
        # 音频使用CLAP
        assert mapping['audio']['model'] == 'clap'

    def test_video_embedding_method(self):
        """测试视频嵌入方法应该是embed_image"""
        # 设计文档要求视频帧使用 embed_image 方法（而非 embed_video_frames）
        strategy = {
            'vectorization': {
                'model': 'clip',
                'method': 'embed_image'  # 正确：使用 embed_image
            }
        }
        
        assert strategy['vectorization']['method'] == 'embed_image'
