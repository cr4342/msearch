#!/usr/bin/env python3
"""
系统集成测试脚本 - pytest版本
"""

import sys
import os
import asyncio
import time
import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_imports():
    """测试关键模块导入"""
    print("测试模块导入...")
    
    try:
        from src.business.temporal_localization_engine import TemporalLocalizationEngine
        print("✓ 时间定位引擎导入成功")
    except Exception as e:
        print(f"✗ 时间定位引擎导入失败: {e}")
        return False
    
    try:
        from src.storage.vector_store import VectorStore
        print("✓ 向量存储导入成功")
    except Exception as e:
        print(f"✗ 向量存储导入失败: {e}")
        return False
    
    try:
        from src.business.search_engine import SearchEngine
        print("✓ 搜索引擎导入成功")
    except Exception as e:
        print(f"✗ 搜索引擎导入失败: {e}")
        return False
    
    try:
        from src.business.smart_retrieval import SmartRetrievalEngine
        print("✓ 智能检索引擎导入成功")
    except Exception as e:
        print(f"✗ 智能检索引擎导入失败: {e}")
        return False
    
    try:
        from src.business.processing_orchestrator import ProcessingOrchestrator
        print("✓ 处理编排器导入成功")
    except Exception as e:
        print(f"✗ 处理编排器导入失败: {e}")
        return False
    
    return True

@pytest.mark.asyncio
async def test_time_processing():
    """测试时间戳处理功能"""
    print("\n测试时间戳处理功能...")
    
    try:
        from src.business.temporal_localization_engine import (
            TemporalLocalizationEngine,
            TimestampMatch
        )
        
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
        
        # 测试融合时间戳结果
        fused_results = await engine.fuse_temporal_results(
            visual_matches, audio_matches, speech_matches
        )
        
        print(f"✓ 时间戳融合成功，结果数量: {len(fused_results)}")
        
        # 测试定位最佳时间戳
        best_timestamp = await engine.locate_best_timestamp(
            visual_matches, audio_matches, speech_matches, query="测试查询"
        )
        
        if best_timestamp:
            print(f"✓ 最佳时间戳定位成功: {best_timestamp.timestamp:.1f}s")
        else:
            print("⚠ 未找到最佳时间戳")
        
        return True
        
    except Exception as e:
        print(f"✗ 时间戳处理测试失败: {e}")
        return False

def test_configuration():
    """测试配置加载"""
    print("\n测试配置加载...")
    
    try:
        from src.core.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        config = config_manager.config  # 直接访问config属性
        
        print(f"✓ 配置加载成功，配置项数量: {len(config)}")
        return True
        
    except Exception as e:
        print(f"✗ 配置加载测试失败: {e}")
        return False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])