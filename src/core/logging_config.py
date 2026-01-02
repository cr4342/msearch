"""
日志配置
"""

import logging
import logging.handlers
import os
import traceback
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from src.core.config_manager import get_config_manager


class ErrorCodeFormatter(logging.Formatter):
    """错误码格式化器，添加错误码和上下文信息"""
    
    def format(self, record):
        # 添加错误码（如果存在）
        if hasattr(record, 'error_code'):
            record.msg = f"[{record.error_code}] {record.msg}"
        
        # 添加请求ID（如果存在）
        if hasattr(record, 'request_id'):
            record.msg = f"[REQ:{record.request_id}] {record.msg}"
        
        # 添加组件名称（如果存在）
        if hasattr(record, 'component'):
            record.msg = f"[{record.component}] {record.msg}"
        
        # 添加上下文信息（如果存在）
        if hasattr(record, 'context'):
            record.msg = f"{record.msg} | Context: {record.context}"
        
        return super().format(record)


def setup_logging(log_level: str = "INFO", log_dir: str = "./logs"):
    """
    设置日志系统
    
    Args:
        log_level: 日志级别
        log_dir: 日志目录
    """
    # 确保日志目录存在
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 创建格式化器
    base_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建错误码格式化器（用于错误日志）
    error_formatter = ErrorCodeFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'  # Python 3.10兼容的时间戳格式
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(error_formatter)  # 控制台使用带错误码的格式化器
    root_logger.addHandler(console_handler)
    
    # 主日志文件处理器
    main_log_file = log_path / "msearch.log"
    main_handler = logging.handlers.RotatingFileHandler(
        main_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    main_handler.setLevel(getattr(logging, log_level.upper()))
    main_handler.setFormatter(error_formatter)  # 主日志使用带错误码的格式化器
    root_logger.addHandler(main_handler)
    
    # 错误日志文件处理器（更详细的错误信息）
    error_log_file = log_path / "error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)
    
    # 详细错误日志（包含完整堆栈跟踪）
    detailed_error_log_file = log_path / "detailed_error.log"
    detailed_error_handler = logging.handlers.RotatingFileHandler(
        detailed_error_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    detailed_error_handler.setLevel(logging.ERROR)
    # 详细错误日志使用特殊格式化器，包含完整堆栈
    detailed_formatter = ErrorCodeFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(exc_info)s',
        datefmt='%Y-%m-%d %H:%M:%S'  # Python 3.10兼容的时间戳格式
    )
    detailed_error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(detailed_error_handler)
    
    # 性能日志文件处理器
    performance_log_file = log_path / "performance.log"
    performance_handler = logging.handlers.RotatingFileHandler(
        performance_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    performance_handler.setLevel(logging.INFO)
    performance_handler.setFormatter(base_formatter)
    
    # 创建性能日志记录器
    performance_logger = logging.getLogger("performance")
    performance_logger.addHandler(performance_handler)
    performance_logger.setLevel(logging.INFO)
    performance_logger.propagate = False  # 防止传播到根日志记录器
    
    # 时间戳日志文件处理器（用于调试时间精度问题）
    timestamp_log_file = log_path / "timestamp.log"
    timestamp_handler = logging.handlers.RotatingFileHandler(
        timestamp_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    timestamp_handler.setLevel(logging.DEBUG)
    timestamp_handler.setFormatter(base_formatter)
    
    # 创建时间戳日志记录器
    timestamp_logger = logging.getLogger("timestamp")
    timestamp_logger.addHandler(timestamp_handler)
    timestamp_logger.setLevel(logging.DEBUG)
    timestamp_logger.propagate = False  # 防止传播到根日志记录器
    
    # 操作日志（记录用户操作）
    operation_log_file = log_path / "operation.log"
    operation_handler = logging.handlers.RotatingFileHandler(
        operation_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    operation_handler.setLevel(logging.INFO)
    operation_formatter = ErrorCodeFormatter(
        '%(asctime)s - %(levelname)s - [%(operation)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    operation_handler.setFormatter(operation_formatter)
    
    # 创建操作日志记录器
    operation_logger = logging.getLogger("operation")
    operation_logger.addHandler(operation_handler)
    operation_logger.setLevel(logging.INFO)
    operation_logger.propagate = False  # 防止传播到根日志记录器
    
    # 设置第三方库日志级别
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
    logging.getLogger("milvus").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)


def log_error(
    logger: logging.Logger,
    message: str,
    error_code: str = None,
    request_id: str = None,
    component: str = None,
    context: Dict[str, Any] = None,
    exc_info: Optional[Exception] = None
):
    """
    统一的错误日志记录函数
    
    Args:
        logger: 日志记录器实例
        message: 错误消息
        error_code: 错误码
        request_id: 请求ID
        component: 组件名称
        context: 上下文信息
        exc_info: 异常对象
    """
    # 创建日志记录
    extra = {}
    if error_code:
        extra['error_code'] = error_code
    if request_id:
        extra['request_id'] = request_id
    if component:
        extra['component'] = component
    if context:
        extra['context'] = context
    
    # 记录错误日志
    if exc_info:
        logger.error(message, extra=extra, exc_info=exc_info)
    else:
        logger.error(message, extra=extra)


def log_operation(
    logger: logging.Logger,
    operation: str,
    message: str,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
):
    """
    统一的操作日志记录函数
    
    Args:
        logger: 日志记录器实例
        operation: 操作名称
        message: 操作消息
        user_id: 用户ID
        request_id: 请求ID
        context: 上下文信息
    """
    extra = {
        'operation': operation
    }
    if user_id:
        extra['user_id'] = user_id
    if request_id:
        extra['request_id'] = request_id
    if context:
        extra['context'] = context
    
    logger.info(message, extra=extra)


class EnhancedLogger:
    """增强型日志记录器，提供更丰富的日志记录功能"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def error(
        self,
        message: str,
        error_code: str = None,
        request_id: str = None,
        component: str = None,
        context: Dict[str, Any] = None,
        exc_info: Optional[Exception] = None
    ):
        """记录错误日志"""
        log_error(
            self.logger,
            message,
            error_code=error_code,
            request_id=request_id,
            component=component,
            context=context,
            exc_info=exc_info
        )
    
    def operation(
        self,
        operation: str,
        message: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """记录操作日志"""
        log_operation(
            self.logger,
            operation,
            message,
            user_id=user_id,
            request_id=request_id,
            context=context
        )
    
    def info(self, msg, *args, **kwargs):
        """包装info方法"""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        """包装warning方法"""
        self.logger.warning(msg, *args, **kwargs)
    
    def debug(self, msg, *args, **kwargs):
        """包装debug方法"""
        self.logger.debug(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        """包装critical方法"""
        self.logger.critical(msg, *args, **kwargs)


def get_enhanced_logger(name: str) -> EnhancedLogger:
    """
    获取增强型日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        增强型日志记录器实例
    """
    return EnhancedLogger(logging.getLogger(name))


class PerformanceLogger:
    """性能日志记录器"""
    
    def __init__(self):
        self.logger = logging.getLogger("performance")
    
    def log_processing_time(self, operation: str, duration: float, metadata: Dict[str, Any] = None):
        """
        记录处理时间
        
        Args:
            operation: 操作名称
            duration: 处理时间（秒）
            metadata: 额外元数据
        """
        log_data = f"Operation: {operation}, Duration: {duration:.4f}s"
        if metadata:
            log_data += f", Metadata: {metadata}"
        self.logger.info(log_data)
    
    def log_throughput(self, operation: str, count: int, duration: float, unit: str = "items"):
        """
        记录吞吐量
        
        Args:
            operation: 操作名称
            count: 处理数量
            duration: 处理时间（秒）
            unit: 单位
        """
        throughput = count / duration if duration > 0 else 0
        self.logger.info(f"Operation: {operation}, Throughput: {throughput:.2f} {unit}/s ({count} {unit} in {duration:.4f}s)")
    
    def log_memory_usage(self, component: str, memory_mb: float):
        """
        记录内存使用情况
        
        Args:
            component: 组件名称
            memory_mb: 内存使用量（MB）
        """
        self.logger.info(f"Component: {component}, Memory: {memory_mb:.2f} MB")
    
    def log_gpu_usage(self, component: str, gpu_memory_mb: float, gpu_utilization: float):
        """
        记录GPU使用情况
        
        Args:
            component: 组件名称
            gpu_memory_mb: GPU内存使用量（MB）
            gpu_utilization: GPU利用率（%）
        """
        self.logger.info(f"Component: {component}, GPU Memory: {gpu_memory_mb:.2f} MB, GPU Utilization: {gpu_utilization:.1f}%")


class TimestampLogger:
    """时间戳日志记录器"""
    
    def __init__(self):
        self.logger = logging.getLogger("timestamp")
    
    def log_timestamp_calculation(self, segment_id: str, relative_time: float, absolute_time: float, validation_result: bool):
        """
        记录时间戳计算
        
        Args:
            segment_id: 片段ID
            relative_time: 相对时间（秒）
            absolute_time: 绝对时间（秒）
            validation_result: 验证结果
        """
        status = "PASS" if validation_result else "FAIL"
        self.logger.debug(f"Segment: {segment_id}, Relative: {relative_time:.3f}s, Absolute: {absolute_time:.3f}s, Validation: {status}")
    
    def log_scene_detection(self, file_path: str, scene_count: int, total_duration: float, avg_segment_duration: float):
        """
        记录场景检测结果
        
        Args:
            file_path: 文件路径
            scene_count: 场景数量
            total_duration: 总时长（秒）
            avg_segment_duration: 平均片段时长（秒）
        """
        self.logger.info(f"File: {file_path}, Scenes: {scene_count}, Duration: {total_duration:.2f}s, Avg Segment: {avg_segment_duration:.2f}s")
    
    def log_frame_extraction(self, segment_id: str, frame_time: float, extraction_success: bool):
        """
        记录帧提取结果
        
        Args:
            segment_id: 片段ID
            frame_time: 帧时间（秒）
            extraction_success: 提取是否成功
        """
        status = "SUCCESS" if extraction_success else "FAILED"
        self.logger.debug(f"Segment: {segment_id}, Frame Time: {frame_time:.3f}s, Status: {status}")


# 全局日志记录器实例
performance_logger = PerformanceLogger()
timestamp_logger = TimestampLogger()