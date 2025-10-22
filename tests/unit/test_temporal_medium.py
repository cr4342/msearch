#!/usr/bin/env python3
"""
中等复杂度时间定位引擎测试
"""

import sys
import os
import asyncio
import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.business.temporal_localization_engine import (
    TemporalLocalizationEngine,
    TimestampMatch,
    FusedTimestamp
)


class TestTemporalLocalizationEngineMedium:
    """时间定位引擎中等复杂度测试"""
    
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])