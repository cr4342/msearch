#!/usr/bin/env python3
"""
文件监控器诊断测试
"""

import asyncio
import hashlib
import os
import tempfile
import time
import uuid
from pathlib import Path

from src.core.config_manager import ConfigManager
from src.common.storage.database_adapter import DatabaseAdapter
from src.processing_service.file_monitor import FileMonitor


async def test_file_monitor_diagnosis():
    """测试文件监控器的诊断信息"""
    print("🔍 文件监控器诊断测试")
    
    # 创建临时测试环境
    test_dir = tempfile.mkdtemp(prefix="msearch_test_monitor_")
    db_path = f"{test_dir}/test_database.db"
    
    try:
        # 初始化配置和组件
        config_manager = ConfigManager()
        config_manager.set("database.sqlite.path", db_path)
        config_manager.set("system.monitored_directories", [test_dir])
        config_manager.set("system.supported_extensions", ['.jpg', '.jpeg', '.png', '.mp3', '.mp4'])
        config_manager.set("system.debounce_delay", 0.1)
        
        db_adapter = DatabaseAdapter(config_manager)
        file_monitor = FileMonitor(config_manager)
        
        print(f"📁 测试目录: {test_dir}")
        print(f"🗃️  数据库路径: {db_path}")
        print(f"📡 监控目录: {config_manager.get('system.monitored_directories')}")
        
        # 创建测试文件
        test_file_path = os.path.join(test_dir, "test_image_001.jpg")
        
        # 创建简单的测试文件
        content = b"Test image content"
        with open(test_file_path, 'wb') as f:
            f.write(b'\xFF\xD8\xFF')  # JPEG header
            f.write(content)
            f.write(b'\xFF\xD9')  # JPEG footer
        
        print(f"📄 创建测试文件: {test_file_path}")
        
        # 测试文件类型检查
        print("\n🧪 测试1: 文件类型检查")
        is_supported = file_monitor._is_supported_file(test_file_path)
        print(f"  📋 文件支持检查: {is_supported}")
        
        # 测试文件元数据提取
        print("\n🧪 测试2: 文件元数据提取")
        try:
            file_info = await file_monitor._extract_file_metadata(test_file_path)
            print(f"  📊 文件信息提取成功:")
            for key, value in file_info.items():
                if key == 'file_hash':
                    print(f"    {key}: {value[:16]}...")
                else:
                    print(f"    {key}: {value}")
        except Exception as e:
            print(f"  ❌ 文件信息提取失败: {e}")
            return False
        
        # 测试文件哈希计算
        print("\n🧪 测试3: 文件哈希计算")
        try:
            file_hash = await file_monitor._calculate_file_hash(test_file_path)
            print(f"  🔐 文件哈希: {file_hash[:16]}...")
        except Exception as e:
            print(f"  ❌ 文件哈希计算失败: {e}")
            return False
        
        # 测试直接文件处理
        print("\n🧪 测试4: 直接文件处理")
        try:
            await file_monitor._process_file(test_file_path)
            print(f"  ✅ 文件处理完成")
        except Exception as e:
            print(f"  ❌ 文件处理失败: {e}")
            return False
        
        # 等待片刻确保处理完成
        await asyncio.sleep(1)
        
        # 检查数据库记录
        print("\n🧪 测试5: 数据库记录检查")
        try:
            file_record = await db_adapter.get_file_by_path(test_file_path)
            if file_record:
                print(f"  ✅ 数据库记录找到:")
                print(f"    📄 文件名: {file_record.get('file_name')}")
                print(f"    🏷️  类型: {file_record.get('file_type')}")
                print(f"    📊 状态: {file_record.get('status')}")
                print(f"    🔐 哈希: {file_record.get('file_hash', '')[:16]}...")
            else:
                print(f"  ❌ 数据库记录未找到")
                
                # 检查所有文件记录
                print(f"  📋 检查所有pending文件...")
                pending_files = await db_adapter.get_pending_files(50)
                print(f"  📁 数据库中pending文件数: {len(pending_files)}")
                
                for file in pending_files[:3]:  # 显示前3个
                    print(f"    📄 {file.get('file_name')} - {file.get('file_path')}")
                
                return False
        except Exception as e:
            print(f"  ❌ 检查数据库记录失败: {e}")
            return False
        
        print("\n✅ 文件监控器诊断测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 诊断测试失败: {e}")
        return False
    finally:
        # 清理测试环境
        import shutil
        try:
            shutil.rmtree(test_dir)
            print(f"🧹 测试环境清理完成")
        except Exception as e:
            print(f"⚠️  清理测试环境失败: {e}")


