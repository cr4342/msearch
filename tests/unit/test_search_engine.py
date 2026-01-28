#!/usr/bin/env python3
"""
测试搜索引擎核心功能

测试 SearchEngine 使用依赖注入的正确实现
"""

import asyncio
import logging
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock
from typing import List, Dict, Any, Optional

# 设置日志级别
logging.basicConfig(level=logging.INFO)

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.search.search_engine import SearchEngine, EmbeddingEngine, VectorStore


def create_mock_embedding_engine():
    """创建模拟的向量化引擎"""
    mock_engine = Mock(spec=EmbeddingEngine)
    mock_engine.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4, 0.5])
    mock_engine.embed_image = AsyncMock(return_value=[0.2, 0.3, 0.4, 0.5, 0.6])
    mock_engine.embed_audio = AsyncMock(return_value=[0.3, 0.4, 0.5, 0.6, 0.7])
    mock_engine.embed_video_segment = AsyncMock(return_value=[0.4, 0.5, 0.6, 0.7, 0.8])
    return mock_engine


def create_mock_vector_store():
    """创建模拟的向量存储"""
    mock_store = Mock(spec=VectorStore)
    mock_store.search_vectors = Mock(return_value=[
        {
            'id': 'file1',
            'score': 0.95,
            'metadata': {
                'file_path': '/test/video1.mp4',
                'file_name': 'video1.mp4',
                'modality': 'video',
                'start_time': 0.0,
                'end_time': 5.0,
                'duration': 5.0
            }
        },
        {
            'id': 'file2',
            'score': 0.85,
            'metadata': {
                'file_path': '/test/image1.jpg',
                'file_name': 'image1.jpg',
                'modality': 'image'
            }
        }
    ])
    return mock_store


def test_create_search_engine():
    """测试创建搜索引擎"""
    print("\n=== 测试创建搜索引擎 ===")
    
    mock_embedding_engine = create_mock_embedding_engine()
    mock_vector_store = create_mock_vector_store()
    
    search_engine = SearchEngine(mock_embedding_engine, mock_vector_store)
    
    print(f"  向量化引擎: {type(search_engine.embedding_engine).__name__}")
    print(f"  向量存储: {type(search_engine.vector_store).__name__}")
    
    assert search_engine.embedding_engine == mock_embedding_engine
    assert search_engine.vector_store == mock_vector_store
    
    print("  ✓ 创建搜索引擎 测试通过")


def test_search_engine_initialize():
    """测试搜索引擎初始化"""
    print("\n=== 测试搜索引擎初始化 ===")
    
    mock_embedding_engine = create_mock_embedding_engine()
    mock_vector_store = create_mock_vector_store()
    
    search_engine = SearchEngine(mock_embedding_engine, mock_vector_store)
    result = search_engine.initialize()
    
    print(f"  初始化结果: {result}")
    
    assert result == True
    
    print("  ✓ 搜索引擎初始化 测试通过")


@pytest.mark.asyncio
async def test_search():
    """测试搜索功能"""
    print("\n=== 测试搜索功能 ===")
    
    mock_embedding_engine = create_mock_embedding_engine()
    mock_vector_store = create_mock_vector_store()
    
    search_engine = SearchEngine(mock_embedding_engine, mock_vector_store)
    
    # 执行搜索
    results = await search_engine.search('test query', k=5)
    
    print(f"  查询: test query")
    print(f"  结果数量: {len(results.get('results', []))}")
    print(f"  搜索状态: {results.get('status')}")
    
    # 验证查询被调用
    mock_embedding_engine.embed_text.assert_called_once_with('test query')
    
    print("  ✓ 搜索功能 测试通过")


@pytest.mark.asyncio
async def test_image_search():
    """测试图像搜索"""
    print("\n=== 测试图像搜索 ===")
    
    mock_embedding_engine = create_mock_embedding_engine()
    mock_vector_store = create_mock_vector_store()
    
    search_engine = SearchEngine(mock_embedding_engine, mock_vector_store)
    
    # 执行图像搜索
    results = await search_engine.image_search('/test/image.jpg', k=5)
    
    print(f"  图像路径: /test/image.jpg")
    print(f"  结果数量: {len(results.get('results', []))}")
    
    # 验证图像嵌入被调用
    mock_embedding_engine.embed_image.assert_called_once_with('/test/image.jpg')
    
    print("  ✓ 图像搜索 测试通过")


