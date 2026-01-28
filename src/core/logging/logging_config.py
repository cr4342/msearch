"""
统一日志配置管理器
配置和管理系统日志系统
"""

import logging
import logging.handlers
from typing import Any, Dict, Optional, List, Callable
from pathlib import Path
import time
import threading


class LoggingConfig:
    """统一日志配置管理器"""

    def __init__(self, config: Dict[str, Any], log_dir: Optional[str] = None):
        """
        初始化日志配置管理器

        Args:
            config: 日志配置字典
            log_dir: 日志目录
        """
        self.config = config
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.loggers: Dict[str, logging.Logger] = {}
        self.custom_handlers: List[logging.Handler] = []
        self._initialized = False

    def initialize(self) -> bool:
        """
        初始化日志系统

        Returns:
            初始化是否成功
        """
        try:
            # 设置根日志记录器
            root_logger = logging.getLogger()
            root_logger.setLevel(getattr(logging, self.config.get("level", "INFO")))

            # 清除现有处理器
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            # 添加处理器
            handlers = self.config.get("handlers", {})

            # 控制台处理器
            if handlers.get("console", {}).get("enabled", True):
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.DEBUG)
                console_formatter = logging.Formatter(self.config.get("format", '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                console_handler.setFormatter(console_formatter)
                root_logger.addHandler(console_handler)

            # 文件处理器
            file_config = handlers.get("file", {})
            if file_config.get("enabled", True):
                file_handler = self._create_file_handler(
                    file_config.get("path", "logs/msearch.log"),
                    logging.DEBUG
                )
                if file_handler:
                    root_logger.addHandler(file_handler)

            # 错误文件处理器
            error_config = handlers.get("error_file", {})
            if error_config.get("enabled", True):
                error_handler = self._create_file_handler(
                    error_config.get("path", "logs/error.log"),
                    getattr(logging, error_config.get("level", "ERROR"))
                )
                if error_handler:
                    root_logger.addHandler(error_handler)

            # 性能文件处理器
            perf_config = handlers.get("performance_file", {})
            if perf_config.get("enabled", True):
                perf_handler = self._create_file_handler(
                    perf_config.get("path", "logs/performance.log"),
                    getattr(logging, perf_config.get("level", "INFO"))
                )
                if perf_handler:
                    root_logger.addHandler(perf_handler)

            # 时间戳文件处理器
            timestamp_config = handlers.get("timestamp_file", {})
            if timestamp_config.get("enabled", True):
                timestamp_handler = self._create_file_handler(
                    timestamp_config.get("path", "logs/timestamp.log"),
                    getattr(logging, timestamp_config.get("level", "DEBUG"))
                )
                if timestamp_handler:
                    root_logger.addHandler(timestamp_handler)

            self._initialized = True
            return True
        except Exception as e:
            print(f"初始化日志系统失败: {e}")
            return False

    def _create_file_handler(self, log_path: str, level: int) -> Optional[logging.Handler]:
        """
        创建文件处理器

        Args:
            log_path: 日志文件路径
            level: 日志级别

        Returns:
            文件处理器或None
        """
        try:
            log_file = self.log_dir / Path(log_path).name
            log_file.parent.mkdir(parents=True, exist_ok=True)

            rotation = self.config.get("rotation", {})
            max_size = rotation.get("max_size_mb", 100) * 1024 * 1024
            backup_count = rotation.get("backup_count", 10)

            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            handler.setLevel(level)
            formatter = logging.Formatter(self.config.get("format", '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            handler.setFormatter(formatter)
            return handler
        except Exception as e:
            print(f"创建文件处理器失败: {e}")
            return None

    def get_logger(self, name: str) -> logging.Logger:
        """
        获取日志记录器

        Args:
            name: 记录器名称

        Returns:
            Logger实例
        """
        if name not in self.loggers:
            logger = logging.getLogger(name)
            logger.setLevel(getattr(logging, self.config.get("level", "INFO")))
            self.loggers[name] = logger
        return self.loggers[name]

    def set_log_level(self, level: str) -> None:
        """
        设置日志级别

        Args:
            level: 日志级别
        """
        try:
            log_level = getattr(logging, level.upper())
            logging.getLogger().setLevel(log_level)
            for logger in self.loggers.values():
                logger.setLevel(log_level)
        except AttributeError:
            print(f"无效的日志级别: {level}")

    def get_log_level(self) -> str:
        """
        获取当前日志级别

        Returns:
            日志级别
        """
        return logging.getLogger().getEffectiveLevel()

    def rotate_logs(self) -> bool:
        """
        手动触发日志轮转

        Returns:
            轮转是否成功
        """
        try:
            for handler in logging.getLogger().handlers:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    handler.doRollover()
            return True
        except Exception as e:
            print(f"日志轮转失败: {e}")
            return False

    def add_custom_handler(self, handler: logging.Handler, level: Optional[int] = None) -> None:
        """
        添加自定义日志处理器

        Args:
            handler: 日志处理器
            level: 可选的日志级别
        """
        if level is not None:
            handler.setLevel(level)
        logging.getLogger().addHandler(handler)
        self.custom_handlers.append(handler)

    def remove_custom_handler(self, handler: logging.Handler) -> None:
        """
        移除自定义日志处理器

        Args:
            handler: 日志处理器
        """
        logging.getLogger().removeHandler(handler)
        if handler in self.custom_handlers:
            self.custom_handlers.remove(handler)

    def shutdown(self) -> None:
        """关闭日志系统"""
        for handler in logging.getLogger().handlers[:]:
            handler.close()
            logging.getLogger().removeHandler(handler)
        self._initialized = False