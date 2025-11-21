"""
日志配置
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, Any

from src.core.config_manager import get_config_manager


def setup_logging(log_level: str = "INFO", log_dir: str = "./logs"):
    """
    设置日志系统
    
    Args:
        log_level: 日志级别
        log_dir: 日志目录
    """
    # 确保日志目录存在
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 主日志文件处理器
    main_log_file = os.path.join(log_dir, "msearch.log")
    main_handler = logging.handlers.RotatingFileHandler(
        main_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    main_handler.setLevel(getattr(logging, log_level.upper()))
    main_handler.setFormatter(formatter)
    root_logger.addHandler(main_handler)
    
    # 错误日志文件处理器
    error_log_file = os.path.join(log_dir, "error.log")
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # 性能日志文件处理器
    performance_log_file = os.path.join(log_dir, "performance.log")
    performance_handler = logging.handlers.RotatingFileHandler(
        performance_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    performance_handler.setLevel(logging.INFO)
    performance_handler.setFormatter(formatter)
    
    # 创建性能日志记录器
    performance_logger = logging.getLogger("performance")
    performance_logger.addHandler(performance_handler)
    performance_logger.setLevel(logging.INFO)
    performance_logger.propagate = False  # 防止传播到根日志记录器
    
    # 时间戳日志文件处理器（用于调试时间精度问题）
    timestamp_log_file = os.path.join(log_dir, "timestamp.log")
    timestamp_handler = logging.handlers.RotatingFileHandler(
        timestamp_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    timestamp_handler.setLevel(logging.DEBUG)
    timestamp_handler.setFormatter(formatter)
    
    # 创建时间戳日志记录器
    timestamp_logger = logging.getLogger("timestamp")
    timestamp_logger.addHandler(timestamp_handler)
    timestamp_logger.setLevel(logging.DEBUG)
    timestamp_logger.propagate = False  # 防止传播到根日志记录器
    
    # 设置第三方库日志级别
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)


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