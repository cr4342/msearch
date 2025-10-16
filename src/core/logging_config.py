"""
日志配置模块
负责设置和管理应用程序日志
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Dict, Any


def setup_logging(config: Dict[str, Any] = None):
    """
    设置日志配置
    
    Args:
        config: 配置字典
    """
    # 确保日志目录存在
    log_dir = Path("logs")
    if config and "paths" in config and "log_file_path" in config["paths"]:
        log_dir = Path(config["paths"]["log_file_path"]).parent
    log_dir.mkdir(exist_ok=True)
    
    # 日志配置
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": str(log_dir / "msearch.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(log_dir / "error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console", "file", "error_file"],
                "level": "DEBUG",
                "propagate": False
            }
        }
    }
    
    # 应用日志配置
    logging.config.dictConfig(log_config)


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)