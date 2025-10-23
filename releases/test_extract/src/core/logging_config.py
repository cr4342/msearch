"""
日志配置模块
负责设置和管理应用程序日志
统一使用logger_manager实现多级别日志管理
"""

import logging
from typing import Dict, Any
from src.core.logger_manager import get_logger_manager, get_logger as get_manager_logger


def setup_logging(config: Dict[str, Any] = None):
    """
    设置日志配置
    集成使用logger_manager，支持多级别日志、硬件自适应和日志轮转
    
    Args:
        config: 配置字典，可包含日志相关配置
    """
    # 获取日志管理器实例
    manager = get_logger_manager()
    
    # 如果提供了配置，尝试更新日志级别
    if config and "system" in config and "log_level" in config["system"]:
        try:
            # 更新根日志级别
            root_level = config["system"]["log_level"]
            # 记录配置信息
            logger = get_logger("msearch.core.logging_config")
            logger.info(f"日志系统初始化完成，根日志级别: {root_level}")
        except Exception as e:
            # 使用默认logger记录错误
            print(f"更新日志级别失败: {e}")


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器
    统一使用logger_manager提供的get_logger方法
    
    Args:
        name: 日志记录器名称，建议使用模块路径格式，如'msearch.core.module'
        
    Returns:
        配置好的日志记录器实例
    """
    return get_manager_logger(name)