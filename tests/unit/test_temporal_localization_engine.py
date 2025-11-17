"""
时间定位引擎单元测试
测试TemporalLocalizationEngine的核心功能
"""
import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.business.temporal_localization_engine import (
    TemporalLocalizationEngine, 
    TimestampMatch, 
    FusedTimestamp
)


class TestTemporalLocalizationEngine:
    """时间定位引擎核心功能测试"""
    
    @pytest.fixture
    def temporal_engine(self):
        """时间定位引擎实例"""
        with patch('src.business.temporal_localization_engine.get_config_manager') as mock_config_manager:
            mock_config = {
                'temporal_localization': {
                    'accuracy_requirement': 2.0,
                    'time_window_size': 2,
                    'min_confidence': 0.3,
                    'max_results': 10,
                    'timestamp_precision': 2
                }
            }
            mock_config_manager.return_value.config = mock_config
            mock_config_manager.return_value.get = Mock(side_effect=lambda key, default=None: {
                'temporal_localization': mock_config['temporal_localization'],
                'temporal_localization.accuracy_requirement': 2.0,
                'temporal_localization.time_window_size': 2,
                'temporal_localization.min_confidence': 0.3,
                'temporal_localization.max_results': 10,
                'temporal_localization.timestamp_precision': 2
            }.get(key, default))
            mock_config_manager.return_value.watch = Mock()
            
            engine = TemporalLocalizationEngine()
            return engine
    
    def test_init_success(self):
        """测试初始化成功"""
        with patch('src.business.temporal_localization_engine.get_config_manager') as mock_config_manager:
            mock_config = {
                'temporal_localization': {
                    'accuracy_requirement': 2.0,
                    'time_window_size': 2,
                    'min_confidence': 0.3,
                    'max_results': 10,
                    'timestamp_precision': 2
                }
            }
            mock_config_manager.return_value.config = mock_config
            mock_config_manager.return_value.get = Mock(side_effect=lambda key, default=None: {
                'temporal_localization': mock_config['temporal_localization'],
                'temporal_localization.accuracy_requirement': 2.0,
                'temporal_localization.time_window_size': 2,
                'temporal_localization.min_confidence': 0.3,
                'temporal_localization.max_results': 10,
                'temporal_localization.timestamp_precision': 2
            }.get(key, default))
            mock_config_manager.return_value.watch = Mock()
            
            engine = TemporalLocalizationEngine()
            
            # 验证组件是否正确初始化
            assert engine.time_window_size == 2
            assert engine.min_confidence == 0.3
            assert engine.max_results == 10
            assert engine.timestamp_precision == 2
            assert engine.accuracy_requirement == 2.0
    
    def test_set_precision(self, temporal_engine):
        """测试设置时间戳精度"""
        engine = temporal_engine
        
        # 执行测试
        engine.set_precision(3)
        
        # 验证结果
        assert engine.timestamp_precision == 3
    
    def test_set_precision_invalid_value(self, temporal_engine):
        """测试设置无效时间戳精度"""
        engine = temporal_engine
        
        # 执行测试
        original_precision = engine.timestamp_precision
        engine.set_precision(5)  # 无效值
        
        # 验证结果 - 应该保持原值或使用默认值
        assert engine.timestamp_precision == original_precision
    
    def test_set_window_size(self, temporal_engine):
        """测试设置时间窗口大小"""
        engine = temporal_engine
        
        # 执行测试
        engine.set_window_size(3.0)
        
        # 验证结果
        assert engine.time_window_size == 3.0
    
    def test_set_window_size_invalid_value(self, temporal_engine):
        """测试设置无效时间窗口大小"""
        engine = temporal_engine
        
        # 执行测试
        original_window_size = engine.time_window_size
        engine.set_window_size(0.1)  # 无效值
        
        # 验证结果 - 应该保持原值或使用默认值
        assert engine.time_window_size == original_window_size
    
    def test_round_timestamp(self, temporal_engine):
        """测试时间戳舍入"""
        engine = temporal_engine
        
        # 设置精度为2位小数
        engine.timestamp_precision = 2
        
        # 执行测试
        result = engine._round_timestamp(1.23456)
        
        # 验证结果
        assert result == 1.23
    
    def test_resolve_timestamp_conflicts(self, temporal_engine):
        """测试解决时间戳冲突"""
        engine = temporal_engine
        
        # 创建测试数据
        timestamps = [
            FusedTimestamp(timestamp=1.0, total_score=0.9),
            FusedTimestamp(timestamp=1.5, total_score=0.8),  # 与第一个太近，应该合并
            FusedTimestamp(timestamp=5.0, total_score=0.7)   # 距离较远，保留
        ]
        
        # 执行测试
        result = engine._resolve_timestamp_conflicts(timestamps, min_distance=2.0)
        
        # 验证结果
        assert isinstance(result, list)
        # 结果数量应该减少（因为合并了冲突的时间戳）
        assert len(result) <= len(timestamps)
    
    def test_adjust_weights_based_on_query_visual(self, temporal_engine):
        """测试基于查询内容调整权重（视觉）"""
        engine = temporal_engine
        
        # 执行测试
        result = engine.adjust_weights_based_on_query("查找图片和视频画面")
        
        # 验证结果 - 视觉权重应该最高
        assert result['visual'] >= result['audio']
        assert result['visual'] >= result['speech']
    
    def test_adjust_weights_based_on_query_audio(self, temporal_engine):
        """测试基于查询内容调整权重（音频）"""
        engine = temporal_engine
        
        # 执行测试
        result = engine.adjust_weights_based_on_query("搜索音乐和声音")
        
        # 验证结果 - 音频权重应该最高
        assert result['audio'] >= result['visual']
        assert result['audio'] >= result['speech']
    
    def test_adjust_weights_based_on_query_speech(self, temporal_engine):
        """测试基于查询内容调整权重（语音）"""
        engine = temporal_engine
        
        # 执行测试
        result = engine.adjust_weights_based_on_query("查找说话和对话内容")
        
        # 验证结果 - 语音权重应该最高
        assert result['speech'] >= result['visual']
        assert result['speech'] >= result['audio']
    
    @pytest.mark.asyncio
    async def test_fuse_temporal_results_success(self, temporal_engine):
        """测试成功融合时间戳结果"""
        engine = temporal_engine
        
        # 创建测试数据
        visual_matches = [
            TimestampMatch(timestamp=1.0, similarity=0.9, modality='visual'),
            TimestampMatch(timestamp=2.0, similarity=0.8, modality='visual')
        ]
        audio_matches = [
            TimestampMatch(timestamp=1.5, similarity=0.7, modality='audio'),
            TimestampMatch(timestamp=3.0, similarity=0.6, modality='audio')
        ]
        speech_matches = [
            TimestampMatch(timestamp=1.2, similarity=0.8, modality='speech')
        ]
        
        # 执行测试
        result = await engine.fuse_temporal_results(visual_matches, audio_matches, speech_matches)
        
        # 验证结果
        assert isinstance(result, list)
        assert all(isinstance(item, FusedTimestamp) for item in result)
        # 结果应该按总分降序排列
        if len(result) > 1:
            scores = [item.total_score for item in result]
            assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_fuse_temporal_results_empty_input(self, temporal_engine):
        """测试融合空时间戳结果"""
        engine = temporal_engine
        
        # 执行测试
        result = await engine.fuse_temporal_results([], [], [])
        
        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_fuse_temporal_results_with_weights(self, temporal_engine):
        """测试使用自定义权重融合时间戳结果"""
        engine = temporal_engine
        
        # 创建测试数据
        visual_matches = [TimestampMatch(timestamp=1.0, similarity=0.9, modality='visual')]
        audio_matches = [TimestampMatch(timestamp=1.5, similarity=0.7, modality='audio')]
        speech_matches = [TimestampMatch(timestamp=1.2, similarity=0.8, modality='speech')]
        
        # 自定义权重
        weights = {
            'visual': 0.6,
            'audio': 0.3,
            'speech': 0.1
        }
        
        # 执行测试
        result = await engine.fuse_temporal_results(visual_matches, audio_matches, speech_matches, weights)
        
        # 验证结果
        assert isinstance(result, list)
        # 结果应该包含融合的时间戳
        if result:
            assert all(isinstance(item, FusedTimestamp) for item in result)
    
    @pytest.mark.asyncio
    async def test_fuse_temporal_results_invalid_input_types(self, temporal_engine):
        """测试融合无效输入类型的时间戳结果"""
        engine = temporal_engine
        
        # 执行测试 - 传入无效类型
        result = await engine.fuse_temporal_results("invalid", [], [])
        
        # 验证结果 - 应该返回空列表而不是抛出异常
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_locate_best_timestamp(self, temporal_engine):
        """测试定位最佳时间戳"""
        engine = temporal_engine
        
        # 创建测试数据
        visual_matches = [TimestampMatch(timestamp=1.0, similarity=0.9, modality='visual')]
        audio_matches = [TimestampMatch(timestamp=1.5, similarity=0.7, modality='audio')]
        speech_matches = [TimestampMatch(timestamp=1.2, similarity=0.8, modality='speech')]
        
        # 执行测试
        result = await engine.locate_best_timestamp(visual_matches, audio_matches, speech_matches, "查找最佳匹配")
        
        # 验证结果
        assert result is None or isinstance(result, FusedTimestamp)
    
    @pytest.mark.asyncio
    async def test_locate_multiple_timestamps(self, temporal_engine):
        """测试定位多个时间戳"""
        engine = temporal_engine
        
        # 创建测试数据
        visual_matches = [
            TimestampMatch(timestamp=1.0, similarity=0.9, modality='visual'),
            TimestampMatch(timestamp=2.0, similarity=0.8, modality='visual')
        ]
        audio_matches = [
            TimestampMatch(timestamp=1.5, similarity=0.7, modality='audio'),
            TimestampMatch(timestamp=3.0, similarity=0.6, modality='audio')
        ]
        speech_matches = [
            TimestampMatch(timestamp=1.2, similarity=0.8, modality='speech'),
            TimestampMatch(timestamp=2.5, similarity=0.7, modality='speech')
        ]
        
        # 执行测试
        result = await engine.locate_multiple_timestamps(visual_matches, audio_matches, speech_matches, top_k=3, query="查找多个匹配")
        
        # 验证结果
        assert isinstance(result, list)
        assert len(result) <= 3  # 不超过top_k
        if result:
            assert all(isinstance(item, FusedTimestamp) for item in result)
    
    def test_validate_precision(self, temporal_engine):
        """测试验证时间戳精度"""
        engine = temporal_engine
        
        # 执行测试
        result = engine.validate_precision(1.0, 2.5)  # 1.5秒差距，应该在±2秒范围内
        
        # 验证结果
        assert result is True
        
        # 测试超出精度范围
        result = engine.validate_precision(1.0, 5.0)  # 4秒差距，超出±2秒范围
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__])