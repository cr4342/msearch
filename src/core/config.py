"""
配置管理器
负责加载、管理和验证系统配置
"""

import os
import yaml
from typing import Any, Dict, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config", config_file: str = "config.yml"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
            config_file: 配置文件名
        """
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / config_file
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"配置文件加载成功: {self.config_file}")
            else:
                logger.warning(f"配置文件不存在: {self.config_file}, 使用默认配置")
                self.config = self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "system": {
                "debug": False,
                "data_dir": "data/",
                "log_level": "INFO",
                "check_interval": 5,
                "hardware_level": "auto",
                "auto_model_selection": True
            },
            "task_manager": {
                "max_concurrent_tasks": 4,
                "max_retries": 3,
                "retry_delay": 1.0,
                "task_timeout": 300,
                "enable_persistence": True,
                "persistence_file": "data/tasks/task_queue.json",
                "max_concurrent_by_type": {
                    "file_scan": 1,
                    "file_embed": 2,
                    "video_slice": 2,
                    "audio_segment": 2
                },
                "task_priorities": {
                    "file_scan": 0,
                    "file_embed_image": 1,
                    "file_embed_video": 1,
                    "video_slice": 2,
                    "file_embed_text": 3,
                    "audio_segment": 4,
                    "file_embed_audio": 5,
                    "thumbnail_generate": 6,
                    "preview_generate": 7
                },
                "resource_limits": {
                    "max_memory_usage": 8589934592,
                    "max_cpu_usage": 80,
                    "max_gpu_usage": 90
                }
            },
            "monitoring": {
                "directories": [],
                "check_interval": 5,
                "debounce_delay": 500
            },
            "processing": {
                "image": {
                    "max_resolution": 2048,
                    "max_size_mb": 10,
                    "supported_formats": ['jpg', 'jpeg', 'png', 'webp']
                },
                "video": {
                    "target_resolution": 720,
                    "target_fps": 8,
                    "max_segment_duration": 5,
                    "scene_threshold": 0.15,
                    "supported_formats": ['mp4', 'avi', 'mov', 'mkv'],
                    "short_video": {
                        "enabled": True,
                        "threshold": 6.0,
                        "very_short_threshold": 2.0,
                        "short_segment_threshold": 4.0,
                        "very_short_frames": 1,
                        "short_frames": 2,
                        "medium_short_frames": 3,
                        "frame_distribution": "uniform"
                    },
                    "large_video": {
                        "size_threshold_gb": 3.0,
                        "duration_threshold_min": 30.0,
                        "initial_duration": 300.0,
                        "key_transitions": 10
                    },
                    "thumbnail": {
                        "time_offset": 0.3,
                        "size": 256
                    }
                },
                "audio": {
                    "sample_rate": 16000,
                    "channels": 1,
                    "min_music_duration": 30,
                    "min_speech_duration": 3,
                    "supported_formats": ['mp3', 'wav', 'flac', 'aac'],
                    "value_threshold": 5.0,
                    "enable_value_check": True,
                    "log_skipped_audio": True
                }
            },
            "models": {
                "cache_dir": "data/models",
                "clip_model": "openai/clip-vit-base-patch32",
                "clap_model": "laion/clap-htsat-fused",
                "whisper_model": "openai/whisper-base",
                "facenet_model": "facenet-pytorch",
                "enable_model_warmup": True,
                "image_video_model": {
                    "auto_select": True,
                    "mobileclip": {
                        "model_name": "apple/mobileclip",
                        "device": "auto",
                        "batch_size": 16,
                        "precision": "float16",
                        "max_resolution": 224,
                        "memory_requirement": "2GB",
                        "enable_cache": True
                    },
                    "colsmol_500m": {
                        "model_name": "vidore/colSmol-500M",
                        "device": "auto",
                        "batch_size": 12,
                        "precision": "float16",
                        "max_resolution": 336,
                        "max_frames": 16,
                        "frame_interval": 2,
                        "memory_requirement": "4GB"
                    },
                    "colqwen2_5_v0_2": {
                        "model_name": "vidore/colqwen2.5-v0.2",
                        "device": "auto",
                        "batch_size": 8,
                        "precision": "float16",
                        "max_resolution": 448,
                        "max_frames": 32,
                        "frame_interval": 1,
                        "memory_requirement": "8GB"
                    }
                }
            },
            "database": {
                "sqlite": {
                    "path": "data/database/sqlite/msearch.db",
                    "enable_wal": True
                },
                "lancedb": {
                    "data_dir": "data/database/lancedb",
                    "index_type": "ivf_pq",
                    "num_partitions": 128
                }
            },
            "retry": {
                "initial_delay": 1,
                "multiplier": 2,
                "max_attempts": 5,
                "task_specific": {
                    "preprocessing": {
                        "max_attempts": 3,
                        "initial_delay": 0.5
                    },
                    "vectorization": {
                        "max_attempts": 5,
                        "initial_delay": 1
                    },
                    "storage": {
                        "max_attempts": 3,
                        "initial_delay": 0.5
                    }
                }
            },
            "logging": {
                "level": "INFO",
                "format": '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                "rotation": {
                    "max_size_mb": 100,
                    "backup_count": 10
                },
                "handlers": {
                    "console": {
                        "enabled": True
                    },
                    "file": {
                        "enabled": True,
                        "path": "logs/msearch.log"
                    },
                    "error_file": {
                        "enabled": True,
                        "path": "logs/error.log",
                        "level": "ERROR"
                    },
                    "performance_file": {
                        "enabled": True,
                        "path": "logs/performance.log",
                        "level": "INFO"
                    },
                    "timestamp_file": {
                        "enabled": True,
                        "path": "logs/timestamp.log",
                        "level": "DEBUG"
                    }
                }
            },
            "api": {
                "host": "127.0.0.1",
                "port": 8000,
                "enable_cors": True,
                "rate_limit": {
                    "enabled": True,
                    "requests_per_minute": 60
                }
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，使用点号分隔，如 "system.log_level"
            default: 默认值
        
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key_path: 配置键路径，使用点号分隔
            value: 配置值
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            配置字典
        """
        return self.config.copy()
    
    def reload(self) -> bool:
        """
        重新加载配置文件
        
        Returns:
            是否成功
        """
        try:
            self._load_config()
            return True
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            return False
    
    def validate(self) -> Tuple[bool, list]:
        """
        验证配置完整性
        
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        # 验证必需的配置项
        required_keys = [
            "system.data_dir",
            "system.log_level",
            "database.sqlite.path",
            "database.lancedb.data_dir",
            "models.cache_dir"
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                errors.append(f"缺少必需的配置项: {key}")
        
        # 验证日志级别
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = self.get("system.log_level")
        if log_level and log_level not in valid_log_levels:
            errors.append(f"无效的日志级别: {log_level}")
        
        return (len(errors) == 0, errors)
    
    def save(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            是否成功
        """
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"配置文件保存成功: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def get_schema(self) -> Dict[str, Any]:
        """
        获取配置schema
        
        Returns:
            配置schema
        """
        return {
            "system": {
                "debug": "boolean",
                "data_dir": "string",
                "log_level": "enum(DEBUG,INFO,WARNING,ERROR,CRITICAL)",
                "check_interval": "integer",
                "hardware_level": "enum(auto,low,mid,high)",
                "auto_model_selection": "boolean"
            },
            "task_manager": {
                "max_concurrent_tasks": "integer",
                "max_retries": "integer",
                "retry_delay": "float",
                "task_timeout": "integer",
                "enable_persistence": "boolean"
            },
            "database": {
                "sqlite": {
                    "path": "string",
                    "enable_wal": "boolean"
                },
                "lancedb": {
                    "data_dir": "string",
                    "index_type": "string",
                    "num_partitions": "integer"
                }
            },
            "models": {
                "cache_dir": "string",
                "clip_model": "string",
                "clap_model": "string",
                "whisper_model": "string",
                "enable_model_warmup": "boolean"
            }
        }
    
    def apply_schema(self, schema: Dict[str, Any]) -> bool:
        """
        应用配置schema
        
        Args:
            schema: 配置schema
        
        Returns:
            是否成功
        """
        # TODO: 实现schema验证和应用逻辑
        return True
    
    def convert_types(self) -> None:
        """转换配置值类型"""
        # TODO: 实现类型转换逻辑
        pass
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            默认配置字典
        """
        return self._get_default_config()
    
    def export_config(self, export_path: str) -> bool:
        """
        导出配置到文件
        
        Args:
            export_path: 导出路径
        
        Returns:
            是否成功
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"配置导出成功: {export_path}")
            return True
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """
        从文件导入配置
        
        Args:
            import_path: 导入路径
        
        Returns:
            是否成功
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = yaml.safe_load(f)
            
            # 合并配置
            self._deep_merge(self.config, imported_config)
            logger.info(f"配置导入成功: {import_path}")
            return True
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False
    
    def _deep_merge(self, base: Dict, update: Dict) -> None:
        """
        深度合并字典
        
        Args:
            base: 基础字典
            update: 更新字典
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value