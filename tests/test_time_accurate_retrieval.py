"""
时间戳精确检索测试 - 验证±2秒精度的时间戳检索功能
"""
import unittest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from src.business.time_accurate_retrieval import (
    TimeAccurateRetrievalEngine, RetrievalQuery, TimeAccurateResult
)
from src.processors.timestamp_processor import TimestampInfo, ModalityType
from src.storage.timestamp_database import TimestampDatabase


class TestTimeAccurateRetrieval(unittest.TestCase):
    """时间戳精确检索测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.config = {
            'search': {
                'timestamp_retrieval': {
                    'accuracy_requirement': 2.0,
                    'enable_segment_merging': True,
                    'merge_threshold': 2.0,
                    'continuity_detection': True,
                    'max_gap_tolerance': 4.0
                }
            }
        }
        
        # 创建模拟的向量存储和时间戳数据库
        self.mock_vector_store = Mock()
        self.mock_timestamp_db = Mock(spec=TimestampDatabase)
        
        # 创建检索引擎
        self.retrieval_engine = TimeAccurateRetrievalEngine(
            self.config, self.mock_vector_store, self.mock_timestamp_db
        )
    
    def create_mock_timestamp_info(self, segment_id: str, start_time: float, 
                                 end_time: float, modality: ModalityType = ModalityType.VISUAL,
                                 confidence: float = 1.0) -> TimestampInfo:
        """创建模拟的时间戳信息"""
        return TimestampInfo(
            file_id="test_video.mp4",
            segment_id=segment_id,
            modality=modality,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            frame_index=int(start_time * 30) if modality == ModalityType.VISUAL else None,
            vector_id=f"vector_{segment_id}",
            confidence=confidence,
            scene_boundary=False
        )
    
    def test_validate_time_accuracy(self):
        """测试时间精度验证"""
        # 创建满足精度要求的时间戳
        valid_timestamp = self.create_mock_timestamp_info("valid", 10.0, 12.0)  # 2秒时长
        self.assertTrue(self.retrieval_engine._validate_time_accuracy(valid_timestamp))
        
        # 创建不满足精度要求的时间戳
        invalid_timestamp = self.create_mock_timestamp_info("invalid", 10.0, 15.0)  # 5秒时长
        self.assertFalse(self.retrieval_engine._validate_time_accuracy(invalid_timestamp))
    
    @patch('src.business.time_accurate_retrieval.TimeAccurateRetrievalEngine._vector_search')
    async def test_retrieve_with_timestamp_basic(self, mock_vector_search):
        """测试基本的时间戳检索功能"""
        # 设置模拟向量搜索结果
        mock_vector_search.return_value = [
            {'vector_id': 'vector_1', 'score': 0.9},
            {'vector_id': 'vector_2', 'score': 0.8}
        ]
        
        # 设置模拟时间戳数据库返回
        timestamp_1 = self.create_mock_timestamp_info("segment_1", 10.0, 12.0)
        timestamp_2 = self.create_mock_timestamp_info("segment_2", 15.0, 17.0)
        
        self.mock_timestamp_db.get_timestamp_info_by_vector_id.side_effect = [
            timestamp_1, timestamp_2
        ]
        
        # 创建查询
        query = RetrievalQuery(
            query_vector=np.random.rand(512),
            target_modality=ModalityType.VISUAL,
            top_k=10
        )
        
        # 执行检索
        results = await self.retrieval_engine.retrieve_with_timestamp(query)
        
        # 验证结果
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], TimeAccurateResult)
        self.assertEqual(results[0].file_id, "test_video.mp4")
        self.assertEqual(results[0].time_accuracy, "±2.0s")
    
    def test_merge_overlapping_segments(self):
        """测试重叠时间段合并"""
        from src.processors.timestamp_processor import TimeStampedResult
        
        # 创建重叠的时间段
        timestamp_1 = self.create_mock_timestamp_info("segment_1", 10.0, 15.0)
        timestamp_2 = self.create_mock_timestamp_info("segment_2", 14.0, 19.0)  # 与segment_1重叠
        timestamp_3 = self.create_mock_timestamp_info("segment_3", 25.0, 30.0)  # 独立段
        
        results = [
            TimeStampedResult(
                file_id="test_video.mp4",
                start_time=ts.start_time,
                end_time=ts.end_time,
                score=0.9,
                vector_id=ts.vector_id,
                modality=ts.modality,
                timestamp_info=ts
            )
            for ts in [timestamp_1, timestamp_2, timestamp_3]
        ]
        
        # 执行合并
        merged_segments = self.retrieval_engine._merge_overlapping_segments(results)
        
        # 验证合并结果
        self.assertEqual(len(merged_segments), 2)  # 前两个段应该合并，第三个独立
        
        # 验证合并后的时间范围
        first_merged = merged_segments[0]
        self.assertEqual(first_merged.start_time, 10.0)
        self.assertEqual(first_merged.end_time, 19.0)
        self.assertEqual(len(first_merged.results), 2)
    
    def test_get_precise_video_segment(self):
        """测试精确视频段定位"""
        # 设置模拟时间戳数据库返回
        timestamps = [
            self.create_mock_timestamp_info("segment_1", 8.0, 10.0),
            self.create_mock_timestamp_info("segment_2", 10.0, 12.0),  # 最接近目标时间11.0
            self.create_mock_timestamp_info("segment_3", 12.0, 14.0)
        ]
        
        self.mock_timestamp_db.get_timestamp_infos_by_time_range.return_value = timestamps
        
        # 执行精确定位
        result = self.retrieval_engine.get_precise_video_segment("test_video.mp4", 11.0)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.segment_id, "segment_2")
        self.assertEqual(result.start_time, 10.0)
        self.assertEqual(result.end_time, 12.0)
    
    def test_get_continuous_video_timeline(self):
        """测试连续视频时间线获取"""
        # 设置模拟时间戳数据库返回
        timestamps = [
            self.create_mock_timestamp_info("segment_1", 0.0, 2.0),
            self.create_mock_timestamp_info("segment_2", 2.0, 4.0),
            self.create_mock_timestamp_info("segment_3", 4.0, 6.0),
            self.create_mock_timestamp_info("segment_4", 8.0, 10.0)  # 有间隙
        ]
        
        self.mock_timestamp_db.get_timestamp_infos_by_file_id.return_value = timestamps
        self.mock_timestamp_db.get_timestamp_infos_by_time_range.return_value = timestamps
        
        # 执行时间线获取
        timeline = self.retrieval_engine.get_continuous_video_timeline("test_video.mp4")
        
        # 验证结果
        self.assertEqual(len(timeline), 4)
        
        # 验证时间连续性（前三个段应该连续）
        for i in range(2):
            self.assertEqual(timeline[i].end_time, timeline[i + 1].start_time)
        
        # 验证间隙检测（第3和第4段之间有间隙）
        gap = timeline[3].start_time - timeline[2].end_time
        self.assertEqual(gap, 2.0)
    
    def test_get_multimodal_synchronized_results(self):
        """测试多模态同步结果获取"""
        # 设置模拟时间戳数据库返回
        timestamps = [
            self.create_mock_timestamp_info("video_1", 10.0, 12.0, ModalityType.VISUAL),
            self.create_mock_timestamp_info("audio_1", 10.1, 12.1, ModalityType.AUDIO_MUSIC),
            self.create_mock_timestamp_info("speech_1", 10.2, 12.2, ModalityType.AUDIO_SPEECH)
        ]
        
        self.mock_timestamp_db.get_timestamp_infos_by_time_range.return_value = timestamps
        
        # 执行多模态同步查询
        results = self.retrieval_engine.get_multimodal_synchronized_results(
            "test_video.mp4", 11.0, 5.0
        )
        
        # 验证结果
        self.assertIn('visual', results)
        self.assertIn('audio_music', results)
        self.assertIn('audio_speech', results)
        
        self.assertEqual(len(results['visual']), 1)
        self.assertEqual(len(results['audio_music']), 1)
        self.assertEqual(len(results['audio_speech']), 1)
    
    def test_validate_retrieval_accuracy(self):
        """测试检索精度验证"""
        # 创建测试结果
        results = [
            TimeAccurateResult(
                file_id="test_video.mp4",
                start_time=10.0,
                end_time=12.0,  # 2秒时长，满足精度要求
                duration=2.0,
                score=0.9,
                confidence=0.9,
                modality=ModalityType.VISUAL,
                vector_id="vector_1",
                segment_id="segment_1",
                time_accuracy="±2.0s",
                is_merged=False,
                merged_count=1
            ),
            TimeAccurateResult(
                file_id="test_video.mp4",
                start_time=15.0,
                end_time=20.0,  # 5秒时长，不满足精度要求
                duration=5.0,
                score=0.8,
                confidence=0.8,
                modality=ModalityType.VISUAL,
                vector_id="vector_2",
                segment_id="segment_2",
                time_accuracy="±2.0s",
                is_merged=False,
                merged_count=1
            )
        ]
        
        # 执行精度验证
        validation_report = self.retrieval_engine.validate_retrieval_accuracy(results)
        
        # 验证报告
        self.assertEqual(validation_report['total_results'], 2)
        self.assertEqual(validation_report['accuracy_compliant'], 1)
        self.assertEqual(validation_report['accuracy_violations'], 1)
        self.assertEqual(validation_report['accuracy_rate'], 0.5)
        self.assertEqual(len(validation_report['violations']), 1)
    
    def test_sort_by_relevance_and_continuity(self):
        """测试按相关性和连续性排序"""
        from src.processors.timestamp_processor import MergedTimeSegment, TimeStampedResult
        
        # 创建测试段
        timestamp_1 = self.create_mock_timestamp_info("segment_1", 10.0, 12.0, confidence=0.8)
        timestamp_2 = self.create_mock_timestamp_info("segment_2", 15.0, 17.0, confidence=0.9)
        
        result_1 = TimeStampedResult(
            file_id="test_video.mp4",
            start_time=timestamp_1.start_time,
            end_time=timestamp_1.end_time,
            score=0.8,
            vector_id=timestamp_1.vector_id,
            modality=timestamp_1.modality,
            timestamp_info=timestamp_1
        )
        
        result_2 = TimeStampedResult(
            file_id="test_video.mp4",
            start_time=timestamp_2.start_time,
            end_time=timestamp_2.end_time,
            score=0.9,
            vector_id=timestamp_2.vector_id,
            modality=timestamp_2.modality,
            timestamp_info=timestamp_2
        )
        
        # 创建合并段（模拟连续性奖励）
        segment_1 = MergedTimeSegment(result_1)
        segment_2 = MergedTimeSegment(result_2)
        segment_2.merge(result_1)  # segment_2包含更多结果，应该得到连续性奖励
        
        segments = [segment_1, segment_2]
        
        # 执行排序
        sorted_segments = self.retrieval_engine._sort_by_relevance_and_continuity(segments)
        
        # 验证排序结果（segment_2应该排在前面，因为有连续性奖励）
        self.assertEqual(len(sorted_segments), 2)
        self.assertGreater(sorted_segments[0].final_score, sorted_segments[1].final_score)


class TestVideoTimelineGenerator(unittest.TestCase):
    """视频时间线生成器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.config = {
            'search': {
                'timestamp_retrieval': {
                    'accuracy_requirement': 2.0
                }
            }
        }
        
        self.mock_vector_store = Mock()
        self.mock_timestamp_db = Mock(spec=TimestampDatabase)
        
        self.retrieval_engine = TimeAccurateRetrievalEngine(
            self.config, self.mock_vector_store, self.mock_timestamp_db
        )
        
        from src.business.time_accurate_retrieval import VideoTimelineGenerator
        self.timeline_generator = VideoTimelineGenerator(self.retrieval_engine)
    
    def test_generate_timeline(self):
        """测试时间线生成"""
        # 设置模拟时间戳数据
        timestamps = [
            TimestampInfo(
                file_id="test_video.mp4",
                segment_id=f"segment_{i}",
                modality=ModalityType.VISUAL,
                start_time=i * 2.0,
                end_time=(i + 1) * 2.0,
                duration=2.0,
                confidence=0.8 + i * 0.1
            )
            for i in range(5)
        ]
        
        self.mock_timestamp_db.get_timestamp_infos_by_file_id.return_value = timestamps
        self.retrieval_engine.get_scene_boundaries.return_value = [
            TimeAccurateResult(
                file_id="test_video.mp4",
                start_time=0.0,
                end_time=2.0,
                duration=2.0,
                score=1.0,
                confidence=1.0,
                modality=ModalityType.VISUAL,
                vector_id="vector_scene_0",
                segment_id="scene_0",
                time_accuracy="±2.0s",
                is_merged=False,
                merged_count=1
            )
        ]
        
        # 执行时间线生成
        timeline_data = self.timeline_generator.generate_timeline("test_video.mp4", resolution=50)
        
        # 验证时间线数据
        self.assertIn('file_id', timeline_data)
        self.assertIn('time_points', timeline_data)
        self.assertIn('scene_boundaries', timeline_data)
        self.assertIn('statistics', timeline_data)
        
        self.assertEqual(timeline_data['file_id'], "test_video.mp4")
        self.assertEqual(len(timeline_data['time_points']), 50)
        self.assertEqual(len(timeline_data['scene_boundaries']), 1)
        
        # 验证统计信息
        stats = timeline_data['statistics']
        self.assertEqual(stats['total_segments'], 5)
        self.assertEqual(stats['visual_segments'], 5)
        self.assertEqual(stats['scene_count'], 1)


if __name__ == '__main__':
    # 运行异步测试
    def run_async_test(test_func):
        """运行异步测试函数"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_func())
        finally:
            loop.close()
    
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加同步测试
    suite.addTest(TestTimeAccurateRetrieval('test_validate_time_accuracy'))
    suite.addTest(TestTimeAccurateRetrieval('test_merge_overlapping_segments'))
    suite.addTest(TestTimeAccurateRetrieval('test_get_precise_video_segment'))
    suite.addTest(TestTimeAccurateRetrieval('test_get_continuous_video_timeline'))
    suite.addTest(TestTimeAccurateRetrieval('test_get_multimodal_synchronized_results'))
    suite.addTest(TestTimeAccurateRetrieval('test_validate_retrieval_accuracy'))
    suite.addTest(TestTimeAccurateRetrieval('test_sort_by_relevance_and_continuity'))
    
    suite.addTest(TestVideoTimelineGenerator('test_generate_timeline'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 运行异步测试
    print("\n运行异步测试...")
    test_instance = TestTimeAccurateRetrieval()
    test_instance.setUp()
    run_async_test(test_instance.test_retrieve_with_timestamp_basic)
    print("异步测试完成")