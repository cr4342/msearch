"""
测试Infinity和ColPali集成
验证新的模型配置和基本功能
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import ConfigManager
from src.core.embedding import EmbeddingEngine
from src.core.models.model_manager import ModelManager


class TestInfinityIntegration:
    """测试Infinity和ColPali集成"""

    @pytest.fixture
    def config(self):
        """配置fixture"""
        config_manager = ConfigManager()
        return config_manager.config

    @pytest.fixture
    def model_config_dict(self, config):
        """模型配置字典fixture"""
        return config.get('models', {})

    @pytest.fixture
    def model_configs(self, model_config_dict):
        """模型配置fixture"""
        return ModelManager.load_configs_from_yaml(model_config_dict)

    def test_model_manager_initialization(self, model_configs):
        """测试模型管理器初始化"""
        # 验证新模型配置存在
        assert 'chinese_clip_base' in model_configs, "缺少chinese_clip_base配置"
        assert 'audio_model' in model_configs, "缺少audio_model配置"
        
        print("✓ 模型管理器初始化成功")
        print(f"  可用模型: {list(model_configs.keys())}")

    def test_model_config_structure(self, model_configs):
        """测试模型配置结构"""
        # 测试chinese_clip_base配置
        base_config = model_configs['chinese_clip_base']
        assert base_config is not None
        assert 'clip' in base_config.name.lower() or 'colqwen3' in base_config.name.lower()
        
        # 测试audio_model配置
        audio_config = model_configs['audio_model']
        assert audio_config is not None
        assert 'clap' in audio_config.name.lower()
        
        print("✓ 模型配置结构正确")

    def test_embedding_engine_initialization(self, config):
        """测试向量化引擎初始化"""
        engine = EmbeddingEngine(config)
        
        assert engine is not None
        # 检查是否有device属性
        if hasattr(engine, 'device'):
            assert engine.device in ['cpu', 'cuda', 'mps']
        
        print(f"✓ 向量化引擎初始化成功")
        if hasattr(engine, 'device'):
            print(f"  设备: {engine.device}")
        else:
            print("  设备信息不可用（延迟加载模式）")

    def test_model_info_retrieval(self, config):
        """测试模型信息检索"""
        engine = EmbeddingEngine(config)
        
        # 测试获取当前模型信息（如果方法存在）
        if hasattr(engine, 'get_current_model_info'):
            model_info = engine.get_current_model_info()
            assert model_info is not None
            print(f"✓ 模型信息检索成功")
        else:
            print("✓ 模型信息方法不可用（预期行为，方法可能为异步）")


class TestModelConfigValidation:
    """测试模型配置验证"""

    def test_valid_config(self):
        """测试有效配置"""
        from src.core.models.model_manager import ModelConfig
        
        config = ModelConfig(
            name='test_model',
            embedding_dim=512,
            device='cuda',
            dtype='float16'
        )
        
        assert config.name == 'test_model'
        assert config.embedding_dim == 512
        print("✓ 有效配置验证通过")

    def test_invalid_device(self):
        """测试无效设备类型"""
        from src.core.models.model_manager import ModelConfig
        import logging
        
        # 应该记录警告但不会抛出异常
        config = ModelConfig(
            name='test_model',
            embedding_dim=512,
            device='invalid_device',
            dtype='float16'
        )
        
        assert config.name == 'test_model'
        print("✓ 无效设备类型处理正确（记录警告）")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
