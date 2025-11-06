"""
人脸API路由单元测试
测试人脸管理API的各个端点
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json
from fastapi.testclient import TestClient

from src.api.main import app
from src.business.face_manager import FaceManager

client = TestClient(app)

class TestFaceAPI:
    """人脸API路由测试"""
    
    @pytest.fixture
    def mock_face_manager(self):
        """Mock人脸管理器"""
        with patch('src.api.routes.face.face_manager') as mock_face_manager:
            mock_face_manager.add_person = AsyncMock(return_value="person_123")
            mock_face_manager.get_all_persons = AsyncMock(return_value=[])
            mock_face_manager.delete_person = AsyncMock(return_value=None)
            mock_face_manager.search_faces = AsyncMock(return_value=[])
            mock_face_manager.get_status = AsyncMock(return_value={"total_persons": 0})
            mock_face_manager.recognize_faces_in_file = AsyncMock(return_value=[])
            yield mock_face_manager
    
    def test_add_person_success(self, mock_face_manager):
        """测试成功添加人员"""
        # 准备测试数据
        test_data = {
            "name": "张三",
            "aliases": "小张,张总",
            "description": "测试人员"
        }
        
        # 模拟文件上传
        test_file = ("test.jpg", b"fake image data", "image/jpeg")
        
        # 发送POST请求
        response = client.post(
            "/api/v1/faces/persons",
            data=test_data,
            files={"images": test_file}
        )
        
        # 验证响应
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["person_id"] == "person_123"
        assert "成功添加人员" in response_data["message"]
        
        # 验证调用了add_person方法
        mock_face_manager.add_person.assert_called_once()
    
    def test_get_persons_success(self, mock_face_manager):
        """测试获取所有人脸库信息"""
        # 设置mock返回值
        mock_face_manager.get_all_persons = AsyncMock(return_value=[
            {
                "id": "person_123",
                "name": "张三",
                "aliases": ["小张", "张总"],
                "description": "测试人员"
            }
        ])
        
        # 发送GET请求
        response = client.get("/api/v1/faces/persons")
        
        # 验证响应
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert len(response_data["persons"]) == 1
        assert response_data["persons"][0]["name"] == "张三"
    
    def test_delete_person_success(self, mock_face_manager):
        """测试成功删除人员"""
        # 发送DELETE请求
        response = client.delete("/api/v1/faces/persons/person_123")
        
        # 验证响应
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert "成功删除人员" in response_data["message"]
        
        # 验证调用了delete_person方法
        mock_face_manager.delete_person.assert_called_once_with("person_123")
    
    def test_search_by_face_success(self, mock_face_manager):
        """测试人脸搜索成功"""
        # 设置mock返回值
        mock_face_manager.search_faces = AsyncMock(return_value=[
            {
                "file_id": "file_123",
                "person_name": "张三",
                "confidence": 0.95,
                "timestamp": 10.5
            }
        ])
        
        # 准备请求数据
        search_data = {
            "query": "张三",
            "top_k": 10,
            "threshold": 0.7
        }
        
        # 发送POST请求
        response = client.post("/api/v1/search/face", json=search_data)
        
        # 验证响应
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert len(response_data["results"]) == 1
        assert response_data["results"][0]["person_name"] == "张三"
        assert response_data["query_type"] == "face_search"
    
    def test_get_face_status_success(self, mock_face_manager):
        """测试获取人脸库状态成功"""
        # 设置mock返回值
        mock_face_manager.get_status = AsyncMock(return_value={
            "total_persons": 5,
            "total_faces": 12,
            "last_updated": "2023-01-01T00:00:00"
        })
        
        # 发送GET请求
        response = client.get("/api/v1/faces/status")
        
        # 验证响应
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["status"]["total_persons"] == 5
        assert response_data["status"]["total_faces"] == 12
    
    def test_recognize_faces_in_file_success(self, mock_face_manager):
        """测试识别人脸文件中的所有人脸成功"""
        # 设置mock返回值
        mock_face_manager.recognize_faces_in_file = AsyncMock(return_value=[
            {
                "bbox": [10, 20, 50, 60],
                "person_name": "张三",
                "confidence": 0.92
            }
        ])
        
        # 准备测试文件
        test_file = ("test.jpg", b"fake image data", "image/jpeg")
        
        # 发送POST请求
        response = client.post(
            "/api/v1/faces/recognize",
            files={"file": test_file}
        )
        
        # 验证响应
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert len(response_data["recognized_faces"]) == 1
        assert response_data["recognized_faces"][0]["person_name"] == "张三"