async def test_multiple_files():
    """测试多个文件的处理"""
    print("\n🔍 多文件处理测试")
    
    # 创建临时测试环境
    test_dir = tempfile.mkdtemp(prefix="msearch_test_multiple_")
    db_path = f"{test_dir}/test_database.db"
    
    try:
        # 初始化配置和组件
        config_manager = ConfigManager()
        config_manager.set("database.sqlite.path", db_path)
        config_manager.set("system.monitored_directories", [test_dir])
        config_manager.set("system.supported_extensions", ['.jpg', '.jpeg', '.png', '.mp3', '.mp4'])
        config_manager.set("system.debounce_delay", 0.1)
        
        db_adapter = DatabaseAdapter(config_manager)
        file_monitor = FileMonitor(config_manager)
        
        # 创建多个测试文件
        test_files = []
        file_types = ['.jpg', '.mp3', '.mp4']
        
        for i in range(5):
            file_ext = file_types[i % len(file_types)]
            test_file_path = os.path.join(test_dir, f"test_file_{i:03d}{file_ext}")
            
            # 创建不同类型的测试文件
            with open(test_file_path, 'wb') as f:
                if file_ext == '.jpg':
                    f.write(b'\xFF\xD8\xFF')  # JPEG header
                    f.write(f"Test image {i}".encode())
                    f.write(b'\xFF\xD9')  # JPEG footer
                elif file_ext == '.mp3':
                    f.write(b'ID3')  # MP3 header
                    f.write(f"Test audio {i}".encode())
                elif file_ext == '.mp4':
                    f.write(b'ftypmp4')  # MP4 header
                    f.write(f"Test video {i}".encode())
            
            test_files.append(test_file_path)
        
        print(f"📁 创建了 {len(test_files)} 个测试文件")
        
        # 逐个处理文件
        for i, file_path in enumerate(test_files):
            print(f"\n🧪 处理文件 {i+1}/{len(test_files)}: {os.path.basename(file_path)}")
            try:
                await file_monitor._process_file(file_path)
                print(f"  ✅ 处理完成")
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
        
        # 等待处理完成
        await asyncio.sleep(2)
        
        # 检查数据库记录
        print(f"\n📊 数据库记录检查")
        found_count = 0
        for file_path in test_files:
            file_record = await db_adapter.get_file_by_path(file_path)
            if file_record:
                found_count += 1
                print(f"  ✅ {os.path.basename(file_path)}: {file_record.get('status')}")
            else:
                print(f"  ❌ {os.path.basename(file_path)}: 未找到记录")
        
        success_rate = (found_count / len(test_files)) * 100
        print(f"\n📈 成功率: {found_count}/{len(test_files)} ({success_rate:.1f}%)")
        
        return success_rate > 80
        
    except Exception as e:
        print(f"❌ 多文件测试失败: {e}")
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
    print("🔍 多模态检索系统 - 文件监控器诊断测试")
    print("=" * 60)
    
    # 运行诊断测试
    basic_success = await test_file_monitor_diagnosis()
    
    # 运行多文件测试
    multiple_success = await test_multiple_files()
    
    print("=" * 60)
    print("📋 诊断结果:")
    print(f"  🔍 基础诊断: {'✅ 通过' if basic_success else '❌ 失败'}")
    print(f"  📁 多文件测试: {'✅ 通过' if multiple_success else '❌ 失败'}")
    
    if basic_success and multiple_success:
        print("🎉 所有诊断测试通过")
    else:
        print("❌ 诊断测试发现问题")


if __name__ == "__main__":
    asyncio.run(main())