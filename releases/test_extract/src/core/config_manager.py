"""
统一配置管理器
负责加载和管理应用程序配置，支持热重载和环境变量覆盖
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class ConfigManager:
    """统一配置管理器 - 配置驱动设计"""
    
    def __init__(self, config_path: str = "config/config.yml"):
        self.config_path = config_path
        self.config = {}
        self.watchers: List[tuple] = []  # 配置变更监听器
        self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 环境变量覆盖
            config = self._apply_env_overrides(config)
            
            # 配置验证
            self._validate_config(config)
            
            self.config = config
            logger.info("配置文件加载成功")
            return config
            
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {self.config_path}")
            return self._generate_default_config()
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            raise
    
    def get(self, key: str, default=None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        
        # 通知监听器
        self._notify_watchers(key, value)
    
    def watch(self, key: str, callback: Callable[[str, Any], None]) -> None:
        """监听配置变更"""
        self.watchers.append((key, callback))
    
    def _notify_watchers(self, key: str, value: Any) -> None:
        """通知监听器配置变更"""
        for watch_key, callback in self.watchers:
            if key.startswith(watch_key) or watch_key.startswith(key):
                try:
                    callback(key, value)
                except Exception as e:
                    logger.error(f"配置监听器回调失败: {e}")
    
    def _apply_env_overrides(self, config: Dict) -> Dict:
        """应用环境变量覆盖"""
        # 支持 MSEARCH_DATABASE_SQLITE_PATH 格式的环境变量
        for key, value in os.environ.items():
            if key.startswith('MSEARCH_'):
                config_key = key[8:].lower().replace('_', '.')
                self._set_nested_value(config, config_key, value)
        
        return config
    
    def _set_nested_value(self, config: Dict, key: str, value: Any) -> None:
        """设置嵌套配置值"""
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # 尝试转换值类型
        try:
            # 如果是数字
            if value.isdigit():
                current[keys[-1]] = int(value)
            elif value.lower() in ('true', 'false'):
                current[keys[-1]] = value.lower() == 'true'
            else:
                current[keys[-1]] = value
        except:
            current[keys[-1]] = value
    
    def _validate_config(self, config: Dict) -> None:
        """验证配置完整性"""
        required_keys = [
            'database.sqlite.path',
            'database.qdrant.host',
            'infinity.services.clip.port',
            'face_recognition.matching.similarity_threshold'
        ]
        
        missing_keys = []
        for key in required_keys:
            if self._get_nested_value(config, key) is None:
                missing_keys.append(key)
        
        if missing_keys:
            logger.warning(f"缺少必需的配置项: {missing_keys}")
    
    def _get_nested_value(self, config: Dict, key: str) -> Any:
        """获取嵌套配置值"""
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value
    
    def _generate_default_config(self) -> Dict:
        """生成默认配置"""
        return {
            "system": {
                "log_level": "INFO",
                "data_dir": "./data",
                "temp_dir": "./temp",
                "max_workers": 4
            },
            "database": {
                "sqlite": {
                    "path": "./data/msearch.db",
                    "connection_pool_size": 10,
                    "timeout": 30
                },
                "qdrant": {
                    "host": "localhost",
                    "port": 6333,
                    "timeout": 30,
                    "collections": {
                        "visual_vectors": "visual_vectors",
                        "audio_music_vectors": "audio_music_vectors",
                        "audio_speech_vectors": "audio_speech_vectors"
                    }
                }
            },
            "infinity": {
                "services": {
                    "clip": {
                        "model_id": "openai/clip-vit-base-patch32",
                        "port": 7997,
                        "device": "cuda:0",
                        "max_batch_size": 32,
                        "dtype": "float16"
                    },
                    "clap": {
                        "model_id": "laion/clap-htsat-fused",
                        "port": 7998,
                        "device": "cuda:0",
                        "max_batch_size": 16,
                        "dtype": "float16"
                    },
                    "whisper": {
                        "model_id": "openai/whisper-base",
                        "port": 7999,
                        "device": "cuda:1",
                        "max_batch_size": 8,
                        "dtype": "float16"
                    }
                },
                "health_check": {
                    "interval": 30,
                    "failure_threshold": 3,
                    "timeout": 5
                },
                "resource_monitor": {
                    "interval": 60,
                    "gpu_threshold": 0.9,
                    "memory_threshold": 0.85,
                    "auto_cleanup": True
                }
            },
            "media_processing": {
                "video": {
                    "max_resolution": 960,
                    "target_fps": 8,
                    "codec": "h264",
                    "scene_detection": {
                        "enabled": True,
                        "threshold": 30.0,
                        "min_scene_length": 30,
                        "max_scene_length": 120
                    }
                },
                "audio": {
                    "sample_rate": 16000,
                    "channels": 1,
                    "bitrate": 64000,
                    "codec": "aac",
                    "quality_filter": {
                        "min_duration": 3.0,
                        "min_snr_ratio": 5.0,
                        "enable_silence_detection": True
                    }
                }
            },
            "face_recognition": {
                "enabled": True,
                "model": "facenet",
                "detector": "mtcnn",
                "detection": {
                    "min_face_size": 40,
                    "confidence_threshold": 0.9,
                    "nms_threshold": 0.4
                },
                "feature_extraction": {
                    "vector_dim": 512,
                    "normalize": True
                },
                "matching": {
                    "similarity_threshold": 0.6,
                    "enable_fuzzy_matching": True,
                    "fuzzy_threshold": 0.8,
                    "max_matches": 10
                },
                "indexing": {
                    "video_sample_interval": 5,
                    "batch_size": 16,
                    "enable_clustering": False
                }
            },
            "smart_retrieval": {
                "default_weights": {
                    "clip": 0.4,
                    "clap": 0.3,
                    "whisper": 0.3
                },
                "person_weights": {
                    "clip": 0.5,
                    "clap": 0.25,
                    "whisper": 0.25
                },
                "audio_weights": {
                    "music": {
                        "clip": 0.2,
                        "clap": 0.7,
                        "whisper": 0.1
                    },
                    "speech": {
                        "clip": 0.2,
                        "clap": 0.1,
                        "whisper": 0.7
                    }
                },
                "visual_weights": {
                    "clip": 0.7,
                    "clap": 0.15,
                    "whisper": 0.15
                },
                "keywords": {
                    "music": ["音乐", "歌曲", "MV", "音乐视频", "歌", "曲子", "旋律", "节拍"],
                    "speech": ["讲话", "演讲", "会议", "访谈", "对话", "发言", "语音"],
                    "visual": ["画面", "场景", "图像", "图片", "视频画面", "截图"]
                }
            }
        }


# 全局配置实例
config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    return config_manager


def get_config() -> Dict[str, Any]:
    """获取全局配置字典"""
    return config_manager.config


def get_config_value(key: str, default=None) -> Any:
    """获取配置值"""
    return config_manager.get(key, default)