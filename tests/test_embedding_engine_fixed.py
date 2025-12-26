"""
测试EmbeddingEngine组件的修复功能
"""

import os
import tempfile
import pytest
import numpy as np
from src.common.embedding.embedding_engine import EmbeddingEngine
from src.core.config_manager import ConfigManager


class TestEmbeddingEngineFixed:
    """测试EmbeddingEngine修复后的功能"""
    
    def test_embedding_engine_initialization(self):
        """测试EmbeddingEngine初始化"""
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
            import yaml
            yaml.dump(config, f)
            config_path = f.name
        
        try:
            # 创建配置管理器实例
            config_manager = ConfigManager(config_path)
            
            # 创建EmbeddingEngine实例
            embedding_engine = EmbeddingEngine(config_manager)
            
            # 验证引擎初始化成功
            assert embedding_engine is not None
            
            # 验证faiss_adapter已初始化
            assert hasattr(embedding_engine, 'faiss_adapter')
            
        finally:
            # 清理临时文件
            os.unlink(config_path)
    
    def test_get_available_models(self):
        """测试获取可用模型列表"""
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
                        },
                        'clap': {
                            'port': 7998
                        },
                        'whisper': {
                            'port': 7999
                        }
                    }
                },
                'face_recognition': {
                    'matching': {
                        'similarity_threshold': 0.6
                    }
                }
            }
            import yaml
            yaml.dump(config, f)
            config_path = f.name
        
        try:
            # 创建配置管理器实例
            config_manager = ConfigManager(config_path)
            
            # 创建EmbeddingEngine实例
            embedding_engine = EmbeddingEngine(config_manager)
            
            # 测试获取可用模型列表
            models = embedding_engine.get_available_models()
            assert isinstance(models, list)
            
        finally:
            # 清理临时文件
            os.unlink(config_path)
    
    def test_is_model_available(self):
        """测试模型可用性检查"""
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
            import yaml
            yaml.dump(config, f)
            config_path = f.name
        
        try:
            # 创建配置管理器实例
            config_manager = ConfigManager(config_path)
            
            # 创建EmbeddingEngine实例
            embedding_engine = EmbeddingEngine(config_manager)
            
            # 测试模型可用性检查
            assert isinstance(embedding_engine.is_model_available('clip'), bool)
            assert isinstance(embedding_engine.is_model_available('non_existent_model'), bool)
            
        finally:
            # 清理临时文件
            os.unlink(config_path)
    
    @pytest.mark.asyncio
    async def test_faiss_health_check(self):
        """测试FAISS健康检查"""
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
            import yaml
            yaml.dump(config, f)
            config_path = f.name
        
        try:
            # 创建配置管理器实例
            config_manager = ConfigManager(config_path)
            
            # 创建EmbeddingEngine实例
            embedding_engine = EmbeddingEngine(config_manager)
            
            # 测试FAISS健康检查
            health_status = await embedding_engine.faiss_health_check()
            assert isinstance(health_status, dict)
            assert 'status' in health_status
            
        finally:
            # 清理临时文件
            os.unlink(config_path)
    
    def test_get_model_info(self):
        """测试获取模型信息"""
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
                            'port': 7997,
                            'device': 'cpu'  # 使用CPU设备，避免CUDA错误
                        }
                    }
                },
                'face_recognition': {
                    'matching': {
                        'similarity_threshold': 0.6
                    }
                }
            }
            import yaml
            yaml.dump(config, f)
            config_path = f.name
        
        try:
            # 创建配置管理器实例
            config_manager = ConfigManager(config_path)
            
            # 创建EmbeddingEngine实例
            embedding_engine = EmbeddingEngine(config_manager)
            
            # 测试获取模型信息
            # 检查clip模型是否可用
            if embedding_engine.is_model_available('clip'):
                model_info = embedding_engine.get_model_info('clip')
                assert isinstance(model_info, dict)
                assert 'name' in model_info
                assert 'status' in model_info
            else:
                # 如果模型不可用，验证get_model_info会抛出ValueError
                with pytest.raises(ValueError):
                    embedding_engine.get_model_info('clip')
            
        finally:
            # 清理临时文件
            os.unlink(config_path)
