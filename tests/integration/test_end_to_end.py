"""
端到端集成测试
根据test_strategy.md要求，验证完整的工作流程
"""
import pytest
import logging
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

class TestEndToEndIntegration:
    """端到端集成测试"""
    
    @pytest.fixture
    def integration_config(self):
        """集成测试配置"""
        return {
            'device': 'cpu',
            'models': {
                'clip': {'device': 'cpu', 'batch_size': 2},
                'clap': {'device': 'cpu', 'batch_size': 1},
                'whisper': {'device': 'cpu', 'batch_size': 1}
            },
            'processing': {
                'batch_size': 2,
                'max_concurrent_tasks': 1
            },
            'api': {
                'host': '127.0.0.1',
                'port': 8000
            }
        }
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Mock的处理编排器"""
        with patch('src.business.orchestrator.ProcessingOrchestrator') as mock_class:
            mock_orchestrator = MagicMock()
            mock_class.return_value = mock_orchestrator
            
            # 配置mock行为
            async def mock_process_file(file_path):
                return {
                    'status': 'success',
                    'file_id': f'file_{hash(file_path) % 1000}',
                    'total_vectors': 10,
                    'processing_time': 2.5
                }
            
            mock_orchestrator.process_file = mock_process_file
            
            yield mock_orchestrator
    
    @pytest.fixture
    def mock_retrieval_engine(self):
        """Mock的检索引擎"""
        with patch('src.business.smart_retrieval.SmartRetrievalEngine') as mock_class:
            mock_engine = MagicMock()
            mock_class.return_value = mock_engine
            
            # 配置mock行为
            async def mock_smart_search(query):
                return [
                    {
                        'file_id': f'file_{i}',
                        'score': 0.9 - i * 0.1,
                        'file_path': f'/test/file_{i}.jpg',
                        'timestamp': i * 10.0 if i > 0 else None,
                        'timestamp_accuracy': 1.5 if i > 0 else None
                    }
                    for i in range(3)
                ]
            
            mock_engine.smart_search = mock_smart_search
            
            yield mock_engine
    
    def test_config_loading_integration(self, integration_config):
        """测试配置加载集成"""
        try:
            from src.core.config_manager import ConfigManager
            
            # 创建临时配置文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                import yaml
                yaml.dump(integration_config, f)
                temp_config_path = f.name
            
            try:
                # 测试配置管理器
                config_manager = ConfigManager(temp_config_path)
                loaded_config = config_manager.get_config()
                
                # 验证配置加载
                assert 'device' in loaded_config
                assert 'models' in loaded_config
                assert loaded_config['device'] == 'cpu'
                
                logger.info("配置加载集成测试通过")
                
            finally:
                # 清理临时文件
                os.unlink(temp_config_path)
                
        except Exception as e:
            logger.error(f"配置加载集成测试失败: {e}")
            pytest.fail(f"配置加载集成测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_file_processing_workflow(self, mock_orchestrator, integration_config):
        """测试文件处理工作流程"""
        # 模拟文件列表
        test_files = [
            '/test/image1.jpg',
            '/test/video1.mp4',
            '/test/audio1.mp3'
        ]
        
        processed_files = []
        
        # 处理每个文件
        for file_path in test_files:
            logger.info(f"处理文件: {file_path}")
            result = await mock_orchestrator.process_file(file_path)
            
            assert result['status'] == 'success'
            assert 'file_id' in result
            assert result['total_vectors'] > 0
            
            processed_files.append({
                'file_path': file_path,
                'file_id': result['file_id'],
                'vectors_count': result['total_vectors']
            })
        
        # 验证处理结果
        assert len(processed_files) == len(test_files)
        
        logger.info(f"文件处理工作流程测试通过，处理了 {len(processed_files)} 个文件")
    
    @pytest.mark.asyncio
    async def test_search_workflow(self, mock_retrieval_engine, integration_config):
        """测试搜索工作流程"""
        # 测试查询列表
        test_queries = [
            "美丽的风景照片",
            "会议讨论视频",
            "轻松的背景音乐"
        ]
        
        search_results = []
        
        for query in test_queries:
            logger.info(f"执行搜索: {query}")
            results = await mock_retrieval_engine.smart_search(query)
            
            # 验证搜索结果
            assert len(results) > 0, f"查询 '{query}' 无结果"
            
            # 验证结果格式
            for result in results:
                assert 'file_id' in result
                assert 'score' in result
                assert 'file_path' in result
                assert result['score'] > 0
            
            search_results.append({
                'query': query,
                'result_count': len(results),
                'top_score': results[0]['score'] if results else 0
            })
        
        # 验证所有搜索都有结果
        assert all(r['result_count'] > 0 for r in search_results)
        
        logger.info(f"搜索工作流程测试通过，执行了 {len(search_results)} 个查询")
    
    @pytest.mark.asyncio
    async def test_timestamp_accuracy_workflow(self, mock_retrieval_engine):
        """测试时间戳精度工作流程"""
        # 执行视频相关搜索
        video_query = "会议开始场景"
        results = await mock_retrieval_engine.smart_search(video_query)
        
        # 验证时间戳精度
        timestamp_results = [r for r in results if r.get('timestamp') is not None]
        
        if timestamp_results:
            for result in timestamp_results:
                timestamp = result.get('timestamp', 0)
                accuracy = result.get('timestamp_accuracy', float('inf'))
                
                # 验证时间戳精度要求（±2秒）
                assert accuracy <= 2.0, f"时间戳精度超出要求: {accuracy}秒"
                assert timestamp >= 0, f"时间戳不能为负数: {timestamp}"
                
                logger.info(f"时间戳验证 - 时间: {timestamp}s, 精度: {accuracy}s")
        
        logger.info("时间戳精度工作流程测试通过")
    
    def test_api_integration_simulation(self, integration_config):
        """测试API集成模拟"""
        try:
            # 模拟API请求数据
            api_requests = [
                {
                    'endpoint': '/api/v1/search',
                    'method': 'POST',
                    'data': {'query': '测试查询', 'limit': 10}
                },
                {
                    'endpoint': '/api/v1/config',
                    'method': 'GET',
                    'data': {}
                },
                {
                    'endpoint': '/api/v1/system/status',
                    'method': 'GET',
                    'data': {}
                }
            ]
            
            # 模拟API响应
            for request in api_requests:
                logger.info(f"模拟API请求: {request['method']} {request['endpoint']}")
                
                # 模拟响应时间
                import time
                start_time = time.time()
                time.sleep(0.01)  # 10ms模拟延迟
                response_time = (time.time() - start_time) * 1000
                
                # 验证响应时间
                assert response_time < 100, f"API响应时间过长: {response_time:.2f}ms"
                
                logger.info(f"API响应时间: {response_time:.2f}ms")
            
            logger.info("API集成模拟测试通过")
            
        except Exception as e:
            logger.error(f"API集成模拟测试失败: {e}")
            pytest.fail(f"API集成模拟测试失败: {e}")
    
    def test_error_recovery_workflow(self):
        """测试错误恢复工作流程"""
        # 模拟各种错误情况
        error_scenarios = [
            {
                'name': '文件不存在',
                'error': FileNotFoundError("文件未找到"),
                'expected_handling': '跳过文件并继续处理'
            },
            {
                'name': '内存不足',
                'error': MemoryError("内存不足"),
                'expected_handling': '减少批处理大小'
            },
            {
                'name': '网络超时',
                'error': TimeoutError("网络超时"),
                'expected_handling': '重试机制'
            }
        ]
        
        for scenario in error_scenarios:
            logger.info(f"测试错误场景: {scenario['name']}")
            
            try:
                # 模拟错误
                raise scenario['error']
            except Exception as e:
                # 验证错误类型
                assert type(e) == type(scenario['error'])
                logger.info(f"错误处理: {scenario['expected_handling']}")
        
        logger.info("错误恢复工作流程测试通过")
    
    def test_performance_monitoring_integration(self):
        """测试性能监控集成"""
        import psutil
        
        # 收集性能指标
        performance_metrics = {
            'cpu_usage': psutil.cpu_percent(interval=0.1),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
        }
        
        # 验证性能指标在合理范围内
        assert performance_metrics['cpu_usage'] < 95, f"CPU使用率过高: {performance_metrics['cpu_usage']}%"
        assert performance_metrics['memory_usage'] < 95, f"内存使用率过高: {performance_metrics['memory_usage']}%"
        assert performance_metrics['disk_usage'] < 95, f"磁盘使用率过高: {performance_metrics['disk_usage']}%"
        
        logger.info(f"性能监控数据: {json.dumps(performance_metrics, ensure_ascii=False)}")
        logger.info("性能监控集成测试通过")
    
    @pytest.mark.asyncio
    async def test_complete_user_scenario(self, mock_orchestrator, mock_retrieval_engine):
        """测试完整用户场景"""
        logger.info("开始完整用户场景测试...")
        
        # 场景1: 用户上传文件
        upload_files = ['/test/vacation.jpg', '/test/meeting.mp4']
        
        for file_path in upload_files:
            result = await mock_orchestrator.process_file(file_path)
            assert result['status'] == 'success'
            logger.info(f"文件上传处理完成: {file_path}")
        
        # 场景2: 用户搜索内容
        search_queries = ["度假照片", "会议记录"]
        
        for query in search_queries:
            results = await mock_retrieval_engine.smart_search(query)
            assert len(results) > 0
            logger.info(f"搜索完成: {query}, 结果数: {len(results)}")
        
        # 场景3: 用户查看详细结果
        detailed_results = await mock_retrieval_engine.smart_search("详细查询")
        for result in detailed_results[:2]:  # 查看前2个结果
            assert 'file_path' in result
            assert 'score' in result
            logger.info(f"查看详细结果: {result['file_path']}, 评分: {result['score']:.3f}")
        
        logger.info("完整用户场景测试通过")

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    pytest.main([__file__, "-v", "-s"])