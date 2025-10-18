"""
时间戳处理功能增强测试
为时间戳处理功能添加更多测试用例
"""

import unittest
from unittest.mock import patch
import asyncio
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.business.temporal_localization_engine import (
    TemporalLocalizationEngine,
    TimestampMatch,
    FusedTimestamp
)


class TestTemporalLocalizationEngineEnhanced(unittest.IsolatedAsyncioTestCase):
    """时间定位引擎增强测试"""
    
    def setUp(self):
        """测试前的准备工作"""
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
    
    def test_precision_settings(self):
        """测试精度设置功能"""
        # 测试默认精度
        self.assertEqual(self.engine.timestamp_precision, 1)
        
        # 测试设置有效精度
        self.engine.set_precision(2)
        self.assertEqual(self.engine.timestamp_precision, 2)
        
        # 测试时间戳舍入
        self.assertEqual(self.engine._round_timestamp(10.123), 10.12)
        self.assertEqual(self.engine._round_timestamp(10.156), 10.16)
        
        # 测试设置无效精度（应该保持当前值）
        self.engine.set_precision(0)
        self.assertEqual(self.engine.timestamp_precision, 2)  # 应该保持2
        
        self.engine.set_precision(5)
        self.assertEqual(self.engine.timestamp_precision, 2)  # 应该保持2
    
    def test_window_size_settings(self):
        """测试窗口大小设置功能"""
        # 测试默认窗口大小
        self.assertEqual(self.engine.time_window_size, 5)
        
        # 测试设置有效窗口大小
        self.engine.set_window_size(2.0)
        self.assertEqual(self.engine.time_window_size, 2.0)
        
        # 测试时间戳舍入到窗口
        self.assertEqual(self.engine._round_to_window(10.5), 10.0)
        self.assertEqual(self.engine._round_to_window(11.2), 12.0)
        
        # 测试设置无效窗口大小（应该保持当前值）
        self.engine.set_window_size(0.1)
        self.assertEqual(self.engine.time_window_size, 2.0)  # 应该保持2.0
        
        self.engine.set_window_size(15.0)
        self.assertEqual(self.engine.time_window_size, 2.0)  # 应该保持2.0
    
    def test_create_time_windows_with_overlapping_matches(self):
        """测试创建时间窗口功能（重叠匹配）"""
        # 创建重叠的时间戳匹配
        visual_matches = [
            TimestampMatch(timestamp=10.1, similarity=0.9, modality="visual"),
            TimestampMatch(timestamp=10.8, similarity=0.8, modality="visual"),
            TimestampMatch(timestamp=11.2, similarity=0.7, modality="visual")
        ]
        
        audio_matches = [
            TimestampMatch(timestamp=10.5, similarity=0.85, modality="audio"),
            TimestampMatch(timestamp=11.0, similarity=0.75, modality="audio")
        ]
        
        speech_matches = [
            TimestampMatch(timestamp=10.3, similarity=0.95, modality="speech"),
            TimestampMatch(timestamp=10.9, similarity=0.85, modality="speech")
        ]
        
        # 使用默认窗口大小5秒
        self.engine.set_window_size(5.0)
        
        time_windows = self.engine._create_time_windows(visual_matches, audio_matches, speech_matches)
        
        # 应该只有一个窗口，因为所有时间戳都在0-5秒范围内
        self.assertEqual(len(time_windows), 1)
        
        # 验证窗口中的所有匹配都被正确聚合
        window_data = time_windows[10.0]  # 窗口中心应该是10.0
        self.assertEqual(len(window_data["visual_matches"]), 3)
        self.assertEqual(len(window_data["audio_matches"]), 2)
        self.assertEqual(len(window_data["speech_matches"]), 2)
    
    def test_calculate_fused_score_with_multiple_matches(self):
        """测试计算融合分数（多个匹配）"""
        # 创建包含多个匹配的窗口数据
        window_data = {
            "window_center": 10.0,
            "visual_matches": [
                TimestampMatch(timestamp=10.1, similarity=0.9, modality="visual"),
                TimestampMatch(timestamp=10.5, similarity=0.8, modality="visual"),
                TimestampMatch(timestamp=10.8, similarity=0.7, modality="visual")
            ],
            "audio_matches": [
                TimestampMatch(timestamp=10.3, similarity=0.85, modality="audio"),
                TimestampMatch(timestamp=10.7, similarity=0.75, modality="audio")
            ],
            "speech_matches": [
                TimestampMatch(timestamp=10.2, similarity=0.95, modality="speech"),
                TimestampMatch(timestamp=10.6, similarity=0.85, modality="speech"),
                TimestampMatch(timestamp=10.9, similarity=0.75, modality="speech")
            ]
        }
        
        weights = {"visual": 0.4, "audio": 0.3, "speech": 0.3}
        
        # 计算融合分数
        fused_timestamp = self.engine._calculate_fused_score(window_data, weights)
        
        # 验证计算结果
        # 视觉平均分数: (0.9 + 0.8 + 0.7) / 3 = 0.8
        # 音频平均分数: (0.85 + 0.75) / 2 = 0.8
        # 语音平均分数: (0.95 + 0.85 + 0.75) / 3 = 0.85
        # 总分 = 0.8*0.4 + 0.8*0.3 + 0.85*0.3 = 0.32 + 0.24 + 0.255 = 0.815
        self.assertAlmostEqual(fused_timestamp.total_score, 0.815, places=3)
        self.assertAlmostEqual(fused_timestamp.visual_score, 0.8, places=3)
        self.assertAlmostEqual(fused_timestamp.audio_score, 0.8, places=3)
        self.assertAlmostEqual(fused_timestamp.speech_score, 0.85, places=3)
        self.assertEqual(fused_timestamp.timestamp, 10.0)
        
        # 验证置信度计算（3个模态都活跃）
        # base_confidence = 0.815
        # modality_factor = 3/3 = 1.0
        # confidence = min(0.815 * (0.7 + 1.0 * 0.3), 1.0) = min(0.815 * 1.0, 1.0) = 0.815
        self.assertAlmostEqual(fused_timestamp.confidence, 0.815, places=3)
    
    def test_adjust_weights_based_on_query(self):
        """测试根据查询调整权重"""
        # 测试视觉主导查询
        weights = self.engine.adjust_weights_based_on_query("查找图片中的蓝色天空")
        self.assertEqual(weights["visual"], 0.6)
        self.assertEqual(weights["audio"], 0.2)
        self.assertEqual(weights["speech"], 0.2)
        
        # 测试音频主导查询
        weights = self.engine.adjust_weights_based_on_query("搜索旋律优美的音乐")
        self.assertEqual(weights["visual"], 0.2)
        self.assertEqual(weights["audio"], 0.6)
        self.assertEqual(weights["speech"], 0.2)
        
        # 测试语音主导查询
        weights = self.engine.adjust_weights_based_on_query("查找会议中的讨论内容")
        self.assertEqual(weights["visual"], 0.2)
        self.assertEqual(weights["audio"], 0.2)
        self.assertEqual(weights["speech"], 0.6)
        
        # 测试均衡查询
        weights = self.engine.adjust_weights_based_on_query("查找相关内容")
        self.assertEqual(weights["visual"], 0.4)
        self.assertEqual(weights["audio"], 0.3)
        self.assertEqual(weights["speech"], 0.3)
    
    async def test_locate_best_timestamp_with_query(self):
        """测试定位最佳时间戳（带查询）"""
        # 使用视觉主导查询
        best_timestamp = await self.engine.locate_best_timestamp(
            self.visual_matches,
            self.audio_matches,
            self.speech_matches,
            query="查找图片中的内容"
        )
        
        # 验证返回类型
        self.assertIsInstance(best_timestamp, FusedTimestamp)
        
        # 验证有合理的时间戳值和分数
        self.assertGreater(best_timestamp.timestamp, 0)
        self.assertGreaterEqual(best_timestamp.total_score, 0)
        self.assertLessEqual(best_timestamp.total_score, 1)
    
    async def test_locate_multiple_timestamps_with_query(self):
        """测试定位多个时间戳（带查询）"""
        # 使用语音主导查询
        multiple_timestamps = await self.engine.locate_multiple_timestamps(
            self.visual_matches,
            self.audio_matches,
            self.speech_matches,
            top_k=5,
            query="查找对话内容"
        )
        
        # 验证返回类型和数量
        self.assertIsInstance(multiple_timestamps, list)
        self.assertLessEqual(len(multiple_timestamps), 5)
        
        # 验证所有结果都是FusedTimestamp类型
        for ts in multiple_timestamps:
            self.assertIsInstance(ts, FusedTimestamp)
        
        # 验证结果按分数降序排列
        if len(multiple_timestamps) > 1:
            self.assertGreaterEqual(multiple_timestamps[0].total_score, multiple_timestamps[1].total_score)
    
    def test_resolve_timestamp_conflicts_with_custom_distance(self):
        """测试解决时间戳冲突（自定义距离）"""
        # 创建时间戳，其中一些在自定义距离内
        timestamps = [
            FusedTimestamp(timestamp=10.0, total_score=0.9, confidence=0.95),
            FusedTimestamp(timestamp=11.5, total_score=0.85, confidence=0.9),
            FusedTimestamp(timestamp=12.0, total_score=0.88, confidence=0.92),
            FusedTimestamp(timestamp=20.0, total_score=0.8, confidence=0.85)
        ]
        
        # 使用更小的最小距离（1秒）
        resolved = self.engine._resolve_timestamp_conflicts(timestamps, min_distance=1.0)
        
        # 应该合并更多的时间戳
        self.assertLess(len(resolved), len(timestamps))
        
        # 验证保留了最高分的时间戳
        if len(resolved) > 0:
            self.assertEqual(resolved[0].timestamp, 10.0)  # 应该保留最高分的10.0
    
    async def test_fuse_temporal_results_with_empty_inputs(self):
        """测试融合时间戳结果（空输入）"""
        # 测试所有输入都为空的情况
        results = await self.engine.fuse_temporal_results([], [], [])
        self.assertEqual(len(results), 0)
        
        # 测试部分输入为空的情况
        results = await self.engine.fuse_temporal_results(self.visual_matches, [], [])
        self.assertGreater(len(results), 0)
        
        # 验证只有视觉匹配被处理
        for result in results:
            self.assertGreater(result.visual_score, 0)
            self.assertEqual(result.audio_score, 0)
            self.assertEqual(result.speech_score, 0)
    
    async def test_edge_cases_in_time_window_creation(self):
        """测试时间窗口创建的边界情况"""
        # 创建边界情况的时间戳
        edge_matches = [
            TimestampMatch(timestamp=0.0, similarity=0.9, modality="visual"),  # 边界时间戳
            TimestampMatch(timestamp=2.5, similarity=0.8, modality="visual"),  # 窗口边界
            TimestampMatch(timestamp=5.0, similarity=0.7, modality="visual"),  # 窗口边界
            TimestampMatch(timestamp=7.5, similarity=0.6, modality="visual"),  # 窗口中间
        ]
        
        # 使用2秒窗口大小
        self.engine.set_window_size(2.0)
        
        time_windows = self.engine._create_time_windows(edge_matches, [], [])
        
        # 验证窗口创建正确
        expected_windows = [0.0, 2.0, 4.0, 6.0, 8.0]  # 预期的窗口中心
        for window_center in expected_windows:
            self.assertIn(window_center, time_windows)
        
        # 验证时间戳被正确分配到窗口
        self.assertEqual(len(time_windows[0.0]["visual_matches"]), 1)  # 0.0
        self.assertEqual(len(time_windows[2.0]["visual_matches"]), 1)  # 2.5
        self.assertEqual(len(time_windows[4.0]["visual_matches"]), 1)  # 5.0
        self.assertEqual(len(time_windows[6.0]["visual_matches"]), 0)  # 无匹配
        self.assertEqual(len(time_windows[8.0]["visual_matches"]), 1)  # 7.5
    
    def test_timestamp_rounding_precision(self):
        """测试时间戳舍入精度"""
        # 测试不同的精度设置
        test_cases = [
            (1, 10.123, 10.1),
            (1, 10.156, 10.2),
            (2, 10.123, 10.12),
            (2, 10.125, 10.12),  # 银行家舍入
            (2, 10.135, 10.14),
            (3, 10.1234, 10.123),
            (3, 10.1235, 10.124),
        ]
        
        for precision, input_val, expected in test_cases:
            self.engine.set_precision(precision)
            result = self.engine._round_timestamp(input_val)
            self.assertEqual(result, expected, 
                           f"精度{precision}时，{input_val}应该舍入为{expected}，实际为{result}")


if __name__ == "__main__":
    unittest.main()