# -*- coding: utf-8 -*-
"""
系统配置文件
定义所有配置类和配置加载逻辑
"""

import os
import yaml
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """数据库配置"""
    type: str = "sqlite"
    path: str = "./data/msearch.db"
    connection_pool_size: int = 10
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class ModelConfig:
    """模型配置"""
    model_name: str
    port: int
    path: str = ""
    vector_dim: int = 512
    local: bool = True
    device: str = "auto"
    max_batch_size: int = 32
    dtype: str = "float32"


@dataclass
class InfinityConfig:
    """Infinity引擎配置"""
    host: str = "localhost"
    port: int = 7997
    timeout: int = 30
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    health_check: Dict[str, Any] = field(default_factory=dict)
    resource_monitor: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MilvusConfig:
    """Milvus Lite配置"""
    type: str = "milvus_lite"
    host: str = "127.0.0.1"
    port: int = 19530
    uri: str = "./data/milvus/milvus.db"
    data_dir: str = "./data/milvus"
    metric_type: str = "COSINE"
    index_type: str = "IVF_FLAT"
    nlist: int = 1024
    nprobe: int = 10
    batch_size: int = 100
    collections: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApiConfig:
    """API配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    debug: bool = False
    timeout: int = 30
    enable_cors: bool = True


@dataclass
class ProcessingConfig:
    """处理配置"""
    max_workers: int = 4
    batch_size: int = 10
    timeout: int = 300
    enable_scene_detection: bool = True
    enable_face_detection: bool = False
    enable_audio_separation: bool = True


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    file_path: str = "./logs/msearch.log"
    max_bytes: int = 10485760
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class StorageConfig:
    """存储配置"""
    data_path: str = "./data"
    models_path: str = "./data/models"
    cache_path: str = "./cache"
    temp_path: str = "./temp"
    max_cache_size: int = 1073741824
    milvus_path: str = "./data/milvus"


@dataclass
class CacheConfig:
    """缓存配置"""
    memory: Dict[str, Any] = field(default_factory=dict)
    disk: Dict[str, Any] = field(default_factory=dict)
    vector: Dict[str, Any] = field(default_factory=dict)
    strategies: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemConfig:
    """系统配置"""
    name: str = "msearch"
    version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    data_dir: str = "./data"
    temp_dir: str = "./temp"
    monitored_directories: List[str] = field(default_factory=list)
    supported_extensions: List[str] = field(default_factory=list)
    debounce_delay: float = 0.5
    max_workers: int = 4
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    milvus: MilvusConfig = field(default_factory=MilvusConfig)
    infinity: InfinityConfig = field(default_factory=InfinityConfig)
    api: ApiConfig = field(default_factory=ApiConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    performance: Dict[str, Any] = field(default_factory=dict)
    media_processing: Dict[str, Any] = field(default_factory=dict)
    face_recognition: Dict[str, Any] = field(default_factory=dict)
    smart_retrieval: Dict[str, Any] = field(default_factory=dict)
    orchestrator: Dict[str, Any] = field(default_factory=dict)
    task_manager: Dict[str, Any] = field(default_factory=dict)
    model_download: Dict[str, Any] = field(default_factory=dict)


def load_config(config_path: Optional[str] = None) -> SystemConfig:
    """从配置文件加载系统配置
    
    Args:
        config_path: 配置文件路径，如果为None则使用默认路径
        
    Returns:
        SystemConfig: 系统配置对象
    """
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "msearch.yml")
    
    if not os.path.exists(config_path):
        return SystemConfig()
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    system_config = SystemConfig()
    
    if 'system' in config_data:
        system_config.name = config_data['system'].get('name', system_config.name)
        system_config.version = config_data['system'].get('version', system_config.version)
        system_config.debug = config_data['system'].get('debug', system_config.debug)
        system_config.log_level = config_data['system'].get('log_level', system_config.log_level)
        system_config.data_dir = config_data['system'].get('data_dir', system_config.data_dir)
        system_config.temp_dir = config_data['system'].get('temp_dir', system_config.temp_dir)
        system_config.monitored_directories = config_data['system'].get('monitored_directories', [])
        system_config.supported_extensions = config_data['system'].get('supported_extensions', [])
        system_config.debounce_delay = config_data['system'].get('debounce_delay', system_config.debounce_delay)
        system_config.max_workers = config_data['system'].get('max_workers', system_config.max_workers)
    
    if 'storage' in config_data:
        storage_data = config_data['storage']
        system_config.storage = StorageConfig(
            data_path=storage_data.get('data_path', './data'),
            models_path=storage_data.get('models_path', './data/models'),
            cache_path=storage_data.get('cache_path', './cache'),
            temp_path=storage_data.get('temp_path', './temp'),
            max_cache_size=storage_data.get('max_cache_size', 1073741824),
            milvus_path=storage_data.get('milvus_path', './data/milvus')
        )
    
    if 'logging' in config_data:
        logging_data = config_data['logging']
        system_config.logging = LoggingConfig(
            level=logging_data.get('level', 'INFO'),
            file_path=logging_data.get('file_path', './logs/msearch.log'),
            max_bytes=logging_data.get('max_bytes', 10485760),
            backup_count=logging_data.get('backup_count', 5),
            format=logging_data.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
    
    if 'database' in config_data:
        db_data = config_data['database']
        
        # 加载SQLite配置
        system_config.database = DatabaseConfig(
            type='sqlite',
            path=db_data.get('sqlite', {}).get('path', './data/msearch.db'),
            connection_pool_size=db_data.get('sqlite', {}).get('connection_pool_size', 10),
            timeout=db_data.get('sqlite', {}).get('timeout', 30),
            max_retries=3,
            retry_delay=1.0
        )
        
        # 加载Milvus配置
        milvus_data = db_data.get('milvus', {})
        system_config.milvus = MilvusConfig(
            type=db_data.get('vector_db', {}).get('type', 'milvus_lite'),
            host=milvus_data.get('host', '127.0.0.1'),
            port=milvus_data.get('port', 19530),
            uri=milvus_data.get('uri', './data/milvus/milvus.db'),
            data_dir=milvus_data.get('data_dir', './data/milvus'),
            metric_type=milvus_data.get('collections', {}).get('image_vectors', {}).get('metric_type', 'COSINE'),
            index_type=milvus_data.get('collections', {}).get('image_vectors', {}).get('index_type', 'IVF_FLAT'),
            nlist=milvus_data.get('collections', {}).get('image_vectors', {}).get('index_params', {}).get('nlist', 1024),
            nprobe=milvus_data.get('collections', {}).get('image_vectors', {}).get('search_params', {}).get('nprobe', 10),
            batch_size=100,
            collections=milvus_data.get('collections', {})
        )
    
    if 'models' in config_data:
        models_data = config_data['models']
        system_config.models = {}
        for model_name, model_info in models_data.items():
            system_config.models[model_name] = ModelConfig(
                model_name=model_info.get('model_name', ''),
                port=model_info.get('port', 0),
                path=model_info.get('path', ''),
                vector_dim=model_info.get('vector_dim', 512),
                local=model_info.get('local', True),
                device=model_info.get('device', 'auto'),
                max_batch_size=model_info.get('max_batch_size', 32),
                dtype=model_info.get('dtype', 'float32')
            )
    
    if 'infinity' in config_data:
        inf_data = config_data['infinity']
        system_config.infinity = InfinityConfig(
            host=inf_data.get('host', 'localhost'),
            port=inf_data.get('port', 7997),
            timeout=inf_data.get('timeout', 30),
            models=system_config.models,
            health_check=inf_data.get('health_check', {}),
            resource_monitor=inf_data.get('resource_monitor', {})
        )
    
    if 'api' in config_data:
        api_data = config_data['api']
        system_config.api = ApiConfig(
            host=api_data.get('host', '0.0.0.0'),
            port=api_data.get('port', 8000),
            workers=api_data.get('workers', 4),
            debug=api_data.get('debug', False),
            timeout=api_data.get('timeout', 30),
            enable_cors=api_data.get('enable_cors', True)
        )
    
    if 'performance' in config_data:
        system_config.performance = config_data['performance']
    
    if 'cache' in config_data:
        cache_data = config_data['cache']
        system_config.cache = CacheConfig(
            memory=cache_data.get('memory', {}),
            disk=cache_data.get('disk', {}),
            vector=cache_data.get('vector', {}),
            strategies=cache_data.get('strategies', {})
        )
    
    if 'media_processing' in config_data:
        media_data = config_data['media_processing']
        system_config.processing = ProcessingConfig(
            max_workers=media_data.get('max_workers', 4),
            batch_size=media_data.get('batch_size', 10),
            timeout=media_data.get('timeout', 300),
            enable_scene_detection=media_data.get('enable_scene_detection', True),
            enable_face_detection=media_data.get('enable_face_detection', False),
            enable_audio_separation=media_data.get('enable_audio_separation', True)
        )
        system_config.media_processing = media_data
    
    if 'face_recognition' in config_data:
        system_config.face_recognition = config_data['face_recognition']
    
    if 'smart_retrieval' in config_data:
        system_config.smart_retrieval = config_data['smart_retrieval']
    
    if 'orchestrator' in config_data:
        system_config.orchestrator = config_data['orchestrator']
    
    if 'task_manager' in config_data:
        system_config.task_manager = config_data['task_manager']
    
    if 'model_download' in config_data:
        system_config.model_download = config_data['model_download']
    
    return system_config


_global_config: Optional[SystemConfig] = None


def get_config(config_path: Optional[str] = None) -> SystemConfig:
    """获取全局配置对象
    
    Args:
        config_path: 配置文件路径，如果为None则使用默认路径
        
    Returns:
        SystemConfig: 系统配置对象
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config(config_path)
    return _global_config


def reset_config():
    """重置全局配置对象"""
    global _global_config
    _global_config = None
