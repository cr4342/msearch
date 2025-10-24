"""
TimestampProcessor单元测试
测试时间戳精度±2秒要求的核心实现
"""
import pytest
import time
from unittest.mock import Mock, patch
import numpy as np

from src.processors.timestamp_processor import TimestampProcessor
from src.core.config_manager import ConfigManager


class TestTimestampProcessor:
    """时间戳处理器核心功能测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            'processing.video.timestamp_processing.accuracy_requirement': 2.0,
            'processing.video.timestamp_processing.sync_tolerance': {
                'visual': 0.033,
                'audio_music': 0.1,
                'audio_speech': 0.2
            },
            'processing.video.frame_rate': 30.0
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
            
            # 验证帧级精度（±0.033s@30fps）
            assert abs(calculated_timestamp - expected_timestamp) < 0.001
            assert calculated_timestamp == expected_timestamp
    
    def test_timestamp_accuracy_validation(self, timestamp_processor):
        """测试±2秒精度要求验证"""
        # 测试满足精度要求的时间戳
        valid_cases = [
            2.0,   # 2秒持续时长
            1.5,   # 1.5秒持续时长
            4.0,   # 4秒持续时长（边界情况）
        ]
        
        for duration in valid_cases:
            is_valid = timestamp_processor.validate_timestamp_accuracy(duration)
            assert is_valid == True, f"持续时长 {duration}s 应该满足精度要求"
        
        # 测试不满足精度要求的时间戳
        invalid_cases = [
            5.0,   # 5秒持续时长，超过±2秒要求
            6.5,   # 6.5秒持续时长
        ]
        
        for duration in invalid_cases:
            is_valid = timestamp_processor.validate_timestamp_accuracy(duration)
            assert is_valid == False, f"持续时长 {duration}s 不应该满足精度要求"
    
    def test_multimodal_time_sync_validation(self, timestamp_processor):
        """测试多模态时间同步验证"""
        # 测试不同模态的同步容差
        sync_test_cases = [
            ('visual', 10.0, 10.02, True),    # 视觉模态：20ms差异，应该通过
            ('visual', 10.0, 10.05, False),   # 视觉模态：50ms差异，应该失败
            ('audio_music', 10.0, 10.08, True),   # 音频模态：80ms差异，应该通过
            ('audio_music', 10.0, 10.15, False),  # 音频模态：150ms差异，应该失败
            ('audio_speech', 10.0, 10.15, True),  # 语音模态：150ms差异，应该通过
            ('audio_speech', 10.0, 10.25, False), # 语音模态：250ms差异，应该失败
        ]
        
        for modality, visual_time, audio_time, expected_result in sync_test_cases:
            result = timestamp_processor.validate_multimodal_sync(
                visual_time, audio_time, modality
            )
            assert result == expected_result, \
                f"模态 {modality}: 视觉时间 {visual_time}s, 音频时间 {audio_time}s, 期望结果 {expected_result}"
    
    def test_overlapping_time_windows(self, timestamp_processor):
        """测试重叠时间窗口策略"""
        # 创建测试时间戳数据
        timestamps = [
            {'file_id': 'file1', 'start_time': 10.0, 'end_time': 12.0, 'duration': 2.0},
            {'file_id': 'file1', 'start_time': 11.5, 'end_time': 13.5, 'duration': 2.0},
            {'file_id': 'file1', 'start_time': 13.0, 'end_time': 15.0, 'duration': 2.0},
            {'file_id': 'file1', 'start_time': 20.0, 'end_time': 22.0, 'duration': 2.0},
        ]
        
        # 测试时间段合并
        merged_segments = timestamp_processor.merge_overlapping_segments(timestamps)
        
        # 验证合并结果
        assert len(merged_segments) == 2  # 应该合并为2个连续段
        
        # 第一个合并段应该包含v1, v2, v3的时间范围
        first_segment = merged_segments[0]
        assert first_segment['start_time'] == 10.0
        assert first_segment['end_time'] == 15.0
        
        # 第二个段应该只包含v4
        second_segment = merged_segments[1]
        assert second_segment['start_time'] == 20.0
        assert second_segment['end_time'] == 22.0
    
    def test_scene_aware_timestamp_processing(self, timestamp_processor):
        """测试场景感知的时间戳处理"""
        # 模拟场景边界数据
        scene_boundaries = [
            {'start_time': 0.0, 'end_time': 30.0, 'scene_id': 'scene_1'},
            {'start_time': 30.0, 'end_time': 60.0, 'scene_id': 'scene_2'},
            {'start_time': 60.0, 'end_time': 90.0, 'scene_id': 'scene_3'},
        ]
        
        # 测试场景边界处理
        processed_timestamps = timestamp_processor.process_scene_aware_timestamps(
            scene_boundaries, frame_rate=30.0
        )
        
        # 验证场景边界不被破坏
        for i, scene in enumerate(processed_timestamps):
            assert scene['scene_id'] == f'scene_{i+1}'
            assert scene['start_time'] == i * 30.0
            assert scene['end_time'] == (i + 1) * 30.0
            
            # 验证场景内的时间戳连续性
            timestamps_in_scene = scene['timestamps']
            for j in range(len(timestamps_in_scene) - 1):
                current_end = timestamps_in_scene[j]['timestamp']
                next_start = timestamps_in_scene[j + 1]['timestamp']
                # 时间戳应该连续或有合理的重叠
                assert abs(next_start - current_end) <= 2.0
    
    def test_timestamp_drift_correction(self, timestamp_processor):
        """测试时间戳漂移校正"""
        # 模拟有漂移的时间戳数据
        timestamps_with_drift = [
            {'modality': 'visual', 'start_time': 10.0, 'end_time': 12.0},
            {'modality': 'audio_music', 'start_time': 10.1, 'end_time': 12.1},  # 100ms漂移
            {'modality': 'audio_speech', 'start_time': 10.15, 'end_time': 12.15},  # 150ms漂移
        ]
        
        # 执行漂移校正
        corrected_timestamps = timestamp_processor.correct_timestamp_drift(timestamps_with_drift)
        
        # 验证校正结果
        visual_timestamp = next(ts for ts in corrected_timestamps if ts['modality'] == 'visual')
        audio_music_timestamp = next(ts for ts in corrected_timestamps if ts['modality'] == 'audio_music')
        audio_speech_timestamp = next(ts for ts in corrected_timestamps if ts['modality'] == 'audio_speech')
        
        # 视觉时间戳应该保持不变（作为基准）
        assert visual_timestamp['start_time'] == 10.0
        
        # 音频时间戳应该被校正到视觉基准
        assert abs(audio_music_timestamp['start_time'] - visual_timestamp['start_time']) <= 0.1
        assert abs(audio_speech_timestamp['start_time'] - visual_timestamp['start_time']) <= 0.2


class TestTimestampProcessorPerformance:
    """时间戳处理器性能测试"""
    
    @pytest.fixture
    def performance_config(self):
        """性能测试配置"""
        return {
            'processing.video.timestamp_processing.accuracy_requirement': 2.0,
            'processing.video.timestamp_processing.sync_tolerance': {
                'visual': 0.033,
                'audio_music': 0.1,
                'audio_speech': 0.2
            },
            'processing.video.frame_rate': 30.0
        }
    
    def test_timestamp_query_performance(self, performance_config):
        """测试时间戳查询性能"""
        timestamp_processor = TimestampProcessor(config=performance_config)
        
        # 创建大量时间戳数据进行性能测试
        large_timestamp_dataset = []
        for i in range(1000):
            large_timestamp_dataset.append({
                'vector_id': f'vector_{i}',
                'start_time': i * 2.0,
                'end_time': i * 2.0 + 2.0,
                'duration': 2.0,
                'modality': 'visual'
            })
        
        # 测试批量查询性能
        start_time = time.time()
        
        # 模拟50个向量的时间戳查询
        query_vector_ids = [f'vector_{i}' for i in range(50)]
        results = timestamp_processor.batch_query_timestamps(
            query_vector_ids, large_timestamp_dataset
        )
        
        end_time = time.time()
        query_time = (end_time - start_time) * 1000  # 转换为毫秒
        
        # 验证性能要求：50个查询<50ms
        assert query_time < 50, f"批量查询时间过长: {query_time}ms"
        assert len(results) == 50
        
        # 验证单次查询性能
        start_time = time.time()
        single_result = timestamp_processor.query_timestamp('vector_0', large_timestamp_dataset)
        end_time = time.time()
        single_query_time = (end_time - start_time) * 1000
        
        # 单次查询应该<10ms
        assert single_query_time < 10, f"单次查询时间过长: {single_query_time}ms"
        assert single_result is not None
    
    def test_memory_efficient_processing(self, performance_config):
        """测试内存高效的时间戳处理"""
        timestamp_processor = TimestampProcessor(config=performance_config)
        
        # 测试大规模时间戳数据的内存使用
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        # 处理大量时间戳数据
        large_video_timestamps = []
        for i in range(10000):  # 10000个时间戳
            large_video_timestamps.append({
                'frame_index': i,
                'timestamp': i / 30.0,  # 30fps
                'duration': 2.0,
                'vector_id': f'frame_{i}'
            })
        
        # 执行批量处理
        processed_timestamps = timestamp_processor.batch_process_timestamps(large_video_timestamps)
        
        final_memory = process.memory_info().rss / (1024 * 1024)  # MB
        memory_increase = final_memory - initial_memory
        
        # 内存增长应该在合理范围内
        assert memory_increase < 100, f"内存增长过多: {memory_increase}MB"
        assert len(processed_timestamps) == 10000
    
    def test_concurrent_timestamp_processing(self, performance_config):
        """测试并发时间戳处理"""
        timestamp_processor = TimestampProcessor(config=performance_config)
        
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def worker(worker_id, timestamp_data):
            """工作线程函数"""
            start_time = time.time()
            result = timestamp_processor.process_timestamps(timestamp_data)
            end_time = time.time()
            
            results_queue.put({
                'worker_id': worker_id,
                'processing_time': (end_time - start_time) * 1000,
                'result_count': len(result)
            })
        
        # 创建多个工作线程
        threads = []
        for i in range(4):  # 4个并发线程
            timestamp_data = [
                {
                    'start_time': j * 2.0,
                    'end_time': j * 2.0 + 2.0,
                    'duration': 2.0,
                    'vector_id': f'worker_{i}_vector_{j}'
                }
                for j in range(100)  # 每个线程处理100个时间戳
            ]
            
            thread = threading.Thread(target=worker, args=(i, timestamp_data))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 收集结果
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # 验证并发处理结果
        assert len(results) == 4
        for result in results:
            assert result['processing_time'] < 1000  # 每个线程处理时间<1秒
            assert result['result_count'] == 100  # 每个线程处理100个时间戳