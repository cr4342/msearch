"""
处理编排器增强测试
为ProcessingOrchestrator添加更多测试用例
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
import sys
import os
import numpy as np

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.business.processing_orchestrator import ProcessingOrchestrator


class TestProcessingOrchestratorEnhanced(unittest.IsolatedAsyncioTestCase):
    """处理编排器增强测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 配置
        self.config = {
            'task': {
                'max_retry_count': 3,
                'max_concurrent_tasks': 4
            },
            'processing': {
                'image': {
                    'target_size': 224,
                    'max_resolution': (1920, 1080),
                    'quality_threshold': 0.5
                },
                'video': {
                    'target_size': 224,
                    'max_resolution': (1280, 720),
                    'scene_threshold': 0.3,
                    'frame_interval': 2.0
                },
                'audio': {
                    'target_sample_rate': 16000,
                    'target_channels': 1,
                    'segment_duration': 10.0,
                    'quality_threshold': 0.5
                },
                'text': {
                    'max_file_size': 10 * 1024 * 1024,
                    'encoding_priority': ['utf-8', 'gbk', 'gb2312', 'latin-1']
                }
            },
            'file_monitoring.file_extensions': {
                'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'],
                'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
                'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac'],
                'text': ['.txt', '.md', '.csv', '.json', '.xml']
            },
            'file_monitoring.mime_types': {
                'image': ['image/jpeg', 'image/png', 'image/bmp', 'image/gif', 'image/webp'],
                'video': ['video/mp4', 'video/x-msvideo', 'video/quicktime', 'video/x-matroska', 'video/webm'],
                'audio': ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/flac', 'audio/aac'],
                'text': ['text/plain', 'text/markdown', 'text/csv', 'application/json', 'application/xml']
            }
        }
    
    @patch('src.business.processing_orchestrator.get_file_type_detector')
    @patch('src.business.processing_orchestrator.MediaProcessor')
    @patch('src.business.processing_orchestrator.EmbeddingEngine')
    @patch('src.business.processing_orchestrator.TaskManager')
    @patch('src.business.processing_orchestrator.VectorStore')
    async def test_video_processing_flow(self, mock_vector_store, mock_task_manager, 
                                       mock_embedding_engine, mock_media_processor, 
                                       mock_file_type_detector):
        """测试视频处理流程"""
        # 创建模拟对象
        mock_detector_instance = Mock()
        mock_file_type_detector.return_value = mock_detector_instance
        
        # 模拟文件类型检测结果
        mock_detector_instance.detect_file_type.return_value = {
            'type': 'video',
            'subtype': 'mp4',
            'extension': '.mp4',
            'confidence': 0.95
        }
        
        mock_media_processor_instance = AsyncMock()
        mock_media_processor.return_value = mock_media_processor_instance
        
        # 模拟视频处理结果
        mock_media_processor_instance.process_file.return_value = {
            'status': 'success',
            'result': {
                'keyframes': [
                    {
                        'frame_data': np.random.rand(224, 224, 3).astype(np.float32),
                        'timestamp': 5.0,
                        'frame_index': 0
                    },
                    {
                        'frame_data': np.random.rand(224, 224, 3).astype(np.float32),
                        'timestamp': 10.0,
                        'frame_index': 1
                    }
                ],
                'duration': 30.0,
                'fps': 30.0
            }
        }
        
        mock_embedding_engine_instance = AsyncMock()
        mock_embedding_engine.return_value = mock_embedding_engine_instance
        
        # 模拟视频帧向量化结果
        mock_embedding_engine_instance.embed_image.side_effect = [
            np.random.rand(512).astype(np.float32),  # 第一帧向量
            np.random.rand(512).astype(np.float32)   # 第二帧向量
        ]
        
        mock_task_manager_instance = AsyncMock()
        mock_task_manager.return_value = mock_task_manager_instance
        
        # 模拟任务管理
        mock_task_manager_instance.add_task.return_value = "task_video_123"
        mock_task_manager_instance.update_task_progress.return_value = True
        mock_task_manager_instance.complete_task.return_value = True
        
        mock_vector_store_instance = AsyncMock()
        mock_vector_store.return_value = mock_vector_store_instance
        
        # 模拟向量存储
        mock_vector_store_instance.store_vector.return_value = True
        
        # 创建处理编排器实例
        orchestrator = ProcessingOrchestrator(self.config)
        
        # 执行视频处理
        result = await orchestrator.process_file("test_video.mp4")
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['file_type'], 'video')
        self.assertIn('processing_time', result)
        
        # 验证各组件是否被正确调用
        mock_detector_instance.detect_file_type.assert_called_once_with("test_video.mp4")
        mock_media_processor_instance.process_file.assert_called_once_with("test_video.mp4", "video")
        # 视频处理应该调用两次帧向量化（两个关键帧）
        self.assertEqual(mock_embedding_engine_instance.embed_image.call_count, 2)
        mock_task_manager_instance.add_task.assert_called_once_with("test_video.mp4")
        # 视频处理应该存储两个向量
        self.assertEqual(mock_vector_store_instance.store_vector.call_count, 2)
    
    @patch('src.business.processing_orchestrator.get_file_type_detector')
    @patch('src.business.processing_orchestrator.MediaProcessor')
    @patch('src.business.processing_orchestrator.EmbeddingEngine')
    @patch('src.business.processing_orchestrator.TaskManager')
    @patch('src.business.processing_orchestrator.VectorStore')
    async def test_audio_processing_flow(self, mock_vector_store, mock_task_manager, 
                                       mock_embedding_engine, mock_media_processor, 
                                       mock_file_type_detector):
        """测试音频处理流程"""
        # 创建模拟对象
        mock_detector_instance = Mock()
        mock_file_type_detector.return_value = mock_detector_instance
        
        # 模拟文件类型检测结果
        mock_detector_instance.detect_file_type.return_value = {
            'type': 'audio',
            'subtype': 'mp3',
            'extension': '.mp3',
            'confidence': 0.92
        }
        
        mock_media_processor_instance = AsyncMock()
        mock_media_processor.return_value = mock_media_processor_instance
        
        # 模拟音频处理结果
        mock_media_processor_instance.process_file.return_value = {
            'status': 'success',
            'result': {
                'segments': [
                    {
                        'audio_data': np.random.rand(160000).astype(np.float32),  # 10秒音频
                        'start_time': 0.0,
                        'end_time': 10.0
                    },
                    {
                        'audio_data': np.random.rand(160000).astype(np.float32),  # 10秒音频
                        'start_time': 10.0,
                        'end_time': 20.0
                    }
                ],
                'classification': {
                    'primary_type': 'music',  # 音乐类型
                    'confidence': 0.85
                },
                'duration': 20.0
            }
        }
        
        mock_embedding_engine_instance = AsyncMock()
        mock_embedding_engine.return_value = mock_embedding_engine_instance
        
        # 模拟音频向量化结果
        mock_embedding_engine_instance.embed_audio_music.side_effect = [
            np.random.rand(512).astype(np.float32),  # 第一段音频向量
            np.random.rand(512).astype(np.float32)   # 第二段音频向量
        ]
        
        mock_task_manager_instance = AsyncMock()
        mock_task_manager.return_value = mock_task_manager_instance
        
        # 模拟任务管理
        mock_task_manager_instance.add_task.return_value = "task_audio_123"
        mock_task_manager_instance.update_task_progress.return_value = True
        mock_task_manager_instance.complete_task.return_value = True
        
        mock_vector_store_instance = AsyncMock()
        mock_vector_store.return_value = mock_vector_store_instance
        
        # 模拟向量存储
        mock_vector_store_instance.store_vector.return_value = True
        
        # 创建处理编排器实例
        orchestrator = ProcessingOrchestrator(self.config)
        
        # 执行音频处理
        result = await orchestrator.process_file("test_audio.mp3")
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['file_type'], 'audio')
        self.assertIn('processing_time', result)
        
        # 验证各组件是否被正确调用
        mock_detector_instance.detect_file_type.assert_called_once_with("test_audio.mp3")
        mock_media_processor_instance.process_file.assert_called_once_with("test_audio.mp3", "audio")
        # 音频处理应该调用两次音乐向量化（两个片段）
        self.assertEqual(mock_embedding_engine_instance.embed_audio_music.call_count, 2)
        mock_task_manager_instance.add_task.assert_called_once_with("test_audio.mp3")
        # 音频处理应该存储两个向量
        self.assertEqual(mock_vector_store_instance.store_vector.call_count, 2)
    
    @patch('src.business.processing_orchestrator.get_file_type_detector')
    @patch('src.business.processing_orchestrator.MediaProcessor')
    @patch('src.business.processing_orchestrator.EmbeddingEngine')
    @patch('src.business.processing_orchestrator.TaskManager')
    @patch('src.business.processing_orchestrator.VectorStore')
    async def test_text_processing_flow(self, mock_vector_store, mock_task_manager, 
                                      mock_embedding_engine, mock_media_processor, 
                                      mock_file_type_detector):
        """测试文本处理流程"""
        # 创建模拟对象
        mock_detector_instance = Mock()
        mock_file_type_detector.return_value = mock_detector_instance
        
        # 模拟文件类型检测结果
        mock_detector_instance.detect_file_type.return_value = {
            'type': 'text',
            'subtype': 'txt',
            'extension': '.txt',
            'confidence': 0.98
        }
        
        mock_media_processor_instance = AsyncMock()
        mock_media_processor.return_value = mock_media_processor_instance
        
        # 模拟文本处理结果
        mock_media_processor_instance.process_file.return_value = {
            'status': 'success',
            'result': {
                'cleaned_content': "这是测试文本内容，用于向量化处理。",
                'original_encoding': 'utf-8',
                'file_size': 1024
            }
        }
        
        mock_embedding_engine_instance = AsyncMock()
        mock_embedding_engine.return_value = mock_embedding_engine_instance
        
        # 模拟文本向量化结果
        mock_embedding_engine_instance.embed_text.return_value = np.random.rand(512).astype(np.float32)
        
        mock_task_manager_instance = AsyncMock()
        mock_task_manager.return_value = mock_task_manager_instance
        
        # 模拟任务管理
        mock_task_manager_instance.add_task.return_value = "task_text_123"
        mock_task_manager_instance.update_task_progress.return_value = True
        mock_task_manager_instance.complete_task.return_value = True
        
        mock_vector_store_instance = AsyncMock()
        mock_vector_store.return_value = mock_vector_store_instance
        
        # 模拟向量存储
        mock_vector_store_instance.store_vector.return_value = True
        
        # 创建处理编排器实例
        orchestrator = ProcessingOrchestrator(self.config)
        
        # 执行文本处理
        result = await orchestrator.process_file("test_text.txt")
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['file_type'], 'text')
        self.assertIn('processing_time', result)
        
        # 验证各组件是否被正确调用
        mock_detector_instance.detect_file_type.assert_called_once_with("test_text.txt")
        mock_media_processor_instance.process_file.assert_called_once_with("test_text.txt", "text")
        mock_embedding_engine_instance.embed_text.assert_called_once_with("这是测试文本内容，用于向量化处理。")
        mock_task_manager_instance.add_task.assert_called_once_with("test_text.txt")
        mock_vector_store_instance.store_vector.assert_called_once()
    
    @patch('src.business.processing_orchestrator.get_file_type_detector')
    @patch('src.business.processing_orchestrator.MediaProcessor')
    @patch('src.business.processing_orchestrator.EmbeddingEngine')
    @patch('src.business.processing_orchestrator.TaskManager')
    @patch('src.business.processing_orchestrator.VectorStore')
    async def test_processing_with_unknown_file_type(self, mock_vector_store, mock_task_manager, 
                                                   mock_embedding_engine, mock_media_processor, 
                                                   mock_file_type_detector):
        """测试处理未知文件类型"""
        # 创建模拟对象
        mock_detector_instance = Mock()
        mock_file_type_detector.return_value = mock_detector_instance
        
        # 模拟未知文件类型检测结果
        mock_detector_instance.detect_file_type.return_value = {
            'type': 'unknown',
            'subtype': 'unknown',
            'extension': '.xyz',
            'confidence': 0.1
        }
        
        mock_media_processor_instance = AsyncMock()
        mock_media_processor.return_value = mock_media_processor_instance
        
        mock_embedding_engine_instance = AsyncMock()
        mock_embedding_engine.return_value = mock_embedding_engine_instance
        
        mock_task_manager_instance = AsyncMock()
        mock_task_manager.return_value = mock_task_manager_instance
        
        mock_vector_store_instance = AsyncMock()
        mock_vector_store.return_value = mock_vector_store_instance
        
        # 创建处理编排器实例
        orchestrator = ProcessingOrchestrator(self.config)
        
        # 执行处理
        result = await orchestrator.process_file("unknown_file.xyz")
        
        # 验证结果
        self.assertEqual(result['status'], 'error')
        self.assertIn('不支持的文件类型', result['error'])
        self.assertEqual(result['file_path'], 'unknown_file.xyz')
    
    @patch('src.business.processing_orchestrator.get_file_type_detector')
    @patch('src.business.processing_orchestrator.MediaProcessor')
    @patch('src.business.processing_orchestrator.EmbeddingEngine')
    @patch('src.business.processing_orchestrator.TaskManager')
    @patch('src.business.processing_orchestrator.VectorStore')
    async def test_processing_with_preprocessing_failure(self, mock_vector_store, mock_task_manager, 
                                                       mock_embedding_engine, mock_media_processor, 
                                                       mock_file_type_detector):
        """测试预处理失败的情况"""
        # 创建模拟对象
        mock_detector_instance = Mock()
        mock_file_type_detector.return_value = mock_detector_instance
        
        # 模拟文件类型检测结果
        mock_detector_instance.detect_file_type.return_value = {
            'type': 'image',
            'subtype': 'jpg',
            'extension': '.jpg',
            'confidence': 0.9
        }
        
        mock_media_processor_instance = AsyncMock()
        mock_media_processor.return_value = mock_media_processor_instance
        
        # 模拟预处理失败
        mock_media_processor_instance.process_file.return_value = {
            'status': 'error',
            'error': '文件损坏无法处理'
        }
        
        mock_embedding_engine_instance = AsyncMock()
        mock_embedding_engine.return_value = mock_embedding_engine_instance
        
        mock_task_manager_instance = AsyncMock()
        mock_task_manager.return_value = mock_task_manager_instance
        
        # 模拟任务管理
        mock_task_manager_instance.add_task.return_value = "task_failed_123"
        mock_task_manager_instance.complete_task.return_value = True
        
        mock_vector_store_instance = AsyncMock()
        mock_vector_store.return_value = mock_vector_store_instance
        
        # 创建处理编排器实例
        orchestrator = ProcessingOrchestrator(self.config)
        
        # 执行处理
        result = await orchestrator.process_file("corrupted_image.jpg")
        
        # 验证结果
        self.assertEqual(result['status'], 'error')
        self.assertIn('预处理失败', result['error'])
        self.assertEqual(result['file_path'], 'corrupted_image.jpg')
        
        # 验证任务被标记为失败
        mock_task_manager_instance.complete_task.assert_called_once_with(
            "task_failed_123", success=False, error_message="预处理失败: 文件损坏无法处理"
        )
    
    @patch('src.business.processing_orchestrator.get_file_type_detector')
    @patch('src.business.processing_orchestrator.MediaProcessor')
    @patch('src.business.processing_orchestrator.EmbeddingEngine')
    @patch('src.business.processing_orchestrator.TaskManager')
    @patch('src.business.processing_orchestrator.VectorStore')
    async def test_processing_with_vectorization_failure(self, mock_vector_store, mock_task_manager, 
                                                       mock_embedding_engine, mock_media_processor, 
                                                       mock_file_type_detector):
        """测试向量化失败的情况"""
        # 创建模拟对象
        mock_detector_instance = Mock()
        mock_file_type_detector.return_value = mock_detector_instance
        
        # 模拟文件类型检测结果
        mock_detector_instance.detect_file_type.return_value = {
            'type': 'image',
            'subtype': 'png',
            'extension': '.png',
            'confidence': 0.85
        }
        
        mock_media_processor_instance = AsyncMock()
        mock_media_processor.return_value = mock_media_processor_instance
        
        # 模拟预处理成功
        mock_media_processor_instance.process_file.return_value = {
            'status': 'success',
            'result': {
                'image_data': np.random.rand(224, 224, 3).astype(np.float32),
                'quality_score': 0.9
            }
        }
        
        mock_embedding_engine_instance = AsyncMock()
        mock_embedding_engine.return_value = mock_embedding_engine_instance
        
        # 模拟向量化失败
        mock_embedding_engine_instance.embed_image.side_effect = Exception("模型加载失败")
        
        mock_task_manager_instance = AsyncMock()
        mock_task_manager.return_value = mock_task_manager_instance
        
        # 模拟任务管理
        mock_task_manager_instance.add_task.return_value = "task_vector_123"
        mock_task_manager_instance.update_task_progress.return_value = True
        mock_task_manager_instance.complete_task.return_value = True
        
        mock_vector_store_instance = AsyncMock()
        mock_vector_store.return_value = mock_vector_store_instance
        
        # 创建处理编排器实例
        orchestrator = ProcessingOrchestrator(self.config)
        
        # 执行处理
        result = await orchestrator.process_file("test_image.png")
        
        # 验证结果
        self.assertEqual(result['status'], 'error')
        self.assertIn('向量化失败', result['error'])
        self.assertEqual(result['file_path'], 'test_image.png')
        
        # 验证任务被标记为失败
        mock_task_manager_instance.complete_task.assert_called_once_with(
            "task_vector_123", success=False, error_message="向量化失败: 模型加载失败"
        )
    
    @patch('src.business.processing_orchestrator.get_file_type_detector')
    @patch('src.business.processing_orchestrator.MediaProcessor')
    @patch('src.business.processing_orchestrator.EmbeddingEngine')
    @patch('src.business.processing_orchestrator.TaskManager')
    @patch('src.business.processing_orchestrator.VectorStore')
    async def test_processing_with_storage_failure(self, mock_vector_store, mock_task_manager, 
                                                 mock_embedding_engine, mock_media_processor, 
                                                 mock_file_type_detector):
        """测试存储失败的情况"""
        # 创建模拟对象
        mock_detector_instance = Mock()
        mock_file_type_detector.return_value = mock_detector_instance
        
        # 模拟文件类型检测结果
        mock_detector_instance.detect_file_type.return_value = {
            'type': 'image',
            'subtype': 'jpeg',
            'extension': '.jpeg',
            'confidence': 0.92
        }
        
        mock_media_processor_instance = AsyncMock()
        mock_media_processor.return_value = mock_media_processor_instance
        
        # 模拟预处理成功
        mock_media_processor_instance.process_file.return_value = {
            'status': 'success',
            'result': {
                'image_data': np.random.rand(224, 224, 3).astype(np.float32),
                'quality_score': 0.88
            }
        }
        
        mock_embedding_engine_instance = AsyncMock()
        mock_embedding_engine.return_value = mock_embedding_engine_instance
        
        # 模拟向量化成功
        mock_embedding_engine_instance.embed_image.return_value = np.random.rand(512).astype(np.float32)
        
        mock_task_manager_instance = AsyncMock()
        mock_task_manager.return_value = mock_task_manager_instance
        
        # 模拟任务管理
        mock_task_manager_instance.add_task.return_value = "task_store_123"
        mock_task_manager_instance.update_task_progress.return_value = True
        mock_task_manager_instance.complete_task.return_value = True
        
        mock_vector_store_instance = AsyncMock()
        mock_vector_store.return_value = mock_vector_store_instance
        
        # 模拟存储失败
        mock_vector_store_instance.store_vector.side_effect = Exception("数据库连接失败")
        
        # 创建处理编排器实例
        orchestrator = ProcessingOrchestrator(self.config)
        
        # 执行处理
        result = await orchestrator.process_file("test_image.jpeg")
        
        # 验证结果
        self.assertEqual(result['status'], 'error')
        self.assertIn('存储失败', result['error'])
        self.assertEqual(result['file_path'], 'test_image.jpeg')
        
        # 验证任务被标记为失败
        mock_task_manager_instance.complete_task.assert_called_once_with(
            "task_store_123", success=False, error_message="存储失败: 数据库连接失败"
        )
    
    def test_find_task_id_by_file(self):
        """测试根据文件路径查找任务ID"""
        with patch('src.business.processing_orchestrator.get_file_type_detector'), \
             patch('src.business.processing_orchestrator.MediaProcessor'), \
             patch('src.business.processing_orchestrator.EmbeddingEngine'), \
             patch('src.business.processing_orchestrator.TaskManager'), \
             patch('src.business.processing_orchestrator.VectorStore'):
            
            # 创建处理编排器实例
            orchestrator = ProcessingOrchestrator(self.config)
            
            # 测试方法存在且可调用
            result = orchestrator._find_task_id_by_file("test_file.jpg")
            # 当前实现返回None，这是预期的行为
            self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()