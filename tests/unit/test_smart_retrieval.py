"""
智能检索引擎单元测试
测试SmartRetrievalEngine的核心功能
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.business.smart_retrieval import SmartRetrievalEngine


class TestSmartRetrievalEngine(unittest.IsolatedAsyncioTestCase):
    """智能检索引擎单元测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 配置
        self.config = {
            'retrieval': {
                'audio_keywords': [
                    '音乐', '歌曲', '旋律', '节奏', '节拍', '乐器', '演奏', '演唱',
                    'audio', 'music', 'song', 'melody', 'rhythm', 'instrument'
                ],
                'visual_keywords': [
                    '图片', '照片', '图像', '画面', '视觉', '颜色', '场景',
                    'image', 'photo', 'picture', 'visual', 'color', 'scene'
                ]
            },
            'database': {
                'sqlite': {
                    'path': './data/database/msearch.db'
                }
            }
        }
    
    @patch('src.business.smart_retrieval.SearchEngine')
    @patch('src.business.smart_retrieval.MultiModalFusionEngine')
    @patch('src.business.smart_retrieval.FaceDatabase')
    @patch('src.business.smart_retrieval.FaceManager')
    def test_smart_retrieval_initialization(self, mock_face_manager, mock_face_database, 
                                          mock_fusion_engine, mock_search_engine):
        """测试智能检索引擎初始化"""
        # 创建模拟对象
        mock_search_engine_instance = Mock()
        mock_search_engine.return_value = mock_search_engine_instance
        
        mock_fusion_engine_instance = Mock()
        mock_fusion_engine.return_value = mock_fusion_engine_instance
        
        mock_face_database_instance = Mock()
        mock_face_database.return_value = mock_face_database_instance
        
        mock_face_manager_instance = Mock()
        mock_face_manager.return_value = mock_face_manager_instance
        
        # 创建智能检索引擎实例
        engine = SmartRetrievalEngine(self.config)
        
        # 验证组件是否正确初始化
        self.assertIsNotNone(engine.search_engine)
        self.assertIsNotNone(engine.fusion_engine)
        self.assertIsNotNone(engine.face_database)
        self.assertIsNotNone(engine.face_manager)
        self.assertIsNotNone(engine.audio_keywords)
        self.assertIsNotNone(engine.visual_keywords)
    
    @patch('src.business.smart_retrieval.SearchEngine')
    @patch('src.business.smart_retrieval.MultiModalFusionEngine')
    @patch('src.business.smart_retrieval.FaceDatabase')
    @patch('src.business.smart_retrieval.FaceManager')
    def test_query_type_identification(self, mock_face_manager, mock_face_database, 
                                     mock_fusion_engine, mock_search_engine):
        """测试查询类型识别"""
        # 创建模拟对象
        mock_search_engine_instance = Mock()
        mock_search_engine.return_value = mock_search_engine_instance
        
        mock_fusion_engine_instance = Mock()
        mock_fusion_engine.return_value = mock_fusion_engine_instance
        
        mock_face_database_instance = Mock()
        mock_face_database.return_value = mock_face_database_instance
        
        mock_face_manager_instance = Mock()
        mock_face_manager.return_value = mock_face_manager_instance
        
        # 模拟人脸数据库返回人名
        mock_face_database_instance.get_all_persons.return_value = [
            {'name': '张三', 'aliases': ['张三丰']},
            {'name': '李四', 'aliases': []}
        ]
        
        # 创建智能检索引擎实例
        engine = SmartRetrievalEngine(self.config)
        
        # 测试人名查询识别
        self.assertEqual(engine._identify_query_type("查找张三的照片"), "person")
        self.assertEqual(engine._identify_query_type("寻找李四的视频"), "person")
        
        # 测试音频查询识别
        self.assertEqual(engine._identify_query_type("搜索音乐"), "audio")
        self.assertEqual(engine._identify_query_type("找一首旋律优美的歌曲"), "audio")
        
        # 测试视觉查询识别
        self.assertEqual(engine._identify_query_type("查找图片"), "visual")
        self.assertEqual(engine._identify_query_type("搜索颜色鲜艳的画面"), "visual")
        
        # 测试通用查询识别
        self.assertEqual(engine._identify_query_type("查找相关文件"), "generic")
        self.assertEqual(engine._identify_query_type("搜索文档"), "generic")
    
    @patch('src.business.smart_retrieval.SearchEngine')
    @patch('src.business.smart_retrieval.MultiModalFusionEngine')
    @patch('src.business.smart_retrieval.FaceDatabase')
    @patch('src.business.smart_retrieval.FaceManager')
    async def test_generic_search(self, mock_face_manager, mock_face_database, 
                                mock_fusion_engine, mock_search_engine):
        """测试通用搜索"""
        # 创建模拟对象
        mock_search_engine_instance = AsyncMock()
        mock_search_engine.return_value = mock_search_engine_instance
        
        mock_fusion_engine_instance = Mock()
        mock_fusion_engine.return_value = mock_fusion_engine_instance
        
        mock_face_database_instance = Mock()
        mock_face_database.return_value = mock_face_database_instance
        
        mock_face_manager_instance = Mock()
        mock_face_manager.return_value = mock_face_manager_instance
        
        # 模拟搜索引擎的多模态搜索结果
        mock_search_engine_instance.multimodal_search.return_value = {
            'status': 'success',
            'query_id': 'test_query_123',
            'modality_results': {
                'text': [
                    {'file_id': 1, 'score': 0.9, 'payload': {'path': 'file1.txt'}},
                    {'file_id': 2, 'score': 0.8, 'payload': {'path': 'file2.txt'}}
                ],
                'image': [
                    {'file_id': 3, 'score': 0.85, 'payload': {'path': 'file3.jpg'}}
                ]
            }
        }
        
        # 模拟融合引擎的结果
        mock_fusion_engine_instance.fuse_results.return_value = [
            {'file_id': 1, 'score': 0.9, 'payload': {'path': 'file1.txt'}},
            {'file_id': 3, 'score': 0.85, 'payload': {'path': 'file3.jpg'}},
            {'file_id': 2, 'score': 0.8, 'payload': {'path': 'file2.txt'}}
        ]
        
        # 创建智能检索引擎实例
        engine = SmartRetrievalEngine(self.config)
        
        # 执行通用搜索
        result = await engine._generic_search("测试搜索")
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['query'], '测试搜索')
        self.assertEqual(result['query_type'], 'generic')
        self.assertEqual(len(result['results']), 3)
        self.assertIn('weights_used', result)
        
        # 验证各组件是否被正确调用
        mock_search_engine_instance.multimodal_search.assert_called_once_with({'text': '测试搜索'})
        mock_fusion_engine_instance.fuse_results.assert_called_once()
    
    @patch('src.business.smart_retrieval.SearchEngine')
    @patch('src.business.smart_retrieval.MultiModalFusionEngine')
    @patch('src.business.smart_retrieval.FaceDatabase')
    @patch('src.business.smart_retrieval.FaceManager')
    async def test_audio_search(self, mock_face_manager, mock_face_database, 
                              mock_fusion_engine, mock_search_engine):
        """测试音频搜索"""
        # 创建模拟对象
        mock_search_engine_instance = AsyncMock()
        mock_search_engine.return_value = mock_search_engine_instance
        
        mock_fusion_engine_instance = Mock()
        mock_fusion_engine.return_value = mock_fusion_engine_instance
        
        mock_face_database_instance = Mock()
        mock_face_database.return_value = mock_face_database_instance
        
        mock_face_manager_instance = Mock()
        mock_face_manager.return_value = mock_face_manager_instance
        
        # 模拟搜索引擎的多模态搜索结果
        mock_search_engine_instance.multimodal_search.return_value = {
            'status': 'success',
            'query_id': 'test_query_123',
            'modality_results': {
                'text': [
                    {'file_id': 1, 'score': 0.9, 'payload': {'path': 'file1.txt'}}
                ],
                'audio_music': [
                    {'file_id': 2, 'score': 0.85, 'payload': {'path': 'file2.mp3'}}
                ],
                'audio_speech': [
                    {'file_id': 3, 'score': 0.8, 'payload': {'path': 'file3.wav'}}
                ]
            }
        }
        
        # 模拟融合引擎的结果
        mock_fusion_engine_instance.fuse_results.return_value = [
            {'file_id': 2, 'score': 0.85, 'payload': {'path': 'file2.mp3'}},
            {'file_id': 1, 'score': 0.9, 'payload': {'path': 'file1.txt'}},
            {'file_id': 3, 'score': 0.8, 'payload': {'path': 'file3.wav'}}
        ]
        
        # 创建智能检索引擎实例
        engine = SmartRetrievalEngine(self.config)
        
        # 执行音频搜索
        result = await engine._audio_search("搜索音乐")
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['query'], '搜索音乐')
        self.assertEqual(result['query_type'], 'audio')
        self.assertEqual(len(result['results']), 3)
        self.assertIn('weights_used', result)
        
        # 验证权重是否正确设置（音频权重应该更高）
        weights = result['weights_used']
        self.assertGreater(weights['audio_music'], 0.25)
        self.assertGreater(weights['audio_speech'], 0.25)
    
    @patch('src.business.smart_retrieval.SearchEngine')
    @patch('src.business.smart_retrieval.MultiModalFusionEngine')
    @patch('src.business.smart_retrieval.FaceDatabase')
    @patch('src.business.smart_retrieval.FaceManager')
    async def test_visual_search(self, mock_face_manager, mock_face_database, 
                               mock_fusion_engine, mock_search_engine):
        """测试视觉搜索"""
        # 创建模拟对象
        mock_search_engine_instance = AsyncMock()
        mock_search_engine.return_value = mock_search_engine_instance
        
        mock_fusion_engine_instance = Mock()
        mock_fusion_engine.return_value = mock_fusion_engine_instance
        
        mock_face_database_instance = Mock()
        mock_face_database.return_value = mock_face_database_instance
        
        mock_face_manager_instance = Mock()
        mock_face_manager.return_value = mock_face_manager_instance
        
        # 模拟搜索引擎的多模态搜索结果
        mock_search_engine_instance.multimodal_search.return_value = {
            'status': 'success',
            'query_id': 'test_query_123',
            'modality_results': {
                'text': [
                    {'file_id': 1, 'score': 0.9, 'payload': {'path': 'file1.txt'}}
                ],
                'image': [
                    {'file_id': 2, 'score': 0.85, 'payload': {'path': 'file2.jpg'}},
                    {'file_id': 3, 'score': 0.8, 'payload': {'path': 'file3.png'}}
                ]
            }
        }
        
        # 模拟融合引擎的结果
        mock_fusion_engine_instance.fuse_results.return_value = [
            {'file_id': 2, 'score': 0.85, 'payload': {'path': 'file2.jpg'}},
            {'file_id': 3, 'score': 0.8, 'payload': {'path': 'file3.png'}},
            {'file_id': 1, 'score': 0.9, 'payload': {'path': 'file1.txt'}}
        ]
        
        # 创建智能检索引擎实例
        engine = SmartRetrievalEngine(self.config)
        
        # 执行视觉搜索
        result = await engine._visual_search("查找图片")
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['query'], '查找图片')
        self.assertEqual(result['query_type'], 'visual')
        self.assertEqual(len(result['results']), 3)
        self.assertIn('weights_used', result)
        
        # 验证权重是否正确设置（视觉权重应该更高）
        weights = result['weights_used']
        self.assertGreater(weights['image'], 0.25)
    
    @patch('src.business.smart_retrieval.SearchEngine')
    @patch('src.business.smart_retrieval.MultiModalFusionEngine')
    @patch('src.business.smart_retrieval.FaceDatabase')
    @patch('src.business.smart_retrieval.FaceManager')
    async def test_person_search(self, mock_face_manager, mock_face_database, 
                               mock_fusion_engine, mock_search_engine):
        """测试人名搜索"""
        # 创建模拟对象
        mock_search_engine_instance = AsyncMock()
        mock_search_engine.return_value = mock_search_engine_instance
        
        mock_fusion_engine_instance = Mock()
        mock_fusion_engine.return_value = mock_fusion_engine_instance
        
        mock_face_database_instance = Mock()
        mock_face_database.return_value = mock_face_database_instance
        
        mock_face_manager_instance = AsyncMock()
        mock_face_manager.return_value = mock_face_manager_instance
        
        # 模拟人脸数据库返回人名
        mock_face_database_instance.get_all_persons.return_value = [
            {'name': '张三', 'aliases': ['张三丰']},
            {'name': '李四', 'aliases': []}
        ]
        
        # 模拟人脸管理器的搜索结果
        mock_face_manager_instance.search_by_person_name.return_value = {
            'status': 'success',
            'files': [
                {'file_id': 1, 'file_path': 'file1.jpg'},
                {'file_id': 2, 'file_path': 'file2.mp4'}
            ]
        }
        
        # 创建智能检索引擎实例
        engine = SmartRetrievalEngine(self.config)
        
        # 执行人名搜索
        result = await engine._person_search("查找张三的照片")
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['query'], '查找张三的照片')
        self.assertEqual(result['query_type'], 'person')
        self.assertEqual(len(result['results']), 2)
        self.assertTrue(result['whitelist_used'])
        self.assertEqual(result['whitelist_size'], 2)
        
        # 验证人脸管理器被正确调用
        mock_face_manager_instance.search_by_person_name.assert_called_once_with('张三')
    
    @patch('src.business.smart_retrieval.SearchEngine')
    @patch('src.business.smart_retrieval.MultiModalFusionEngine')
    @patch('src.business.smart_retrieval.FaceDatabase')
    @patch('src.business.smart_retrieval.FaceManager')
    async def test_main_search_method(self, mock_face_manager, mock_face_database, 
                                    mock_fusion_engine, mock_search_engine):
        """测试主搜索方法"""
        # 创建模拟对象
        mock_search_engine_instance = AsyncMock()
        mock_search_engine.return_value = mock_search_engine_instance
        
        mock_fusion_engine_instance = Mock()
        mock_fusion_engine.return_value = mock_fusion_engine_instance
        
        mock_face_database_instance = Mock()
        mock_face_database.return_value = mock_face_database_instance
        
        mock_face_manager_instance = Mock()
        mock_face_manager.return_value = mock_face_manager_instance
        
        # 模拟人脸数据库返回人名
        mock_face_database_instance.get_all_persons.return_value = [
            {'name': '张三', 'aliases': ['张三丰']},
            {'name': '李四', 'aliases': []}
        ]
        
        # 模拟通用搜索的结果
        mock_search_engine_instance.multimodal_search.return_value = {
            'status': 'success',
            'query_id': 'test_query_123',
            'modality_results': {
                'text': [
                    {'file_id': 1, 'score': 0.9, 'payload': {'path': 'file1.txt'}}
                ]
            }
        }
        
        mock_fusion_engine_instance.fuse_results.return_value = [
            {'file_id': 1, 'score': 0.9, 'payload': {'path': 'file1.txt'}}
        ]
        
        # 创建智能检索引擎实例
        engine = SmartRetrievalEngine(self.config)
        
        # 执行主搜索方法
        result = await engine.search("测试搜索")
        
        # 验证结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['query'], '测试搜索')
        self.assertIn('results', result)
        
        # 验证各组件是否被正确调用
        mock_search_engine_instance.multimodal_search.assert_called_once()


if __name__ == '__main__':
    unittest.main()