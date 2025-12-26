"""
测试ConfigManager组件的修复功能
"""

import os
import tempfile
import time
import pytest
import yaml
from src.core.config_manager import ConfigManager


class TestConfigManagerFixed:
    """测试ConfigManager修复后的功能"""
    
    def test_config_validation(self):
        """测试配置验证功能"""
        # 创建一个临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            config = {
                'database': {
                    'sqlite': {
                        'path': './data/msearch.db'
                    },
                    'faiss': {
                        'data_dir': './data/faiss'
                    }
                },
                'infinity': {
                    'services': {
                        'clip': {
                            'port': 7997
                        }
                    }
                },
                'face_recognition': {
                    'matching': {
                        'similarity_threshold': 0.6
                    }
                }
            }
            yaml.dump(config, f)
            config_path = f.name
        
        try:
            # 创建配置管理器实例
            config_manager = ConfigManager(config_path)
            
            # 测试validate_config方法
            assert config_manager.validate_config() == True
            
            # 测试无效配置
            invalid_config = config.copy()
            invalid_config['database']['faiss']['data_dir'] = None
            assert config_manager.validate_config(invalid_config) == False
            
        finally:
            # 清理临时文件
            os.unlink(config_path)
    
    def test_config_validation_with_default_config(self):
        """测试使用默认配置的验证"""
        # 创建一个空的配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            config_path = f.name
        
        try:
            # 创建配置管理器实例
            config_manager = ConfigManager(config_path)
            
            # 测试validate_config方法（使用默认配置）
            assert config_manager.validate_config() == True
            
        finally:
            # 清理临时文件
            os.unlink(config_path)
    
    def test_config_reload(self):
        """测试配置重新加载功能"""
        # 创建初始配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            config = {
                'system': {
                    'log_level': 'INFO'
                },
                'database': {
                    'sqlite': {
                        'path': './data/msearch.db'
                    },
                    'faiss': {
                        'data_dir': './data/faiss'
                    }
                },
                'infinity': {
                    'services': {
                        'clip': {
                            'port': 7997
                        }
                    }
                },
                'face_recognition': {
                    'matching': {
                        'similarity_threshold': 0.6
                    }
                }
            }
            yaml.dump(config, f)
            config_path = f.name
        
        try:
            # 创建配置管理器实例
            config_manager = ConfigManager(config_path)
            
            # 获取初始配置
            initial_log_level = config_manager.get('system.log_level')
            assert initial_log_level == 'INFO'
            
            # 修改配置文件
            with open(config_path, 'w') as f:
                config['system']['log_level'] = 'DEBUG'
                yaml.dump(config, f)
            
            # 手动调用reload方法
            config_manager.reload()
            
            # 检查配置是否已更新
            updated_log_level = config_manager.get('system.log_level')
            assert updated_log_level == 'DEBUG'
            
        finally:
            # 清理临时文件
            os.unlink(config_path)
    
    def test_config_manager_initialization(self):
        """测试配置管理器初始化"""
        # 创建一个有效的配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            config = {
                'database': {
                    'sqlite': {
                        'path': './data/msearch.db'
                    },
                    'faiss': {
                        'data_dir': './data/faiss'
                    }
                },
                'infinity': {
                    'services': {
                        'clip': {
                            'port': 7997
                        }
                    }
                },
                'face_recognition': {
                    'matching': {
                        'similarity_threshold': 0.6
                    }
                }
            }
            yaml.dump(config, f)
            config_path = f.name
        
        try:
            # 创建配置管理器实例
            config_manager = ConfigManager(config_path)
            
            # 验证配置已正确加载
            assert config_manager.get('database.sqlite.path') == './data/msearch.db'
            assert config_manager.get('database.faiss.data_dir') == './data/faiss'
            assert config_manager.get('infinity.services.clip.port') == 7997
            assert config_manager.get('face_recognition.matching.similarity_threshold') == 0.6
            
        finally:
            # 清理临时文件
            os.unlink(config_path)
    
    def test_missing_config_file(self):
        """测试配置文件不存在的情况"""
        # 使用一个不存在的配置文件路径
        non_existent_path = './non_existent_config.yml'
        
        # 确保文件不存在
        if os.path.exists(non_existent_path):
            os.unlink(non_existent_path)
        
        # 创建配置管理器实例，应该使用默认配置
        config_manager = ConfigManager(non_existent_path)
        
        # 验证配置已使用默认值
        assert config_manager.get('database.sqlite.path') == './data/msearch.db'
        assert config_manager.get('database.faiss.data_dir') == './data/faiss'
        assert config_manager.validate_config() == True
