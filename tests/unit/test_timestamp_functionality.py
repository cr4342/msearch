#!/usr/bin/env python3
"""
测试时间戳处理功能 - pytest版本
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

@pytest.mark.asyncio
async def test_temporal_localization():
    """测试时间定位功能"""
    print("开始测试时间定位引擎...")
    
    # 创建时间定位引擎实例
    engine = TemporalLocalizationEngine()
    
    # 创建测试数据
    visual_matches = [
        TimestampMatch(timestamp=10.5, similarity=0.9, modality="visual"),
        TimestampMatch(timestamp=12.3, similarity=0.7, modality="visual"),
        TimestampMatch(timestamp=25.1, similarity=0.8, modality="visual")
    ]
    
    audio_matches = [
        TimestampMatch(timestamp=11.2, similarity=0.85, modality="audio"),
        TimestampMatch(timestamp=24.8, similarity=0.75, modality="audio")
    ]
    
    speech_matches = [
        TimestampMatch(timestamp=10.8, similarity=0.8, modality="speech"),
        TimestampMatch(timestamp=15.0, similarity=0.6, modality="speech"),
        TimestampMatch(timestamp=30.2, similarity=0.95, modality="speech")
    ]
    
    print("测试数据创建完成")
    
    # 测试融合时间戳结果
    print("测试融合时间戳结果...")
    fused_results = await engine.fuse_temporal_results(
        visual_matches, audio_matches, speech_matches
    )
    
    print(f"融合结果数量: {len(fused_results)}")
    for i, result in enumerate(fused_results):
        print(f"  结果 {i+1}: 时间={result.timestamp:.1f}s, 分数={result.total_score:.3f}, 置信度={result.confidence:.3f}")
    
    # 测试定位最佳时间戳
    print("测试定位最佳时间戳...")
    best_timestamp = await engine.locate_best_timestamp(
        visual_matches, audio_matches, speech_matches, query="测试查询"
    )
    
    if best_timestamp:
        print(f"最佳时间戳: {best_timestamp.timestamp:.1f}s, 分数={best_timestamp.total_score:.3f}")
    else:
        print("未找到最佳时间戳")
    
    # 测试定位多个时间戳
    print("测试定位多个时间戳...")
    multiple_timestamps = await engine.locate_multiple_timestamps(
        visual_matches, audio_matches, speech_matches, top_k=3, query="测试查询"
    )
    
    print(f"多个时间戳结果数量: {len(multiple_timestamps)}")
    for i, ts in enumerate(multiple_timestamps):
        print(f"  时间戳 {i+1}: {ts.timestamp:.1f}s, 分数={ts.total_score:.3f}")
    
    print("时间定位引擎测试完成!")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])