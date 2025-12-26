"""
日志管理器模块
提供统一的多级别日志管理功能，支持动态配置和硬件自适应
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Any
import yaml
import psutil
from datetime import datetime


class LoggerManager:
    """统一的日志管理器
    
    功能特性：
    - 多级别日志支持 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - 可配置的输出处理器 (控制台、文件、错误文件、性能文件)
    - 动态日志级别调整
    - 硬件自适应日志策略
    - 组件特定日志级别配置
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls, config_path: Optional[str] = None):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_manager=None, config_path: Optional[str] = None):
        """初始化日志管理器"""
        if self._initialized:
            return
            
        from src.core.config_manager import get_config_manager
        self.config_manager = config_manager or get_config_manager()
        self.config_path = config_path
        self.config = self._load_config()
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
        self._adjust_for_hardware()
        self._initialized = True
    
    def _load_config(self) -> dict:
        """加载日志配置"""
        # 从全局配置管理器获取日志配置
        logging_config = self.config_manager.get("logging", {})
        if logging_config:
            return logging_config
        
        # 如果没有配置，使用默认配置
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    return config_data.get('logging', {})
            except Exception as e:
                print(f"加载日志配置失败: {e}，使用默认配置")
        
        return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """获取默认日志配置"""
        return {
            'level': 'INFO',
            'format': {
                'standard': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'detailed': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
                'simple': '%(levelname)s - %(message)s',
                'performance': '%(asctime)s - PERF - %(message)s'
            },
            'handlers': {
                'console': {
                    'enabled': True, 
                    'level': 'INFO', 
                    'format': 'standard'
                },
                'file': {
                    'enabled': True, 
                    'level': 'DEBUG', 
                    'format': 'detailed',
                    'path': './data/logs/msearch.log', 
                    'max_size': '100MB', 
                    'backup_count': 5,
                    'encoding': 'utf-8'
                },
                'error_file': {
                    'enabled': True, 
                    'level': 'ERROR', 
                    'format': 'detailed',
                    'path': './data/logs/error.log', 
                    'max_size': '50MB', 
                    'backup_count': 10,
                    'encoding': 'utf-8'
                }
            },
            'loggers': {
                'msearch.core': 'INFO',
                'msearch.business': 'INFO',
                'msearch.processors': 'WARNING',
                'msearch.models': 'WARNING',
                'msearch.storage': 'INFO'
            }
        }
    
    def _setup_logging(self):
        """设置日志系统"""
        # 创建日志目录
        self._create_log_directories()
        
        # 设置根日志级别
        root_level = getattr(logging, self.config.get('level', 'INFO').upper())
        logging.getLogger().setLevel(root_level)
        
        # 清除根日志器的默认处理器
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    
    def _create_log_directories(self):
        """创建日志目录"""
        handlers_config = self.config.get('handlers', {})
        for handler_config in handlers_config.values():
            if 'path' in handler_config:
                log_path = Path(handler_config['path'])
                log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _adjust_for_hardware(self):
        """根据硬件条件调整日志策略"""
        try:
            # 检测可用内存
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            if memory_gb < 8:  # 低内存环境
                self._apply_low_memory_config()
                self.get_logger('msearch.core.logger_manager').warning(
                    f"检测到低内存环境({memory_gb:.1f}GB)，已调整日志级别以减少内存使用"
                )
            
            # 检测磁盘空间
            # 从日志配置中获取日志目录
            handlers_config = self.config.get('handlers', {})
            log_dir = None
            for handler_config in handlers_config.values():
                if 'path' in handler_config:
                    log_path = Path(handler_config['path'])
                    log_dir = log_path.parent
                    break
            
            # 默认使用./data/logs
            if log_dir is None:
                log_dir = Path('./data/logs')
            
            if log_dir.exists():
                disk_usage = psutil.disk_usage(str(log_dir))
                free_space_gb = disk_usage.free / (1024**3)
                
                if free_space_gb < 1:  # 磁盘空间不足1GB
                    self._apply_low_disk_config()
                    self.get_logger('msearch.core.logger_manager').warning(
                        f"磁盘空间不足({free_space_gb:.1f}GB)，已调整日志配置"
                    )
            
        except Exception as e:
            print(f"硬件检测失败: {e}")
    
    def _apply_low_memory_config(self):
        """应用低内存配置"""
        # 减少详细日志输出
        low_memory_loggers = {
            'msearch.processors': 'ERROR',
            'msearch.models': 'ERROR',
            'transformers': 'CRITICAL',
            'torch': 'CRITICAL'
        }
        
        if 'loggers' not in self.config:
            self.config['loggers'] = {}
        
        self.config['loggers'].update(low_memory_loggers)
    
    def _apply_low_disk_config(self):
        """应用低磁盘空间配置"""
        # 减少日志文件大小和备份数量
        handlers = self.config.get('handlers', {})
        
        for handler_name, handler_config in handlers.items():
            if 'max_size' in handler_config:
                handler_config['max_size'] = '10MB'  # 减少文件大小
            if 'backup_count' in handler_config:
                handler_config['backup_count'] = 2   # 减少备份数量
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志器"""
        if name not in self.loggers:
            self.loggers[name] = self._create_logger(name)
        return self.loggers[name]
    
    def _create_logger(self, name: str) -> logging.Logger:
        """创建日志器"""
        logger = logging.getLogger(name)
        
        # 防止重复添加处理器
        if logger.handlers:
            return logger
        
        # 设置日志级别
        logger_config = self.config.get('loggers', {})
        logger_level = self._get_logger_level(name, logger_config)
        logger.setLevel(getattr(logging, logger_level.upper()))
        
        # 防止向上传播到根日志器
        logger.propagate = False
        
        # 添加处理器
        self._add_handlers_to_logger(logger)
        
        return logger
    
    def _get_logger_level(self, name: str, logger_config: dict) -> str:
        """获取日志器级别"""
        # 精确匹配
        if name in logger_config:
            return logger_config[name]
        
        # 前缀匹配
        for logger_name, level in logger_config.items():
            if name.startswith(logger_name):
                return level
        
        # 默认级别
        return self.config.get('level', 'INFO')
    
    def _add_handlers_to_logger(self, logger: logging.Logger):
        """为日志器添加处理器"""
        handlers_config = self.config.get('handlers', {})
        
        # 控制台处理器
        if handlers_config.get('console', {}).get('enabled', True):
            console_handler = self._create_console_handler()
            if console_handler:
                logger.addHandler(console_handler)
        
        # 文件处理器
        if handlers_config.get('file', {}).get('enabled', True):
            file_handler = self._create_file_handler('file')
            if file_handler:
                logger.addHandler(file_handler)
        
        # 错误文件处理器
        if handlers_config.get('error_file', {}).get('enabled', True):
            error_handler = self._create_file_handler('error_file')
            if error_handler:
                logger.addHandler(error_handler)
        
        # 性能日志处理器
        if handlers_config.get('performance', {}).get('enabled', False):
            perf_handler = self._create_file_handler('performance')
            if perf_handler:
                logger.addHandler(perf_handler)
        
        # 时间戳处理器
        if handlers_config.get('timestamp', {}).get('enabled', False):
            timestamp_handler = self._create_file_handler('timestamp')
            if timestamp_handler:
                logger.addHandler(timestamp_handler)
    
    def _create_console_handler(self) -> Optional[logging.StreamHandler]:
        """创建控制台处理器"""
        try:
            handler_config = self.config['handlers']['console']
            handler = logging.StreamHandler(sys.stdout)
            
            level = getattr(logging, handler_config.get('level', 'INFO').upper())
            handler.setLevel(level)
            
            format_name = handler_config.get('format', 'standard')
            format_str = self.config['format'][format_name]
            formatter = logging.Formatter(format_str)
            handler.setFormatter(formatter)
            
            return handler
        except Exception as e:
            print(f"创建控制台处理器失败: {e}")
            return None
    
    def _create_file_handler(self, handler_name: str) -> Optional[logging.Handler]:
        """创建文件处理器"""
        try:
            handler_config = self.config['handlers'][handler_name]
            
            # 解析文件大小
            max_size = self._parse_size(handler_config.get('max_size', '100MB'))
            backup_count = handler_config.get('backup_count', 5)
            
            handler = logging.handlers.RotatingFileHandler(
                filename=handler_config['path'],
                maxBytes=max_size,
                backupCount=backup_count,
                encoding=handler_config.get('encoding', 'utf-8')
            )
            
            level = getattr(logging, handler_config.get('level', 'DEBUG').upper())
            handler.setLevel(level)
            
            format_name = handler_config.get('format', 'detailed')
            format_str = self.config['format'][format_name]
            formatter = logging.Formatter(format_str)
            handler.setFormatter(formatter)
            
            return handler
        except Exception as e:
            print(f"创建文件处理器失败 ({handler_name}): {e}")
            return None
    
    def _parse_size(self, size_str: str) -> int:
        """解析文件大小字符串"""
        size_str = size_str.upper().strip()
        
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def update_level(self, logger_name: str, level: str):
        """动态更新日志级别"""
        try:
            # 更新现有日志器
            if logger_name in self.loggers:
                logger = self.loggers[logger_name]
                logger.setLevel(getattr(logging, level.upper()))
            
            # 更新配置
            if 'loggers' not in self.config:
                self.config['loggers'] = {}
            self.config['loggers'][logger_name] = level.upper()
            
            # 记录级别变更
            self.get_logger('msearch.core.logger_manager').info(
                f"日志级别已更新: {logger_name} -> {level.upper()}"
            )
            
        except Exception as e:
            print(f"更新日志级别失败: {e}")
    
    def get_log_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        stats = {
            'active_loggers': len(self.loggers),
            'log_files': [],
            'disk_usage': {}
        }
        
        # 统计日志文件信息
        handlers_config = self.config.get('handlers', {})
        for handler_name, handler_config in handlers_config.items():
            if 'path' in handler_config and handler_config.get('enabled', True):
                log_path = Path(handler_config['path'])
                if log_path.exists():
                    file_size = log_path.stat().st_size
                    stats['log_files'].append({
                        'name': handler_name,
                        'path': str(log_path),
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'modified': datetime.fromtimestamp(log_path.stat().st_mtime).isoformat()
                    })
        
        # 统计磁盘使用情况
        try:
            log_dir = Path('./data/logs')
            if log_dir.exists():
                disk_usage = psutil.disk_usage(str(log_dir))
                stats['disk_usage'] = {
                    'total_gb': round(disk_usage.total / (1024**3), 2),
                    'used_gb': round(disk_usage.used / (1024**3), 2),
                    'free_gb': round(disk_usage.free / (1024**3), 2),
                    'usage_percent': round((disk_usage.used / disk_usage.total) * 100, 1)
                }
        except Exception as e:
            stats['disk_usage'] = {'error': str(e)}
        
        return stats
    
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志文件"""
        try:
            # 从日志配置中获取日志目录
            handlers_config = self.config.get('handlers', {})
            log_dirs = set()
            for handler_config in handlers_config.values():
                if 'path' in handler_config:
                    log_path = Path(handler_config['path'])
                    log_dirs.add(log_path.parent)
            
            # 如果没有配置，使用默认目录
            if not log_dirs:
                log_dirs.add(Path('./data/logs'))
            
            import time
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            
            cleaned_files = []
            for log_dir in log_dirs:
                if not log_dir.exists():
                    continue
                
                for log_file in log_dir.glob('*.log*'):
                    if log_file.stat().st_mtime < cutoff_time:
                        file_size = log_file.stat().st_size
                        log_file.unlink()
                        cleaned_files.append({
                            'file': str(log_file),
                            'size_mb': round(file_size / (1024 * 1024), 2)
                        })
            
            if cleaned_files:
                total_size = sum(f['size_mb'] for f in cleaned_files)
                self.get_logger('msearch.core.logger_manager').info(
                    f"清理了{len(cleaned_files)}个旧日志文件，释放空间: {total_size:.1f}MB"
                )
            
            return cleaned_files
            
        except Exception as e:
            self.get_logger('msearch.core.logger_manager').error(f"清理日志文件失败: {e}")
            return []
    
    def configure_logger(self, logger_name: str, config: Dict[str, Any]) -> None:
        """配置指定名称的日志器
        
        Args:
            logger_name: 日志器名称
            config: 日志器配置
        """
        try:
            # 更新日志器配置
            if 'loggers' not in self.config:
                self.config['loggers'] = {}
            
            # 设置日志级别
            if 'level' in config:
                self.config['loggers'][logger_name] = config['level'].upper()
                # 更新现有日志器的级别
                if logger_name in self.loggers:
                    logger = self.loggers[logger_name]
                    logger.setLevel(getattr(logging, config['level'].upper()))
            
            self.get_logger('msearch.core.logger_manager').info(
                f"日志器配置已更新: {logger_name}"
            )
        except Exception as e:
            self.get_logger('msearch.core.logger_manager').error(f"配置日志器失败: {e}")


# 全局日志管理器实例
_logger_manager = None

def get_logger_manager(config_path: Optional[str] = None) -> LoggerManager:
    """获取全局日志管理器实例"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager(config_path)
    return _logger_manager

def get_logger(name: str) -> logging.Logger:
    """便捷函数：获取日志器"""
    return get_logger_manager().get_logger(name)


# 使用示例
if __name__ == "__main__":
    # 基本使用
    logger = get_logger('msearch.test')
    
    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.critical("这是严重错误信息")
    
    # 动态调整日志级别
    manager = get_logger_manager()
    manager.update_level('msearch.test', 'DEBUG')
    
    logger.debug("现在可以看到调试信息了")
    
    # 获取日志统计
    stats = manager.get_log_stats()
    print(f"日志统计: {stats}")