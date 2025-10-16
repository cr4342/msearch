
"""
ProcessingOrchestrator Unit Tests
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from src.core.processing_orchestrator import ProcessingOrchestrator


class TestProcessingOrchestrator:
    """ProcessingOrchestrator Test Class"""
    
    @pytest.fixture
    def orchestrator(self):
        """Fixture to create ProcessingOrchestrator instance"""
        with patch('src.core.processing_orchestrator.get_config_manager'), \
             patch('src.core.processing_orchestrator.get_db_adapter'), \
             patch('src.core.processing_orchestrator.get_media_processor'), \
             patch('src.core.processing_orchestrator.get_model_manager'), \
             patch('src.core.processing_orchestrator.get_vector_store'):
            orchestrator = ProcessingOrchestrator()
            yield orchestrator
    
    def test_init(self, orchestrator):
        """Test initialization"""
        assert orchestrator is not None
        assert hasattr(orchestrator, 'processing_status')
        assert isinstance(orchestrator.processing_status, dict)
    
    def test_determine_file_type_image(self, orchestrator):
        """Test image file type detection"""
        # Create a temporary file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
            # Mock the file_type_detector to return image type
            with patch('src.core.processing_orchestrator.get_file_type_detector') as mock_get_detector:
                mock_detector = Mock()
                mock_detector.detect_file_type.return_value = {
                    'type': 'image',
                    'subtype': 'jpg',
                    'confidence': 0.9
                }
                mock_get_detector.return_value = mock_detector
                
                file_type = orchestrator._determine_file_type(tmp_file.name)
                assert file_type == 'image'
    
    def test_determine_file_type_video(self, orchestrator):
        """Test video file type detection"""
        # Create a temporary file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.mp4') as tmp_file:
            # Mock the file_type_detector to return video type
            with patch('src.core.processing_orchestrator.get_file_type_detector') as mock_get_detector:
                mock_detector = Mock()
                mock_detector.detect_file_type.return_value = {
                    'type': 'video',
                    'subtype': 'mp4',
                    'confidence': 0.9
                }
                mock_get_detector.return_value = mock_detector
                
                file_type = orchestrator._determine_file_type(tmp_file.name)
                assert file_type == 'video'
    
    def test_determine_file_type_audio(self, orchestrator):
        """Test audio file type detection"""
        # Create a temporary file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.mp3') as tmp_file:
            # Mock the file_type_detector to return audio type
            with patch('src.core.processing_orchestrator.get_file_type_detector') as mock_get_detector:
                mock_detector = Mock()
                mock_detector.detect_file_type.return_value = {
                    'type': 'audio',
                    'subtype': 'mp3',
                    'confidence': 0.9
                }
                mock_get_detector.return_value = mock_detector
                
                file_type = orchestrator._determine_file_type(tmp_file.name)
                assert file_type == 'audio'
    
    def test_determine_file_type_unknown(self, orchestrator):
        """Test unknown file type detection"""
        # Create a temporary file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp_file:
            # Mock the file_type_detector to return unknown type
            with patch('src.core.processing_orchestrator.get_file_type_detector') as mock_get_detector:
                mock_detector = Mock()
                mock_detector.detect_file_type.return_value = {
                    'type': 'unknown',
                    'subtype': 'unknown',
                    'confidence': 0.1
                }
                mock_get_detector.return_value = mock_detector
                
                # Also mock config_manager.get for fallback detection
                with patch.object(orchestrator.config_manager, 'get', 
                                 return_value={
                                     '.jpg': 'image',
                                     '.png': 'image',
                                     '.mp4': 'video',
                                     '.mp3': 'audio'
                                 }):
                    file_type = orchestrator._determine_file_type(tmp_file.name)
                    assert file_type == 'unknown'
    
    def test_select_processing_strategy(self, orchestrator):
        """Test processing strategy selection"""
        # Test image processing strategy
        strategy = orchestrator._select_processing_strategy('image')
        assert strategy == 'image_processing'
        
        # Test video processing strategy
        strategy = orchestrator._select_processing_strategy('video')
        assert strategy == 'video_processing'
        
        # Test audio processing strategy
        strategy = orchestrator._select_processing_strategy('audio')
        assert strategy == 'audio_processing'
        
        # Test unknown type strategy
        strategy = orchestrator._select_processing_strategy('unknown')
        assert strategy == 'default_processing'
    
    def test_get_processing_status(self, orchestrator):
        """Test getting processing status"""
        # Test non-existent file status
        status = orchestrator.get_processing_status('nonexistent')
        assert status['status'] == 'unknown'
        assert status['progress'] == 0
        assert status['error'] is None
        
        # Test existing file status
        orchestrator.processing_status['test_file'] = {
            'status': 'processing',
            'progress': 50,
            'error': None
        }
        status = orchestrator.get_processing_status('test_file')
        assert status['status'] == 'processing'
        assert status['progress'] == 50
        assert status['error'] is None
    
    @pytest.mark.asyncio
    async def test_preprocess_file_image(self, orchestrator):
        """Test image file preprocessing"""
        # Create mock preprocessing result
        mock_result = {
            'status': 'success',
            'original_path': '/path/to/image.jpg',
            'processed_path': '/path/to/processed_image.jpg',
            'width': 1920,
            'height': 1080,
            'media_type': 'image'
        }
        
        # Mock media_processor.process_image method
        orchestrator.media_processor.process_image = AsyncMock(return_value=mock_result)
        
        result = await orchestrator._preprocess_file('/path/to/image.jpg', 'image')
        assert result == mock_result
        orchestrator.media_processor.process_image.assert_called_once_with('/path/to/image.jpg')
    
    @pytest.mark.asyncio
    async def test_preprocess_file_video(self, orchestrator):
        """Test video file preprocessing"""
        # Create mock preprocessing result
        mock_result = {
            'status': 'success',
            'original_path': '/path/to/video.mp4',
            'processed_path': '/path/to/processed_video.mp4',
            'duration': 120.5,
            'chunks': [],
            'chunks_created': 0,
            'keyframes': []
        }
        
        # Mock media_processor.process_video method
        orchestrator.media_processor.process_video = AsyncMock(return_value=mock_result)
        
        result = await orchestrator._preprocess_file('/path/to/video.mp4', 'video')
        assert result == mock_result
        orchestrator.media_processor.process_video.assert_called_once_with('/path/to/video.mp4')
    
    @pytest.mark.asyncio
    async def test_preprocess_file_audio(self, orchestrator):
        """Test audio file preprocessing"""
        # Create mock preprocessing result
        mock_result = {
            'status': 'success',
            'original_path': '/path/to/audio.mp3',
            'processed_path': '/path/to/processed_audio.wav',
            'duration': 180.2,
            'segments': [],
            'media_type': 'audio'
        }
        
        # Mock media_processor.process_audio method
        orchestrator.media_processor.process_audio = AsyncMock(return_value=mock_result)
        
        result = await orchestrator._preprocess_file('/path/to/audio.mp3', 'audio')
        assert result == mock_result
        orchestrator.media_processor.process_audio.assert_called_once_with('/path/to/audio.mp3')
    
    def test_get_collection_name(self, orchestrator):
        """Test getting collection name"""
        # Test image type
        collection = orchestrator._get_collection_name('image')
        assert collection == 'visual_vectors'
        
        # Test visual type
        collection = orchestrator._get_collection_name('visual')
        assert collection == 'visual_vectors'
        
        # Test keyframe type
        collection = orchestrator._get_collection_name('keyframe')
        assert collection == 'visual_vectors'
        
        # Test audio music type
        collection = orchestrator._get_collection_name('audio_music')
        assert collection == 'audio_music_vectors'
        
        # Test audio speech type
        collection = orchestrator._get_collection_name('audio_speech')
        assert collection == 'audio_speech_vectors'
        
        # Test unknown type
        collection = orchestrator._get_collection_name('unknown')
        assert collection is None
    
    @pytest.mark.asyncio
    async def test_vectorize_content_image(self, orchestrator):
        """Test image content vectorization"""
        # Create mock preprocessing data
        preprocessed_data = {
            'processed_path': '/path/to/processed_image.jpg',
            'original_path': '/path/to/image.jpg'
        }
        
        # Create mock vector result
        mock_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Mock model_manager.embed_image method
        orchestrator.model_manager.embed_image = AsyncMock(return_value=mock_vector)
        
        result = await orchestrator._vectorize_content(preprocessed_data, 'image', 'test_file_id')
        
        assert result['file_type'] == 'image'
        assert len(result['segments']) == 1
        assert result['segments'][0]['type'] == 'image'
        assert result['segments'][0]['vector'] == mock_vector
        assert result['segments'][0]['timestamp'] == 0
        
        orchestrator.model_manager.embed_image.assert_called_once_with('/path/to/processed_image.jpg')
    
    @pytest.mark.asyncio
    async def test_vectorize_content_video(self, orchestrator):
        """Test video content vectorization"""
        # Create mock preprocessing data
        preprocessed_data = {
            'chunks': [
                {
                    'index': 0,
                    'start_time': 0,
                    'end_time': 30,
                    'output_path': '/path/to/chunk_0.mp4'
                }
            ],
            'keyframes': ['/path/to/keyframe_0.jpg']
        }
        
        # Create mock vector results
        mock_visual_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_keyframe_vector = [0.2, 0.3, 0.4, 0.5, 0.6]
        
        # Mock model_manager.embed_image method
        orchestrator.model_manager.embed_image = AsyncMock()
        orchestrator.model_manager.embed_image.side_effect = [
            mock_visual_vector,  # Video chunk vector
            mock_keyframe_vector  # Keyframe vector
        ]
        
        with patch('pathlib.Path.exists', return_value=True):
            # Also patch the _index_video_faces method to avoid issues with face recognition
            with patch.object(orchestrator, '_index_video_faces'):
                result = await orchestrator._vectorize_content(preprocessed_data, 'video', 'test_file_id')
        
        assert result['file_type'] == 'video'
        assert len(result['segments']) == 2  # 1 video chunk + 1 keyframe
        
        # Verify video chunk vector
        visual_segment = result['segments'][0]
        assert visual_segment['type'] == 'visual'
        assert visual_segment['vector'] == mock_visual_vector
        assert visual_segment['timestamp'] == 0
        assert visual_segment['end_time'] == 30
        assert visual_segment['chunk_index'] == 0
        
        # Verify keyframe vector
        keyframe_segment = result['segments'][1]
        assert keyframe_segment['type'] == 'keyframe'
        assert keyframe_segment['vector'] == mock_keyframe_vector
        assert keyframe_segment['timestamp'] == 0
        assert keyframe_segment['keyframe_index'] == 0
    
    @pytest.mark.asyncio
    async def test_vectorize_content_audio(self, orchestrator):
        """Test audio content vectorization"""
        # Create mock preprocessing data
        preprocessed_data = {
            'processed_path': '/path/to/processed_audio.wav',
            'original_path': '/path/to/audio.mp3'
        }
        
        # Create mock audio processing results
        mock_audio_results = [
            {
                'segment_type': 'audio_music',
                'vector': [0.1, 0.2, 0.3, 0.4, 0.5],
                'start_time': 0,
                'end_time': 30,
                'transcribed_text': '',
                'quality_score': 0.9
            },
            {
                'segment_type': 'audio_speech',
                'vector': [0.2, 0.3, 0.4, 0.5, 0.6],
                'start_time': 30,
                'end_time': 60,
                'transcribed_text': 'Test speech content',
                'quality_score': 0.85
            }
        ]
        
        # Mock model_manager.process_video_audio_intelligently method
        orchestrator.model_manager.process_video_audio_intelligently = AsyncMock(
            return_value=mock_audio_results
        )
        
        with patch('pathlib.Path.exists', return_value=True):
            result = await orchestrator._vectorize_content(preprocessed_data, 'audio', 'test_file_id')
        
        assert result['file_type'] == 'audio'
        assert len(result['segments']) == 2
        
        # Verify music segment vector
        music_segment = result['segments'][0]
        assert music_segment['type'] == 'audio_music'
        assert music_segment['vector'] == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert music_segment['timestamp'] == 0
        assert music_segment['end_time'] == 30
        assert music_segment['quality_score'] == 0.9
        
        # Verify speech segment vector
        speech_segment = result['segments'][1]
        assert speech_segment['type'] == 'audio_speech'
        assert speech_segment['vector'] == [0.2, 0.3, 0.4, 0.5, 0.6]
        assert speech_segment['timestamp'] == 30
        assert speech_segment['end_time'] == 60
        assert speech_segment['transcribed_text'] == 'Test speech content'
        assert speech_segment['quality_score'] == 0.85
    
    @pytest.mark.asyncio
    async def test_store_vectors_success(self, orchestrator):
        """Test vector storage success"""
        # Create mock vector data
        vector_data = {
            'file_type': 'image',
            'segments': [
                {
                    'type': 'image',
                    'vector': [0.1, 0.2, 0.3, 0.4, 0.5],
                    'timestamp': 0
                }
            ]
        }
        
        # Mock vector_store.store_vectors method
        orchestrator.vector_store.store_vectors = AsyncMock(return_value=True)
        
        result = await orchestrator._store_vectors(vector_data, 'test_file_1')
        
        assert result is True
        orchestrator.vector_store.store_vectors.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_vectors_failure(self, orchestrator):
        """Test vector storage failure"""
        # Create mock vector data
        vector_data = {
            'file_type': 'image',
            'segments': [
                {
                    'type': 'image',
                    'vector': [0.1, 0.2, 0.3, 0.4, 0.5],
                    'timestamp': 0
                }
            ]
        }
        
        # Mock vector_store.store_vectors method returning failure
        orchestrator.vector_store.store_vectors = AsyncMock(return_value=False)
        
        result = await orchestrator._store_vectors(vector_data, 'test_file_1')
        
        assert result is True  # Method should return True, even if storage fails it just logs warning
        orchestrator.vector_store.store_vectors.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_vectors_empty_vector(self, orchestrator):
        """Test empty vector storage"""
        # Create mock vector data with empty vector
        vector_data = {
            'file_type': 'image',
            'segments': [
                {
                    'type': 'image',
                    'vector': [],  # Empty vector
                    'timestamp': 0
                },
                {
                    'type': 'image',
                    'vector': [0.1, 0.2, 0.3, 0.4, 0.5],  # Valid vector
                    'timestamp': 10
                }
            ]
        }
        
        # Mock vector_store.store_vectors method
        orchestrator.vector_store.store_vectors = AsyncMock(return_value=True)
        
        result = await orchestrator._store_vectors(vector_data, 'test_file_1')
        
        # Should only call storage once (empty vector is skipped)
        assert result is True
        orchestrator.vector_store.store_vectors.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_processing_status(self, orchestrator):
        """Test updating processing status"""
        # Mock db_adapter.update_queue_status method
        orchestrator.db_adapter.update_queue_status = AsyncMock(return_value=True)
        
        await orchestrator._update_processing_status('test_file_1', 'processing', 50)
        
        # Verify memory status update
        assert orchestrator.processing_status['test_file_1']['status'] == 'processing'
        assert orchestrator.processing_status['test_file_1']['progress'] == 50
        assert orchestrator.processing_status['test_file_1']['error'] is None
        
        # Verify database status update
        orchestrator.db_adapter.update_queue_status.assert_called_once_with(
            'test_file_1', 'processing', None
        )
    
    @pytest.mark.asyncio
    async def test_update_processing_status_with_error(self, orchestrator):
        """Test updating processing status with error"""
        # Mock db_adapter.update_queue_status method
        orchestrator.db_adapter.update_queue_status = AsyncMock(return_value=True)
        
        await orchestrator._update_processing_status('test_file_1', 'failed', 0, 'Test error')
        
        # Verify memory status update
        assert orchestrator.processing_status['test_file_1']['status'] == 'failed'
        assert orchestrator.processing_status['test_file_1']['progress'] == 0
        assert orchestrator.processing_status['test_file_1']['error'] == 'Test error'
        
        # Verify database status update
        orchestrator.db_adapter.update_queue_status.assert_called_once_with(
            'test_file_1', 'failed', 'Test error'
        )
    
    @pytest.mark.asyncio
    async def test_process_file_success(self, orchestrator):
        """Test successful file processing"""
        # Mock processing steps
        orchestrator._determine_file_type = Mock(return_value='image')
        orchestrator._select_processing_strategy = Mock(return_value='image_processing')
        orchestrator._update_processing_status = AsyncMock()
        orchestrator._preprocess_file = AsyncMock(return_value={
            'status': 'success',
            'processed_path': '/path/to/processed_image.jpg'
        })
        orchestrator._vectorize_content = AsyncMock(return_value={
            'file_type': 'image',
            'segments': [{'type': 'image', 'vector': [0.1, 0.2, 0.3], 'timestamp': 0}]
        })
        orchestrator._store_vectors = AsyncMock(return_value=True)
        
        result = await orchestrator.process_file('/path/to/image.jpg', 'test_file_1')
        
        assert result['success'] is True
        assert result['file_id'] == 'test_file_1'
        assert result['file_path'] == '/path/to/image.jpg'
        assert result['file_type'] == 'image'
        assert result['strategy'] == 'image_processing'
        assert result['status'] == 'completed'
    
    @pytest.mark.asyncio
    async def test_process_file_failure(self, orchestrator):
        """Test file processing failure"""
        # Mock exception during processing
        orchestrator._determine_file_type = Mock(return_value='image')
        orchestrator._select_processing_strategy = Mock(return_value='image_processing')
        orchestrator._update_processing_status = AsyncMock()
        orchestrator._preprocess_file = AsyncMock(side_effect=Exception('Processing failed'))
        
        result = await orchestrator.process_file('/path/to/image.jpg', 'test_file_1')
        
        assert result['success'] is False
        assert result['file_id'] == 'test_file_1'
        assert result['file_path'] == '/path/to/image.jpg'
        assert 'Processing failed' in result['error']
        assert result['status'] == 'failed'
    
    @pytest.mark.asyncio
    async def test_batch_process_files_success(self, orchestrator):
        """Test successful batch file processing"""
        # Create test file list
        file_list = [
            {'file_path': '/path/to/image1.jpg', 'file_id': 'file_1'},
            {'file_path': '/path/to/image2.jpg', 'file_id': 'file_2'}
        ]
        
        # Mock process_file method
        async def mock_process_file(file_path, file_id):
            return {
                'success': True,
                'file_id': file_id,
                'file_path': file_path,
                'file_type': 'image',
                'strategy': 'image_processing',
                'status': 'completed'
            }
        
        orchestrator.process_file = mock_process_file
        
        # Mock config manager
        orchestrator.config_manager.get = Mock(return_value={'max_concurrent': 2})
        
        results = await orchestrator.batch_process_files(file_list)
        
        assert len(results) == 2
        assert all(result['success'] for result in results)
        assert results[0]['file_id'] == 'file_1'
        assert results[1]['file_id'] == 'file_2'
    
    @pytest.mark.asyncio
    async def test_batch_process_files_partial_failure(self, orchestrator):
        """Test partial failure in batch file processing"""
        # Create test file list
        file_list = [
            {'file_path': '/path/to/image1.jpg', 'file_id': 'file_1'},
            {'file_path': '/path/to/image2.jpg', 'file_id': 'file_2'}
        ]
        
        # Mock process_file method, first succeeds, second fails
        async def mock_process_file(file_path, file_id):
            if file_id == 'file_1':
                return {
                    'success': True,
                    'file_id': file_id,
                    'file_path': file_path,
                    'file_type': 'image',
                    'strategy': 'image_processing',
                    'status': 'completed'
                }
            else:
                raise Exception('Processing failed')
        
        orchestrator.process_file = mock_process_file
        
        # Mock config manager
        orchestrator.config_manager.get = Mock(return_value={'max_concurrent': 2})
        
        results = await orchestrator.batch_process_files(file_list)
        
        assert len(results) == 2
        assert results[0]['success'] is True
        assert results[1]['success'] is False
        assert 'Processing failed' in results[1]['error']
    
    def test_get_processing_orchestrator_singleton(self):
        """Test ProcessingOrchestrator singleton pattern"""
        with patch('src.core.processing_orchestrator.get_config_manager'), \
             patch('src.core.processing_orchestrator.get_db_adapter'), \
             patch('src.core.processing_orchestrator.get_media_processor'), \
             patch('src.core.processing_orchestrator.get_model_manager'), \
             patch('src.core.processing_orchestrator.get_vector_store'):
            
            from src.core.processing_orchestrator import get_processing_orchestrator
            
            # Reset global instance
            import src.core.processing_orchestrator as po_module
            po_module._processing_orchestrator = None
            
            # Get first instance
            orchestrator1 = get_processing_orchestrator()
            assert orchestrator1 is not None
            
            # Get second instance, should be the same
            orchestrator2 = get_processing_orchestrator()
            assert orchestrator1 is orchestrator2
