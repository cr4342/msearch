"""
端到端集成测试
验证完整的多模态检索工作流程
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import tempfile
import os
import json
from pathlib import Path

from src.api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

class TestEndToEndWorkflow:
    """端到端工作流程测试"""
    
    def test_complete_text_search_workflow(self):
        """测试完整的文本搜索工作流程"""
        # 准备测试数据
        search_query = "机器学习算法"
        
        # 模拟处理编排器返回结果
        with patch('src.business.orchestrator.ProcessingOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = MagicMock()
            mock_orchestrator.process_file = AsyncMock(return_value={
                'file_id': 'file_123',
                'status': 'completed',
                'processing_time': 0.5
            })
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # 模拟智能检索引擎返回结果
            with patch('src.business.smart_retrieval.SmartRetrievalEngine') as mock_retrieval_class:
                mock_retrieval = MagicMock()
                mock_retrieval.search = AsyncMock(return_value={
                    'results': [
                        {
                            'file_id': 'file_123',
                            'file_path': '/test/documents/ml_notes.txt',
                            'content_preview': '机器学习算法是人工智能...',
                            'score': 0.95,
                            'file_type': 'text'
                        }
                    ],
                    'query_type': 'text',
                    'processing_time': 0.1
                })
                mock_retrieval_class.return_value = mock_retrieval
                
                # 发送搜索请求
                response = client.post(
                    "/api/v1/search/text",
                    json={"query": search_query, "limit": 10}
                )
                
                # 验证响应
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["status"] == "success"
                assert response_data["query"] == search_query
                assert len(response_data["results"]) == 1
                assert response_data["results"][0]["score"] == 0.95
                
                # 验证调用了正确的组件
                mock_retrieval.search.assert_called_once_with(search_query, search_type="text")
    
    def test_complete_image_search_workflow(self):
        """测试完整的图像搜索工作流程"""
        # 准备测试图像数据
        test_image_content = b"fake image data for testing"
        
        # 模拟处理编排器返回结果
        with patch('src.business.orchestrator.ProcessingOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = MagicMock()
            mock_orchestrator.process_file = AsyncMock(return_value={
                'file_id': 'image_123',
                'status': 'completed',
                'processing_time': 0.3
            })
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # 模拟智能检索引擎返回结果
            with patch('src.business.smart_retrieval.SmartRetrievalEngine') as mock_retrieval_class:
                mock_retrieval = MagicMock()
                mock_retrieval.search = AsyncMock(return_value={
                    'results': [
                        {
                            'file_id': 'image_123',
                            'file_path': '/test/images/sample.jpg',
                            'preview_url': '/api/v1/files/image_123/thumb',
                            'score': 0.88,
                            'file_type': 'image'
                        }
                    ],
                    'query_type': 'image_to_image',
                    'processing_time': 0.15
                })
                mock_retrieval_class.return_value = mock_retrieval
                
                # 发送图像搜索请求
                response = client.post(
                    "/api/v1/search/image",
                    files={"file": ("test.jpg", test_image_content, "image/jpeg")},
                    data={"limit": "10"}
                )
                
                # 验证响应
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["status"] == "success"
                assert "sample.jpg" in response_data["results"][0]["file_path"]
                assert response_data["results"][0]["score"] == 0.88
                
                # 验证调用了正确的组件
                mock_retrieval.search.assert_called_once()
    
    def test_complete_video_processing_and_search_workflow(self):
        """测试完整的视频处理和搜索工作流程"""
        # 准备测试视频文件
        test_video_content = b"fake video data for testing"
        
        # 模拟文件类型检测器
        with patch('src.core.file_type_detector.FileTypeDetector') as mock_detector_class:
            mock_detector = MagicMock()
            mock_detector.detect_file_type = Mock(return_value={
                'type': 'video',
                'subtype': 'mp4',
                'mime_type': 'video/mp4'
            })
            mock_detector_class.return_value = mock_detector
            
            # 模拟处理编排器
            with patch('src.business.orchestrator.ProcessingOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = MagicMock()
                mock_orchestrator.process_file = AsyncMock(return_value={
                    'file_id': 'video_123',
                    'status': 'completed',
                    'processing_time': 2.5,
                    'segments': [
                        {
                            'segment_id': 'seg_1',
                            'start_time': 0.0,
                            'end_time': 30.0,
                            'frame_count': 900,
                            'vectors_stored': 45
                        }
                    ]
                })
                mock_orchestrator_class.return_value = mock_orchestrator
                
                # 模拟时间戳处理器
                with patch('src.processors.timestamp_processor.TimestampProcessor') as mock_timestamp_class:
                    mock_timestamp = MagicMock()
                    mock_timestamp.create_scene_aware_segments = Mock(return_value=[
                        {
                            'segment_id': 'seg_1',
                            'start_frame': 0,
                            'end_frame': 900,
                            'start_time': 0.0,
                            'end_time': 30.0
                        }
                    ])
                    mock_timestamp_class.return_value = mock_timestamp
                    
                    # 创建临时文件进行测试
                    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
                        tmp_file.write(test_video_content)
                        tmp_file_path = tmp_file.name
                    
                    try:
                        # 发送文件处理请求
                        with open(tmp_file_path, 'rb') as video_file:
                            files = {"file": ("test.mp4", video_file, "video/mp4")}
                            response = client.post(
                                "/api/v1/files/process",
                                files=files,
                                data={"file_path": tmp_file_path, "file_id": 1}
                            )
                        
                        # 验证处理响应
                        assert response.status_code == 200
                        response_data = response.json()
                        assert response_data["success"] is True
                        assert response_data["data"]["status"] == "completed"
                        
                        # 验证调用了正确的组件
                        mock_detector.detect_file_type.assert_called()
                        mock_orchestrator.process_file.assert_called()
                        mock_timestamp.create_scene_aware_segments.assert_called()
                        
                    finally:
                        # 清理临时文件
                        os.unlink(tmp_file_path)
    
    def test_complete_multimodal_search_with_face_recognition(self):
        """测试包含人脸识别的完整多模态搜索工作流程"""
        # 准备搜索查询
        search_query = "张三在会议上发言"
        
        # 模拟智能检索引擎
        with patch('src.business.smart_retrieval.SmartRetrievalEngine') as mock_retrieval_class:
            mock_retrieval = MagicMock()
            mock_retrieval.search = AsyncMock(return_value={
                'results': [
                    {
                        'file_id': 'video_123',
                        'file_path': '/test/videos/meeting.mp4',
                        'timestamp': 120.5,
                        'score': 0.92,
                        'file_type': 'video',
                        'persons_detected': ['张三'],
                        'confidence': 0.88
                    }
                ],
                'query_type': 'smart',
                'processing_time': 0.25
            })
            mock_retrieval_class.return_value = mock_retrieval
            
            # 模拟人脸管理器
            with patch('src.business.face_manager.FaceManager') as mock_face_class:
                mock_face_manager = MagicMock()
                mock_face_manager.search_faces = AsyncMock(return_value=[
                    {
                        'file_id': 'video_123',
                        'timestamp': 120.5,
                        'person_name': '张三',
                        'confidence': 0.88
                    }
                ])
                mock_face_manager.get_all_persons = AsyncMock(return_value=[
                    {'id': 'person_123', 'name': '张三', 'aliases': ['小张']}
                ])
                mock_face_class.return_value = mock_face_manager
                
                # 发送智能搜索请求
                response = client.post(
                    "/api/v1/search/smart",
                    json={"query": search_query, "limit": 10}
                )
                
                # 验证响应
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["status"] == "success"
                assert response_data["query"] == search_query
                assert len(response_data["results"]) == 1
                assert response_data["results"][0]["persons_detected"] == ['张三']
                assert response_data["results"][0]["score"] == 0.92
                
                # 验证调用了正确的组件
                mock_retrieval.search.assert_called_once_with(search_query, search_type="smart")
                mock_face_manager.search_faces.assert_called()
    
    def test_system_health_and_performance_monitoring(self):
        """测试系统健康检查和性能监控"""
        # 发送健康检查请求
        response = client.get("/health")
        
        # 验证健康检查响应
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["message"] == "服务运行正常"
        assert "data" in response_data
        assert "status" in response_data["data"]
        assert response_data["data"]["status"] == "healthy"
        
        # 发送系统状态请求
        response = client.get("/api/v1/system/status")
        
        # 验证系统状态响应
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "cpu_usage" in response_data["data"]
        assert "memory_usage" in response_data["data"]
        
        # 发送数据库状态请求
        response = client.get("/api/v1/system/db-status")
        
        # 验证数据库状态响应
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "sqlite_connected" in response_data["data"]
        assert "qdrant_connected" in response_data["data"]
    
    def test_configuration_management_workflow(self):
        """测试配置管理完整工作流程"""
        # 获取当前配置
        response = client.get("/api/v1/config")
        
        # 验证配置获取响应
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        
        # 准备配置更新数据
        config_updates = {
            "processing": {
                "batch_size": 8,
                "max_concurrent_tasks": 4
            }
        }
        
        # 更新配置
        response = client.put(
            "/api/v1/config",
            json=config_updates
        )
        
        # 验证配置更新响应
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["message"] == "配置更新成功"
        
        # 验证配置已更新
        response = client.get("/api/v1/config")
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["data"]["processing"]["batch_size"] == 8
        assert response_data["data"]["processing"]["max_concurrent_tasks"] == 4