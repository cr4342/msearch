"""
简化媒体预处理系统测试
"""
import unittest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors.media_preprocessing_system import (
    preprocess_media_file,
    batch_preprocess_files,
    SegmentMappingManager,
    FileSegmentMapping,
    PreprocessingResult,
    get_segment_mapping_manager,
    validate_file,
    get_supported_formats,
    _detect_file_type,
    _extract_image_metadata
)
from src.processors.timestamp_processor import TimestampInfo, ModalityType


class TestSegmentMappingManager(unittest.TestCase):
    """切片映射管理器测试"""
    
    def setUp(self):
        """测试初始化"""
        # 创建临时存储文件
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        
        self.manager = SegmentMappingManager(self.temp_file.name)
    
    def tearDown(self):
        """测试清理"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_add_and_get_segment_mapping(self):
        """测试添加和获取切片映射"""
        # 创建测试映射
        mapping = FileSegmentMapping(
            original_file_id="file_123",
            original_file_path="/path/to/video.mp4",
            segment_id="segment_456",
            segment_path="/path/to/segment_0.mp4",
            segment_index=0,
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            modality="visual",
            created_at=1234567890.0
        )
        
        # 添加映射
        self.manager.add_segment_mapping(mapping)
        
        # 获取映射
        segments = self.manager.get_segments_by_file_id("file_123")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].segment_id, "segment_456")
        self.assertEqual(segments[0].start_time, 0.0)
        self.assertEqual(segments[0].end_time, 30.0)
    
    def test_calculate_original_timestamp(self):
        """测试原始时间戳计算"""
        # 添加测试映射
        mapping = FileSegmentMapping(
            original_file_id="file_123",
            original_file_path="/path/to/video.mp4",
            segment_id="segment_456",
            segment_path="/path/to/segment_0.mp4",
            segment_index=0,
            start_time=60.0,  # 切片从60秒开始
            end_time=90.0,
            duration=30.0,
            modality="visual",
            created_at=1234567890.0
        )
        
        self.manager.add_segment_mapping(mapping)
        
        # 测试时间戳计算
        # 切片内15秒 = 原始文件75秒
        original_timestamp = self.manager.calculate_original_timestamp("segment_456", 15.0)
        self.assertEqual(original_timestamp, 75.0)
        
        # 测试不存在的切片
        result = self.manager.calculate_original_timestamp("nonexistent", 10.0)
        self.assertIsNone(result)
    
    def test_find_segment_by_original_timestamp(self):
        """测试根据原始时间戳查找切片"""
        # 添加多个切片映射
        mappings = [
            FileSegmentMapping(
                original_file_id="file_123",
                original_file_path="/path/to/video.mp4",
                segment_id="segment_1",
                segment_path="/path/to/segment_0.mp4",
                segment_index=0,
                start_time=0.0,
                end_time=30.0,
                duration=30.0,
                modality="visual",
                created_at=1234567890.0
            ),
            FileSegmentMapping(
                original_file_id="file_123",
                original_file_path="/path/to/video.mp4",
                segment_id="segment_2",
                segment_path="/path/to/segment_1.mp4",
                segment_index=1,
                start_time=30.0,
                end_time=60.0,
                duration=30.0,
                modality="visual",
                created_at=1234567890.0
            )
        ]
        
        for mapping in mappings:
            self.manager.add_segment_mapping(mapping)
        
        # 测试查找切片
        # 原始时间45秒应该在第二个切片中
        result = self.manager.find_segment_by_original_timestamp("file_123", 45.0)
        self.assertIsNotNone(result)
        
        segment_info, segment_timestamp = result
        self.assertEqual(segment_info.segment_id, "segment_2")
        self.assertEqual(segment_timestamp, 15.0)  # 45 - 30 = 15
        
        # 测试超出范围的时间戳
        result = self.manager.find_segment_by_original_timestamp("file_123", 100.0)
        self.assertIsNone(result)
    
    def test_persistence(self):
        """测试数据持久化"""
        # 添加测试数据
        mapping = FileSegmentMapping(
            original_file_id="file_123",
            original_file_path="/path/to/video.mp4",
            segment_id="segment_456",
            segment_path="/path/to/segment_0.mp4",
            segment_index=0,
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            modality="visual",
            created_at=1234567890.0
        )
        
        self.manager.add_segment_mapping(mapping)
        
        # 创建新的管理器实例，应该能加载之前的数据
        new_manager = SegmentMappingManager(self.temp_file.name)
        segments = new_manager.get_segments_by_file_id("file_123")
        
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].segment_id, "segment_456")
    
    def test_statistics(self):
        """测试统计信息"""
        # 添加测试数据
        mappings = [
            FileSegmentMapping(
                original_file_id="file_1",
                original_file_path="/path/to/video1.mp4",
                segment_id="segment_1",
                segment_path="/path/to/segment_1.mp4",
                segment_index=0,
                start_time=0.0,
                end_time=30.0,
                duration=30.0,
                modality="visual",
                created_at=1234567890.0
            ),
            FileSegmentMapping(
                original_file_id="file_1",
                original_file_path="/path/to/video1.mp4",
                segment_id="segment_2",
                segment_path="/path/to/segment_2.mp4",
                segment_index=1,
                start_time=30.0,
                end_time=60.0,
                duration=30.0,
                modality="audio_music",
                created_at=1234567890.0
            ),
            FileSegmentMapping(
                original_file_id="file_2",
                original_file_path="/path/to/audio.mp3",
                segment_id="segment_3",
                segment_path="/path/to/audio_segment.wav",
                segment_index=0,
                start_time=0.0,
                end_time=10.0,
                duration=10.0,
                modality="audio_music",
                created_at=1234567890.0
            )
        ]
        
        for mapping in mappings:
            self.manager.add_segment_mapping(mapping)
        
        # 获取统计信息
        stats = self.manager.get_statistics()
        
        self.assertEqual(stats['total_files'], 2)
        self.assertEqual(stats['total_segments'], 3)
        self.assertEqual(stats['avg_segments_per_file'], 1.5)
        self.assertEqual(stats['modality_distribution']['visual'], 1)
        self.assertEqual(stats['modality_distribution']['audio_music'], 2)


class TestUtilityFunctions(unittest.TestCase):
    """工具函数测试"""
    
    def test_detect_file_type(self):
        """测试文件类型检测"""
        test_cases = [
            ('image.jpg', 'image'),
            ('video.mp4', 'video'),
            ('audio.mp3', 'audio'),
            ('document.txt', 'text'),
            ('unknown.xyz', 'unknown')
        ]
        
        for file_path, expected_type in test_cases:
            result = _detect_file_type(file_path)
            self.assertEqual(result, expected_type, f"文件 {file_path} 应该被识别为 {expected_type}")
    
    def test_validate_file(self):
        """测试文件验证"""
        # 测试不存在的文件
        result = validate_file("nonexistent_file.mp4")
        self.assertFalse(result['valid'])
        self.assertIn("文件不存在", result['errors'])
        
        # 测试不支持的文件类型
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = validate_file(temp_path)
            self.assertFalse(result['valid'])
            self.assertIn("不支持的文件类型", result['errors'])
        finally:
            os.unlink(temp_path)
    
    def test_get_supported_formats(self):
        """测试获取支持的格式"""
        formats = get_supported_formats()
        
        self.assertIn('image', formats)
        self.assertIn('video', formats)
        self.assertIn('audio', formats)
        self.assertIn('text', formats)
        
        self.assertIn('.jpg', formats['image'])
        self.assertIn('.mp4', formats['video'])
        self.assertIn('.mp3', formats['audio'])
        self.assertIn('.txt', formats['text'])


class TestPreprocessingIntegration(unittest.TestCase):
    """预处理集成测试"""
    
    @patch('src.processors.media_preprocessing_system.MediaProcessor')
    @patch('src.processors.media_preprocessing_system.TimestampProcessor')
    @patch('src.processors.media_preprocessing_system.get_config_manager')
    def test_preprocess_media_file_video(self, mock_config_manager, mock_timestamp_processor, mock_media_processor):
        """测试视频文件预处理"""
        # 设置模拟
        mock_config_manager.return_value.config = {}
        
        # 模拟媒体处理器返回
        mock_media_instance = mock_media_processor.return_value
        mock_media_instance.process_video_with_timestamps.return_value = {
            'status': 'success',
            'video_info': {'duration': 120.0, 'fps': 30.0},
            'chunks': [
                {
                    'start_time': 0.0,
                    'end_time': 60.0,
                    'duration': 60.0,
                    'output_path': 'chunk_0.mp4'
                },
                {
                    'start_time': 60.0,
                    'end_time': 120.0,
                    'duration': 60.0,
                    'output_path': 'chunk_1.mp4'
                }
            ],
            'video_timestamps': [
                {
                    'segment_id': 'video_segment_0',
                    'modality': 'visual',
                    'start_time': 0.0,
                    'end_time': 2.0,
                    'duration': 2.0,
                    'frame_index': 0,
                    'confidence': 0.9
                }
            ],
            'audio_timestamps': []
        }
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # 执行预处理
            result = preprocess_media_file(temp_path)
            
            # 验证结果
            self.assertEqual(result.status, 'success')
            self.assertEqual(result.file_type, 'video')
            self.assertEqual(len(result.segments), 2)  # 两个切片
            self.assertEqual(len(result.timestamp_infos), 1)  # 一个时间戳
            
            # 验证切片信息
            self.assertEqual(result.segments[0].start_time, 0.0)
            self.assertEqual(result.segments[0].end_time, 60.0)
            self.assertEqual(result.segments[1].start_time, 60.0)
            self.assertEqual(result.segments[1].end_time, 120.0)
            
        finally:
            os.unlink(temp_path)
    
    def test_batch_preprocess_files(self):
        """测试批量预处理"""
        # 创建临时文件
        temp_files = []
        for suffix in ['.jpg', '.mp4', '.mp3']:
            temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
            temp_files.append(temp_file.name)
            temp_file.close()
        
        try:
            with patch('src.processors.media_preprocessing_system.preprocess_media_file') as mock_preprocess:
                # 模拟预处理结果
                mock_preprocess.side_effect = [
                    PreprocessingResult(
                        status='success',
                        original_file_id='file_1',
                        original_file_path=temp_files[0],
                        file_type='image',
                        segments=[],
                        metadata={},
                        timestamp_infos=[],
                        processing_time=1.0
                    ),
                    PreprocessingResult(
                        status='error',
                        original_file_id='file_2',
                        original_file_path=temp_files[1],
                        file_type='video',
                        segments=[],
                        metadata={},
                        timestamp_infos=[],
                        processing_time=2.0,
                        error_message='处理失败'
                    ),
                    PreprocessingResult(
                        status='success',
                        original_file_id='file_3',
                        original_file_path=temp_files[2],
                        file_type='audio',
                        segments=[],
                        metadata={},
                        timestamp_infos=[],
                        processing_time=1.5
                    )
                ]
                
                # 执行批量预处理
                results = batch_preprocess_files(temp_files)
                
                # 验证结果
                self.assertEqual(len(results), 3)
                self.assertEqual(results[0].status, 'success')
                self.assertEqual(results[1].status, 'error')
                self.assertEqual(results[2].status, 'success')
                
        finally:
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)