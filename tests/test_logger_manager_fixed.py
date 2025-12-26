import pytest
from src.core.logger_manager import LoggerManager, get_logger_manager
from src.core.config_manager import get_config_manager


class TestLoggerManagerFixed:
    """测试修复后的LoggerManager类"""
    
    def test_logger_manager_initialization(self):
        """测试日志管理器初始化"""
        logger_manager = get_logger_manager()
        assert logger_manager is not None
        assert isinstance(logger_manager, LoggerManager)
    
    def test_get_logger(self):
        """测试获取日志器"""
        logger_manager = get_logger_manager()
        logger = logger_manager.get_logger('test.logger')
        assert logger is not None
        
    def test_configure_logger_method_exists(self):
        """测试configure_logger方法存在"""
        logger_manager = get_logger_manager()
        assert hasattr(logger_manager, 'configure_logger')
    
    def test_configure_logger(self):
        """测试配置日志器"""
        logger_manager = get_logger_manager()
        
        # 配置一个日志器
        logger_manager.configure_logger('test.configure', {'level': 'DEBUG'})
        
        # 获取配置后的日志器
        logger = logger_manager.get_logger('test.configure')
        assert logger.level == 10  # DEBUG级别
    
    def test_logger_manager_singleton(self):
        """测试日志管理器单例模式"""
        logger_manager1 = get_logger_manager()
        logger_manager2 = get_logger_manager()
        assert logger_manager1 is logger_manager2
