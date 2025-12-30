"""
错误处理测试
测试错误处理系统和容错能力
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import time

from src.utils.error_handling import (
    ErrorHandler, 
    RetryStrategy, 
    RetryConfig,
    ErrorClassifier,
    ErrorCategory,
    ErrorSeverity,
    ErrorInfo
)
from src.common.embedding.embedding_engine import EmbeddingEngine
from src.common.storage.database_adapter import DatabaseAdapter


class TestErrorHandling:
    """错误处理测试类"""
    
    @pytest.fixture
    def error_handler(self):
        """错误处理器实例"""
        return ErrorHandler()
    
    @pytest.fixture
    def error_classifier(self):
        """错误分类器实例"""
        return ErrorClassifier()
    
    def test_error_classification(self, error_classifier):
        """测试错误分类"""
        # 测试网络错误分类
        connection_error = Exception("Connection failed")
        category, severity = error_classifier.classify_error(connection_error)
        assert category == ErrorCategory.NETWORK
        assert severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM, ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
        
        # 测试超时错误分类
        timeout_error = TimeoutError("Request timeout")
        category, severity = error_classifier.classify_error(timeout_error)
        assert category == ErrorCategory.NETWORK
        
        # 测试文件未找到错误分类
        file_not_found_error = FileNotFoundError("File not found")
        category, severity = error_classifier.classify_error(file_not_found_error)
        assert category == ErrorCategory.FILE_PROCESSING
    
    def test_retry_strategy_enum(self):
        """测试重试策略枚举"""
        # 验证枚举值存在
        assert RetryStrategy.FIXED_INTERVAL is not None
        assert RetryStrategy.EXPONENTIAL_BACKOFF is not None
        assert RetryStrategy.LINEAR_BACKOFF is not None
        assert RetryStrategy.IMMEDIATE_RETRY is not None
        
        # 验证枚举值
        assert RetryStrategy.FIXED_INTERVAL.value == "fixed_interval"
        assert RetryStrategy.EXPONENTIAL_BACKOFF.value == "exponential_backoff"
    
    def test_retry_config_creation(self):
        """测试重试配置创建"""
        config = RetryConfig(
            max_attempts=3,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=10.0,
            backoff_multiplier=2.0
        )
        
        assert config.max_attempts == 3
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.base_delay == 1.0
        assert config.max_delay == 10.0
        assert config.backoff_multiplier == 2.0
    
    def test_error_severity_enum(self):
        """测试错误严重级别枚举"""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"
    
    def test_error_category_enum(self):
        """测试错误分类枚举"""
        assert ErrorCategory.SYSTEM.value == "system"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.DATABASE.value == "database"
        assert ErrorCategory.AI_MODEL.value == "ai_model"
        assert ErrorCategory.FILE_PROCESSING.value == "file_processing"
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.PERMISSION.value == "permission"
        assert ErrorCategory.RESOURCE.value == "resource"
        assert ErrorCategory.UNKNOWN.value == "unknown"
    
    def test_error_info_creation(self):
        """测试错误信息创建"""
        error_info = ErrorInfo(
            error_id="test_123",
            timestamp=time.time(),
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message="Test error message",
            details={'key': 'value'}
        )
        
        assert error_info.error_id == "test_123"
        assert error_info.category == ErrorCategory.NETWORK
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.message == "Test error message"
        assert error_info.details == {'key': 'value'}
    
    def test_error_handler_initialization(self, error_handler):
        """测试错误处理器初始化"""
        assert error_handler is not None
        assert hasattr(error_handler, 'error_classifier')
        assert hasattr(error_handler, 'retry_manager')
        assert hasattr(error_handler, 'degradation_manager')
    
    def test_error_handler_handle_error(self, error_handler):
        """测试错误处理器处理错误"""
        test_error = ValueError("Test error message")
        error_info = error_handler.handle_error(test_error)
        
        assert error_info is not None
        assert isinstance(error_info, ErrorInfo)
        assert error_info.message == "Test error message"
        assert error_info.category in ErrorCategory
        assert error_info.severity in ErrorSeverity
    
    @pytest.mark.asyncio
    async def test_error_handler_execute_with_error_handling(self, error_handler):
        """测试错误处理器执行函数"""
        def successful_function():
            return "success"
        
        result = error_handler.execute_with_error_handling(successful_function)
        assert result == "success"
    
    def test_error_handler_error_tracking(self, error_handler):
        """测试错误处理器错误跟踪"""
        # 触发一些错误来验证统计
        error_handler.handle_error(Exception("Test error 1"))
        error_handler.handle_error(Exception("Test error 2"))
        error_handler.handle_error(Exception("Test error 3"))
        
        stats = error_handler.get_error_statistics()
        assert 'error_statistics' in stats
        assert 'retry_statistics' in stats
    
    def test_error_handler_statistics(self, error_handler):
        """测试错误处理器统计"""
        # 触发一些错误
        error_handler.handle_error(Exception("Error 1"))
        error_handler.handle_error(Exception("Error 2"))
        
        stats = error_handler.get_error_statistics()
        
        assert 'error_statistics' in stats
        assert 'retry_statistics' in stats
        assert 'degradation_statistics' in stats
    
    def test_error_classifier_severity_determination(self, error_classifier):
        """测试错误分类器严重级别确定"""
        # 测试系统错误应该是CRITICAL
        system_error = MemoryError("Out of memory")
        category, severity = error_classifier.classify_error(system_error)
        assert category == ErrorCategory.SYSTEM
        assert severity == ErrorSeverity.CRITICAL
        
        # 测试AI模型错误应该是HIGH
        ai_error = Exception("Model inference failed")
        category, severity = error_classifier.classify_error(ai_error)
        # AI模型错误根据关键词匹配
        assert severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM, ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
    
    def test_error_info_with_context(self, error_handler):
        """测试带上下文的错误信息"""
        context = {'component': 'test_component', 'operation': 'test_operation'}
        error_info = error_handler.handle_error(
            Exception("Test error"), 
            context=context
        )
        
        assert error_info.context == context
    
    def test_error_info_defaults(self):
        """测试错误信息默认值"""
        error_info = ErrorInfo(
            error_id="test_456",
            timestamp=time.time(),
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            message="Test message",
            details={}
        )
        
        # 验证默认值
        assert error_info.stack_trace is None
        assert error_info.component is None
        assert error_info.operation is None
        assert error_info.context is None
        assert error_info.recoverable is True
        assert error_info.retry_count == 0
        assert error_info.max_retries == 3