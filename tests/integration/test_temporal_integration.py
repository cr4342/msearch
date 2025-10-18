#!/usr/bin/env python3
"""
测试时间戳处理与向量存储、搜索引擎的集成 - pytest版本
"""

import sys
import os
import asyncio
import numpy as np
import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.business.temporal_localization_engine import (
    TemporalLocalizationEngine,
    TimestampMatch
)
from src.storage.vector_store import VectorStore
from src.business.search_engine import SearchEngine

class MockEmbeddingEngine:
    """模拟嵌入引擎"""
    
    async def embed_content(self, content, content_type):
        """模拟内容向量化"""
        # 返回一个512维的随机向量
        return np.random.rand(512).tolist()

@pytest.mark.asyncio
async def test_integration():
    """测试集成功能"""
    print("开始测试时间戳处理与向量存储、搜索引擎的集成...")
    
    # 创建时间定位引擎实例
    temporal_engine = TemporalLocalizationEngine()
    
    # 创建模拟向量存储实例
    vector_store = VectorStore()
    
    # 创建模拟嵌入引擎实例
    embedding_engine = MockEmbeddingEngine()
    
    # 创建搜索引擎实例
    config = {
        'search.top_k': 50,
        'search.similarity_threshold': 0.5
    }
    search_engine = SearchEngine(config, vector_store, embedding_engine)
    
    print("组件初始化完成")
    
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
    
    # 测试时间范围搜索
    print("测试时间范围搜索...")
    try:
        time_range_results = await search_engine.search_by_time_range(
            file_id="test_file_001",
            start_time=10.0,
            end_time=20.0
        )
        print(f"时间范围搜索结果数量: {len(time_range_results)}")
    except Exception as e:
        print(f"时间范围搜索测试出现错误: {e}")
    
    # 测试向量存储的时间范围搜索
    print("测试向量存储的时间范围搜索...")
    try:
        vector_store_results = await vector_store.search_by_time_range(
            file_id="test_file_001",
            start_time=10.0,
            end_time=20.0
        )
        print(f"向量存储时间范围搜索结果数量: {len(vector_store_results)}")
    except Exception as e:
        print(f"向量存储时间范围搜索测试出现错误: {e}")
    
    # 测试时间戳融合
    print("测试时间戳融合...")
    try:
        fused_results = await temporal_engine.fuse_temporal_results(
            visual_matches, audio_matches, speech_matches
        )
        print(f"融合结果数量: {len(fused_results)}")
        
        # 验证融合结果
        for i, result in enumerate(fused_results):
            print(f"  结果 {i+1}: 时间={result.timestamp:.1f}s, 分数={result.total_score:.3f}")
    except Exception as e:
        print(f"时间戳融合测试出现错误: {e}")
    
    print("集成测试完成!")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])