@pytest.mark.asyncio
async def test_audio_search():
    """测试音频搜索"""
    print("\n=== 测试音频搜索 ===")
    
    mock_embedding_engine = create_mock_embedding_engine()
    mock_vector_store = create_mock_vector_store()
    
    search_engine = SearchEngine(mock_embedding_engine, mock_vector_store)
    
    # 执行音频搜索
    results = await search_engine.audio_search('/test/audio.mp3', k=5)
    
    print(f"  音频路径: /test/audio.mp3")
    print(f"  结果数量: {len(results.get('results', []))}")
    
    # 验证音频嵌入被调用
    mock_embedding_engine.embed_audio.assert_called_once_with('/test/audio.mp3')
    
    print("  ✓ 音频搜索 测试通过")


def test_rank_results():
    """测试结果排序"""
    print("\n=== 测试结果排序 ===")
    
    mock_embedding_engine = create_mock_embedding_engine()
    mock_vector_store = create_mock_vector_store()
    
    search_engine = SearchEngine(mock_embedding_engine, mock_vector_store)
    
    # 测试结果排序
    test_results = [
        {'score': 0.5, 'file_id': 'file1'},
        {'score': 0.9, 'file_id': 'file2'},
        {'score': 0.7, 'file_id': 'file3'}
    ]
    
    # 使用私有方法_rank_results
    ranked_results = search_engine._rank_results(test_results)
    
    print(f"  排序前结果数: {len(test_results)}")
    print(f"  排序后结果数: {len(ranked_results)}")
    print(f"  最高分结果: {ranked_results[0]['score']}")
    
    # 验证结果已排序
    assert ranked_results[0]['score'] == 0.9
    assert ranked_results[1]['score'] == 0.7
    assert ranked_results[2]['score'] == 0.5
    
    print("  ✓ 结果排序 测试通过")


def test_aggregate_results():
    """测试结果聚合"""
    print("\n=== 测试结果聚合 ===")
    
    mock_embedding_engine = create_mock_embedding_engine()
    mock_vector_store = create_mock_vector_store()
    
    search_engine = SearchEngine(mock_embedding_engine, mock_vector_store)
    
    # 测试结果聚合
    test_results = [
        {'score': 0.5, 'file_id': 'file1', 'file_path': '/test/file1.mp4'},
        {'score': 0.9, 'file_id': 'file1', 'file_path': '/test/file1.mp4'},  # 相同file_id
        {'score': 0.7, 'file_id': 'file2', 'file_path': '/test/file2.mp4'}
    ]
    
    aggregated_results = search_engine._aggregate_results(test_results)
    
    print(f"  聚合前结果数: {len(test_results)}")
    print(f"  聚合后结果数: {len(aggregated_results)}")
    
    # 验证聚合结果
    assert len(aggregated_results) == 2  # file1被合并
    file1_result = next((r for r in aggregated_results if r['file_id'] == 'file1'), None)
    assert file1_result['score'] == 0.9  # 保留最高分
    
    print("  ✓ 结果聚合 测试通过")


def test_format_results():
    """测试结果格式化"""
    print("\n=== 测试结果格式化 ===")
    
    mock_embedding_engine = create_mock_embedding_engine()
    mock_vector_store = create_mock_vector_store()
    
    search_engine = SearchEngine(mock_embedding_engine, mock_vector_store)
    
    # 测试结果格式化 - 使用正确的字段名
    test_results = [
        {'file_id': 'file1', 'score': 0.9, 'file_path': '/test/file1.mp4', 
         'file_name': 'file1.mp4', 'modality': 'video', 'metadata': {'duration': 5.0}}
    ]
    
    formatted_results = search_engine._format_results(test_results)
    
    print(f"  格式化前结果数: {len(test_results)}")
    print(f"  格式化后结果数: {len(formatted_results)}")
    print(f"  格式化结果: {formatted_results[0]}")
    
    # 验证格式化结果
    assert formatted_results[0]['file_id'] == 'file1'
    assert formatted_results[0]['score'] == 0.9
    assert formatted_results[0]['modality'] == 'video'
    
    print("  ✓ 结果格式化 测试通过")


def main():
    """主函数"""
    print("=" * 60)
    print("搜索引擎核心功能测试")
    print("=" * 60)
    
    try:
        test_create_search_engine()
        test_search_engine_initialize()
        
        # 异步测试
        asyncio.run(test_search())
        asyncio.run(test_image_search())
        asyncio.run(test_audio_search())
        
        # 同步测试
        test_rank_results()
        test_aggregate_results()
        test_format_results()
        
        print("\n" + "=" * 60)
        print("所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()