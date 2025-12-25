#!/usr/bin/env python3

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.common.storage.vector_storage_manager import VectorStorageManager, VectorType, VectorMetadata

async def test_vector_storage():
    """测试向量存储管理器的完整功能"""
    print("=== 测试向量存储管理器 ===")
    
    try:
        # 初始化向量存储管理器
        storage_manager = VectorStorageManager()
        print("✓ 向量存储管理器初始化成功")
        
        # 初始化存储
        initialized = await storage_manager.initialize()
        if not initialized:
            print("✗ 向量存储初始化失败")
            return False
        print("✓ 向量存储初始化成功")
        
        # 测试插入向量
        vectors = {
            VectorType.VISUAL: [0.1] * 512,
            VectorType.AUDIO_MUSIC: [0.2] * 512,
            VectorType.TEXT: [0.3] * 512
        }
        
        inserted_vector_ids = []
        for vector_type, vector in vectors.items():
            metadata = VectorMetadata(
                file_id=f"test_file_{vector_type.value}",
                file_path=f"/test/path/{vector_type.value}.mp4",
                file_name=f"{vector_type.value}.mp4",
                file_type="video",
                file_size=1024 * 1024,  # 1MB
                created_at=1672531200.0,  # 2023-01-01T00:00:00
                segment_id=f"segment_{vector_type.value}_1",
                start_time=0.0,
                end_time=10.0,
                duration=10.0,
                confidence=0.9,
                model_name="test_model",
                additional_data={
                    "frame_rate": 30.0,
                    "resolution": "1920x1080"
                }
            )
            
            try:
                vector_id = await storage_manager.store_vector(vector_type, vector, metadata)
                if vector_id:
                    print(f"✓ 插入{vector_type.name}向量成功，ID: {vector_id}")
                    inserted_vector_ids.append(vector_id)
                else:
                    print(f"✗ 插入{vector_type.name}向量失败")
                    return False
            except Exception as e:
                print(f"✗ 插入{vector_type.name}向量异常: {e}")
                return False
        
        # 测试检索向量
        query_vector = [0.1] * 512
        results = await storage_manager.search_vectors(VectorType.VISUAL, query_vector, limit=3, score_threshold=0.0)
        if results:
            print(f"✓ 检索VISUAL向量成功，返回{len(results)}个结果")
            for idx, result in enumerate(results):
                print(f"   结果{idx+1}: ID={result.vector_id}, 相似度={result.score:.4f}")
        else:
            print("✗ 检索VISUAL向量失败")
            return False
        
        # 测试删除向量
        file_id = "test_file_1"  # VISUAL的value是1
        delete_result = await storage_manager.delete_vectors_by_file(file_id)
        if delete_result:
            print(f"✓ 删除向量成功，删除结果: {delete_result}")
        else:
            print("✗ 删除向量失败")
            return False
        
        # 测试向量计数
        count_result = await storage_manager.get_vector_count()
        if count_result:
            print(f"✓ 获取向量计数成功: {count_result}")
        else:
            print("✗ 获取向量计数失败")
            return False
        
        # 清理资源
        await storage_manager.cleanup()
        print("✓ 清理资源成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 向量存储测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    success = await test_vector_storage()
    
    print("\n=== 测试结果 ===")
    if success:
        print("✓ 所有向量存储测试通过！FAISS替换成功。")
        return 0
    else:
        print("✗ 向量存储测试失败！")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
