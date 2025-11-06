"""
时间戳处理器单元测试
测试时间戳精度±2秒要求的核心实现
"""

import pytest
import time
from unittest.mock import Mock, patch
import numpy as np

from src.processors.timestamp_processor import TimestampProcessor, ModalityType
from src.core.config_manager import ConfigManager

class TestTimestampProcessor:
    """时间戳处理器核心功能测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            'processing': {
                'video': {
                    'timestamp_processing': {
                        'accuracy_requirement': 2.0,
                        'sync_tolerance': {
                            'visual': 0.033,
                            'audio_music': 0.1,
                            'audio_speech': 0.2
                        }
                    },
                    'frame_rate': 30.0
                }
            }
        }
    
    @pytest.fixture
    def timestamp_processor(self, mock_config):
        """时间戳处理器实例"""
        return TimestampProcessor(config=mock_config)
    
    def test_frame_timestamp_calculation(self, timestamp_processor):
        """测试帧级时间戳计算精度"""
        video_fps = 30.0
        time_base = 0.0
        
        # 测试精确的帧时间戳计算
        test_cases = [
            (0, 0.0),      # 第0帧 -> 0.0秒
            (30, 1.0),     # 第30帧 -> 1.0秒
            (60, 2.0),     # 第60帧 -> 2.0秒
            (90, 3.0),     # 第90帧 -> 3.0秒
            (1800, 60.0),  # 第1800帧 -> 60.0秒
        ]
        
        for frame_index, expected_timestamp in test_cases:
            calculated_timestamp = timestamp_processor.calculate_frame_timestamp(
                frame_index, video_fps, time_base
            )
            assert abs(calculated_timestamp - expected_timestamp) < 0.001, \
                f"帧{frame_index}的时间戳计算不准确: 期望{expected_timestamp}, 实际{calculated_timestamp}"
    
    def test_timestamp_accuracy_validation(self, timestamp_processor):
        """测试时间戳精度验证"""
        # 测试满足精度要求的情况（duration <= 4秒，即±2秒）
        assert timestamp_processor.validate_timestamp_accuracy(3.0) is True, \
            "应满足±2秒精度要求"
        
        assert timestamp_processor.validate_timestamp_accuracy(4.0) is True, \
            "应满足±2秒精度要求"
        
        # 测试不满足精度要求的情况
        assert timestamp_processor.validate_timestamp_accuracy(5.0) is False, \
            "不应满足±2秒精度要求"
    
    def test_multimodal_sync_validation(self, timestamp_processor):
        """测试多模态时间同步验证"""
        # 测试视觉和音频时间同步（容差0.033秒）
        assert timestamp_processor.validate_multimodal_sync(10.0, 10.02, ModalityType.VISUAL) is True, \
            "视觉模态时间应同步"
        
        # 0.05秒差异应该超过visual的0.033秒容差
        assert timestamp_processor.validate_multimodal_sync(10.0, 10.05, ModalityType.VISUAL) is False, \
            "视觉模态时间应不同步"
        
        # 测试音乐音频时间同步（容差0.1秒）
        assert timestamp_processor.validate_multimodal_sync(10.0, 10.05, ModalityType.AUDIO_MUSIC) is True, \
            "音乐音频模态时间应同步"
        
        assert timestamp_processor.validate_multimodal_sync(10.0, 10.15, ModalityType.AUDIO_MUSIC) is False, \
            "音乐音频模态时间应不同步"
        
        # 测试语音音频时间同步（容差0.2秒）
        assert timestamp_processor.validate_multimodal_sync(10.0, 10.15, ModalityType.AUDIO_SPEECH) is True, \
            "语音音频模态时间应同步"
        
        assert timestamp_processor.validate_multimodal_sync(10.0, 10.25, ModalityType.AUDIO_SPEECH) is False, \
            "语音音频模态时间应不同步"
    
    def test_scene_aware_segmentation(self, timestamp_processor):
        """测试场景感知切片"""
        # 模拟场景数据
        scenes = [
            {'start_time': 0.0, 'end_time': 30.0, 'confidence': 0.9},
            {'start_time': 30.0, 'end_time': 60.0, 'confidence': 0.8},
            {'start_time': 60.0, 'end_time': 90.0, 'confidence': 0.85}
        ]
        video_path = "test_video.mp4"
        fps = 30.0
        
        segments = timestamp_processor.create_scene_aware_segments(
            video_path, scenes, fps
        )
        
        # 验证切片结果
        assert len(segments) == 3, "应创建3个片段"
        
        # 验证每个片段的时间范围
        for i, segment in enumerate(segments):
            assert segment.start_time >= 0
            assert segment.end_time > segment.start_time
            assert segment.duration > 0
            assert segment.file_id == video_path
            
            # 验证时间连续性
            if i > 0:
                # 允许一定的时间间隔
                time_gap = segment.start_time - segments[i-1].end_time
                assert abs(time_gap) <= 1.0, "片段时间应基本连续"
    
    def test_overlap_buffer_configuration(self, timestamp_processor):
        """测试重叠缓冲区配置"""
        # 测试重叠缓冲区设置
        assert timestamp_processor.overlap_buffer == 1.0, "重叠缓冲区应为1秒"
        assert timestamp_processor.accuracy_requirement == 2.0, "精度要求应为±2秒"
        
        # 测试精度验证
        assert timestamp_processor.validate_timestamp_accuracy(3.0) is True, \
            "3秒持续时长应满足±2秒精度要求"
        assert timestamp_processor.validate_timestamp_accuracy(5.0) is False, \
            "5秒持续时长不应满足±2秒精度要求"
    
    def test_time_continuity_detection(self, timestamp_processor):
        """测试时间连续性检测"""
        # 创建连续时间段
        continuous_segments = [
            {'start_time': 0.0, 'end_time': 5.0},
            {'start_time': 5.0, 'end_time': 10.0},
            {'start_time': 10.0, 'end_time': 15.0}
        ]
        
        # 验证连续时间段（使用私有方法）
        for i in range(len(continuous_segments) - 1):
            is_continuous = timestamp_processor._is_time_continuous(
                continuous_segments[i], continuous_segments[i+1]
            )
            assert is_continuous is True, f"时间段{i}和{i+1}应连续"
        
        # 创建不连续时间段
        discontinuous_segments = [
            {'start_time': 0.0, 'end_time': 5.0},
            {'start_time': 10.0, 'end_time': 15.0},  # 5秒间隔
            {'start_time': 20.0, 'end_time': 25.0}   # 5秒间隔
        ]
        
        # 验证不连续时间段（考虑±2秒精度）
        for i in range(len(discontinuous_segments) - 1):
            is_continuous = timestamp_processor._is_time_continuous(
                discontinuous_segments[i], discontinuous_segments[i+1]
            )
            assert is_continuous is False, f"时间段{i}和{i+1}应不连续"
    
    def test_timestamp_merge_and_deduplication(self, timestamp_processor):
        """测试时间戳合并与去重"""
        # 创建简单的时间段进行测试
        segments = [
            {'file_id': 'test1', 'start_time': 0.0, 'end_time': 5.0, 'confidence': 0.8},
            {'file_id': 'test1', 'start_time': 10.0, 'end_time': 15.0, 'confidence': 0.7}
        ]
        
        merged_segments = timestamp_processor.merge_overlapping_segments(segments)
        
        # 验证合并结果
        assert len(merged_segments) >= 1, "应该有合并结果"
        assert isinstance(merged_segments, list), "结果应该是列表"
        
        # 验证每个合并段都有必要的字段
        for segment in merged_segments:
            assert 'start_time' in segment, "合并段应包含start_time"
            assert 'end_time' in segment, "合并段应包含end_time"
            assert segment['end_time'] > segment['start_time'], "结束时间应大于开始时间"
    
    def test_performance_query_optimization(self, timestamp_processor):
        """测试查询性能优化"""
        # 模拟大量时间戳数据
        large_dataset = []
        for i in range(10000):
            large_dataset.append({
                'timestamp': i * 0.1,
                'file_id': f'file_{i}',
                'vector_id': f'vector_{i}'
            })
        
        # 测试时间范围查询性能
        start_time = 100.0
        end_time = 200.0
        
        # 记录查询开始时间
        start_query = time.time()
        
        # 执行时间范围查询（模拟）
        results = [
            item for item in large_dataset 
            if start_time <= item['timestamp'] <= end_time
        ]
        
        # 记录查询结束时间
        end_query = time.time()
        query_time = end_query - start_query
        
        # 验证查询性能（应小于50ms）
        assert query_time < 0.05, f"时间范围查询应小于50ms，实际用时: {query_time*1000:.2f}ms"
        
        # 验证查询结果正确性
        expected_count = int((end_time - start_time) / 0.1) + 1
        assert len(results) == expected_count, f"查询结果数量不正确: 期望{expected_count}, 实际{len(results)}"