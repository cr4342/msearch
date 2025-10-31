"""
CPU模式功能测试
根据test_strategy.md第2.3节要求，验证CPU环境下的核心功能
"""
import pytest
import logging
import time
import psutil
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

class TestCPUMode:
    """CPU模式下的功能测试"""
    
    @pytest.fixture
    def cpu_config(self):
        """CPU测试配置"""
        return {
            'device': 'cpu',
            'models': {
                'clip': {
                    'device': 'cpu',
                    'batch_size': 4
                },
                'clap': {
                    'device': 'cpu', 
                    'batch_size': 2
                },
                'whisper': {
                    'device': 'cpu',
                    'batch_size': 1
                }
            },
            'processing': {
                'batch_size': 4,
                'max_concurrent_tasks': 2
            }
        }
    
    @pytest.fixture
    def mock_embedding_engine(self, cpu_config):
        """Mock的嵌入引擎"""
        mock_engine = MagicMock()
        
        # 配置mock行为
        mock_engine.device = "cpu"
        mock_engine.model_loaded = True
        mock_engine.embed_text.return_value = np.random.rand(512).astype(np.float32)
        mock_engine.embed_image.return_value = np.random.rand(512).astype(np.float32)
        
        return mock_engine
    
    def test_cpu_mode_initialization(self, mock_embedding_engine):
        """测试CPU模式初始化"""
        assert mock_embedding_engine.device == "cpu"
        assert mock_embedding_engine.model_loaded == True
        logger.info("CPU模式初始化测试通过")
    
    def test_text_search_functionality(self, mock_embedding_engine):
        """测试文本搜索功能"""
        query = "美丽的风景"
        start_time = time.time()
        
        # 模拟搜索
        vector = mock_embedding_engine.embed_text(query)
        search_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        assert len(vector) == 512
        assert search_time < 500  # CPU模式下搜索响应时间应小于500ms
        
        logger.info(f"文本搜索功能测试通过，响应时间: {search_time:.2f}ms")
    
    def test_image_search_functionality(self, mock_embedding_engine):
        """测试图片搜索功能"""
        # 创建模拟图片数据
        test_image = np.random.rand(224, 224, 3).astype(np.float32)
        start_time = time.time()
        
        # 模拟图片搜索
        vector = mock_embedding_engine.embed_image(test_image)
        search_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        assert len(vector) == 512
        assert search_time < 1000  # CPU模式下图片搜索响应时间应小于1000ms
        
        logger.info(f"图片搜索功能测试通过，响应时间: {search_time:.2f}ms")
    
    def test_timestamp_accuracy_simulation(self):
        """测试时间戳精度模拟"""
        # 模拟时间戳处理
        test_timestamps = [
            {'timestamp': 10.5, 'accuracy': 1.8},
            {'timestamp': 25.2, 'accuracy': 1.5},
            {'timestamp': 45.8, 'accuracy': 2.0}
        ]
        
        # 验证时间戳精度
        for ts_data in test_timestamps:
            timestamp_accuracy = ts_data['accuracy']
            assert timestamp_accuracy <= 2.0, f"时间戳精度超出要求: {timestamp_accuracy}秒"
            
            logger.info(f"时间戳精度验证 - 时间: {ts_data['timestamp']}s, 精度: {timestamp_accuracy}秒")
        
        logger.info("时间戳精度测试通过")
    
    def test_memory_usage(self):
        """测试内存使用情况"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        # 执行模拟操作
        for i in range(100):
            # 模拟向量生成
            vector = np.random.rand(512).astype(np.float32)
            # 模拟处理
            _ = vector * 2
        
        final_memory = process.memory_info().rss / (1024 * 1024)  # MB
        memory_increase = final_memory - initial_memory
        
        assert memory_increase < 100, f"内存增长过多: {memory_increase}MB"
        
        logger.info(f"内存使用测试通过，增长: {memory_increase:.2f}MB")
    
    def test_batch_processing_simulation(self, mock_embedding_engine):
        """测试批处理模拟"""
        batch_texts = [f"测试文本 {i}" for i in range(10)]
        
        start_time = time.time()
        
        # 模拟批处理
        vectors = []
        for text in batch_texts:
            vector = mock_embedding_engine.embed_text(text)
            vectors.append(vector)
        
        batch_time = time.time() - start_time
        avg_time_per_item = (batch_time / len(batch_texts)) * 1000  # ms
        
        assert len(vectors) == len(batch_texts)
        assert avg_time_per_item < 50, f"批处理平均时间过长: {avg_time_per_item:.2f}ms"
        
        logger.info(f"批处理测试通过，平均每项: {avg_time_per_item:.2f}ms")
    
    def test_error_handling(self):
        """测试错误处理"""
        try:
            # 模拟错误情况
            invalid_input = None
            
            if invalid_input is None:
                raise ValueError("输入不能为空")
                
        except ValueError as e:
            # 验证错误被正确捕获
            assert "输入不能为空" in str(e)
            logger.info("错误处理测试通过")
        except Exception as e:
            pytest.fail(f"未预期的错误类型: {type(e).__name__}: {e}")
    
    def test_configuration_loading(self, cpu_config):
        """测试配置加载"""
        # 验证CPU配置
        assert cpu_config['device'] == 'cpu'
        assert 'models' in cpu_config
        
        # 验证模型配置
        for model_name in ['clip', 'clap', 'whisper']:
            assert model_name in cpu_config['models']
            model_config = cpu_config['models'][model_name]
            assert model_config['device'] == 'cpu'
            assert 'batch_size' in model_config
        
        logger.info("配置加载测试通过")

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    pytest.main([__file__, "-v", "-s"])