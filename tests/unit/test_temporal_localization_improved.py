#!/usr/bin/env python3
"""
时间定位引擎改进功能测试
测试增强的错误处理和边界情况处理
"""

import sys
import os
import pytest
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.business.temporal_localization_engine import (
    TemporalLocalizationEngine,
    TimestampMatch,
    FusedTimestamp
)


class TestTemporalLocalizationEngineImproved:
    """时间定位引擎改进功能测试"""
    
    @pytest.fixture
    def engine(self):
        """创建时间定位引擎实例"""
        return TemporalLocalizationEngine()
    
    @pytest.mark.asyncio
    async def test_fuse_temporal_results_with_none_inputs(self, engine):
        """测试fuse_temporal_results方法处理None输入"""
        # 测试所有参数为None的情况
        result = await engine.fuse_temporal_results(None, None, None)
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_fuse_temporal_results_with_empty_inputs(self, engine):
        """测试fuse_temporal_results方法处理空列表输入"""
        # 测试所有参数为空列表的情况
        result = await engine.fuse_temporal_results([], [], [])
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_fuse_temporal_results_with_invalid_weights_type(self, engine):
        """测试fuse_temporal_results方法处理无效权重类型"""
        visual_matches = [TimestampMatch(timestamp=10.0, similarity=0.8, modality="visual")]
        
        # 测试权重为非字典类型
        result = await engine.fuse_temporal_results(visual_matches, [], [], "invalid_weights")
        # 应该使用默认权重并正常处理
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_fuse_temporal_results_with_missing_weights_keys(self, engine):
        """测试fuse_temporal_results方法处理缺少权重键的情况"""
        visual_matches = [TimestampMatch(timestamp=10.0, similarity=0.8, modality="visual")]
        
        # 测试权重字典缺少必要键
        incomplete_weights = {"visual": 0.5}  # 缺少audio和speech键
        result = await engine.fuse_temporal_results(visual_matches, [], [], incomplete_weights)
        # 应该补充缺失的权重并正常处理
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_fuse_temporal_results_with_invalid_match_objects(self, engine):
        """测试fuse_temporal_results方法处理无效匹配对象"""
        # 测试包含无效匹配对象的情况
        invalid_matches = [{"invalid": "object"}]  # 不是TimestampMatch对象
        result = await engine.fuse_temporal_results(invalid_matches, [], [])
        # 应该记录警告并继续处理
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_fuse_temporal_results_normal_case(self, engine):
        """测试fuse_temporal_results方法正常情况"""
        visual_matches = [
            TimestampMatch(timestamp=10.0, similarity=0.8, modality="visual"),
            TimestampMatch(timestamp=12.0, similarity=0.7, modality="visual")
        ]
        audio_matches = [
            TimestampMatch(timestamp=11.0, similarity=0.75, modality="audio")
        ]
        speech_matches = [
            TimestampMatch(timestamp=10.5, similarity=0.85, modality="speech")
        ]
        
        result = await engine.fuse_temporal_results(visual_matches, audio_matches, speech_matches)
        assert isinstance(result, list)
        # 应该返回融合后的时间戳结果
        assert all(isinstance(ts, FusedTimestamp) for ts in result)
    
    @pytest.mark.asyncio
    async def test_fuse_temporal_results_result_limiting(self, engine):
        """测试fuse_temporal_results方法结果数量限制"""
        # 创建超过最大结果数量的匹配
        visual_matches = []
        for i in range(engine.max_results + 5):  # 超过最大结果数量
            visual_matches.append(TimestampMatch(timestamp=float(i), similarity=0.8, modality="visual"))
        
        result = await engine.fuse_temporal_results(visual_matches, [], [])
        assert isinstance(result, list)
        # 结果数量应该被限制在max_results以内
        assert len(result) <= engine.max_results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])