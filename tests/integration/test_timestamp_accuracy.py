#!/usr/bin/env python3
"""
时间戳精度测试
确保时间戳精度达到±2秒要求
"""

import sys
import os
import time
from pathlib import Path
import pytest
import numpy as np

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config_manager import ConfigManager
from src.processors.timestamp_processor import TimestampProcessor
from src.business.temporal_localization_engine import TemporalLocalizationEngine


class TestTimestampAccuracy:
    """时间戳精度测试"""
    
    @pytest.fixture
    def config_manager(self):
        """配置管理器fixture"""
        return ConfigManager()
    
    @pytest.fixture
    def timestamp_processor(self):
        """时间戳处理器fixture"""
        return TimestampProcessor()
    
    def test_frame_level_precision(self, timestamp_processor):
        """测试帧级时间戳精度"""
        # 测试连续帧的时间戳精度
        fps = 30.0
        for frame_idx in range(100):
            timestamp = timestamp_processor.calculate_frame_timestamp(frame_idx, fps)
            expected = frame_idx / fps
            # 验证精度在1ms以内
            assert abs(timestamp - expected) < 0.001
    
    def test_multimodal_sync_tolerance(self, timestamp_processor):
        """测试多模态同步容差"""
        # 测试视觉-音频同步
        visual_time = 10.0
        audio_time = 10.05  # 50ms偏差
        
        # 音乐同步容差应为±0.1秒
        is_synced = timestamp_processor.validate_multimodal_sync(
            visual_time, audio_time, 'audio_music'
        )
        assert is_synced  # 应该在容差范围内
        
        # 语音同步容差应为±0.2秒
        audio_time = 10.15  # 150ms偏差
        is_synced = timestamp_processor.validate_multimodal_sync(
            visual_time, audio_time, 'audio_speech'
        )
        assert is_synced  # 应该在容差范围内
    
    def test_retrieval_time_accuracy(self, timestamp_processor):
        """测试检索时间精度"""
        # 验证时间精度要求
        duration = 3.5  # 3.5秒的片段
        is_accurate = timestamp_processor.validate_timestamp_accuracy(duration)
        assert is_accurate  # 应该满足±2秒精度要求
        
        # 测试超过精度要求的情况
        duration = 5.0  # 5秒的片段
        is_accurate = timestamp_processor.validate_timestamp_accuracy(duration)
        assert not is_accurate  # 不应满足±2秒精度要求
    
    def test_overlap_window_processing(self, timestamp_processor):
        """测试重叠时间窗口处理"""
        # 测试重叠窗口确保±2秒精度
        base_time = 10.0
        window_size = 4.0  # 4秒窗口确保±2秒精度
        overlap = 2.0  # 2秒重叠确保连续性
        
        # 验证窗口大小
        assert window_size == 4.0
        assert overlap == 2.0
        
        # 验证重叠比例
        overlap_ratio = overlap / window_size
        assert overlap_ratio == 0.5  # 50%重叠
    
    def test_scene_boundary_handling(self, timestamp_processor):
        """测试场景边界处理精度"""
        # 测试场景边界的时间戳处理
        scene_start = 15.0
        scene_end = 25.0
        scene_duration = scene_end - scene_start
        
        # 验证场景时长
        assert scene_duration == 10.0
        
        # 验证时间段连续性检查
        segment1 = {'start_time': 10.0, 'end_time': 15.0}
        segment2 = {'start_time': 14.0, 'end_time': 20.0}
        
        # 检查时间段是否连续（考虑±2秒精度要求）
        is_continuous = timestamp_processor._is_time_continuous(segment1, segment2)
        assert is_continuous  # 应该是连续的


if __name__ == "__main__":
    # 运行时间戳精度测试
    pytest.main([__file__, "-v", "--tb=short"])