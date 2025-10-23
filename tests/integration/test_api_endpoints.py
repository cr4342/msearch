"""
API端点集成测试
测试FastAPI服务层与业务逻辑层的集成
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json
import numpy as np

from src.api.main import app
from src.core.config_manager import ConfigManager


class TestAPIEndpoints:
    """API端点功能测试"""
    
    @pytest.fixture
    def test_client(self):
        """测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_search_engine(self):
        """模拟搜索引擎"""
        with patch('src.api.routes.search.SmartRetrievalEngine') as mock_engine:
            mock_instance = AsyncMock()
            mock_engine.return_value = mock_instance
            
            # 设置默认返回值
            mock_instance.smart_search.return_value = [
                {
                    'file_id': 'test_file_1',
                    'file_path': '/data/videos/test1.mp4',
                    'score': 0.95,
                    'timestamp': 10.5,
                    'duration': 2.0,
                    'modality': 'visual'
                },
                {
                    'file_id': 'test_file_2',
                    'file_path': '/data/images/test2.jpg',
                    'score': 0.88,
                    'timestamp': None,
                    'duration': None,
                    'modality': 'visual'
                }
            ]
            
            yield mock_instance
    
    @pytest.fixture
    def mock_processing_orchestrator(self):
        """模拟处理编排器"""
        with patch('src.api.routes.tasks.ProcessingOrchestrator') as mock_orchestrator:
            mock_instance = AsyncMock()
            mock_orchestrator.return_value = mock_instance
            
            # 设置默认返回值
            mock_instance.process_file.return_value = {
                'status': 'success',
                'file_id': 'test_file_123',
                'processing_time': 5.2,
                'visual_vectors': 10,
                'audio_vectors': 5
            }
            
            yield mock_instance
    
    def test_search_endpoint_text_query(self, test_client, mock_search_engine):
        """测试文本搜索端点"""
        # 发送文本搜索请求
        response = test_client.post(
            "/api/search",
            json={
                "query": "美丽的风景",
                "query_type": "text",
                "top_k": 10,
                "modality": "visual"
            }
        )
        
        # 验证响应
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "success"
        assert "results" in result
        assert len(result["results"]) == 2
        
        # 验证结果格式
        for item in result["results"]:
            assert "file_id" in item
            assert "file_path" in item
            assert "score" in item
            assert "modality" in item
        
        # 验证搜索引擎被正确调用
        mock_search_engine.smart_search.assert_called_once_with("美丽的风景")
    
    def test_search_endpoint_person_query(self, test_client, mock_search_engine):
        """测试人名搜索端点"""
        # 设置人名搜索的返回值
        mock_search_engine.smart_search.return_value = [
            {
                'file_id': 'person_file_1',
                'file_path': '/data/videos/person1.mp4',
                'score': 0.92,
                'timestamp': 25.3,
                'duration': 1.8,
                'modality': 'face',
                'person_name': '张三'
            }
        ]
        
        # 发送人名搜索请求
        response = test_client.post(
            "/api/search",
            json={
                "query": "张三在做什么",
                "query_type": "person",
                "top_k": 5
            }
        )
        
        # 验证响应
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "success"
        assert len(result["results"]) == 1
        
        # 验证人名搜索特有字段
        person_result = result["results"][0]
        assert person_result["modality"] == "face"
        assert person_result["person_name"] == "张三"
        assert person_result["timestamp"] == 25.3
    
    def test_search_endpoint_multimodal_query(self, test_client, mock_search_engine):
        """测试多模态搜索端点"""
        # 设置多模态搜索返回值
        mock_search_engine.smart_search.return_value = [
            {
                'file_id': 'multimodal_file_1',
                'file_path': '/data/videos/multimodal1.mp4',
                'score': 0.89,
                'timestamp': 15.7,
                'duration': 2.5,
                'modality': 'multimodal',
                'modality_scores': {
                    'visual': 0.85,
                    'audio': 0.78,
                    'text': 0.92
                }
            }
        ]
        
        # 发送多模态搜索请求
        response = test_client.post(
            "/api/search",
            json={
                "query": "科比正在投篮",
                "query_type": "multimodal",
                "top_k": 10,
                "include_modality_scores": True
            }
        )
        
        # 验证响应
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "success"
        
        # 验证多模态搜索特有字段
        multimodal_result = result["results"][0]
        assert "modality_scores" in multimodal_result
        assert "visual" in multimodal_result["modality_scores"]
        assert "audio" in multimodal_result["modality_scores"]
        assert "text" in multimodal_result["modality_scores"]
    
    def test_search_endpoint_error_handling(self, test_client, mock_search_engine):
        """测试搜索端点错误处理"""
        # 模拟搜索引擎抛出异常
        mock_search_engine.smart_search.side_effect = Exception("搜索引擎错误")
        
        # 发送搜索请求
        response = test_client.post(
            "/api/search",
            json={
                "query": "测试查询",
                "query_type": "text"
            }
        )
        
        # 验证错误响应
        assert response.status_code == 500
        
        result = response.json()
        assert result["status"] == "error"
        assert "error_message" in result
        assert "搜索引擎错误" in result["error_message"]
    
    def test_search_endpoint_validation(self, test_client):
        """测试搜索端点参数验证"""
        # 测试缺少必需参数
        response = test_client.post(
            "/api/search",
            json={}
        )
        
        assert response.status_code == 422  # Validation Error
        
        # 测试无效参数类型
        response = test_client.post(
            "/api/search",
            json={
                "query": 123,  # 应该是字符串
                "top_k": "invalid"  # 应该是整数
            }
        )
        
        assert response.status_code == 422
    
    def test_tasks_start_endpoint(self, test_client, mock_processing_orchestrator):
        """测试任务启动端点"""
        # 发送任务启动请求
        response = test_client.post(
            "/api/tasks/start",
            json={
                "task_type": "process_files",
                "file_paths": ["/data/videos/test.mp4", "/data/images/test.jpg"],
                "options": {
                    "batch_size": 8,
                    "enable_face_recognition": True
                }
            }
        )
        
        # 验证响应
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "success"
        assert "task_id" in result
        assert result["message"] == "任务已启动"
    
    def test_tasks_stop_endpoint(self, test_client):
        """测试任务停止端点"""
        # 发送任务停止请求
        response = test_client.post(
            "/api/tasks/stop",
            json={
                "task_id": "test_task_123"
            }
        )
        
        # 验证响应
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "success"
        assert result["message"] == "任务已停止"
    
    def test_status_endpoint(self, test_client):
        """测试系统状态端点"""
        with patch('src.api.routes.status.get_system_status') as mock_status:
            mock_status.return_value = {
                'system_health': 'healthy',
                'processing_queue': {
                    'pending_tasks': 5,
                    'active_tasks': 2,
                    'completed_tasks': 100
                },
                'storage_info': {
                    'total_files': 1500,
                    'total_vectors': 15000,
                    'database_size': '2.5GB'
                },
                'performance_metrics': {
                    'avg_processing_time': 3.2,
                    'search_response_time': 0.15,
                    'memory_usage': '4.2GB'
                }
            }
            
            # 发送状态查询请求
            response = test_client.get("/api/status")
            
            # 验证响应
            assert response.status_code == 200
            
            result = response.json()
            assert result["status"] == "success"
            assert "system_health" in result["data"]
            assert "processing_queue" in result["data"]
            assert "storage_info" in result["data"]
            assert "performance_metrics" in result["data"]
    
    def test_config_get_endpoint(self, test_client):
        """测试配置获取端点"""
        with patch('src.api.routes.config.ConfigManager') as mock_config_manager:
            mock_instance = Mock()
            mock_config_manager.return_value = mock_instance
            
            mock_instance.get_all_config.return_value = {
                'general': {
                    'log_level': 'INFO',
                    'data_dir': './data'
                },
                'processing': {
                    'batch_size': 16,
                    'max_concurrent_tasks': 4
                },
                'features': {
                    'enable_face_recognition': True,
                    'enable_audio_processing': True
                }
            }
            
            # 发送配置获取请求
            response = test_client.get("/api/config")
            
            # 验证响应
            assert response.status_code == 200
            
            result = response.json()
            assert result["status"] == "success"
            assert "general" in result["config"]
            assert "processing" in result["config"]
            assert "features" in result["config"]
    
    def test_config_update_endpoint(self, test_client):
        """测试配置更新端点"""
        with patch('src.api.routes.config.ConfigManager') as mock_config_manager:
            mock_instance = Mock()
            mock_config_manager.return_value = mock_instance
            
            mock_instance.update_config.return_value = True
            
            # 发送配置更新请求
            response = test_client.put(
                "/api/config",
                json={
                    "processing.batch_size": 32,
                    "features.enable_face_recognition": False,
                    "general.log_level": "DEBUG"
                }
            )
            
            # 验证响应
            assert response.status_code == 200
            
            result = response.json()
            assert result["status"] == "success"
            assert result["message"] == "配置已更新"
            
            # 验证配置管理器被正确调用
            mock_instance.update_config.assert_called_once()


