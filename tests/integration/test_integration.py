#!/usr/bin/env python3
"""
集成测试套件
测试多模态搜索系统的模块间协作
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from core.config_manager import ConfigManager
from core.processing_orchestrator import ProcessingOrchestrator
from core.multimodal_fusion_engine import MultimodalFusionEngine
from core.smart_retrieval import SmartRetrieval
from models.vector_store import VectorStore
from models.face_database import FaceDatabase


class TestMultimodalSearchIntegration:
    """多模态搜索集成测试"""
    
    @pytest.fixture
    def config_manager(self):
        """配置管理器fixture"""
        return ConfigManager()
    
    @pytest.fixture
    def orchestrator(self, config_manager):
        """处理编排器fixture"""
        return ProcessingOrchestrator(config_manager)
    
    @pytest.fixture
    def fusion_engine(self, config_manager):
        """多模态融合引擎fixture"""
        return MultimodalFusionEngine(config_manager)
    
    @pytest.fixture
    def retrieval_engine(self, config_manager):
        """智能检索引擎fixture"""
        return SmartRetrieval(config_manager)
    
    def test_end_to_end_text_search(self, orchestrator, retrieval_engine):
        """端到端文本搜索测试"""
        # 模拟文本搜索流程
        query = "人工智能技术发展"
        
        # 处理查询
        processed_query = orchestrator.process_text_query(query)
        assert processed_query is not None
        
        # 执行搜索
        results = retrieval_engine.search(processed_query, modality="text", limit=5)
        
        # 验证结果
        assert isinstance(results, list)
        assert len(results) <= 5
        
        if results:
            # 验证结果格式
            result = results[0]
            assert 'content' in result
            assert 'score' in result
            assert 'metadata' in result
    
    def test_end_to_end_image_search(self, orchestrator, retrieval_engine):
        """端到端图像搜索测试"""
        # 模拟图像搜索流程
        image_path = "/tmp/test_image.jpg"
        
        # 创建测试图像文件
        Path(image_path).touch()
        
        try:
            # 处理图像查询
            processed_image = orchestrator.process_image_query(image_path)
            
            if processed_image:
                # 执行搜索
                results = retrieval_engine.search(processed_image, modality="image", limit=3)
                
                # 验证结果
                assert isinstance(results, list)
                assert len(results) <= 3
        finally:
            # 清理测试文件
            if Path(image_path).exists():
                Path(image_path).unlink()
    
    def test_cross_modal_search(self, orchestrator, fusion_engine, retrieval_engine):
        """跨模态搜索测试"""
        # 测试文本搜索图像
        text_query = "猫的照片"
        
        # 处理文本查询
        processed_query = orchestrator.process_text_query(text_query)
        
        # 跨模态融合
        fused_query = fusion_engine.fuse_modalities([processed_query], weights=[1.0])
        
        # 执行跨模态搜索
        results = retrieval_engine.search(fused_query, modality="cross_modal", limit=5)
        
        # 验证结果
        assert isinstance(results, list)
    
    def test_file_processing_pipeline(self, orchestrator):
        """文件处理管道测试"""
        # 创建测试文件
        test_files = [
            "/tmp/test_doc.txt",
            "/tmp/test_image.jpg", 
            "/tmp/test_audio.wav"
        ]
        
        # 创建测试文件
        for file_path in test_files:
            Path(file_path).touch()
        
        try:
            # 批量处理文件
            results = orchestrator.batch_process_files(test_files)
            
            # 验证处理结果
            assert isinstance(results, dict)
            
            for file_path in test_files:
                assert file_path in results
                result = results[file_path]
                assert 'status' in result
                assert 'metadata' in result
        finally:
            # 清理测试文件
            for file_path in test_files:
                if Path(file_path).exists():
                    Path(file_path).unlink()
    
    def test_vector_storage_integration(self, config_manager):
        """向量存储集成测试"""
        vector_store = VectorStore(config_manager)
        
        # 测试向量存储和检索
        test_vectors = [
            {"id": "doc1", "vector": [0.1, 0.2, 0.3, 0.4], "metadata": {"type": "text"}},
            {"id": "doc2", "vector": [0.5, 0.6, 0.7, 0.8], "metadata": {"type": "image"}}
        ]
        
        # 存储向量
        for item in test_vectors:
            vector_store.store_vector(item["id"], item["vector"], item["metadata"])
        
        # 搜索相似向量
        query_vector = [0.15, 0.25, 0.35, 0.45]
        results = vector_store.search_vectors(query_vector, limit=2)
        
        # 验证结果
        assert isinstance(results, list)
        assert len(results) > 0
        
        # 验证结果格式
        result = results[0]
        assert 'id' in result
        assert 'score' in result
        assert 'metadata' in result
    
    def test_face_recognition_pipeline(self, orchestrator):
        """人脸识别管道测试"""
        # 创建测试图像文件
        test_image_path = "/tmp/test_face.jpg"
        Path(test_image_path).touch()
        
        try:
            # 测试人脸索引
            result = orchestrator._index_image_faces(test_image_path)
            
            # 即使没有人脸，也应该返回处理结果
            assert isinstance(result, dict)
            assert 'status' in result
            
        finally:
            # 清理测试文件
            if Path(test_image_path).exists():
                Path(test_image_path).unlink()
    
    def test_configuration_loading(self, config_manager):
        """配置加载集成测试"""
        # 验证配置加载
        config = config_manager.get_config()
        
        # 验证必要配置项
        assert 'api' in config
        assert 'models' in config
        assert 'database' in config
        assert 'search' in config
        
        # 验证API配置
        api_config = config['api']
        assert 'host' in api_config
        assert 'port' in api_config
        
        # 验证模型配置
        models_config = config['models']
        assert 'embedding_model' in models_config
        assert 'face_model' in models_config
    
    def test_error_handling_integration(self, orchestrator):
        """错误处理集成测试"""
        # 测试无效文件处理
        invalid_files = [
            "/nonexistent/file.txt",
            "",
            None
        ]
        
        for invalid_file in invalid_files:
            try:
                result = orchestrator.process_file(invalid_file)
                # 应该优雅处理错误
                assert isinstance(result, dict)
                if 'error' in result:
                    assert 'message' in result['error']
            except Exception as e:
                # 不应该抛出未处理的异常
                pytest.fail(f"未处理的异常: {e}")
    
    @pytest.mark.asyncio
    async def test_async_operations(self, orchestrator):
        """异步操作集成测试"""
        # 测试异步文件处理
        test_file = "/tmp/async_test.txt"
        Path(test_file).touch()
        
        try:
            # 异步处理文件
            result = await orchestrator.process_file_async(test_file)
            
            # 验证异步处理结果
            assert isinstance(result, dict)
            assert 'status' in result
            
        finally:
            # 清理测试文件
            if Path(test_file).exists():
                Path(test_file).unlink()


class TestSystemIntegration:
    """系统集成测试"""
    
    def test_full_system_initialization(self):
        """完整系统初始化测试"""
        # 测试所有组件能否正常初始化
        try:
            config_manager = ConfigManager()
            orchestrator = ProcessingOrchestrator(config_manager)
            fusion_engine = MultimodalFusionEngine(config_manager)
            retrieval_engine = SmartRetrieval(config_manager)
            
            # 验证所有组件都已正确初始化
            assert config_manager is not None
            assert orchestrator is not None
            assert fusion_engine is not None
            assert retrieval_engine is not None
            
        except Exception as e:
            pytest.fail(f"系统初始化失败: {e}")
    
    def test_service_dependencies(self):
        """服务依赖测试"""
        # 验证服务间的依赖关系
        config_manager = ConfigManager()
        
        # 验证配置管理器被正确使用
        orchestrator = ProcessingOrchestrator(config_manager)
        assert orchestrator.config_manager == config_manager
        
        # 验证依赖注入
        fusion_engine = MultimodalFusionEngine(config_manager)
        assert fusion_engine.config_manager == config_manager


if __name__ == "__main__":
    # 运行集成测试
    pytest.main([__file__, "-v", "--tb=short"])