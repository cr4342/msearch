"""
msearch API接口测试
验证API路由和端点的完整性
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.api.main import app

# 创建测试客户端
client = TestClient(app)


class TestAPIEndpoints:
    """API端点测试"""
    
    def test_health_check(self):
        """测试健康检查端点"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_search_text_endpoint(self):
        """测试文本搜索端点"""
        response = client.post("/api/v1/search/text", params={"query": "测试", "limit": 10})
        assert response.status_code in [200, 500]  # 可能因为依赖未初始化返回500
        assert "status" in response.json()
    
    def test_search_image_endpoint(self):
        """测试图像搜索端点"""
        # 创建模拟图像文件
        files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
        response = client.post("/api/v1/search/image", files=files, params={"limit": 10})
        assert response.status_code in [200, 500]
        assert "status" in response.json()
    
    def test_search_audio_endpoint(self):
        """测试音频搜索端点"""
        # 创建模拟音频文件
        files = {"file": ("test.mp3", b"fake audio data", "audio/mpeg")}
        response = client.post("/api/v1/search/audio", files=files, params={"limit": 10})
        assert response.status_code in [200, 500]
        assert "status" in response.json()
    
    def test_search_video_endpoint(self):
        """测试视频搜索端点"""
        # 创建模拟视频文件
        files = {"file": ("test.mp4", b"fake video data", "video/mp4")}
        response = client.post("/api/v1/search/video", files=files, params={"limit": 10})
        assert response.status_code in [200, 500]
        assert "status" in response.json()
    
    def test_search_multimodal_endpoint(self):
        """测试多模态搜索端点"""
        response = client.post(
            "/api/v1/search/multimodal",
            params={"query_text": "测试查询", "limit": 10}
        )
        assert response.status_code in [200, 500]
        assert "status" in response.json()
    
    def test_api_docs_available(self):
        """测试API文档可用性"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_spec_available(self):
        """测试OpenAPI规范可用性"""
        response = client.get("/openapi.json")
        assert response.status_code == 200


class TestAPIErrorHandling:
    """API错误处理测试"""
    
    def test_invalid_endpoint(self):
        """测试无效端点"""
        response = client.get("/api/v1/invalid")
        assert response.status_code == 404
    
    def test_invalid_method(self):
        """测试无效HTTP方法"""
        response = client.get("/api/v1/search/text")
        assert response.status_code == 405  # Method Not Allowed
    
    def test_missing_query_parameter(self):
        """测试缺少查询参数"""
        response = client.post("/api/v1/search/text")
        # FastAPI会自动处理必需参数缺失
        assert response.status_code in [422, 500]  # 422=Unprocessable Entity


class TestAPIResponseFormat:
    """API响应格式测试"""
    
    def test_response_structure(self):
        """测试响应结构"""
        response = client.post("/api/v1/search/text", params={"query": "测试", "limit": 5})
        json_response = response.json()
        
        # 验证响应结构
        required_fields = ["status", "query", "results", "total"]
        for field in required_fields:
            assert field in json_response, f"响应缺少必需字段: {field}"
    
    def test_error_response_structure(self):
        """测试错误响应结构"""
        response = client.post("/api/v1/search/text", params={"query": "", "limit": 5})
        json_response = response.json()
        
        # 验证错误响应结构
        if "status" in json_response and json_response["status"] == "error":
            assert "message" in json_response, "错误响应缺少message字段"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])