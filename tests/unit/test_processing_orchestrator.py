"""
处理编排器单元测试
"""
import unittest
import asyncio
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(0, '..')

from src.business.processing_orchestrator import ProcessingOrchestrator


class TestProcessingOrchestrator(unittest.IsolatedAsyncioTestCase):
    """处理编排器单元测试"""
    
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
    def test_orchestrator_initialization(self, mock_vector_store, mock_task_manager, 
                                       mock_embedding_engine, mock_media_processor, 
                                       mock_file_type_detector):
        """测试处理编排器初始化"""
        # 创建模拟对象
        mock_detector_instance = Mock()
        mock_file_type_detector.return_value = mock_detector_instance
        
        mock_media_processor_instance = Mock()
        mock_media_processor.return_value = mock_media_processor_instance
        
        mock_embedding_engine_instance = Mock()
        mock_embedding_engine.return_value = mock_embedding_engine_instance
        
        mock_task_manager_instance = Mock()
        mock_task_manager.return_value = mock_task_manager_instance
        
        mock_vector_store_instance = Mock()
        mock_vector_store.return_value = mock_vector_store_instance
        
        # 创建处理编排器实例
        orchestrator = ProcessingOrchestrator(self.config)
        
        # 验证组件是否正确初始化
        self.assertIsNotNone(orchestrator.file_type_detector)
        self.assertIsNotNone(orchestrator.media_processor)
        self.assertIsNotNone(orchestrator.embedding_engine)
        self.assertIsNotNone(orchestrator.task_manager)
        self.assertIsNotNone(orchestrator.vector_store)
    
    @patch('src.business.processing_orchestrator.get_file_type_detector')
    @patch('src.business.processing_orchestrator.MediaProcessor')
    @patch('src.business.processing_orchestrator.EmbeddingEngine')
    @patch('src.business.processing_orchestrator.TaskManager')
    @patch('src.business.processing_orchestrator.VectorStore')
    def test_file_type_detection(self, mock_vector_store, mock_task_manager, 
                               mock_embedding_engine, mock_media_processor, 
                               mock_file_type_detector):
        """测试文件类型检测"""
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
        
        mock_media_processor_instance = Mock()
        mock_media_processor.return_value = mock_media_processor_instance
        
        mock_embedding_engine_instance = Mock()
        mock_embedding_engine.return_value = mock_embedding_engine_instance
        
        mock_task_manager_instance = Mock()
        mock_task_manager.return_value = mock_task_manager_instance
        
        mock_vector_store_instance = Mock()
        mock_vector_store.return_value = mock_vector_store_instance
        
        # 创建处理编排器实例
        orchestrator = ProcessingOrchestrator(self.config)
        
        # 调用文件类型检测
        file_type_info = orchestrator.file_type_detector.detect_file_type("test.jpg")
        
        # 验证结果
        self.assertEqual(file_type_info['type'], 'image')
        self.assertEqual(file_type_info['subtype'], 'jpg')
        self.assertEqual(file_type_info['extension'], '.jpg')
        self.assertEqual(file_type_info['confidence'], 0.9)
    
    @patch('src.business.processing_orchestrator.get_file_type_detector')
    @patch('src.business.processing_orchestrator.MediaProcessor')
    @patch('src.business.processing_orchestrator.EmbeddingEngine')
    @patch('src.business.processing_orchestrator.TaskManager')
    @patch('src.business.processing_orchestrator.VectorStore')
    async def test_image_processing_flow(self, mock_vector_store, mock_task_manager, 
                                       mock_embedding_engine, mock_media_processor, 
                                       mock_file_type_detector):
        """测试图片处理流程"""
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
        
        # 模拟媒体处理结果（异步方法）
        mock_media_processor_instance.process_file.return_value = {
            'status': 'success',
            'result': {
                'image_data': np.random.rand(224, 224, 3).astype(np.float32),
                'quality_score': 0.85
            }
        }
        
        mock_embedding_engine_instance = AsyncMock()
        mock_embedding_engine.return_value = mock_embedding_engine_instance
        
        # 模拟向量化结果（异步方法）
        mock_embedding_engine_instance.embed_image.return_value = np.random.rand(512).astype(np.float32)
        
        mock_task_manager_instance = AsyncMock()
        mock_task_manager.return_value = mock_task_manager_instance
        
        # 模拟任务管理（异步方法）
        mock_task_manager_instance.add_task.return_value = "task_123"
        mock_task_manager_instance.update_task_progress.return_value = True
        mock_task_manager_instance.complete_task.return_value = True
        
        mock_vector_store_instance = AsyncMock()
        mock_vector_store.return_value = mock_vector_store_instance
        
        # 模拟向量存储（异步方法）
        mock_vector_store_instance.store_vector.return_value = True
        
        # 创建处理编排器实例
        orchestrator = ProcessingOrchestrator(self.config)
        
        # 直接调用异步方法
        result = await orchestrator.process_file("test.jpg")
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['file_type'], 'image')
        
        # 验证各组件是否被正确调用
        mock_detector_instance.detect_file_type.assert_called_once_with("test.jpg")
        mock_media_processor_instance.process_file.assert_called_once_with("test.jpg", "image")
        mock_embedding_engine_instance.embed_image.assert_called_once()
        mock_task_manager_instance.add_task.assert_called_once_with("test.jpg")
        mock_vector_store_instance.store_vector.assert_called_once()


if __name__ == '__main__':
    unittest.main()