"""
配置管理器单元测试
"""

import pytest
import yaml
import tempfile
import os
from unittest.mock import patch
import sys

sys.path.insert(0, 'src')

from src.core.config_manager import ConfigManager


def test_config_manager_initialization():
    """测试配置管理器初始化"""
    test_config_data = {
        'system': {
            'log_level': 'INFO',
            'data_dir': './data'
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(test_config_data, f)
        config_path = f.name
    
    try:
        config_manager = ConfigManager(config_path)
        assert config_manager.config_path == config_path
        assert config_manager.config is not None
        print("✓ 配置管理器初始化测试通过")
    finally:
        os.unlink(config_path)


def test_get_nested_value():
    """测试获取嵌套配置值"""
    test_config_data = {
        'system': {
            'log_level': 'INFO',
            'max_workers': 4
        },
        'database': {
            'sqlite': {
                'path': './data/msearch.db'
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(test_config_data, f)
        config_path = f.name
    
    try:
        config_manager = ConfigManager(config_path)
        assert config_manager.get('system.log_level') == 'INFO'
        assert config_manager.get('database.sqlite.path') == './data/msearch.db'
        assert config_manager.get('nonexistent.key') is None
        assert config_manager.get('nonexistent.key', 'default') == 'default'
        print("✓ 获取嵌套配置值测试通过")
    finally:
        os.unlink(config_path)


def test_set_config_value():
    """测试设置配置值"""
    test_config_data = {
        'system': {
            'log_level': 'INFO'
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(test_config_data, f)
        config_path = f.name
    
    try:
        config_manager = ConfigManager(config_path)
        config_manager.set('new_section.key', 'new_value')
        assert config_manager.get('new_section.key') == 'new_value'
        print("✓ 设置配置值测试通过")
    finally:
        os.unlink(config_path)


def test_load_nonexistent_config():
    """测试加载不存在的配置文件"""
    config_manager = ConfigManager('nonexistent.yml')
    assert config_manager.config is not None
    assert 'system' in config_manager.config
    print("✓ 加载不存在配置文件测试通过")


def test_env_variable_override():
    """测试环境变量覆盖配置"""
    test_config_data = {
        'system': {
            'log_level': 'INFO',
            'max_workers': 4
        }
    }
    
    with patch.dict(os.environ, {
        'MSEARCH_SYSTEM_LOG_LEVEL': 'ERROR',
        'MSEARCH_SYSTEM_MAX_WORKERS': '8'
    }):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(test_config_data, f)
            config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path)
            # 环境变量应该覆盖配置文件
            assert config_manager.get('system.log_level') == 'ERROR'
            assert config_manager.get('system.max_workers') == 8  # 应该转换为整数
            print("✓ 环境变量覆盖配置测试通过")
        finally:
            os.unlink(config_path)


def test_generate_default_config():
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
    print("✓ 生成默认配置测试通过")


if __name__ == "__main__":
    # 运行所有测试
    test_config_manager_initialization()
    test_get_nested_value()
    test_set_config_value()
    test_load_nonexistent_config()
    test_env_variable_override()
    test_generate_default_config()
    print("\n🎉 所有配置管理器测试通过!")
