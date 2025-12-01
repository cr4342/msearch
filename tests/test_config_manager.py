"""
配置管理器单元测试
测试ConfigManager的各项功能，包括配置加载、设置、监听等
"""

import pytest
import yaml
import tempfile
import os
from unittest.mock import patch, mock_open
import sys

sys.path.insert(0, 'src')

from src.core.config_manager import ConfigManager


class TestConfigManager:
    """配置管理器测试类"""
    
    def setup_method(self):
        """测试方法初始化"""
        self.test_config_data = {
            'system': {
                'log_level': 'INFO',
                'data_dir': './data',
                'temp_dir': './temp',
                'max_workers': 4
            },
            'database': {
                'sqlite': {
                    'path': './data/msearch.db',
                    'connection_pool_size': 10,
                    'timeout': 30
                },
                'qdrant': {
                    'host': 'localhost',
                    'port': 6333
                }
            },
            'custom_section': {
                'nested_value': 'test_value',
                'number_value': 42,
                'boolean_value': True
            }
        }
    
    def test_config_manager_initialization(self):
        """测试配置管理器初始化"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(self.test_config_data, f)
            config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path)
            assert config_manager.config_path == config_path
            assert config_manager.config is not None
        finally:
            os.unlink(config_path)
    
    def test_load_valid_config(self):
        """测试加载有效配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(self.test_config_data, f)
            config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path)
            assert config_manager.get('system.log_level') == 'INFO'
            assert config_manager.get('database.sqlite.path') == './data/msearch.db'
            assert config_manager.get('database.qdrant.port') == 6333
        finally:
            os.unlink(config_path)
    
    def test_load_nonexistent_config(self):
        """测试加载不存在的配置文件"""
        config_manager = ConfigManager('nonexistent.yml')
        assert config_manager.config is not None
        # 应该使用默认配置
        assert 'system' in config_manager.config
    
    def test_get_nested_value_success(self):
        """测试成功获取嵌套配置值"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(self.test_config_data, f)
            config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path)
            assert config_manager.get('system.log_level') == 'INFO'
            assert config_manager.get('database.sqlite.path') == './data/msearch.db'
            assert config_manager.get('custom_section.nested_value') == 'test_value'
        finally:
            os.unlink(config_path)
    
    def test_get_nested_value_nonexistent(self):
        """测试获取不存在的嵌套配置值"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(self.test_config_data, f)
            config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path)
            assert config_manager.get('nonexistent.section.key') is None
            assert config_manager.get('system.nonexistent') is None
        finally:
            os.unlink(config_path)
    
    def test_get_with_default_value(self):
        """测试获取配置值使用默认值"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(self.test_config_data, f)
            config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path)
            assert config_manager.get('nonexistent.key', 'default') == 'default'
            assert config_manager.get('system.log_level', 'DEBUG') == 'INFO'
        finally:
            os.unlink(config_path)
    
    def test_set_config_value(self):
        """测试设置配置值"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(self.test_config_data, f)
            config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path)
            config_manager.set('new_section.key', 'new_value')
            assert config_manager.get('new_section.key') == 'new_value'
        finally:
            os.unlink(config_path)
    
    def test_set_nested_config_value(self):
        """测试设置嵌套配置值"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(self.test_config_data, f)
            config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path)
            config_manager.set('database.sqlite.new_field', 'test')
            assert config_manager.get('database.sqlite.new_field') == 'test'
        finally:
            os.unlink(config_path)
    
    @pytest.mark.asyncio
    async def test_config_watchers(self):
        """测试配置监听器"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(self.test_config_data, f)
            config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path)
            
            # 记录监听器调用
            callback_calls = []
            def callback(key, value):
                callback_calls.append((key, value))
            
            # 注册监听器
            config_manager.watch('system.log_level', callback)
            
            # 修改配置
            config_manager.set('system.log_level', 'DEBUG')
            
            # 验证监听器被调用
            assert len(callback_calls) == 1
            assert callback_calls[0] == ('system.log_level', 'DEBUG')
        finally:
            os.unlink(config_path)
    
    def test_env_variable_override(self):
        """测试环境变量覆盖配置"""
        # 设置环境变量
        with patch.dict(os.environ, {
            'MSEARCH_SYSTEM_LOG_LEVEL': 'ERROR',
            'MSEARCH_DATABASE_SQLITE_PATH': '/custom/path.db'
        }):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                yaml.dump(self.test_config_data, f)
                config_path = f.name
            
            try:
                config_manager = ConfigManager(config_path)
                # 环境变量应该覆盖配置文件
                assert config_manager.get('system.log_level') == 'ERROR'
                assert config_manager.get('database.sqlite.path') == '/custom/path.db'
            finally:
                os.unlink(config_path)
    
    def test_env_variable_type_conversion(self):
        """测试环境变量类型转换"""
        with patch.dict(os.environ, {
            'MSEARCH_SYSTEM_MAX_WORKERS': '8',
            'MSEARCH_CUSTOM_SECTION_BOOLEAN_VALUE': 'false'
        }):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                yaml.dump(self.test_config_data, f)
                config_path = f.name
            
            try:
                config_manager = ConfigManager(config_path)
                assert config_manager.get('system.max_workers') == 8  # 整数转换
                assert config_manager.get('custom_section.boolean_value') == False  # 布尔转换
            finally:
                os.unlink(config_path)
    
    def test_invalid_yaml_config(self):
        """测试无效的YAML配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write('invalid: yaml: content: [')
            config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path)
            # 应该使用默认配置
            assert 'system' in config_manager.config
        finally:
            os.unlink(config_path)
    
    def test_empty_config_file(self):
        """测试空配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write('')
            config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path)
            # 应该使用默认配置
            assert 'system' in config_manager.config
        finally:
            os.unlink(config_path)
    
    def test_generate_default_config(self):
        """测试生成默认配置"""
        config_manager = ConfigManager('nonexistent.yml')
        default_config = config_manager._generate_default_config()
        
        assert 'system' in default_config
        assert 'database' in default_config
        assert 'infinity' in default_config
        assert 'media_processing' in default_config
        assert 'face_recognition' in default_config
        assert 'smart_retrieval' in default_config
        
        # 验证关键配置项
        assert default_config['system']['log_level'] == 'INFO'
        assert 'sqlite' in default_config['database']
        assert 'qdrant' in default_config['database']