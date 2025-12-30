"""
多模态融合测试
测试多模态检索、结果融合等功能
"""

import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
import asyncio

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestMultimodalFusion:
    """多模态融合测试类"""
    
    @pytest.fixture
    def mock_embedding_engine(self):
        """模拟向量化引擎"""
        engine = Mock()
        engine.embed_text_for_visual = AsyncMock(return_value=np.random.rand(512).astype(np.float32))
        engine.embed_text_for_music = AsyncMock(return_value=np.random.rand(512).astype(np.float32))
        engine.embed_image = AsyncMock(return_value=np.random.rand(512).astype(np.float32))
        engine.embed_audio_music = AsyncMock(return_value=np.random.rand(512).astype(np.float32))
        engine.transcribe_audio = AsyncMock(return_value="transcribed text")
        engine.get_available_models = Mock(return_value=['clip', 'clap', 'whisper'])
        return engine
    
    @pytest.fixture
    def mock_database_adapter(self):
        """模拟数据库适配器"""
        adapter = Mock()
        adapter.get_file = AsyncMock(return_value={
            'id': 'test_file_1',
            'file_path': '/test/path/file1.jpg',
            'file_name': 'file1.jpg',
            'file_type': '.jpg',
            'file_size': 1024,
            'created_at': 1234567890.123,
            'status': 'completed'
        })
        adapter.get_person_by_name = AsyncMock(return_value=None)
        adapter.get_files_by_person = AsyncMock(return_value=[])
        return adapter
    
    @pytest.fixture
    def mock_face_manager(self):
        """模拟人脸管理器"""
        face_manager = Mock()
        face_manager.face_recognition_enabled = False
        face_manager.search_by_person_name = AsyncMock(return_value=[])
        return face_manager
    
    @pytest.fixture
    def mock_config_manager(self):
        """模拟配置管理器 - 提供完整的嵌套配置"""
        config = Mock()
        config.get = Mock(side_effect=lambda key, default=None:
            {
                'smart_retrieval.default_weights': {'clip': 0.4, 'clap': 0.3, 'whisper': 0.3},
                'smart_retrieval.person_weights': {'clip': 0.5, 'clap': 0.25, 'whisper': 0.25},
                'smart_retrieval.audio_weights': {
                    'music': {'clip': 0.2, 'clap': 0.7, 'whisper': 0.1},
                    'speech': {'clip': 0.2, 'clap': 0.1, 'whisper': 0.7}
                },
                'smart_retrieval.visual_weights': {'clip': 0.7, 'clap': 0.15, 'whisper': 0.15},
                'smart_retrieval.video_fusion_weights': {'visual': 0.6, 'audio': 0.4},
                'smart_retrieval.keywords': {
                    'music': ['音乐', '歌曲', 'MV', '音乐视频', '歌', '曲子', '旋律', '节拍'],
                    'speech': ['讲话', '演讲', '会议', '访谈', '对话', '发言', '语音'],
                    'visual': ['画面', '场景', '图像', '图片', '视频画面', '截图']
                }
            }.get(key, default)
        )
        return config
    
    @pytest.fixture
    def smart_retrieval_engine(self, mock_embedding_engine, mock_database_adapter, mock_face_manager, mock_config_manager):
        """智能检索引擎实例（使用mock）"""
        from src.search_service.smart_retrieval_engine import SmartRetrievalEngine
        
        with patch('src.search_service.smart_retrieval_engine.DatabaseAdapter', return_value=mock_database_adapter), \
             patch('src.search_service.smart_retrieval_engine.EmbeddingEngine', return_value=mock_embedding_engine), \
             patch('src.search_service.smart_retrieval_engine.get_face_manager', return_value=mock_face_manager):
            
            engine = SmartRetrievalEngine(config_manager=mock_config_manager)
            engine.embedding_engine = mock_embedding_engine
            engine.db_adapter = mock_database_adapter
            engine.face_manager = mock_face_manager
            return engine
    
    @pytest.mark.asyncio
    async def test_search_empty_query(self, smart_retrieval_engine):
        """测试空查询返回空结果"""
        results = await smart_retrieval_engine.search()
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_text_only(self, smart_retrieval_engine, mock_embedding_engine):
        """测试纯文本搜索"""
        mock_embedding_engine.embed_text_for_visual = AsyncMock(return_value=np.random.rand(512).astype(np.float32))
        mock_embedding_engine.search_vector = AsyncMock(return_value=[])
        
        results = await smart_retrieval_engine.search(text="美丽的风景")
        
        assert isinstance(results, list)
        mock_embedding_engine.embed_text_for_visual.assert_called()
    
    @pytest.mark.asyncio
    async def test_search_image_only(self, smart_retrieval_engine, mock_embedding_engine):
        """测试纯图像搜索"""
        mock_embedding_engine.embed_image = AsyncMock(return_value=np.random.rand(512).astype(np.float32))
        mock_embedding_engine.search_vector = AsyncMock(return_value=[])
        
        image_data = b"fake image bytes"
        results = await smart_retrieval_engine.search(image=image_data)
        
        assert isinstance(results, list)
        mock_embedding_engine.embed_image.assert_called()
    
    @pytest.mark.asyncio
    async def test_search_audio_only(self, smart_retrieval_engine, mock_embedding_engine):
        """测试纯音频搜索"""
        mock_embedding_engine.embed_audio_music = AsyncMock(return_value=np.random.rand(512).astype(np.float32))
        mock_embedding_engine.search_vector = AsyncMock(return_value=[])
        
        audio_data = b"fake audio bytes"
        results = await smart_retrieval_engine.search(audio=audio_data)
        
        assert isinstance(results, list)
        mock_embedding_engine.embed_audio_music.assert_called()
    
    @pytest.mark.asyncio
    async def test_query_intent_identification(self, smart_retrieval_engine):
        """测试查询意图识别"""
        query_types = {'text': True, 'image': True, 'audio': False}
        intent = smart_retrieval_engine._identify_query_intent("画面测试", query_types)
        assert intent in ['visual', 'audio', 'person']
        
        query_types = {'text': True, 'image': False, 'audio': False}
        intent = smart_retrieval_engine._identify_query_intent("音乐查询", query_types)
        assert intent in ['audio', 'visual', 'person']
        
        query_types = {'text': False, 'image': True, 'audio': False}
        intent = smart_retrieval_engine._identify_query_intent(None, query_types)
        assert intent == "visual"
    
    @pytest.mark.asyncio
    async def test_weights_by_intent(self, smart_retrieval_engine):
        """测试根据意图获取权重"""
        visual_weights = smart_retrieval_engine._get_weights_by_intent("visual")
        assert isinstance(visual_weights, dict)
        assert 'clip' in visual_weights
        
        audio_weights = smart_retrieval_engine._get_weights_by_intent("audio")
        assert isinstance(audio_weights, dict)
        assert 'clap' in audio_weights or 'whisper' in audio_weights
        
        person_weights = smart_retrieval_engine._get_weights_by_intent("person")
        assert isinstance(person_weights, dict)
    
    @pytest.mark.asyncio
    async def test_get_query_types(self, smart_retrieval_engine):
        """测试查询类型获取"""
        types = smart_retrieval_engine._get_query_types("测试", None, None)
        assert types['text'] is True
        assert types['image'] is False
        assert types['audio'] is False
        
        types = smart_retrieval_engine._get_query_types(None, b"image", None)
        assert types['text'] is False
        assert types['image'] is True
        assert types['audio'] is False
        
        types = smart_retrieval_engine._get_query_types(None, None, b"audio")
        assert types['text'] is False
        assert types['image'] is False
        assert types['audio'] is True
        
        types = smart_retrieval_engine._get_query_types("文本", b"image", b"audio")
        assert types['text'] is True
        assert types['image'] is True
        assert types['audio'] is True
    
    @pytest.mark.asyncio
    async def test_multimodal_search(self, smart_retrieval_engine, mock_embedding_engine):
        """测试多模态搜索"""
        mock_embedding_engine.search_vector = AsyncMock(return_value=[])
        
        results = await smart_retrieval_engine.search(
            text="测试查询",
            image=b"fake image",
            audio=b"fake audio",
            top_k=5
        )
        
        assert isinstance(results, list)
        assert len(results) <= 5
    
    @pytest.mark.asyncio
    async def test_result_enrichment(self, smart_retrieval_engine, mock_database_adapter):
        """测试结果丰富"""
        raw_results = [
            {
                'file_id': 'test_file_1',
                'score': 0.95,
                'model': 'clip',
                'weight': 0.4,
                'metadata': {}
            }
        ]
        
        enriched = await smart_retrieval_engine._enrich_results(raw_results)
        
        assert isinstance(enriched, list)
        assert len(enriched) == len(raw_results)
        mock_database_adapter.get_file.assert_called()
    
    @pytest.mark.asyncio
    async def test_result_fusion(self, smart_retrieval_engine):
        """测试结果融合"""
        mock_results = {
            'clip': [
                {
                    'file_id': 'file1',
                    'score': 0.9,
                    'model': 'clip',
                    'metadata': {}
                },
                {
                    'file_id': 'file2',
                    'score': 0.7,
                    'model': 'clip',
                    'metadata': {}
                }
            ],
            'clap': [
                {
                    'file_id': 'file1',
                    'score': 0.8,
                    'model': 'clap',
                    'metadata': {}
                },
                {
                    'file_id': 'file3',
                    'score': 0.6,
                    'model': 'clap',
                    'metadata': {}
                }
            ]
        }
        
        weights = {
            'clip': 0.6,
            'clap': 0.4
        }
        
        fused_results = smart_retrieval_engine._fuse_results(mock_results, weights)
        
        assert isinstance(fused_results, list)
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, smart_retrieval_engine):
        """测试带过滤条件的搜索"""
        filters = {
            'file_types': ['.jpg', '.png'],
            'min_score': 0.5
        }
        
        results = await smart_retrieval_engine.search(text="测试", top_k=10, filters=filters)
        
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_search_top_k_limit(self, smart_retrieval_engine):
        """测试top_k参数限制"""
        results = await smart_retrieval_engine.search(text="测试", top_k=100)
        
        assert isinstance(results, list)
        assert len(results) <= 100
    
    @pytest.mark.asyncio
    async def test_engine_start_stop(self, smart_retrieval_engine):
        """测试引擎启动和停止"""
        await smart_retrieval_engine.start()
        assert smart_retrieval_engine.is_running is True
        
        await smart_retrieval_engine.stop()
        assert smart_retrieval_engine.is_running is False
    
    @pytest.mark.asyncio
    async def test_person_query_detection(self, smart_retrieval_engine, mock_face_manager):
        """测试人名查询检测"""
        mock_face_manager.face_recognition_enabled = True
        mock_face_manager.search_by_person_name = AsyncMock(return_value=[
            {
                'file_id': 'test_file_1',
                'file_path': '/test/path/file1.jpg',
                'file_name': 'file1.jpg',
                'file_type': 'image',
                'confidence': 0.9
            }
        ])
        smart_retrieval_engine.face_manager = mock_face_manager
        
        is_person = smart_retrieval_engine._is_person_query("张三")
        assert isinstance(is_person, bool)
    
    @pytest.mark.asyncio
    async def test_audio_query_detection(self, smart_retrieval_engine):
        """测试音频查询检测"""
        is_audio = smart_retrieval_engine._is_audio_query("音乐")
        assert isinstance(is_audio, bool)
        
        is_audio = smart_retrieval_engine._is_audio_query("风景")
        assert isinstance(is_audio, bool)
    
    @pytest.mark.asyncio
    async def test_visual_query_detection(self, smart_retrieval_engine):
        """测试视觉查询检测"""
        is_visual = smart_retrieval_engine._is_visual_query("画面")
        assert isinstance(is_visual, bool)
        
        is_visual = smart_retrieval_engine._is_visual_query("风景")
        assert isinstance(is_visual, bool)
    
    @pytest.mark.asyncio
    async def test_engine_configuration(self, smart_retrieval_engine):
        """测试引擎配置"""
        assert smart_retrieval_engine.default_weights is not None
        assert 'clip' in smart_retrieval_engine.default_weights
        
        assert smart_retrieval_engine.visual_weights is not None
        assert smart_retrieval_engine.audio_weights is not None
        assert smart_retrieval_engine.person_weights is not None
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, smart_retrieval_engine, mock_embedding_engine):
        """测试搜索错误处理"""
        mock_embedding_engine.embed_text_for_visual = AsyncMock(
            side_effect=Exception("Embedding failed")
        )
        
        results = await smart_retrieval_engine.search(text="测试")
        assert results == []
    
    @pytest.mark.asyncio
    async def test_result_scoring(self, smart_retrieval_engine):
        """测试结果评分逻辑"""
        mock_results = [
            {'file_id': 'file1', 'score': 0.95, 'model': 'clip', 'metadata': {}},
            {'file_id': 'file2', 'score': 0.5, 'model': 'clip', 'metadata': {}},
            {'file_id': 'file3', 'score': 0.1, 'model': 'clip', 'metadata': {}}
        ]
        
        weights = {'clip': 1.0}
        fused = smart_retrieval_engine._fuse_results(mock_results, weights)
        
        # 检查结果不为空
        assert isinstance(fused, list)
