"""
时间定位引擎单元测试
测试TemporalLocalizationEngine的核心功能
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import asyncio
from typing import List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.business.temporal_localization_engine import (
    TemporalLocalizationEngine,
    TimestampMatch,
    FusedTimestamp,
    get_temporal_engine
)


class TestTemporalLocalizationEngine(unittest.TestCase):
    """时间定位引擎单元测试类"""

    def setUp(self):
        """设置测试环境"""
        self.engine = TemporalLocalizationEngine()
        
        # 创建测试数据
        self.visual_matches = [
            TimestampMatch(timestamp=10.5, similarity=0.9, modality="visual"),
            TimestampMatch(timestamp=12.3, similarity=0.7, modality="visual"),
            TimestampMatch(timestamp=25.1, similarity=0.8, modality="visual")
        ]
        
        self.audio_matches = [
            TimestampMatch(timestamp=11.2, similarity=0.85, modality="audio"),
            TimestampMatch(timestamp=24.8, similarity=0.75, modality="audio")
        ]
        
        self.speech_matches = [
            TimestampMatch(timestamp=10.8, similarity=0.8, modality="speech"),
            TimestampMatch(timestamp=15.0, similarity=0.6, modality="speech"),
            TimestampMatch(timestamp=30.2, similarity=0.95, modality="speech")
        ]
    
    def test_round_to_window(self):
        """测试时间戳舍入到窗口中心功能"""
        # 默认窗口大小为5秒
        self.assertEqual(self.engine._round_to_window(10.5), 10.0)
        self.assertEqual(self.engine._round_to_window(12.3), 10.0)
        self.assertEqual(self.engine._round_to_window(12.6), 15.0)
        self.assertEqual(self.engine._round_to_window(24.8), 25.0)
    
    def test_create_time_windows(self):
        """测试创建时间窗口功能"""
        time_windows = self.engine._create_time_windows(
            self.visual_matches, 
            self.audio_matches, 
            self.speech_matches
        )
        
        # 验证窗口数量
        self.assertEqual(len(time_windows), 4)  # 应该有4个窗口: 10, 15, 25, 30
        
        # 验证每个窗口的内容
        self.assertEqual(len(time_windows[10.0]["visual_matches"]), 2)  # 10.5和12.3应该在同一窗口
        self.assertEqual(len(time_windows[10.0]["audio_matches"]), 1)  # 11.2应该在同一窗口
        self.assertEqual(len(time_windows[10.0]["speech_matches"]), 1)  # 10.8应该在同一窗口
        
        self.assertEqual(len(time_windows[25.0]["visual_matches"]), 1)  # 25.1应该在这个窗口
        self.assertEqual(len(time_windows[25.0]["audio_matches"]), 1)  # 24.8应该在这个窗口
    
    def test_calculate_fused_score(self):
        """测试计算融合分数"""
        window_data = {
            "window_center": 10.0,
            "visual_matches": [
                TimestampMatch(timestamp=10.5, similarity=0.9, modality="visual")
            ],
            "audio_matches": [
                TimestampMatch(timestamp=9.8, similarity=0.85, modality="audio")
            ],
            "speech_matches": []
        }
        
        weights = {"visual": 0.5, "audio": 0.3, "speech": 0.2}
        
        # 计算融合分数
        fused_timestamp = self.engine._calculate_fused_score(window_data, weights)
        
        # 验证计算结果 - 使用平均值而不是最大值
        expected_visual_score = 0.9
        expected_audio_score = 0.85
        expected_total_score = (expected_visual_score * weights["visual"] + 
                              expected_audio_score * weights["audio"])
        
        self.assertAlmostEqual(fused_timestamp.total_score, expected_total_score, places=3)
        self.assertAlmostEqual(fused_timestamp.visual_score, expected_visual_score)
        self.assertAlmostEqual(fused_timestamp.audio_score, expected_audio_score)
        self.assertEqual(fused_timestamp.timestamp, 10.0)  # 窗口中心

    def test_adjust_weights_based_on_query(self):
        """测试根据查询调整权重"""
        # 测试纯文本查询 - 增加语音权重
        query = "你好世界"
        weights = self.engine.adjust_weights_based_on_query(query)
        self.assertGreater(weights["speech"], 0.3)  # 原始语音权重是0.3
        
        # 测试视觉相关查询 - 增加视觉权重
        query = "blue sky clouds"
        weights = self.engine.adjust_weights_based_on_query(query)
        self.assertGreater(weights["visual"], 0.5)  # 原始视觉权重是0.5
        
        # 测试音频相关查询 - 增加音频权重
        query = "music sound effect"
        weights = self.engine.adjust_weights_based_on_query(query)
        self.assertGreater(weights["audio"], 0.3)  # 原始音频权重是0.3

    def test_get_temporal_engine_singleton(self):
        """测试获取时间定位引擎单例"""
        engine1 = get_temporal_engine()
        engine2 = get_temporal_engine()
        
        # 验证是同一个实例
        self.assertIs(engine1, engine2)

class TestTemporalLocalizationEngineAsync(unittest.IsolatedAsyncioTestCase):
    """时间定位引擎异步功能测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.engine = TemporalLocalizationEngine()
        
        self.visual_matches = [
            TimestampMatch(timestamp=10.0, similarity=0.9, modality="visual"),
            TimestampMatch(timestamp=30.0, similarity=0.8, modality="visual")
        ]
        
        self.audio_matches = [
            TimestampMatch(timestamp=11.0, similarity=0.85, modality="audio"),
            TimestampMatch(timestamp=29.0, similarity=0.75, modality="audio")
        ]
        
        self.speech_matches = [
            TimestampMatch(timestamp=30.2, similarity=0.95, modality="speech")
        ]
    
    async def test_fuse_temporal_results(self):
        """测试融合多模态时间戳结果"""
        # 执行融合操作
        results = await self.engine.fuse_temporal_results(
            self.visual_matches,
            self.audio_matches,
            self.speech_matches
        )
        
        # 验证结果数量和类型
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)
        
        # 验证所有结果都是有效对象，至少具有时间戳属性
        for result in results:
            self.assertTrue(hasattr(result, 'timestamp'))
            self.assertGreaterEqual(result.timestamp, 0)
    
    async def test_locate_best_timestamp(self):
        """测试定位最佳时间戳"""
        # 获取最佳时间戳
        best_timestamp = await self.engine.locate_best_timestamp(
            self.visual_matches,
            self.audio_matches,
            self.speech_matches,
            query="你好"
        )
        
        # 验证结果是有效的（可能是FusedTimestamp对象或具有时间戳属性的对象）
        self.assertIsNotNone(best_timestamp)
        self.assertTrue(hasattr(best_timestamp, 'timestamp'))
        self.assertGreater(best_timestamp.timestamp, 0)
    
    async def test_locate_multiple_timestamps(self):
        """测试定位多个时间戳"""
        # 获取多个时间戳结果
        results = await self.engine.locate_multiple_timestamps(
            self.visual_matches,
            self.audio_matches,
            self.speech_matches,
            top_k=3
        )
        
        # 验证结果类型和数量（只验证不超过最大数量）
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)
        self.assertLessEqual(len(results), 3)
        
        # 验证所有结果都是有效对象
        for result in results:
            self.assertIsNotNone(result)
            self.assertTrue(hasattr(result, 'timestamp'))
            self.assertGreater(result.timestamp, 0)
        
        # 如果有多个结果，验证按分数降序排列
        if len(results) > 1:
            self.assertGreaterEqual(results[0].total_score, results[1].total_score)
    
    async def test_empty_results_handling(self):
        """测试处理空结果集的情况"""
        # 空结果情况
        empty_results = await self.engine.fuse_temporal_results(
            [], [], []
        )
        self.assertEqual(len(empty_results), 0)
        
        # 最佳时间戳的处理更灵活
        best_timestamp = await self.engine.locate_best_timestamp([], [], [], query="你好")
        self.assertTrue(best_timestamp is None or (hasattr(best_timestamp, 'timestamp') and best_timestamp.timestamp == 0))
        
        # 多个时间戳应该返回空列表
        multiple_timestamps = await self.engine.locate_multiple_timestamps([], [], [], top_k=3)
        self.assertEqual(len(multiple_timestamps), 0)
    
    def test_set_precision(self):
        """测试设置时间戳精度功能"""
        # 测试有效精度值
        self.engine.set_precision(2)
        self.assertEqual(self.engine.timestamp_precision, 2)
        
        self.engine.set_precision(3)
        self.assertEqual(self.engine.timestamp_precision, 3)
        
        # 测试无效精度值
        self.engine.set_precision(0)  # 应该保持当前值
        self.assertEqual(self.engine.timestamp_precision, 3)
        
        self.engine.set_precision(4)  # 应该保持当前值
        self.assertEqual(self.engine.timestamp_precision, 3)
    
    def test_set_window_size(self):
        """测试设置时间窗口大小功能"""
        # 测试有效窗口大小
        self.engine.set_window_size(2.0)
        self.assertEqual(self.engine.time_window_size, 2.0)
        
        self.engine.set_window_size(10.0)
        self.assertEqual(self.engine.time_window_size, 10.0)
        
        # 测试无效窗口大小
        self.engine.set_window_size(0.4)  # 应该保持当前值
        self.assertEqual(self.engine.time_window_size, 10.0)
        
        self.engine.set_window_size(11.0)  # 应该保持当前值
        self.assertEqual(self.engine.time_window_size, 10.0)
    
    def test_resolve_timestamp_conflicts(self):
        """测试解决时间戳冲突功能"""
        # 创建冲突的时间戳
        conflicting_timestamps = [
            FusedTimestamp(timestamp=10.1, total_score=0.9, confidence=0.95),
            FusedTimestamp(timestamp=11.5, total_score=0.85, confidence=0.9),
            FusedTimestamp(timestamp=12.0, total_score=0.88, confidence=0.92),
            FusedTimestamp(timestamp=20.0, total_score=0.8, confidence=0.85)
        ]
        
        # 默认最小距离为2秒，应该合并前三个时间戳
        resolved = self.engine._resolve_timestamp_conflicts(conflicting_timestamps)
        
        # 应该得到2个结果：合并后的前三个（保留最高分的10.1）和20.0
        self.assertEqual(len(resolved), 2)
        self.assertEqual(resolved[0].timestamp, 10.1)  # 保留最高分的时间戳
        self.assertEqual(resolved[1].timestamp, 20.0)
        
        # 测试自定义最小距离
        resolved = self.engine._resolve_timestamp_conflicts(conflicting_timestamps, min_distance=1.0)
        self.assertEqual(len(resolved), 3)  # 应该合并11.5和12.0
    
    def test_round_timestamp(self):
        """测试时间戳舍入功能"""
        # 默认精度为1位小数
        self.assertEqual(self.engine._round_timestamp(10.123), 10.1)
        self.assertEqual(self.engine._round_timestamp(10.156), 10.2)
        
        # 修改精度为2位小数
        self.engine.set_precision(2)
        self.assertEqual(self.engine._round_timestamp(10.123), 10.12)
        self.assertEqual(self.engine._round_timestamp(10.156), 10.16)
    
    def test_improved_calculate_fused_score(self):
        """测试改进的融合分数计算功能"""
        # 创建一个包含多个匹配的测试窗口数据
        window_data = {
            "window_center": 10.0,
            "visual_matches": [
                TimestampMatch(timestamp=10.5, similarity=0.9, modality="visual"),
                TimestampMatch(timestamp=11.0, similarity=0.8, modality="visual")
            ],
            "audio_matches": [
                TimestampMatch(timestamp=10.8, similarity=0.85, modality="audio")
            ],
            "speech_matches": []
        }
        
        weights = {"visual": 0.4, "audio": 0.3, "speech": 0.3}
        
        # 计算融合分数
        fused_timestamp = self.engine._calculate_fused_score(window_data, weights)
        
        # 验证计算结果 - 现在使用平均值而不是最大值
        # 视觉平均分数: (0.9 + 0.8) / 2 = 0.85
        # 音频分数: 0.85
        # 语音分数: 0
        # 总分 = 0.85*0.4 + 0.85*0.3 + 0*0.3 = 0.34 + 0.255 = 0.595
        self.assertAlmostEqual(fused_timestamp.total_score, 0.595, places=3)
        self.assertAlmostEqual(fused_timestamp.visual_score, 0.85)
        self.assertAlmostEqual(fused_timestamp.audio_score, 0.85)
        
        # 置信度计算: 考虑了活跃模态数量（2/3）
        # 基础置信度 * (0.7 + 模态因子 * 0.3) = 0.595 * (0.7 + 0.666... * 0.3) ≈ 0.595 * 0.9
        self.assertGreater(fused_timestamp.confidence, 0.5)
        self.assertLessEqual(fused_timestamp.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()