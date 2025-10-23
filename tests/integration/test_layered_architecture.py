"""
分层架构集成测试
测试UI层、API层、业务层、AI推理层、存储层的分离和协作
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np

from src.core.config_manager import ConfigManager
from src.api.main import app
from src.business.processing_orchestrator import ProcessingOrchestrator
from src.business.embedding_engine import EmbeddingEngine
from src.storage.qdrant_client import QdrantClient
from src.storage.sqlite_manager import SQLiteManager


class TestLayeredArchitecture:
    """分层架构集成测试"""
    
    @pytest.fixture
    def layered_config(self):
        """分层架构测试配置"""
        config = Mock(spec=ConfigManager)
        config.get.side_effect = lambda key, default=None: {
            # 通用配置
            'general.data_dir': './test_data',
            'general.log_level': 'INFO',
            
            # API层配置
            'api.host': '127.0.0.1',
            'api.port': 8000,
            'api.cors_origins': ['*'],
            
            # 业务层配置
            'processing.batch_size': 16,
            'processing.max_concurrent_tasks': 4,
            
            # AI推理层配置
            'embedding.models_dir': './data/models',
            'embedding.models.clip': 'clip',
            'embedding.models.clap': 'clap',
            'embedding.models.whisper': 'whisper',
            
            # 存储层配置
            'storage.qdrant.host': 'localhost',
            'storage.qdrant.port': 6333,
            'storage.sqlite.path': './test_data/msearch.db',
            
            # 设备配置
            'device': 'cpu'
        }.get(key, default)
        return config
    
    @pytest.fixture
    def mock_storage_layer(self):
        """模拟存储层"""
        qdrant_client = Mock(spec=QdrantClient)
        sqlite_manager = Mock(spec=SQLiteManager)
        
        # 设置Qdrant客户端mock
        qdrant_client.search_vectors.return_value = [
            {'id': 'vector_1', 'score': 0.95, 'payload': {'file_id': 'file_1', 'timestamp': 10.5}},
            {'id': 'vector_2', 'score': 0.88, 'payload': {'file_id': 'file_2', 'timestamp': 25.2}},
        ]
        qdrant_client.insert_vectors.return_value = True
        
        # 设置SQLite管理器mock
        sqlite_manager.get_file_metadata.return_value = {
            'file_id': 'file_1',
            'file_path': '/data/test.mp4',
            'file_type': 'video',
            'duration': 60.0
        }
        sqlite_manager.insert_file_metadata.return_value = True
        
        return {
            'qdrant_client': qdrant_client,
            'sqlite_manager': sqlite_manager
        }
    
    @pytest.fixture
    def mock_ai_inference_layer(self):
        """模拟AI推理层"""
        with patch('src.business.embedding_engine.AsyncEngineArray') as mock_engine_array:
            mock_engine = AsyncMock()
            mock_engine_array.from_args.return_value = mock_engine
            
            # 设置不同模型的返回值
            mock_engine.embed.return_value = [np.random.rand(512).tolist()]
            
            yield mock_engine
    
    @pytest.mark.asyncio
    async def test_data_flow_through_layers(self, layered_config, mock_storage_layer, mock_ai_inference_layer):
        """测试数据在各层间的流转"""
        # 创建各层实例
        embedding_engine = EmbeddingEngine(config=layered_config)
        orchestrator = ProcessingOrchestrator(config=layered_config)
        
        # 注入模拟的存储层
        orchestrator.qdrant_client = mock_storage_layer['qdrant_client']
        orchestrator.sqlite_manager = mock_storage_layer['sqlite_manager']
        orchestrator.embedding_engine = embedding_engine
        
        # 模拟从UI层到API层的请求
        test_file_path = "/data/test_video.mp4"
        
        # 模拟媒体处理器返回
        with patch.object(orchestrator, 'media_processor') as mock_media_processor:
            mock_media_processor.process_video.return_value = {
                'visual_frames': [
                    {'frame_data': np.random.rand(224, 224, 3), 'timestamp': 5.0},
                    {'frame_data': np.random.rand(224, 224, 3), 'timestamp': 10.0},
                ],
                'audio_segments': [
                    {'audio_data': np.random.rand(16000), 'start_time': 0.0, 'end_time': 10.0, 'type': 'music'},
                ],
                'metadata': {'duration': 30.0, 'fps': 30.0}
            }
            
            # 执行完整的数据流转
            result = await orchestrator.process_file(test_file_path)
            
            # 验证数据流转
            # 1. 业务层 -> AI推理层
            mock_ai_inference_layer.embed.assert_called()
            
            # 2. AI推理层 -> 存储层
            mock_storage_layer['qdrant_client'].insert_vectors.assert_called()
            mock_storage_layer['sqlite_manager'].insert_file_metadata.assert_called()
            
            # 3. 验证最终结果
            assert result['status'] == 'success'
            assert 'visual_vectors' in result
            assert 'audio_vectors' in result
    
    def test_layer_isolation_and_boundaries(self, layered_config):
        """测试层间隔离和边界"""
        # 测试各层的职责边界
        
        # 1. API层不应直接调用存储层
        from src.api.routes.search import router as search_router
        
        # 检查API路由中不应该直接导入存储层组件
        import inspect
        source = inspect.getsource(search_router)
        assert 'from src.storage' not in source, "API层不应直接导入存储层"
        
        # 2. 业务层不应直接处理HTTP请求
        from src.business.processing_orchestrator import ProcessingOrchestrator
        
        # 检查业务层不应该导入FastAPI相关组件
        orchestrator_source = inspect.getsource(ProcessingOrchestrator)
        assert 'from fastapi' not in orchestrator_source, "业务层不应直接导入FastAPI"
        
        # 3. 存储层不应包含业务逻辑
        from src.storage.qdrant_client import QdrantClient
        
        # 检查存储层只包含数据操作方法
        qdrant_methods = [method for method in dir(QdrantClient) if not method.startswith('_')]
        business_keywords = ['process', 'analyze', 'recognize', 'classify']
        
        for method in qdrant_methods:
            for keyword in business_keywords:
                assert keyword not in method.lower(), f"存储层方法 {method} 包含业务逻辑关键词"
    
    @pytest.mark.asyncio
    async def test_error_handling_across_layers(self, layered_config, mock_storage_layer):
        """测试错误在各层间的处理"""
        orchestrator = ProcessingOrchestrator(config=layered_config)
        orchestrator.qdrant_client = mock_storage_layer['qdrant_client']
        orchestrator.sqlite_manager = mock_storage_layer['sqlite_manager']
        
        # 模拟存储层错误
        mock_storage_layer['qdrant_client'].insert_vectors.side_effect = Exception("存储层错误")
        
        # 模拟媒体处理器
        with patch.object(orchestrator, 'media_processor') as mock_media_processor:
            mock_media_processor.process_video.return_value = {
                'visual_frames': [{'frame_data': np.random.rand(224, 224, 3), 'timestamp': 5.0}],
                'audio_segments': [],
                'metadata': {'duration': 10.0, 'fps': 30.0}
            }
            
            # 模拟AI推理层
            with patch.object(orchestrator, 'embedding_engine') as mock_embedding_engine:
                mock_embedding_engine.embed_content.return_value = [np.random.rand(512).tolist()]
                
                # 执行处理，应该捕获存储层错误
                result = await orchestrator.process_file("/data/error_test.mp4")
                
                # 验证错误被正确处理和传播
                assert result['status'] == 'error'
                assert '存储层错误' in result['error_message']
                assert result['error_layer'] == 'storage'
    
    def test_configuration_propagation(self, layered_config):
        """测试配置在各层间的传播"""
        # 创建各层实例
        embedding_engine = EmbeddingEngine(config=layered_config)
        orchestrator = ProcessingOrchestrator(config=layered_config)
        qdrant_client = QdrantClient(config=layered_config)
        sqlite_manager = SQLiteManager(config=layered_config)
        
        # 验证配置正确传播到各层
        
        # 1. 验证AI推理层配置
        assert embedding_engine.config == layered_config
        
        # 2. 验证业务层配置
        assert orchestrator.config == layered_config
        
        # 3. 验证存储层配置
        assert qdrant_client.config == layered_config
        assert sqlite_manager.config == layered_config
        
        # 4. 验证配置值被正确读取
        assert layered_config.get.call_count > 0  # 确保配置被访问
    
    @pytest.mark.asyncio
    async def test_async_processing_coordination(self, layered_config, mock_storage_layer, mock_ai_inference_layer):
        """测试异步处理在各层间的协调"""
        orchestrator = ProcessingOrchestrator(config=layered_config)
        orchestrator.qdrant_client = mock_storage_layer['qdrant_client']
        orchestrator.sqlite_manager = mock_storage_layer['sqlite_manager']
        
        # 创建多个异步任务
        tasks = []
        for i in range(5):
            with patch.object(orchestrator, 'media_processor') as mock_media_processor:
                mock_media_processor.process_video.return_value = {
                    'visual_frames': [{'frame_data': np.random.rand(224, 224, 3), 'timestamp': i * 2.0}],
                    'audio_segments': [],
                    'metadata': {'duration': 10.0, 'fps': 30.0}
                }
                
                task = orchestrator.process_file(f"/data/async_test_{i}.mp4")
                tasks.append(task)
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证异步协调结果
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 3  # 至少60%成功率
        
        # 验证各层的异步调用
        assert mock_ai_inference_layer.embed.call_count >= 3
        assert mock_storage_layer['qdrant_client'].insert_vectors.call_count >= 3
    
    def test_dependency_injection_pattern(self, layered_config):
        """测试依赖注入模式"""
        # 创建业务层实例
        orchestrator = ProcessingOrchestrator(config=layered_config)
        
        # 验证依赖注入接口
        assert hasattr(orchestrator, 'set_embedding_engine')
        assert hasattr(orchestrator, 'set_storage_clients')
        
        # 测试依赖注入
        mock_embedding_engine = Mock()
        mock_qdrant_client = Mock()
        mock_sqlite_manager = Mock()
        
        orchestrator.set_embedding_engine(mock_embedding_engine)
        orchestrator.set_storage_clients(mock_qdrant_client, mock_sqlite_manager)
        
        # 验证依赖被正确注入
        assert orchestrator.embedding_engine == mock_embedding_engine
        assert orchestrator.qdrant_client == mock_qdrant_client
        assert orchestrator.sqlite_manager == mock_sqlite_manager
    
    def test_interface_contracts(self, layered_config):
        """测试接口契约"""
        # 验证各层接口的一致性
        
        # 1. 存储层接口契约
        qdrant_client = QdrantClient(config=layered_config)
        sqlite_manager = SQLiteManager(config=layered_config)
        
        # 验证存储层必需方法
        required_qdrant_methods = ['search_vectors', 'insert_vectors', 'delete_vectors', 'create_collection']
        for method in required_qdrant_methods:
            assert hasattr(qdrant_client, method), f"QdrantClient缺少必需方法: {method}"
        
        required_sqlite_methods = ['get_file_metadata', 'insert_file_metadata', 'update_file_metadata', 'delete_file_metadata']
        for method in required_sqlite_methods:
            assert hasattr(sqlite_manager, method), f"SQLiteManager缺少必需方法: {method}"
        
        # 2. AI推理层接口契约
        embedding_engine = EmbeddingEngine(config=layered_config)
        
        required_embedding_methods = ['embed_image', 'embed_audio', 'embed_text', 'embed_content']
        for method in required_embedding_methods:
            assert hasattr(embedding_engine, method), f"EmbeddingEngine缺少必需方法: {method}"
        
        # 3. 业务层接口契约
        orchestrator = ProcessingOrchestrator(config=layered_config)
        
        required_orchestrator_methods = ['process_file', 'process_batch', 'get_processing_status']
        for method in required_orchestrator_methods:
            assert hasattr(orchestrator, method), f"ProcessingOrchestrator缺少必需方法: {method}"


class TestLayeredArchitecturePerformance:
    """分层架构性能测试"""
    
    @pytest.mark.asyncio
    async def test_layer_communication_overhead(self, layered_config):
        """测试层间通信开销"""
        import time
        
        # 创建完整的分层架构
        orchestrator = ProcessingOrchestrator(config=layered_config)
        
        # 模拟各层组件
        with patch.object(orchestrator, 'media_processor') as mock_media_processor, \
             patch.object(orchestrator, 'embedding_engine') as mock_embedding_engine, \
             patch.object(orchestrator, 'qdrant_client') as mock_qdrant_client, \
             patch.object(orchestrator, 'sqlite_manager') as mock_sqlite_manager:
            
            # 设置快速响应的mock
            mock_media_processor.process_video.return_value = {
                'visual_frames': [{'frame_data': np.random.rand(224, 224, 3), 'timestamp': 5.0}],
                'audio_segments': [],
                'metadata': {'duration': 10.0, 'fps': 30.0}
            }
            
            mock_embedding_engine.embed_content.return_value = [np.random.rand(512).tolist()]
            mock_qdrant_client.insert_vectors.return_value = True
            mock_sqlite_manager.insert_file_metadata.return_value = True
            
            # 测试层间通信性能
            start_time = time.time()
            
            result = await orchestrator.process_file("/data/performance_test.mp4")
            
            end_time = time.time()
            communication_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            # 验证层间通信开销在合理范围内
            assert communication_time < 50, f"层间通信开销过大: {communication_time}ms"
            assert result['status'] == 'success'
    
    @pytest.mark.asyncio
    async def test_concurrent_layer_access(self, layered_config):
        """测试并发层访问性能"""
        orchestrator = ProcessingOrchestrator(config=layered_config)
        
        # 模拟高并发访问
        with patch.object(orchestrator, 'embedding_engine') as mock_embedding_engine:
            mock_embedding_engine.embed_content.return_value = [np.random.rand(512).tolist()]
            
            # 创建大量并发任务
            tasks = []
            for i in range(20):  # 20个并发任务
                task = orchestrator.embedding_engine.embed_content(
                    np.random.rand(224, 224, 3), 'image'
                )
                tasks.append(task)
            
            # 执行并发访问
            import time
            start_time = time.time()
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            concurrent_time = (end_time - start_time) * 1000
            
            # 验证并发性能
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) >= 18  # 90%成功率
            assert concurrent_time < 200, f"并发访问时间过长: {concurrent_time}ms"
    
    def test_memory_usage_across_layers(self, layered_config):
        """测试各层内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        # 创建各层实例
        embedding_engine = EmbeddingEngine(config=layered_config)
        orchestrator = ProcessingOrchestrator(config=layered_config)
        qdrant_client = QdrantClient(config=layered_config)
        sqlite_manager = SQLiteManager(config=layered_config)
        
        # 模拟各层操作
        with patch('src.business.embedding_engine.AsyncEngineArray'):
            # 模拟一些操作
            for i in range(10):
                _ = orchestrator.get_processing_status()
                _ = qdrant_client.get_collection_info("test_collection")
                _ = sqlite_manager.get_connection_info()
        
        final_memory = process.memory_info().rss / (1024 * 1024)  # MB
        memory_increase = final_memory - initial_memory
        
        # 验证内存使用在合理范围内
        assert memory_increase < 100, f"分层架构内存增长过多: {memory_increase}MB"