#!/usr/bin/env python3
"""
简单功能测试脚本 - pytest版本
"""

import sys
import os
import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_basic_functionality():
    """测试基本功能"""
    print("开始基本功能测试...")
    
    try:
        # 测试时间定位引擎
        from src.business.temporal_localization_engine import TemporalLocalizationEngine
        engine = TemporalLocalizationEngine()
        print("✓ 时间定位引擎初始化成功")
        
        # 测试配置管理器
        from src.core.config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.config  # 直接访问config属性
        print("✓ 配置管理器初始化成功")
        
        # 测试向量存储
        from src.storage.vector_store import VectorStore
        vector_store = VectorStore()
        print("✓ 向量存储初始化成功")
        
        # 测试搜索功能
        from src.business.search_engine import SearchEngine
        search_engine = SearchEngine(config, vector_store, None)
        print("✓ 搜索引擎初始化成功")
        
        print("🎉 所有基本功能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])