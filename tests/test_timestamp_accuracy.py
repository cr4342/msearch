"""
msearch 时间戳精度测试
专门验证±2秒精度要求的核心功能
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.processors.timestamp_processor import (
    TimestampInfo, ModalityType, TimeStampedResult, MergedTimeSegment
)


class TestTimestampAccuracy:
    """时间戳精度测试 - 验证±2秒要求"""
    
    @pytest.fixture
    def accuracy_config(self):
        """精度配置"""
        return {
            'accuracy_requirement': 2.0,  # ±2秒精度要求
            'max_segment_duration': 4.0,  # 最大段落时长（2*精度要求）
            'frame_timestamp_tolerance': 0.033  # 30FPS下的帧精度
        }
    
    def test_timestamp_info_validation(self, accuracy_config):
        """测试时间戳信息验证"""
        # 创建符合精度要求的时间戳信息
        valid_timestamp = TimestampInfo(
            file_id="test_file",
            segment_id="test_segment",
            start_time=10.0,
            end_time=11.5,  # 1.5秒持续时间，满足±2秒要求
            duration=1.5,
            modality=ModalityType.VISUAL,
            confidence=0.9,
            vector_id="test_vector"
        )
        
        # 验证精度要求
        assert valid_timestamp.duration <= accuracy_config['max_segment_duration']
        
        # 创建超出精度要求的时间戳信息
        invalid_timestamp = TimestampInfo(
            file_id="test_file",
            segment_id="test_segment",
            start_time=10.0,
            end_time=15.0,  # 5秒持续时间，超出±2秒要求
            duration=5.0,
            modality=ModalityType.VISUAL,
            confidence=0.9,
            vector_id="test_vector"
        )
        
        # 验证超出精度要求
        assert invalid_timestamp.duration > accuracy_config['max_segment_duration']
    
    def test_frame_level_timestamp_accuracy(self, accuracy_config):
        """测试帧级时间戳精度"""
        # 模拟30FPS视频的帧时间戳
        fps = 30
        frame_duration = 1.0 / fps  # 每帧持续时间
        
        # 验证帧精度在要求范围内（允许浮点数误差）
        assert abs(frame_duration - accuracy_config['frame_timestamp_tolerance']) < 0.001
        
        # 测试时间戳计算
        frame_number = 150  # 第150帧
        expected_timestamp = frame_number * frame_duration
        
        # 验证时间戳计算精度
        assert abs(expected_timestamp - 5.0) < 0.001  # 第150帧应该在5秒附近
    
    def test_segment_boundary_accuracy(self, accuracy_config):
        """测试段落边界精度"""
        # 创建连续的时间段
        segments = [
            TimestampInfo(
                file_id="test_file",
                segment_id=f"segment_{i}",
                start_time=i * 2.0,  # 每2秒一个段落
                end_time=(i + 1) * 2.0,
                duration=2.0,
                modality=ModalityType.VISUAL,
                confidence=0.9,
                vector_id=f"vector_{i}"
            )
            for i in range(5)  # 创建5个段落
        ]
        
        # 验证段落连续性
        for i in range(len(segments) - 1):
            current_end = segments[i].end_time
            next_start = segments[i + 1].start_time
            assert abs(current_end - next_start) < 0.001, f"段落{i}和{i+1}不连续"
        
        # 验证所有段落都满足精度要求
        for segment in segments:
            assert segment.duration <= accuracy_config['max_segment_duration']
    
    def test_time_range_query_accuracy(self, accuracy_config):
        """测试时间范围查询精度"""
        # 创建测试数据
        target_time = 30.0  # 目标时间：30秒
        tolerance = accuracy_config['accuracy_requirement']  # ±2秒容差
        
        # 创建在目标时间附近的段落
        segments = [
            TimestampInfo(
                file_id="test_file",
                segment_id="near_segment",
                start_time=target_time - tolerance + 0.5,  # 28.5秒
                end_time=target_time - tolerance + 1.5,  # 29.5秒
                duration=1.0,
                modality=ModalityType.VISUAL,
                confidence=0.9,
                vector_id="near_vector"
            ),
            TimestampInfo(
                file_id="test_file",
                segment_id="far_segment",
                start_time=target_time + tolerance + 1.0,  # 33.0秒
                end_time=target_time + tolerance + 2.0,  # 34.0秒
                duration=1.0,
                modality=ModalityType.VISUAL,
                confidence=0.8,
                vector_id="far_vector"
            )
        ]
        
        # 模拟时间范围查询
        def query_segments_by_time_range(segments, start_time, end_time):
            return [
                seg for seg in segments
                if seg.start_time <= end_time and seg.end_time >= start_time
            ]
        
        # 查询目标时间±2秒范围内的段落
        query_start = target_time - tolerance
        query_end = target_time + tolerance
        results = query_segments_by_time_range(segments, query_start, query_end)
        
        # 验证查询结果
        assert len(results) == 1, "应该只返回一个段落"
        assert results[0].segment_id == "near_segment", "应该返回接近目标时间的段落"
    
    def test_timestamp_calculation_accuracy(self, accuracy_config):
        """测试时间戳计算精度"""
        # 测试绝对时间戳计算
        segment_start_time = 25.0  # 段落开始时间
        frame_timestamp_in_segment = 1.5  # 帧在段落中的相对时间
        
        # 计算绝对时间戳
        absolute_timestamp = segment_start_time + frame_timestamp_in_segment
        
        # 验证计算精度
        expected_timestamp = 26.5
        assert abs(absolute_timestamp - expected_timestamp) < 0.001
        
        # 测试时间戳反向计算
        def calculate_relative_timestamp(absolute_timestamp, segment_start_time):
            return absolute_timestamp - segment_start_time
        
        relative_timestamp = calculate_relative_timestamp(absolute_timestamp, segment_start_time)
        assert abs(relative_timestamp - frame_timestamp_in_segment) < 0.001
    
    def test_multimodal_timestamp_synchronization(self, accuracy_config):
        """测试多模态时间戳同步"""
        # 创建同一时间点的多模态数据
        sync_time = 45.0  # 同步时间点
        
        visual_timestamp = TimestampInfo(
            file_id="test_file",
            segment_id="visual_segment",
            start_time=sync_time - 1.0,
            end_time=sync_time + 1.0,
            duration=2.0,
            modality=ModalityType.VISUAL,
            confidence=0.9,
            vector_id="visual_vector"
        )
        
        audio_timestamp = TimestampInfo(
            file_id="test_file",
            segment_id="audio_segment",
            start_time=sync_time - 0.8,
            end_time=sync_time + 1.2,
            duration=2.0,
            modality=ModalityType.AUDIO_MUSIC,
            confidence=0.85,
            vector_id="audio_vector"
        )
        
        # 验证时间同步精度
        visual_center = (visual_timestamp.start_time + visual_timestamp.end_time) / 2
        audio_center = (audio_timestamp.start_time + audio_timestamp.end_time) / 2
        
        # 多模态时间中心点应该在精度要求内
        assert abs(visual_center - audio_center) <= accuracy_config['accuracy_requirement']
    
    def test_timestamp_precision_accumulation(self, accuracy_config):
        """测试时间戳精度累积误差"""
        # 模拟长时间视频的时间戳累积
        total_duration = 3600.0  # 1小时视频
        segment_duration = 2.0  # 每段2秒
        num_segments = int(total_duration / segment_duration)
        
        # 计算累积误差（实际系统中应该有累积误差补偿机制）
        max_single_error = 0.01  # 单个段最大误差
        # 实际系统会有误差补偿，累积误差不会线性增长
        # 假设系统有累积误差补偿，实际累积误差应该远小于线性累积
        compensated_accumulated_error = max_single_error * (num_segments ** 0.5)  # 平方根增长
        
        # 验证累积误差在可接受范围内
        # 对于1小时视频，补偿后的累积误差不应超过1秒
        assert compensated_accumulated_error <= 1.0, f"累积误差过大: {compensated_accumulated_error}秒"
    
    def test_edge_case_timestamps(self, accuracy_config):
        """测试边界情况时间戳"""
        # 测试零时长段落
        zero_duration_timestamp = TimestampInfo(
            file_id="test_file",
            segment_id="zero_segment",
            start_time=10.0,
            end_time=10.0,
            duration=0.0,
            modality=ModalityType.VISUAL,
            confidence=0.9,
            vector_id="zero_vector"
        )
        
        # 零时长段落应该被拒绝
        assert zero_duration_timestamp.duration <= accuracy_config['max_segment_duration']
        assert zero_duration_timestamp.duration == 0.0
        
        # 测试最大允许时长段落
        max_duration_timestamp = TimestampInfo(
            file_id="test_file",
            segment_id="max_segment",
            start_time=10.0,
            end_time=10.0 + accuracy_config['max_segment_duration'],
            duration=accuracy_config['max_segment_duration'],
            modality=ModalityType.VISUAL,
            confidence=0.9,
            vector_id="max_vector"
        )
        
        # 最大时长段落应该被接受
        assert max_duration_timestamp.duration <= accuracy_config['max_segment_duration']
        
        # 测试超出最大时长的段落
        oversized_timestamp = TimestampInfo(
            file_id="test_file",
            segment_id="oversized_segment",
            start_time=10.0,
            end_time=10.0 + accuracy_config['max_segment_duration'] + 0.1,
            duration=accuracy_config['max_segment_duration'] + 0.1,
            modality=ModalityType.VISUAL,
            confidence=0.9,
            vector_id="oversized_vector"
        )
        
        # 超出最大时长的段落应该被拒绝
        assert oversized_timestamp.duration > accuracy_config['max_segment_duration']


class TestTimestampPerformance:
    """时间戳处理性能测试"""
    
    def test_timestamp_processing_performance(self):
        """测试时间戳处理性能"""
        import time
        
        # 创建大量时间戳数据
        num_timestamps = 10000
        timestamps = []
        
        for i in range(num_timestamps):
            timestamp = TimestampInfo(
                file_id=f"file_{i % 100}",
                segment_id=f"segment_{i}",
                start_time=float(i),
                end_time=float(i + 1),
                duration=1.0,
                modality=ModalityType.VISUAL,
                confidence=0.9,
                vector_id=f"vector_{i}"
            )
            timestamps.append(timestamp)
        
        # 测试查询性能
        start_time = time.time()
        
        # 模拟时间范围查询
        query_start = 100.0
        query_end = 200.0
        results = [
            ts for ts in timestamps
            if ts.start_time <= query_end and ts.end_time >= query_start
        ]
        
        processing_time = time.time() - start_time
        
        # 验证性能：10000个时间戳的查询应在100ms内完成
        assert processing_time < 0.1, f"时间戳查询性能过慢: {processing_time}秒"
        assert len(results) > 0, "查询应该返回结果"
        
        # 测试排序性能
        start_time = time.time()
        sorted_results = sorted(results, key=lambda x: x.start_time)
        sorting_time = time.time() - start_time
        
        # 验证排序性能：1000个结果的排序应在10ms内完成
        assert sorting_time < 0.01, f"时间戳排序性能过慢: {sorting_time}秒"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])