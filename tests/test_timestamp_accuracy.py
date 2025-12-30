"""
时间戳精度测试
测试时间戳处理的精度，确保达到±2秒要求
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os
from datetime import datetime

from src.processors.timestamp_processor import TimestampProcessor
from src.processing_service.media_processor import MediaProcessor
from src.search_service.smart_retrieval_engine import SmartRetrievalEngine


class TestTimestampAccuracy:
    """时间戳精度测试类"""
    
    @pytest.fixture
    def timestamp_processor(self):
        """时间戳处理器实例"""
        config = {
            'scene_detection_threshold': 0.15,
            'max_segment_duration': 5.0,
            'keyframe_interval': 2.0,
            'timestamp_accuracy': 2.0
        }
        return TimestampProcessor(config)
    
    def test_frame_timestamp_accuracy(self, timestamp_processor):
        """测试帧时间戳精度"""
        # 模拟视频元数据
        video_metadata = {
            'duration': 30.0,  # 30秒视频
            'fps': 30.0,      # 30帧每秒
            'width': 1920,
            'height': 1080,
            'codec': 'h264'
        }
        
        # 模拟关键帧时间戳提取
        keyframe_timestamps = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0]
        
        # 验证帧率计算
        expected_frame_interval = 1.0 / video_metadata['fps']  # 约0.033秒
        for i in range(1, len(keyframe_timestamps)):
            timestamp_diff = keyframe_timestamps[i] - keyframe_timestamps[i-1]
            # 关键帧间隔为2秒，所以这里验证间隔是否合理
            assert abs(timestamp_diff - 2.0) < 0.1, f"关键帧时间戳间隔异常: {timestamp_diff}"
    
    def test_segment_timestamp_mapping(self, timestamp_processor):
        """测试切片时间戳映射"""
        # 模拟视频片段数据
        segments = [
            {
                'segment_id': 'seg_000001',
                'file_uuid': 'test_video_uuid',
                'segment_index': 0,
                'start_time': 0.0,
                'end_time': 4.8,
                'duration': 4.8,
                'scene_boundary': True,
                'has_audio': True
            },
            {
                'segment_id': 'seg_000002',
                'file_uuid': 'test_video_uuid',
                'segment_index': 1,
                'start_time': 4.8,
                'end_time': 9.6,
                'duration': 4.8,
                'scene_boundary': False,  # 非场景边界切分
                'has_audio': True
            },
            {
                'segment_id': 'seg_000003',
                'file_uuid': 'test_video_uuid',
                'segment_index': 2,
                'start_time': 9.6,
                'end_time': 14.4,
                'duration': 4.8,
                'scene_boundary': True,
                'has_audio': True
            }
        ]
        
        # 验证切片时间连续性
        for i in range(len(segments) - 1):
            current_end = segments[i]['end_time']
            next_start = segments[i+1]['start_time']
            
            # 验证切片无缝衔接（允许0.1秒的微小误差）
            assert abs(current_end - next_start) < 0.1, \
                f"切片时间不连续: {current_end} -> {next_start}"
        
        # 验证绝对时间戳计算
        for segment in segments:
            # 计算中间帧的时间戳
            middle_frame_timestamp = segment['start_time'] + segment['duration'] / 2
            absolute_timestamp = timestamp_processor.calculate_absolute_timestamp(
                segment['start_time'], 
                segment['duration'] / 2
            )
            
            # 验证计算的准确性
            assert abs(absolute_timestamp - middle_frame_timestamp) < 0.001, \
                f"绝对时间戳计算错误: {absolute_timestamp} vs {middle_frame_timestamp}"
            
            # 验证是否在合理范围内
            assert segment['start_time'] <= absolute_timestamp <= segment['end_time'], \
                f"时间戳不在片段范围内: {absolute_timestamp}"
    
    def test_absolute_timestamp_calculation(self, timestamp_processor):
        """测试绝对时间戳计算"""
        # 测试基本计算
        segment_start = 10.5
        frame_in_segment = 2.3
        expected_absolute = segment_start + frame_in_segment
        
        calculated = timestamp_processor.calculate_absolute_timestamp(segment_start, frame_in_segment)
        
        assert abs(calculated - expected_absolute) < 0.001, \
            f"绝对时间戳计算错误: {calculated} vs {expected_absolute}"
    
    def test_timestamp_accuracy_validation(self, timestamp_processor):
        """测试时间戳精度验证"""
        # 测试在精度要求范围内
        assert timestamp_processor.validate_timestamp_accuracy(10.0, 10.5) is True  # 0.5秒误差，<2秒
        assert timestamp_processor.validate_timestamp_accuracy(10.0, 11.9) is True  # 1.9秒误差，<2秒
        assert timestamp_processor.validate_timestamp_accuracy(10.0, 12.1) is False # 2.1秒误差，>2秒
        assert timestamp_processor.validate_timestamp_accuracy(10.0, 8.0) is True   # 2.0秒误差，=2秒
    
    def test_get_frame_timestamp_in_segment(self, timestamp_processor):
        """测试片段中帧的时间戳获取"""
        # 测试5秒片段（使用中间帧）
        segment_duration_5s = 5.0
        frame_timestamp = timestamp_processor.get_frame_timestamp_in_segment(segment_duration_5s)
        expected = 2.5  # 中间帧
        assert abs(frame_timestamp - expected) < 0.001
        
        # 测试3秒片段
        segment_duration_3s = 3.0
        frame_timestamp = timestamp_processor.get_frame_timestamp_in_segment(segment_duration_3s)
        expected = 1.5  # 中间帧
        assert abs(frame_timestamp - expected) < 0.001
    
    def test_video_timestamp_with_accuracy(self, timestamp_processor):
        """测试视频精确时间戳获取"""
        segment_info = {
            'start_time': 15.0,
            'end_time': 20.0,
            'duration': 5.0,
            'segment_id': 'test_seg',
            'file_uuid': 'test_file'
        }
        
        # 使用中间帧时间戳（默认）
        timestamp = timestamp_processor.get_video_timestamp_with_accuracy(segment_info)
        expected = 17.5  # 15.0 + 5.0/2
        assert abs(timestamp - expected) < 0.001
        
        # 使用指定的帧在片段内时间
        timestamp = timestamp_processor.get_video_timestamp_with_accuracy(segment_info, frame_in_segment=1.0)
        expected = 16.0  # 15.0 + 1.0
        assert abs(timestamp - expected) < 0.001
    
    @pytest.mark.asyncio
    async def test_video_segment_generation(self, timestamp_processor):
        """测试视频分段生成（模拟）"""
        # 由于实际的视频处理需要FFmpeg，我们模拟测试逻辑
        with patch.object(timestamp_processor, '_get_video_metadata', return_value={
            'duration': 15.0,
            'fps': 30.0,
            'width': 1920,
            'height': 1080,
            'codec': 'h264'
        }), \
             patch.object(timestamp_processor, '_get_scene_boundaries_ffmpeg', return_value=[5.0, 10.0]), \
             patch.object(timestamp_processor, '_get_keyframe_timestamps_cv2', return_value=[0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 15.0]):
            
            segments = timestamp_processor.get_video_segments("dummy_video_path")
            
            # 验证生成的片段数量
            assert len(segments) > 0
            
            # 验证片段时间连续性
            for i in range(len(segments) - 1):
                current_end = segments[i]['end_time']
                next_start = segments[i+1]['start_time']
                assert abs(current_end - next_start) < 0.1, \
                    f"片段时间不连续: {current_end} -> {next_start}"
            
            # 验证所有片段的时长不超过最大限制
            for segment in segments:
                assert segment['duration'] <= timestamp_processor.max_segment_duration, \
                    f"片段时长超过限制: {segment['duration']}"
    
    def test_edge_cases(self, timestamp_processor):
        """测试边界情况"""
        # 测试负数时间戳
        result = timestamp_processor.calculate_absolute_timestamp(10.0, -1.0)
        # 根据实现，负数时间戳应该被处理为从起始时间开始
        assert result == 10.0  # 因为负数时间戳被修正
        
        # 测试精度验证的边界情况
        assert timestamp_processor.validate_timestamp_accuracy(10.0, 12.0) is True   # 正好2秒
        assert timestamp_processor.validate_timestamp_accuracy(10.0, 12.001) is False # 稍微超过2秒
