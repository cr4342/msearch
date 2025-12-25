#!/usr/bin/env python3

import sys
import os
import asyncio

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.common.storage.faiss_adapter import FaissAdapter
from src.common.storage.vector_storage_manager import VectorStorageManager

async def test_faiss_adapter():
    """测试FAISS适配器是否能正常工作"""
    print("测试FAISS适配器...")
    
    try:
        # 初始化FAISS适配器
        adapter = FaissAdapter()
        print("✓ FAISS适配器初始化成功")
        
        # 连接到FAISS
        connected = await adapter.connect()
        if connected:
            print("✓ FAISS连接成功")
        else:
            print("✗ FAISS连接失败")
            return False
        
        # 测试创建集合
        success = await adapter.create_collection("test_collection", vector_size=512)
        if success:
            print("✓ 创建集合成功")
        else:
            print("✗ 创建集合失败")
            return False
        
        # 测试健康检查
        health = await adapter.health_check()
        if health["status"] == "healthy":
            print("✓ 健康检查成功")
        else:
            print("✗ 健康检查失败")
            return False
        
        # 断开连接
        await adapter.disconnect()
        print("✓ 断开连接成功")
        
        return True
        
    except Exception as e:
        print(f"✗ FAISS适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_vector_storage_manager():
    """测试向量存储管理器是否能正常工作"""
    print("\n测试向量存储管理器...")
    
    try:
        # 初始化向量存储管理器
        manager = VectorStorageManager()
        print("✓ 向量存储管理器初始化成功")
        
        # 初始化
        initialized = await manager.initialize()
        if initialized:
            print("✓ 向量存储管理器初始化成功")
        else:
            print("✗ 向量存储管理器初始化失败")
            return False
        
        # 健康检查
        health = await manager.health_check()
        if health["status"] == "healthy":
            print("✓ 向量存储管理器健康检查成功")
        else:
            print("✗ 向量存储管理器健康检查失败")
            print(f"健康状态: {health}")
            return False
        
        # 清理资源
        await manager.cleanup()
        print("✓ 向量存储管理器清理成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 向量存储管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("=== FAISS替换测试 ===")
    
    # 测试FAISS适配器
    faiss_success = await test_faiss_adapter()
    
    # 测试向量存储管理器
    manager_success = await test_vector_storage_manager()
    
    print("\n=== 测试结果 ===")
    if faiss_success and manager_success:
        print("✓ 所有测试通过！FAISS替换成功。")
        return 0
    else:
        print("✗ 部分测试失败！请检查错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
