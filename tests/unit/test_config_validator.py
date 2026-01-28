"""
配置验证器单元测试

注意：此测试文件已弃用，配置验证功能已集成到ConfigManager中。
保留此文件仅用于参考。
"""

import pytest
import sys
sys.path.insert(0, '/data/project/msearch')

# 跳过此测试文件，因为功能已集成到ConfigManager
pytest.skip("test_config_validator.py已弃用，配置验证已集成到ConfigManager", allow_module_level=True)


class TestConfigValidator:
    """配置验证器测试"""

    @pytest.fixture
    def valid_config(self):
        """创建有效的配置"""
        return {
            'model': {
                'image_video': {
                    'name': 'OFA-Sys/chinese-clip-vit-base-patch16',
                    'device': 'cpu'
                },
                'audio': {
                    'name': 'laion/clap-htsat-unfused',
                    'device': 'cpu'
                },
                'text': {
                    'name': 'OFA-Sys/chinese-clip-vit-base-patch16'
                }
            },
            'database': {
                'type': 'sqlite',
                'connection': {
                    'path': ':memory:'
                }
            },
            'vector_store': {
                'type': 'infinity',
                'connection': {
                    'host': 'localhost',
                    'port': 7777
                },
                'dimension': 768
            },
            'media': {
                'video': {
                    'short_video': {
                        'threshold': 6.0
                    },
                    'large_video': {
                        'segment_duration': 5.0
                    }
                }
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }

    def test_validate_valid_config(self, valid_config):
        """测试验证有效的配置"""
        validator = ConfigValidator(valid_config)
        result = validator.validate()
        
        assert result is True
        assert len(validator.get_errors()) == 0

    def test_validate_missing_required_sections(self):
        """测试验证缺少必需节的配置"""
        invalid_config = {
            'model': {},
            # 缺少其他必需节
        }
        
        validator = ConfigValidator(invalid_config)
        result = validator.validate()
        
        assert result is False
        assert len(validator.get_errors()) > 0

    def test_validate_missing_model_config(self, valid_config):
        """测试验证缺少模型配置"""
        invalid_config = valid_config.copy()
        del invalid_config['model']['image_video']
        
        validator = ConfigValidator(invalid_config)
        result = validator.validate()
        
        assert result is False
        assert len(validator.get_errors()) > 0

    def test_validate_missing_model_name(self, valid_config):
        """测试验证缺少模型名称"""
        invalid_config = valid_config.copy()
        del invalid_config['model']['image_video']['name']
        
        validator = ConfigValidator(invalid_config)
        result = validator.validate()
        
        assert result is False
        assert len(validator.get_errors()) > 0

    def test_validate_invalid_port(self, valid_config):
        """测试验证无效端口"""
        invalid_config = valid_config.copy()
        invalid_config['api']['port'] = 70000  # 无效端口
        
        validator = ConfigValidator(invalid_config)
        result = validator.validate()
        
        assert result is False
        assert len(validator.get_errors()) > 0

    def test_validate_invalid_log_level(self, valid_config):
        """测试验证无效日志级别"""
        invalid_config = valid_config.copy()
        invalid_config['logging']['level'] = 'INVALID_LEVEL'
        
        validator = ConfigValidator(invalid_config)
        result = validator.validate()
        
        assert result is False
        assert len(validator.get_errors()) > 0

    def test_validate_missing_vector_dimension(self, valid_config):
        """测试验证缺少向量维度"""
        invalid_config = valid_config.copy()
        del invalid_config['vector_store']['dimension']
        
        validator = ConfigValidator(invalid_config)
        result = validator.validate()
        
        # 应该通过但有警告
        assert result is True
        assert len(validator.get_warnings()) > 0

    def test_validate_invalid_vector_dimension(self, valid_config):
        """测试验证无效向量维度"""
        invalid_config = valid_config.copy()
        invalid_config['vector_store']['dimension'] = -100  # 无效维度
        
        validator = ConfigValidator(invalid_config)
        result = validator.validate()
        
        assert result is False
        assert len(validator.get_errors()) > 0

    def test_validate_missing_device_warning(self, valid_config):
        """测试验证缺少设备警告"""
        invalid_config = valid_config.copy()
        del invalid_config['model']['image_video']['device']
        
        validator = ConfigValidator(invalid_config)
        result = validator.validate()
        
        # 应该通过但有警告
        assert result is True
        assert len(validator.get_warnings()) > 0

    def test_validate_short_video_threshold(self, valid_config):
        """测试验证短视频阈值"""
        invalid_config = valid_config.copy()
        invalid_config['media']['video']['short_video']['threshold'] = -1.0  # 无效值
        
        validator = ConfigValidator(invalid_config)
        result = validator.validate()
        
        assert result is False
        assert len(validator.get_errors()) > 0

    def test_validate_segment_duration(self, valid_config):
        """测试验证分段时长"""
        invalid_config = valid_config.copy()
        invalid_config['media']['video']['large_video']['segment_duration'] = 0  # 无效值
        
        validator = ConfigValidator(invalid_config)
        result = validator.validate()
        
        assert result is False
        assert len(validator.get_errors()) > 0

    def test_validate_config_convenience_function(self, valid_config):
        """测试验证配置的便捷函数"""
        result = validate_config(valid_config)
        
        assert result is True

    def test_validate_config_or_raise_success(self, valid_config):
        """测试验证配置或抛出异常（成功情况）"""
        # 不应该抛出异常
        validate_config_or_raise(valid_config)

    def test_validate_config_or_raise_failure(self):
        """测试验证配置或抛出异常（失败情况）"""
        invalid_config = {}
        
        with pytest.raises(ConfigError):
            validate_config_or_raise(invalid_config)

    def test_get_errors(self, valid_config):
        """测试获取错误列表"""
        invalid_config = valid_config.copy()
        del invalid_config['model']
        
        validator = ConfigValidator(invalid_config)
        validator.validate()
        
        errors = validator.get_errors()
        assert isinstance(errors, list)
        assert len(errors) > 0

    def test_get_warnings(self, valid_config):
        """测试获取警告列表"""
        config_with_warnings = valid_config.copy()
        del config_with_warnings['model']['image_video']['device']
        
        validator = ConfigValidator(config_with_warnings)
        validator.validate()
        
        warnings = validator.get_warnings()
        assert isinstance(warnings, list)
        assert len(warnings) > 0
