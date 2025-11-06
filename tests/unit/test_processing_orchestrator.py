"""
ProcessingOrchestrator单元测试
测试处理编排器的核心功能，包括策略路由和流程编排
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import uuid

from src.business.orchestrator import ProcessingOrchestrator
from src.core.config_manager import ConfigManager


class TestProcessingOrchestrator:
    """处理编排器核心功能测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            'processing': {
                'batch_size': 4,
                'max_concurrent_tasks': 2
            },
            'models': {
                'clip': {'device': 'cpu'},
                'clap': {'device': 'cpu'},
                'whisper': {'device': 'cpu'}
            }
        }
    
    @pytest.fixture
    def orchestrator(self, mock_config):
        """处理编排器实例"""
        with patch('src.business.orchestrator.MediaProcessor'), \
             patch('src.business.orchestrator.EmbeddingEngine'), \
             patch('src.business.orchestrator.TaskManager'), \
             patch('src.business.orchestrator.VectorStore'), \
             patch('src.business.orchestrator.get_file_type_detector'):
            orchestrator = ProcessingOrchestrator(mock_config)
            yield orchestrator
    
    def test_init_success(self, mock_config):
        """测试初始化成功"""
        with patch('src.business.orchestrator.MediaProcessor') as mock_media_processor, \
             patch('src.business.orchestrator.EmbeddingEngine') as mock_embedding_engine, \
             patch('src.business.orchestrator.TaskManager') as mock_task_manager, \
             patch('src.business.orchestrator.VectorStore') as mock_vector_store, \
             patch('src.business.orchestrator.get_file_type_detector') as mock_file_type_detector:
            
            orchestrator = ProcessingOrchestrator(mock_config)
            
            # 验证组件被正确初始化
            mock_file_type_detector.assert_called_once_with(mock_config)
            mock_media_processor.assert_called_once_with(mock_config)
            mock_embedding_engine.assert_called_once_with(mock_config)
            mock_task_manager.assert_called_once_with(mock_config)
            mock_vector_store.assert_called_once_with(mock_config)
    
    @pytest.mark.asyncio
    async def test_process_file_success(self, orchestrator):
        """测试成功处理文件"""
        # 设置mock对象
        orchestrator.file_type_detector.detect_file_type = Mock(return_value={'type': 'image'})
        orchestrator.media_processor.preprocess_file = AsyncMock(return_value={'preprocessed': True})
        orchestrator.embedding_engine.embed_content = AsyncMock(return_value=[0.1, 0.2, 0.3])
        orchestrator.vector_store.insert_vector = AsyncMock(return_value='vector_123')
        orchestrator.task_manager.create_task = AsyncMock(return_value='task_123')
        orchestrator.task_manager.update_task_status = AsyncMock()
        
        # 执行测试
        result = await orchestrator.process_file('/test/image.jpg')
        
        # 验证结果
        assert 'file_id' in result
        assert result['status'] == 'completed'
        assert 'processing_time' in result
        
        # 验证调用了正确的处理步骤
        orchestrator.file_type_detector.detect_file_type.assert_called_once_with('/test/image.jpg')
        orchestrator.media_processor.preprocess_file.assert_called_once()
        orchestrator.embedding_engine.embed_content.assert_called_once()
        orchestrator.vector_store.insert_vector.assert_called_once()
        assert orchestrator.task_manager.create_task.call_count == 1
        assert orchestrator.task_manager.update_task_status.call_count == 2  # created and completed
    
    @pytest.mark.asyncio
    async def test_process_file_with_error(self, orchestrator):
        """测试处理文件时发生错误"""
        # 设置mock对象，模拟处理过程中发生错误
        orchestrator.file_type_detector.detect_file_type = Mock(return_value={'type': 'image'})
        orchestrator.media_processor.preprocess_file = AsyncMock(side_effect=Exception("预处理失败"))
        orchestrator.task_manager.create_task = AsyncMock(return_value='task_123')
        orchestrator.task_manager.update_task_status = AsyncMock()
        
        # 执行测试
        result = await orchestrator.process_file('/test/image.jpg')
        
        # 验证结果
        assert 'file_id' in result
        assert result['status'] == 'failed'
        assert 'error' in result
        assert '预处理失败' in result['error']
        
        # 验证调用了任务状态更新
        assert orchestrator.task_manager.update_task_status.call_count == 2  # created and failed
    
    def test_determine_processing_strategy_image(self, orchestrator):
        """测试确定图片处理策略"""
        file_info = {'type': 'image', 'subtype': 'jpg'}
        
        strategy = orchestrator._determine_processing_strategy(file_info)
        
        assert strategy['type'] == 'image'
        assert 'preprocess' in strategy
        assert 'embed' in strategy
        assert strategy['embed'] == 'clip'
    
    def test_determine_processing_strategy_video(self, orchestrator):
        """测试确定视频处理策略"""
        file_info = {'type': 'video', 'subtype': 'mp4'}
        
        strategy = orchestrator._determine_processing_strategy(file_info)
        
        assert strategy['type'] == 'video'
        assert 'preprocess' in strategy
        assert 'embed' in strategy
        assert strategy['embed'] == 'clip'
    
    def test_determine_processing_strategy_audio_music(self, orchestrator):
        """测试确定音乐音频处理策略"""
        file_info = {'type': 'audio', 'subtype': 'mp3'}
        
        # 模拟音频分类器返回音乐类型
        with patch.object(orchestrator.media_processor, 'classify_audio_content', return_value='music'):
            strategy = orchestrator._determine_processing_strategy(file_info)
            
            assert strategy['type'] == 'audio'
            assert strategy['audio_type'] == 'music'
            assert 'preprocess' in strategy
            assert 'embed' in strategy
            assert strategy['embed'] == 'clap'
    
    def test_determine_processing_strategy_audio_speech(self, orchestrator):
        """测试确定语音音频处理策略"""
        file_info = {'type': 'audio', 'subtype': 'wav'}
        
        # 模拟音频分类器返回语音类型
        with patch.object(orchestrator.media_processor, 'classify_audio_content', return_value='speech'):
            strategy = orchestrator._determine_processing_strategy(file_info)
            
            assert strategy['type'] == 'audio'
            assert strategy['audio_type'] == 'speech'
            assert 'preprocess' in strategy
            assert 'embed' in strategy
            assert strategy['embed'] == 'whisper'
    
    @pytest.mark.asyncio
    async def test_execute_processing_pipeline_success(self, orchestrator):
        """测试成功执行处理流水线"""
        # 设置mock对象
        orchestrator.media_processor.preprocess_file = AsyncMock(return_value={'preprocessed': True, 'content': 'test'})
        orchestrator.embedding_engine.embed_content = AsyncMock(return_value=[0.1, 0.2, 0.3])
        orchestrator.vector_store.insert_vector = AsyncMock(return_value='vector_123')
        
        # 定义处理策略
        strategy = {
            'type': 'image',
            'preprocess': True,
            'embed': 'clip'
        }
        
        # 执行测试
        result = await orchestrator._execute_processing_pipeline('/test/image.jpg', strategy)
        
        # 验证结果
        assert result['status'] == 'completed'
        assert 'vectors' in result
        assert len(result['vectors']) > 0
        
        # 验证调用了正确的处理步骤
        orchestrator.media_processor.preprocess_file.assert_called_once_with('/test/image.jpg', 'image')
        orchestrator.embedding_engine.embed_content.assert_called_once()
        orchestrator.vector_store.insert_vector.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_processing_pipeline_with_preprocessing_error(self, orchestrator):
        """测试处理流水线中预处理错误"""
        # 设置mock对象，模拟预处理失败
        orchestrator.media_processor.preprocess_file = AsyncMock(side_effect=Exception("预处理失败"))
        
        # 定义处理策略
        strategy = {
            'type': 'image',
            'preprocess': True,
            'embed': 'clip'
        }
        
        # 执行测试
        result = await orchestrator._execute_processing_pipeline('/test/image.jpg', strategy)
        
        # 验证结果
        assert result['status'] == 'failed'
        assert 'error' in result
        assert '预处理失败' in result['error']
        
        # 验证预处理被调用但后续步骤未被调用
        orchestrator.media_processor.preprocess_file.assert_called_once_with('/test/image.jpg', 'image')
        orchestrator.embedding_engine.embed_content.assert_not_called()
        orchestrator.vector_store.insert_vector.assert_not_called()