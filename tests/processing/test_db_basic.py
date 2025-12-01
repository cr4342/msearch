#!/usr/bin/env python3
"""
数据库基础功能测试
"""

import asyncio
import os
import tempfile
import uuid
from pathlib import Path

from src.core.config_manager import ConfigManager
from src.common.storage.database_adapter import DatabaseAdapter


async def test_database_basic_operations():
    """测试数据库基础操作"""
    print("🧪 开始数据库基础功能测试")
    
    # 创建临时测试环境
    test_dir = tempfile.mkdtemp(prefix="msearch_test_db_")
    db_path = f"{test_dir}/test_database.db"
    
    try:
        # 初始化配置和数据库
        config_manager = ConfigManager()
        config_manager.set("database.sqlite.path", db_path)
        
        db_adapter = DatabaseAdapter(config_manager)
        
        print(f"📁 测试目录: {test_dir}")
        print(f"🗃️  数据库路径: {db_path}")
        
        # 创建测试文件
        test_file_path = os.path.join(test_dir, "test_image_001.jpg")
        
        # 创建简单的测试文件
        content = b"Test image content"
        with open(test_file_path, 'wb') as f:
            f.write(b'\xFF\xD8\xFF')  # JPEG header
            f.write(content)
            f.write(b'\xFF\xD9')  # JPEG footer
        
        print(f"📄 创建测试文件: {test_file_path}")
        
        # 测试插入文件记录
        file_info = {
            'id': str(uuid.uuid4()),
            'file_path': test_file_path,
            'file_name': "test_image_001.jpg",
            'file_type': ".jpg",
            'file_size': len(content) + 6,  # content + headers
            'file_hash': "abc123def456",
            'created_at': 1234567890.0,
            'modified_at': 1234567890.0,
            'status': 'pending'
        }
        
        print("📝 尝试插入文件记录...")
        try:
            file_id = await db_adapter.insert_file(file_info)
            print(f"✅ 文件记录插入成功，ID: {file_id}")
        except Exception as e:
            print(f"❌ 文件记录插入失败: {e}")
            return False
        
        # 测试获取文件记录
        print("🔍 尝试获取文件记录...")
        try:
            retrieved_file = await db_adapter.get_file_by_path(test_file_path)
            if retrieved_file:
                print(f"✅ 文件记录获取成功:")
                print(f"  📄 文件名: {retrieved_file.get('file_name')}")
                print(f"  🏷️  类型: {retrieved_file.get('file_type')}")
                print(f"  📊 状态: {retrieved_file.get('status')}")
            else:
                print(f"❌ 文件记录获取失败")
                return False
        except Exception as e:
            print(f"❌ 获取文件记录异常: {e}")
            return False
        
        # 测试更新文件记录
        print("📝 尝试更新文件记录...")
        try:
            success = await db_adapter.update_file(file_id, {'status': 'processing'})
            if success:
                print(f"✅ 文件记录更新成功")
                
                # 验证更新
                updated_file = await db_adapter.get_file(file_id)
                if updated_file and updated_file.get('status') == 'processing':
                    print(f"✅ 文件状态更新验证成功")
                else:
                    print(f"❌ 文件状态更新验证失败")
            else:
                print(f"❌ 文件记录更新失败")
        except Exception as e:
            print(f"❌ 更新文件记录异常: {e}")
            return False
        
        print("✅ 数据库基础功能测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        return False
    finally:
        # 清理测试环境
        import shutil
        try:
            shutil.rmtree(test_dir)
            print(f"🧹 测试环境清理完成")
        except Exception as e:
            print(f"⚠️  清理测试环境失败: {e}")


async def main():
    """主函数"""
    print("🔍 多模态检索系统 - 数据库基础功能测试")
    print("=" * 60)
    
    success = await test_database_basic_operations()
    
    print("=" * 60)
    if success:
        print("🎉 测试通过")
    else:
        print("❌ 测试失败")


if __name__ == "__main__":
    asyncio.run(main())