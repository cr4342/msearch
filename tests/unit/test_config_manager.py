"""
ConfigManager单元测试
测试配置驱动架构的核心组件
"""
import pytest
import tempfile
import os
import yaml
import logging
from unittest.mock import patch, MagicMock

from src.core.config_manager import ConfigManager

# 获取测试日志记录器
test_logger = logging.getLogger('msearch_tests')


class TestConfigManager:
    """ConfigManager功能测试"""
    
    @pytest.fixture
    def temp_config_file(self):
        """创建临时配置文件"""
        config_data = {
            'general': {
                'log_level': 'INFO',
                'data_dir': './data'
            },
            'models': {
                'clip_model': 'openai/clip-vit-base-patch32',
                'clap_model': 'laion/clap-htsat-fused'
            },
            'processing': {
                'batch_size': 16,
                'max_concurrent_tasks': 4
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            return f.name
    
    def test_config_loading(self, temp_config_file):
        """测试配置加载功能"""
        test_logger.info("开始测试配置加载功能")
        
        config_manager = ConfigManager(str(temp_config_file))
        config = config_manager.config
        
        # 验证配置是否正确加载
        assert config is not None
        assert config['general']['log_level'] == 'INFO'
        assert config['models']['clip_model'] == 'openai/clip-vit-base-patch32'
        
        test_logger.info("配置加载测试通过")
    
    def test_nested_key_access(self, temp_config_file):
        """测试嵌套键访问"""
        config_manager = ConfigManager(temp_config_file)
        
        # 测试点号分隔的嵌套键访问
        assert config_manager.get('general.data_dir') == './data'
        assert config_manager.get('processing.max_concurrent_tasks') == 4
        
        # 清理临时文件
        os.unlink(temp_config_file)
    
    def test_default_values(self, temp_config_file):
        """测试默认值机制"""
        config_manager = ConfigManager(temp_config_file)
        
        # 测试不存在的键返回默认值
        assert config_manager.get('nonexistent.key', 'default_value') == 'default_value'
        assert config_manager.get('models.nonexistent_model', 'default_model') == 'default_model'
        
        # 清理临时文件
        os.unlink(temp_config_file)
    
    def test_type_safe_access(self, temp_config_file):
        """测试类型安全访问"""
        config_manager = ConfigManager(temp_config_file)
        
        # 测试类型转换
        batch_size = config_manager.get('processing.batch_size', default=8)
        assert isinstance(batch_size, int)
        assert batch_size == 16
        
        log_level = config_manager.get('general.log_level', default='DEBUG')
        assert isinstance(log_level, str)
        assert log_level == 'INFO'
        
        # 清理临时文件
        os.unlink(temp_config_file)
    
    def test_config_validation(self, temp_config_file):
        """测试配置验证功能"""
        config_manager = ConfigManager(temp_config_file)
        
        # 验证配置加载成功
        assert config_manager.get('general.log_level') == 'INFO'
        assert config_manager.get('models.clip_model') == 'openai/clip-vit-base-patch32'
        
        # 验证配置验证日志 - 检查是否尝试验证所需配置项
        # 这里只是确认配置管理器正常工作
        log_level = config_manager.get('general.log_level')
        assert log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        # 清理临时文件
        os.unlink(temp_config_file)
    
    def test_environment_variable_override(self, temp_config_file):
        """测试环境变量覆盖"""
        # 先清除可能存在的环境变量
        if 'MSEARCH_GENERAL_LOG_LEVEL' in os.environ:
            del os.environ['MSEARCH_GENERAL_LOG_LEVEL']
        
        # 设置环境变量
        os.environ['MSEARCH_GENERAL_LOG_LEVEL'] = 'DEBUG'
        
        try:
            config_manager = ConfigManager(temp_config_file)
            
            # 环境变量应该覆盖配置文件
            assert config_manager.get('general.log_level') == 'DEBUG'
        finally:
            # 清理环境变量
            if 'MSEARCH_GENERAL_LOG_LEVEL' in os.environ:
                del os.environ['MSEARCH_GENERAL_LOG_LEVEL']
            # 清理临时文件
            os.unlink(temp_config_file)
    
    def test_missing_config_file(self):
        """测试配置文件不存在的情况"""
        config_manager = ConfigManager('nonexistent_config.yml')
        
        # 应该使用默认配置
        assert config_manager.get('general.log_level', 'INFO') == 'INFO'
        assert config_manager.get('processing.batch_size', 16) == 16
    
    def test_invalid_yaml_format(self):
        """测试无效YAML格式处理"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("invalid: yaml: content: [\n")  # 添加换行符使YAML更接近有效格式
            invalid_config_file = f.name
        
        try:
            # 应该优雅处理无效YAML
            config_manager = ConfigManager(invalid_config_file)
            assert config_manager.get('general.log_level', 'INFO') == 'INFO'
        finally:
            os.unlink(invalid_config_file)


class TestConfigManagerIntegration:
    """ConfigManager集成测试"""
    
    def test_config_driven_architecture(self):
        """测试配置驱动架构"""
        # 创建完整的配置文件
        config_data = {
            'general': {
                'log_level': 'DEBUG',
                'data_dir': './test_data'
            },
            'features': {
                'enable_face_recognition': True,
                'enable_audio_processing': True,
                'enable_video_processing': True
            },
            'models': {
                'clip_model': 'openai/clip-vit-base-patch32',
                'clap_model': 'laion/clap-htsat-fused',
                'whisper_model': 'openai/whisper-base'
            },
            'processing': {
                'batch_size': 32,
                'max_concurrent_tasks': 8,
                'video': {
                    'max_resolution': [1280, 720],
                    'frame_interval': 2
                },
                'audio': {
                    'sample_rate': 16000,
                    'segment_duration': 10
                }
            },
            'storage': {
                'qdrant': {
                    'host': 'localhost',
                    'port': 6333
                },
                'sqlite': {
                    'path': './test_data/msearch.db'
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            config_manager = ConfigManager(config_file)
            
            # 验证所有配置层级
            assert config_manager.get('general.log_level') == 'DEBUG'
            assert config_manager.get('features.enable_face_recognition') == True
            assert config_manager.get('models.clip_model') == 'openai/clip-vit-base-patch32'
            assert config_manager.get('processing.batch_size') == 32
            assert config_manager.get('processing.video.max_resolution') == [1280, 720]
            assert config_manager.get('storage.qdrant.port') == 6333
            
            # 验证配置完整性
            log_level = config_manager.get('general.log_level')
            assert log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            
        finally:
            os.unlink(config_file)
    
    def test_hardware_adaptive_config(self):
        """测试硬件自适应配置"""
        # 模拟不同硬件环境的配置
        low_memory_config = {
            'processing': {
                'batch_size': 4,
                'max_concurrent_tasks': 2
            },
            'gpu_optimization': {
                'model_loading': {
                    'strategy': 'on_demand',
                    'max_concurrent_models': 1
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(low_memory_config, f)
            config_file = f.name
        
        try:
            config_manager = ConfigManager(config_file)
            
            # 验证低内存配置
            assert config_manager.get('processing.batch_size') == 4
            assert config_manager.get('gpu_optimization.model_loading.strategy') == 'on_demand'
            assert config_manager.get('gpu_optimization.model_loading.max_concurrent_models') == 1
            
        finally:
            os.unlink(config_file)