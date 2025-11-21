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
            
            # 如果配置为空（空文件），使用默认配置
            if config is None:
                config = {}
            
            # 合并默认配置
            default_config = self._generate_default_config()
            config = self._merge_configs(default_config, config)
            
            # 环境变量覆盖
            config = self._apply_env_overrides(config)
            
            # 配置验证
            self._validate_config(config)
            
            self.config = config
            logger.info("配置文件加载成功")
            return config
            
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {self.config_path}")
            config = self._generate_default_config()
            # 应用环境变量覆盖到默认配置
            config = self._apply_env_overrides(config)
            self.config = config
            return config
        except yaml.YAMLError as e:
            logger.error(f"配置文件YAML格式错误: {e}")
            config = self._generate_default_config()
            # 应用环境变量覆盖到默认配置
            config = self._apply_env_overrides(config)
            self.config = config
            return config
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            config = self._generate_default_config()
            # 应用环境变量覆盖到默认配置
            config = self._apply_env_overrides(config)
            self.config = config
            return config
    
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
                # 将环境变量名转换为配置键
                # 环境变量使用 MSEARCH_前缀_KEY_NAME 格式
                # 配置文件中的键使用 key.name 或 key_name 格式
                # 为了简化映射，我们直接使用下划线替换为点的方式
                # 但需要特殊处理，以确保映射到正确的配置键
                
                # 例如: MSEARCH_GENERAL_LOG_LEVEL -> general.log_level
                config_key = key[8:].lower().replace('_', '.')
                
                logger.debug(f"应用环境变量覆盖: {key} -> {config_key} = {value}")
                
                # 特殊处理：对于某些常见的键，需要调整映射
                # 例如 general.log.level 应该映射到 general.log_level
                # 但我们先按当前方式处理，然后在_get_nested_value中处理映射
                
                self._set_nested_value(config, config_key, value)
        
        return config
    
    def _set_nested_value(self, config: Dict, key: str, value: Any) -> None:
        """设置嵌套配置值"""
        # 处理点号分隔的嵌套键
        keys = key.split('.')
        current = config
        
        # 特殊情况处理：对于常见的环境变量映射
        # 如果要设置 general.log.level，但实际配置中是 general.log_level
        # 我们需要检查是否存在替代的键名
        if len(keys) == 3 and keys[0] == 'general' and keys[1] == 'log' and keys[2] == 'level':
            # 直接设置 general.log_level
            try:
                if isinstance(value, str) and value.isdigit():
                    config['general']['log_level'] = int(value)
                elif isinstance(value, str) and value.lower() in ('true', 'false'):
                    config['general']['log_level'] = value.lower() == 'true'
                else:
                    config['general']['log_level'] = value
            except:
                config['general']['log_level'] = value
            return
            
        # 特殊处理：对于数据库路径的环境变量映射
        if len(keys) == 3 and keys[0] == 'database' and keys[1] == 'sqlite' and keys[2] == 'path':
            # 直接设置 database.sqlite.path
            try:
                config['database']['sqlite']['path'] = value
            except:
                if 'database' not in config:
                    config['database'] = {}
                if 'sqlite' not in config['database']:
                    config['database']['sqlite'] = {}
                config['database']['sqlite']['path'] = value
            return
            
        # 对于其他情况，按正常嵌套结构处理
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # 尝试转换值类型
        try:
            # 如果是数字
            if isinstance(value, str) and value.isdigit():
                current[keys[-1]] = int(value)
            elif isinstance(value, str) and value.lower() in ('true', 'false'):
                current[keys[-1]] = value.lower() == 'true'
            else:
                current[keys[-1]] = value
        except:
            current[keys[-1]] = value
    
    def _merge_configs(self, default: Dict, custom: Dict) -> Dict:
        """合并配置，自定义配置覆盖默认配置"""
        result = default.copy()
        
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
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