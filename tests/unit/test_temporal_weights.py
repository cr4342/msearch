#!/usr/bin/env python3
"""
权重相关时间定位引擎测试
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


class TestTemporalLocalizationEngineWeights:
    """时间定位引擎权重相关测试"""
    
    @pytest.fixture
    def engine(self):
        """创建时间定位引擎实例"""
        return TemporalLocalizationEngine()
    
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])