"""
视频切片器
支持多种视频切片策略，改进时序定位机制
根据设计文档优化视频切片时序定位机制
"""

from typing import List, Dict, Any, Optional
import logging

from core.task.video_segment_manager import VideoSegmentManager, VideoSegmentConfig

logger = logging.getLogger(__name__)


class VideoSlicer:
    """视频切片器：支持多种视频切片策略，改进时序定位机制"""
    
    def __init__(self, strategy: str = 'hybrid', **kwargs):
        """
        初始化视频切片器
        
        Args:
            strategy: 切片策略（scene_based/time_based/hybrid）
            **kwargs: 策略参数
        """
        # 创建视频切片配置，明确定义切片参数配置和时间映射
        config_dict = {
            'max_segment_duration': kwargs.get('max_segment_duration', 5.0),  # 最大切片时长（秒）
            'min_segment_duration': kwargs.get('min_segment_duration', 0.5),  # 最小切片时长（秒）
            'segment_overlap': kwargs.get('segment_overlap', 0.0),  # 切片重叠时间（秒）
            'scene_detect_threshold': kwargs.get('scene_detect_threshold', 0.3),  # 场景变化阈值
            'scene_detect_min_duration': kwargs.get('scene_detect_min_duration', 1.0),  # 最小场景时长
            'timestamp_precision': kwargs.get('timestamp_precision', 0.1),  # 时间戳精度（秒）
            'short_video_threshold': kwargs.get('short_video_threshold', 6.0),  # 短视频阈值
            'short_video_handling': kwargs.get('short_video_handling', 'full_process'),  # 短视频处理方式
            'max_resolution_short_edge': kwargs.get('max_resolution_short_edge', 960),  # 短边最大分辨率
            'scene_detect_enabled': kwargs.get('scene_detect_enabled', True)  # 启用场景检测
        }
        
        self.config = VideoSegmentConfig(config_dict)
        self.video_segment_manager = VideoSegmentManager(self.config)
        self.strategy = strategy
        
        logger.info(f"VideoSlicer initialized with strategy: {strategy}")
    
    def slice_video(self, video_path: str) -> List[Dict[str, Any]]:
        """
        切片视频，返回包含时间映射的切片列表
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            切片列表，每个元素包含时间映射信息
        """
        logger.info(f"Slicing video: {video_path} with strategy: {self.strategy}")
        
        try:
            # 使用优化后的视频切片管理器
            segments = self.video_segment_manager.segment_video(video_path)
            return segments
        except Exception as e:
            logger.error(f"Error slicing video {video_path}: {e}")
            raise
    
    def create_segment_file(self, video_path: str, start_time: float, end_time: float, output_path: str) -> bool:
        """
        创建视频切片文件
        
        Args:
            video_path: 原视频路径
            start_time: 开始时间
            end_time: 结束时间
            output_path: 输出路径
        
        Returns:
            是否成功
        """
        return self.video_segment_manager.create_segment_file(video_path, start_time, end_time, output_path)
    
    def get_segment_info(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取切片详细信息
        
        Args:
            segment: 切片信息字典
        
        Returns:
            切片详细信息
        """
        return self.video_segment_manager.get_segment_info(segment)
    
    def validate_config(self) -> bool:
        """
        验证配置的有效性
        
        Returns:
            配置是否有效
        """
        return self.video_segment_manager.validate_config()
    
    def set_strategy(self, strategy: str, **kwargs) -> None:
        """
        设置切片策略
        
        Args:
            strategy: 切片策略
            **kwargs: 策略参数
        """
        self.strategy = strategy
        
        # 更新配置
        config_dict = {
            'max_segment_duration': kwargs.get('max_segment_duration', 5.0),
            'min_segment_duration': kwargs.get('min_segment_duration', 0.5),
            'segment_overlap': kwargs.get('segment_overlap', 0.0),
            'scene_detect_threshold': kwargs.get('scene_detect_threshold', 0.3),
            'scene_detect_min_duration': kwargs.get('scene_detect_min_duration', 1.0),
            'timestamp_precision': kwargs.get('timestamp_precision', 0.1),
            'short_video_threshold': kwargs.get('short_video_threshold', 6.0),
            'short_video_handling': kwargs.get('short_video_handling', 'full_process'),
            'max_resolution_short_edge': kwargs.get('max_resolution_short_edge', 960),
            'scene_detect_enabled': kwargs.get('scene_detect_enabled', True)
        }
        
        self.config = VideoSegmentConfig(config_dict)
        self.video_segment_manager = VideoSegmentManager(self.config)
        
        logger.info(f"VideoSlicer strategy updated to: {strategy}")
    
    def get_strategy_info(self) -> dict:
        """
        获取当前策略信息
        
        Returns:
            策略信息字典
        """
        return {
            'strategy': self.strategy,
            'config': {
                'max_segment_duration': self.config.max_segment_duration,
                'min_segment_duration': self.config.min_segment_duration,
                'scene_detect_threshold': self.config.scene_detect_threshold,
                'timestamp_precision': self.config.timestamp_precision,
                'short_video_threshold': self.config.short_video_threshold
            }
        }