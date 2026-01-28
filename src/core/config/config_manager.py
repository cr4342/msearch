#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
负责加载和管理系统配置
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 从环境变量获取
        if 'MSEARCH_CONFIG' in os.environ:
            return os.environ['MSEARCH_CONFIG']
        
        # 从项目结构获取
        project_root = Path(__file__).parent.parent.parent.parent
        config_path = project_root / 'config' / 'config.yml'
        
        return str(config_path)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            logger.warning(f"配置文件不存在: {self.config_path}")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"配置文件加载成功: {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'models': {
                'model_cache_dir': 'data/models',
                'offline_mode': True,
                'available_models': {
                    'chinese_clip_large': {
                        'model_id': 'chinese_clip_large',
                        'model_name': 'OFA-Sys/chinese-clip-vit-large-patch14-336px',
                        'local_path': 'data/models/chinese-clip-vit-large-patch14-336px',
                        'engine': 'torch',
                        'device': 'cpu',
                        'dtype': 'float32',
                        'embedding_dim': 768,
                        'trust_remote_code': True,
                        'pooling_method': 'mean',
                        'compile': False,
                        'batch_size': 8,
                        'description': '中文CLIP中量级模型，适合生产环境'
                    },
                    'audio_model': {
                        'model_id': 'audio',
                        'model_name': 'laion/clap-htsat-unfused',
                        'local_path': 'data/models/clap-htsat-unfused',
                        'engine': 'torch',
                        'device': 'cpu',
                        'dtype': 'float32',
                        'embedding_dim': 512,
                        'trust_remote_code': True,
                        'pooling_method': 'mean',
                        'compile': False,
                        'batch_size': 8,
                        'description': 'CLAP音频模型，支持文本-音频检索'
                    }
                },
                'active_models': ['chinese_clip_large', 'audio_model'],
                'performance': {
                    'enable_model_warmup': True,
                    'enable_dynamic_batching': True,
                    'max_concurrent_requests': 10,
                    'request_timeout': 30
                },
                'offline_mode': {
                    'enabled': True,
                    'model_cache_dir': 'data/models'
                },
                'infinity_config': {
                    'compile': False,
                    'dtype': 'float32',
                    'embedding_dtype': 'float32',
                    'engine': 'torch',
                    'trust_remote_code': True
                }
            },
            'database': {
                'lancedb': {
                    'data_dir': 'data/database/lancedb',
                    'collection_name': 'unified_vectors',
                    'index_type': 'ivf_pq',
                    'num_partitions': 128,
                    'vector_dimension': 512
                }
            },
            'file_scanner': {
                'enabled': True,
                'scan_interval': 60,
                'max_workers': 4,
                'supported_extensions': {
                    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
                    'video': ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.webm'],
                    'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'],
                    'document': ['.pdf', '.doc', '.docx', '.txt', '.md', '.html']
                }
            },
            'task_manager': {
                'max_concurrent_tasks': 10,
                'task_timeout': 3600,
                'retry_count': 3
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000,
                'workers': 4
            },
            'webui': {
                'host': '0.0.0.0',
                'port': 7860
            }
        }
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            配置字典
        """
        return self.config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点分隔符
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_models_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self.config.get('models', {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self.config.get('database', {})
    
    def get_file_scanner_config(self) -> Dict[str, Any]:
        """获取文件扫描器配置"""
        return self.config.get('file_scanner', {})
    
    def get_task_manager_config(self) -> Dict[str, Any]:
        """获取任务管理器配置"""
        return self.config.get('task_manager', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self.config.get('api', {})
    
    def get_webui_config(self) -> Dict[str, Any]:
        """获取WebUI配置"""
        return self.config.get('webui', {})
    
    def reload(self) -> None:
        """重新加载配置"""
        self.config = self._load_config()
        logger.info("配置已重新加载")
