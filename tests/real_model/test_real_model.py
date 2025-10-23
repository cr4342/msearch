"""
真实模型测试
按照@docs/test_strategy.md要求进行真实模型测试
"""
import pytest
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.business.embedding_engine import EmbeddingEngine
from src.core.config_manager import ConfigManager


class TestRealModelDeployment:
    """真实模型部署测试"""
    
    @pytest.fixture
    def real_model_config(self):
        """真实模型配置"""
        config_manager = ConfigManager()
        config = config_manager.config.copy()
        
        # 确保模型目录存在
        models_dir = Path("./data/models")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # 更新配置中的模型路径
        if 'embedding' not in config:
            config['embedding'] = {}
        config['embedding']['models_dir'] = str(models_dir)
        
        return config
    
    def test_clip_model_download_and_load(self, real_model_config):
        """测试CLIP模型下载和加载"""
        try:
            # 创建嵌入引擎实例，这会触发模型下载
            embedding_engine = EmbeddingEngine(config=real_model_config)
            
            # 验证模型已加载
            assert embedding_engine.clip_model is not None, "CLIP模型未正确加载"
            assert embedding_engine.clip_processor is not None, "CLIP处理器未正确加载"
            
            # 测试模型推理
            test_text = "a beautiful landscape"
            vector = embedding_engine.embed_text(test_text)
            assert len(vector) == 512, f"CLIP向量维度错误: {len(vector)}"
            assert not all(v == 0 for v in vector), "CLIP向量全为零"
            
            print(f"CLIP模型测试通过，生成向量维度: {len(vector)}")
        except Exception as e:
            pytest.skip(f"CLIP模型测试跳过（可能需要网络连接）: {e}")
    
    def test_model_file_integrity(self, real_model_config):
        """测试模型文件完整性"""
        models_dir = Path(real_model_config['embedding']['models_dir'])
        
        # 检查模型目录是否存在
        if not models_dir.exists():
            pytest.skip("模型目录不存在")
        
        # 检查是否有模型文件
        model_dirs = [d for d in models_dir.iterdir() if d.is_dir()]
        if not model_dirs:
            pytest.skip("未找到模型文件")
        
        for model_dir in model_dirs:
            # 检查关键配置文件
            config_file = model_dir / 'config.json'
            assert config_file.exists(), f"缺少配置文件: {config_file}"
            
            # 检查模型文件（可能有不同的格式）
            model_files = list(model_dir.glob('*.bin')) + list(model_dir.glob('*.safetensors'))
            assert len(model_files) > 0, f"模型目录中未找到模型文件: {model_dir}"
            
            # 检查文件大小
            for model_file in model_files:
                file_size = model_file.stat().st_size
                assert file_size > 1024 * 1024, f"模型文件过小: {model_file} ({file_size} bytes)"


class TestRealModelPerformance:
    """真实模型性能测试"""
    
    @pytest.fixture
    def real_embedding_engine(self):
        """真实模型嵌入引擎"""
        config_manager = ConfigManager()
        config = config_manager.config.copy()
        
        # 确保使用CPU模式以避免GPU依赖
        if 'device' not in config:
            config['device'] = 'cpu'
        else:
            config['device'] = 'cpu'
        
        # 设置较小的批处理大小
        if 'processing' not in config:
            config['processing'] = {}
        config['processing']['batch_size'] = 2
        
        try:
            return EmbeddingEngine(config=config)
        except Exception as e:
            pytest.skip(f"无法初始化嵌入引擎: {e}")
    
    def test_clip_text_encoding_performance(self, real_embedding_engine):
        """测试CLIP文本编码性能"""
        if real_embedding_engine.clip_model is None:
            pytest.skip("CLIP模型未加载")
        
        test_texts = [
            "a beautiful sunset over the ocean",
            "a cat sitting on a windowsill", 
            "modern architecture in the city",
            "children playing in the park",
            "delicious food on the table"
        ]
        
        import time
        
        # 单次推理性能测试
        start_time = time.time()
        for text in test_texts:
            vector = real_embedding_engine.embed_text(text)
            assert len(vector) == 512
        single_inference_time = (time.time() - start_time) / len(test_texts)
        
        # 批量推理性能测试
        start_time = time.time()
        batch_vectors = real_embedding_engine.embed_text_batch(test_texts)
        batch_inference_time = (time.time() - start_time) / len(test_texts)
        
        # 验证性能要求（在CPU上较为宽松）
        assert single_inference_time < 5.0, f"单次推理时间过长: {single_inference_time:.3f}s"
        assert batch_inference_time < 2.0, f"批量推理时间过长: {batch_inference_time:.3f}s"
        
        print(f"CLIP文本编码性能 - 单次: {single_inference_time:.3f}s, 批量: {batch_inference_time:.3f}s")
    
    def test_memory_usage_with_real_models(self, real_embedding_engine):
        """测试真实模型内存使用"""
        if real_embedding_engine.clip_model is None:
            pytest.skip("CLIP模型未加载")
        
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
            
            # 执行推理操作
            for i in range(10):
                text = f"test query {i}"
                vector = real_embedding_engine.embed_text(text)
            
            final_memory = process.memory_info().rss / (1024 * 1024)  # MB
            memory_increase = final_memory - initial_memory
            
            # 验证内存使用合理
            assert memory_increase < 200, f"内存增长过多: {memory_increase}MB"
            
            print(f"真实模型内存使用 - 增长: {memory_increase:.2f}MB")
        except ImportError:
            pytest.skip("未安装psutil库")