"""
Qdrant向量存储使用示例
演示如何使用Qdrant向量存储功能
"""

import asyncio
import numpy as np
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.common.storage.vector_storage_manager import (
    VectorStorageManager, VectorType, VectorMetadata, SearchResult
)
from src.core.config_manager import get_config_manager


async def main():
    """主函数"""
    print("🚀 Qdrant向量存储使用示例")
    print("=" * 50)
    
    try:
        # 初始化配置管理器
        config_manager = get_config_manager()
        
        # 创建向量存储管理器
        storage_manager = VectorStorageManager(config_manager)
        
        # 初始化向量存储
        print("📦 初始化向量存储...")
        success = await storage_manager.initialize()
        if not success:
            print("❌ 向量存储初始化失败")
            return
        
        print("✅ 向量存储初始化成功")
        
        # 示例1: 存储单个向量
        await example_store_single_vector(storage_manager)
        
        # 示例2: 批量存储向量
        await example_batch_store_vectors(storage_manager)
        
        # 示例3: 搜索向量
        await example_search_vectors(storage_manager)
        
        # 示例4: 混合搜索
        await example_hybrid_search(storage_manager)
        
        # 示例5: 管理向量
        await example_vector_management(storage_manager)
        
        # 示例6: 健康检查
        await example_health_check(storage_manager)
        
    except Exception as e:
        print(f"❌ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        if 'storage_manager' in locals():
            await storage_manager.cleanup()
            print("🧹 资源清理完成")


async def example_store_single_vector(storage_manager):
    """示例1: 存储单个向量"""
    print("\n📝 示例1: 存储单个向量")
    print("-" * 30)
    
    # 创建测试向量数据
    vector_data = np.random.rand(512).astype(np.float32)
    
    # 创建元数据
    metadata = VectorMetadata(
        file_id="image_001",
        file_path="/data/media/images/sunset.jpg",
        file_name="sunset.jpg",
        file_type=".jpg",
        file_size=2048576,
        created_at=1640995200.0,
        segment_id="segment_001",
        start_time=10.5,
        end_time=15.5,
        duration=5.0,
        confidence=0.95,
        model_name="CLIP-ViT-B-32",
        additional_data={
            "resolution": "1920x1080",
            "format": "JPEG",
            "color_space": "RGB"
        }
    )
    
    # 存储向量
    vector_id = await storage_manager.store_vector(
        vector_type=VectorType.VISUAL,
        vector_data=vector_data,
        metadata=metadata
    )
    
    print(f"✅ 向量存储成功: {vector_id}")
    print(f"   文件: {metadata.file_name}")
    print(f"   类型: {metadata.file_type}")
    print(f"   维度: {vector_data.shape}")


async def example_batch_store_vectors(storage_manager):
    """示例2: 批量存储向量"""
    print("\n📦 示例2: 批量存储向量")
    print("-" * 30)
    
    vectors_data = []
    
    # 创建多个测试向量
    for i in range(5):
        vector_data = np.random.rand(512).astype(np.float32)
        metadata = VectorMetadata(
            file_id=f"image_{i+1:03d}",
            file_path=f"/data/media/images/sample_{i+1:03d}.jpg",
            file_name=f"sample_{i+1:03d}.jpg",
            file_type=".jpg",
            file_size=1024 * 1024 * (i + 1),
            created_at=1640995200.0 + i * 100,
            confidence=0.85 + i * 0.02,
            model_name="CLIP-ViT-B-32"
        )
        vectors_data.append((VectorType.VISUAL, vector_data, metadata))
    
    # 批量存储
    vector_ids = await storage_manager.batch_store_vectors(vectors_data)
    
    print(f"✅ 批量存储成功: {len(vector_ids)} 个向量")
    for i, vector_id in enumerate(vector_ids[:3]):  # 只显示前3个
        print(f"   向量 {i+1}: {vector_id}")


async def example_search_vectors(storage_manager):
    """示例3: 搜索向量"""
    print("\n🔍 示例3: 搜索向量")
    print("-" * 30)
    
    # 创建查询向量
    query_vector = np.random.rand(512).astype(np.float32)
    
    # 搜索相似向量
    results = await storage_manager.search_vectors(
        vector_type=VectorType.VISUAL,
        query_vector=query_vector,
        limit=5,
        score_threshold=0.5
    )
    
    print(f"✅ 搜索完成: 找到 {len(results)} 个结果")
    for i, result in enumerate(results[:3]):  # 只显示前3个
        print(f"   结果 {i+1}:")
        print(f"     向量ID: {result.vector_id}")
        print(f"     相似度: {result.score:.3f}")
        print(f"     距离: {result.distance:.3f}")
        print(f"     文件: {result.metadata.file_name}")
        print(f"   ")


async def example_hybrid_search(storage_manager):
    """示例4: 混合搜索"""
    print("\n🔄 示例4: 混合搜索")
    print("-" * 30)
    
    # 创建不同类型的查询向量
    visual_query = np.random.rand(512).astype(np.float32)
    audio_query = np.random.rand(512).astype(np.float32)
    
    query_vectors = {
        VectorType.VISUAL: visual_query,
        VectorType.AUDIO_MUSIC: audio_query
    }
    
    # 设置权重
    weights = {
        VectorType.VISUAL: 0.7,
        VectorType.AUDIO_MUSIC: 0.3
    }
    
    # 执行混合搜索
    results = await storage_manager.hybrid_search(
        query_vectors=query_vectors,
        weights=weights,
        limit=10,
        score_threshold=0.4
    )
    
    print(f"✅ 混合搜索完成: 找到 {len(results)} 个结果")
    print("   权重配置:")
    for vt, weight in weights.items():
        print(f"     {vt.value}: {weight}")
    
    for i, result in enumerate(results[:3]):  # 只显示前3个
        print(f"   结果 {i+1}:")
        print(f"     向量ID: {result.vector_id}")
        print(f"     综合分数: {result.score:.3f}")
        print(f"     文件: {result.metadata.file_name}")
        print(f"     向量类型: {result.metadata.additional_data.get('vector_type', 'unknown')}")
        print(f"   ")


async def example_vector_management(storage_manager):
    """示例5: 向量管理"""
    print("\n⚙️ 示例5: 向量管理")
    print("-" * 30)
    
    # 获取向量数量
    counts = await storage_manager.get_vector_count()
    print("📊 向量统计:")
    for vector_type, count in counts.items():
        print(f"   {vector_type}: {count} 个向量")
    
    # 获取集合统计
    stats = await storage_manager.get_collection_stats()
    print("\n📊 集合统计:")
    for collection_type, info in stats.items():
        if 'error' not in info:
            print(f"   {collection_type}:")
            print(f"     集合名称: {info.get('collection_name', 'N/A')}")
            print(f"     向量数量: {info.get('vectors_count', 0)}")
            print(f"     状态: {info.get('status', 'N/A')}")
            print(f"     维度: {info.get('dimension', 'N/A')}")
        else:
            print(f"   {collection_type}: 错误 - {info['error']}")
    
    # 删除特定文件的向量
    file_id = "image_001"
    deleted_counts = await storage_manager.delete_vectors_by_file(file_id)
    print(f"\n🗑️ 删除文件 {file_id} 的向量:")
    for vector_type, count in deleted_counts.items():
        if count > 0:
            print(f"   {vector_type}: 删除了 {count} 个向量")


async def example_health_check(storage_manager):
    """示例6: 健康检查"""
    print("\n🏥 示例6: 健康检查")
    print("-" * 30)
    
    # 执行健康检查
    health = await storage_manager.health_check()
    
    print(f"健康状态: {health['status']}")
    
    if health['status'] == 'healthy':
        print("✅ Qdrant服务运行正常")
        print(f"   总向量数: {health['total_vectors']}")
        print(f"   支持的类型: {', '.join(health['supported_types'])}")
        
        print("\n📊 集合状态:")
        for collection_name, info in health.get('collections', {}).items():
            if 'error' not in info:
                print(f"   {collection_name}:")
                print(f"     向量数: {info.get('vectors_count', 0)}")
                print(f"     状态: {info.get('status', 'unknown')}")
    else:
        print("❌ Qdrant服务异常")
        if 'error' in health:
            print(f"   错误: {health['error']}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
