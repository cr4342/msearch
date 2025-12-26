# -*- coding: utf-8 -*-
"""
系统配置文件
定义所有配置类和默认配置
"""

from typing import Dict, Optional, List, Any
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """数据库配置"""
    type: str = "sqlite"
    path: str = "./data/database/msearch.db"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class ModelConfig:
    """模型配置"""
    model_id: str
    port: int
    device: str = "cuda:0"
    max_batch_size: int = 32
    dtype: str = "float16"


@dataclass
class InfinityConfig:
    """Infinity引擎配置"""
    host: str = "localhost"
    port: int = 7997
    timeout: int = 30
    models: Dict[str, ModelConfig] = None
    
    def __post_init__(self):
        if self.models is None:
            self.models = {
                "clip": ModelConfig("openai/clip-vit-base-patch32", 7997),
                "clap": ModelConfig("laion/clap-htsat-unfused", 7998),
                "whisper": ModelConfig("openai/whisper-base", 7999)
            }


@dataclass
class FAISSConfig:
    """FAISS配置"""
    index_path: str = "./data/database/faiss_indices"
    metric_type: str = "cosine"
    nprobe: int = 10
    batch_size: int = 100
    collections: Dict[str, str] = None
    
    def __post_init__(self):
        if self.collections is None:
            self.collections = {
                "visual_vectors": "visual_vectors",
                "audio_music_vectors": "audio_music_vectors",
                "audio_speech_vectors": "audio_speech_vectors",
                "face_vectors": "face_vectors",
                "text_vectors": "text_vectors"
            }


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
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class StorageConfig:
    """存储配置"""
    data_path: str = "./data"
    models_path: str = "./data/models"
    cache_path: str = "./cache"
    temp_path: str = "./temp"
    max_cache_size: int = 1073741824  # 1GB


@dataclass
class SystemConfig:
    """系统配置"""
    name: str = "msearch"
    version: str = "0.1.0"
    debug: bool = False
    database: DatabaseConfig = None
    faiss: FAISSConfig = None
    infinity: InfinityConfig = None
    api: ApiConfig = None
    processing: ProcessingConfig = None
    logging: LoggingConfig = None
    storage: StorageConfig = None
    
    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig()
        if self.faiss is None:
            self.faiss = FAISSConfig()
        if self.infinity is None:
            self.infinity = InfinityConfig()
        if self.api is None:
            self.api = ApiConfig()
        if self.processing is None:
            self.processing = ProcessingConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.storage is None:
            self.storage = StorageConfig()