class TestAPIIntegration:
    """API集成测试"""
    
    @pytest.fixture
    def integration_client(self):
        """集成测试客户端"""
        return TestClient(app)
    
    def test_search_to_processing_integration(self, integration_client):
        """测试搜索到处理的集成流程"""
        with patch('src.api.routes.search.SmartRetrievalEngine') as mock_search, \
             patch('src.api.routes.tasks.ProcessingOrchestrator') as mock_orchestrator:
            
            # 设置搜索引擎mock
            mock_search_instance = AsyncMock()
            mock_search.return_value = mock_search_instance
            mock_search_instance.smart_search.return_value = [
                {
                    'file_id': 'integration_file_1',
                    'file_path': '/data/videos/integration1.mp4',
                    'score': 0.90,
                    'timestamp': 30.5,
                    'needs_reprocessing': True
                }
            ]
            
            # 设置处理编排器mock
            mock_orchestrator_instance = AsyncMock()
            mock_orchestrator.return_value = mock_orchestrator_instance
            mock_orchestrator_instance.process_file.return_value = {
                'status': 'success',
                'file_id': 'integration_file_1',
                'updated_vectors': 15
            }
            
            # 1. 执行搜索
            search_response = integration_client.post(
                "/api/search",
                json={"query": "需要重新处理的内容", "query_type": "text"}
            )
            
            assert search_response.status_code == 200
            search_result = search_response.json()
            
            # 2. 基于搜索结果触发重新处理
            file_to_reprocess = search_result["results"][0]["file_path"]
            
            process_response = integration_client.post(
                "/api/tasks/start",
                json={
                    "task_type": "reprocess_file",
                    "file_paths": [file_to_reprocess]
                }
            )
            
            assert process_response.status_code == 200
            process_result = process_response.json()
            
            # 验证集成流程
            assert search_result["status"] == "success"
            assert process_result["status"] == "success"
    
    def test_config_driven_api_behavior(self, integration_client):
        """测试配置驱动的API行为"""
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_instance = Mock()
            mock_config.return_value = mock_instance
            
            # 设置不同的配置场景
            test_scenarios = [
                {
                    'config': {
                        'api.search.max_results': 5,
                        'api.search.timeout_seconds': 10,
                        'features.enable_face_recognition': True
                    },
                    'expected_behavior': 'face_recognition_enabled'
                },
                {
                    'config': {
                        'api.search.max_results': 20,
                        'api.search.timeout_seconds': 30,
                        'features.enable_face_recognition': False
                    },
                    'expected_behavior': 'face_recognition_disabled'
                }
            ]
            
            for scenario in test_scenarios:
                # 设置配置
                mock_instance.get.side_effect = lambda key, default=None: scenario['config'].get(key, default)
                
                # 发送搜索请求
                response = integration_client.post(
                    "/api/search",
                    json={"query": "配置测试", "query_type": "text"}
                )
                
                # 验证配置驱动的行为
                assert response.status_code == 200
                
                # 根据配置验证不同的行为
                if scenario['expected_behavior'] == 'face_recognition_enabled':
                    # 验证人脸识别功能可用
                    face_response = integration_client.post(
                        "/api/search",
                        json={"query": "张三", "query_type": "person"}
                    )
                    assert face_response.status_code == 200
                
                elif scenario['expected_behavior'] == 'face_recognition_disabled':
                    # 验证人脸识别功能被禁用
                    face_response = integration_client.post(
                        "/api/search",
                        json={"query": "张三", "query_type": "person"}
                    )
                    # 应该返回功能禁用的响应
                    assert face_response.status_code == 400
    
    def test_error_propagation_across_layers(self, integration_client):
        """测试错误在各层间的传播"""
        with patch('src.business.smart_retrieval.SmartRetrievalEngine') as mock_engine:
            # 模拟业务层错误
            mock_instance = AsyncMock()
            mock_engine.return_value = mock_instance
            mock_instance.smart_search.side_effect = ValueError("业务逻辑错误")
            
            # 发送请求
            response = integration_client.post(
                "/api/search",
                json={"query": "错误测试", "query_type": "text"}
            )
            
            # 验证错误正确传播到API层
            assert response.status_code == 500
            
            result = response.json()
            assert result["status"] == "error"
            assert "业务逻辑错误" in result["error_message"]
            assert "error_type" in result
            assert result["error_type"] == "ValueError"
    
    def test_async_processing_integration(self, integration_client):
        """测试异步处理集成"""
        with patch('src.api.routes.tasks.ProcessingOrchestrator') as mock_orchestrator:
            mock_instance = AsyncMock()
            mock_orchestrator.return_value = mock_instance
            
            # 模拟长时间运行的异步任务
            async def long_running_task(*args, **kwargs):
                await asyncio.sleep(0.1)  # 模拟处理时间
                return {
                    'status': 'success',
                    'file_id': 'async_file_123',
                    'processing_time': 10.5
                }
            
            mock_instance.process_file.side_effect = long_running_task
            
            # 启动异步任务
            response = integration_client.post(
                "/api/tasks/start",
                json={
                    "task_type": "async_process",
                    "file_paths": ["/data/large_video.mp4"],
                    "async_mode": True
                }
            )
            
            # 验证异步任务启动
            assert response.status_code == 202  # Accepted
            
            result = response.json()
            assert result["status"] == "accepted"
            assert "task_id" in result
            
            # 查询任务状态
            task_id = result["task_id"]
            status_response = integration_client.get(f"/api/tasks/{task_id}/status")
            
            assert status_response.status_code == 200
            status_result = status_response.json()
            assert "task_status" in status_result