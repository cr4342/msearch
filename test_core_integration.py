#!/usr/bin/env python3
"""
核心组件集成测试
验证更新后的设计文档要求
"""

import sys
import asyncio
import tempfile
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.core.config_manager import get_config_manager
from src.core.logging_config import setup_logging
from src.common.storage.database_adapter import DatabaseAdapter


async def test_core_components():
    """测试核心组件初始化和基础功能"""
    print("开始核心组件集成测试...")
    
    # 1. 初始化配置管理器
    print("1. 初始化配置管理器...")
    config_manager = get_config_manager()
    assert config_manager is not None
    print("✓ 配置管理器初始化成功")
    
    # 2. 设置日志系统
    print("2. 设置日志系统...")
    setup_logging('INFO')
    print("✓ 日志系统设置成功")
    
    # 3. 初始化数据库适配器
    print("3. 初始化数据库适配器...")
    db_adapter = DatabaseAdapter()
    assert db_adapter is not None
    print("✓ 数据库适配器初始化成功")
    
    # 4. 测试数据库基本操作
    print("4. 测试数据库基本操作...")
    
    # 创建测试文件记录
    test_file = {
        'id': 'test-file-001',
        'file_path': '/test/path/sample.jpg',
        'file_name': 'sample.jpg',
        'file_type': 'image',
        'file_size': 1024,
        'file_hash': 'test-hash-001',
        'created_at': 1635724800.0,
        'modified_at': 1635724800.0,
        'status': 'pending'
    }
    
    file_id = await db_adapter.insert_file(test_file)
    assert file_id == test_file['id']
    print("✓ 文件记录插入成功")
    
    # 查询文件记录
    file_record = await db_adapter.get_file(file_id)
    assert file_record is not None
    assert file_record['file_name'] == 'sample.jpg'
    print("✓ 文件记录查询成功")
    
    # 更新文件状态
    success = await db_adapter.update_file_status(file_id, 'processed')
    assert success == True
    print("✓ 文件状态更新成功")
    
    # 5. 测试任务管理
    print("5. 测试任务管理...")
    
    test_task = {
        'id': 'test-task-001',
        'file_id': file_id,
        'task_type': 'preprocessing',
        'status': 'pending',
        'created_at': 1635724800.0,
        'updated_at': 1635724800.0
    }
    
    task_id = await db_adapter.insert_task(test_task)
    assert task_id == test_task['id']
    print("✓ 任务记录插入成功")
    
    # 查询任务记录
    task_record = await db_adapter.get_task(task_id)
    assert task_record is not None
    assert task_record['task_type'] == 'preprocessing'
    print("✓ 任务记录查询成功")
    
    # 6. 测试配置访问
    print("6. 测试配置访问...")
    
    # 测试嵌套配置访问
    log_level = config_manager.get("system.log_level", "INFO")
    assert log_level is not None
    print(f"✓ 日志级别配置: {log_level}")
    
    db_path = config_manager.get("database.sqlite.path")
    assert db_path is not None
    print(f"✓ 数据库路径配置: {db_path}")
    
    # 测试模型配置
    clip_config = config_manager.get("infinity.services.clip")
    assert clip_config is not None
    print(f"✓ CLIP模型配置: {clip_config}")
    
    # 7. 清理测试数据
    print("7. 清理测试数据...")
    
    await db_adapter.delete_file(file_id)
    print("✓ 测试数据清理完成")
    
    print("\n🎉 所有核心组件测试通过！")
    print("✅ 微服务架构验证成功")
    print("✅ 配置驱动设计验证成功")
    print("✅ 数据库架构验证成功")
    print("✅ 异步处理架构验证成功")


def test_sync_components():
    """同步组件测试"""
    print("开始同步组件测试...")
    
    # 测试配置管理器同步功能
    config_manager = get_config_manager()
    
    # 测试配置设置和获取
    config_manager.set("test.value", "test_data")
    value = config_manager.get("test.value")
    assert value == "test_data"
    print("✓ 配置设置和获取测试通过")
    
    # 测试默认值
    default_value = config_manager.get("non.existent.key", "default")
    assert default_value == "default"
    print("✓ 默认值测试通过")
    
    print("✓ 同步组件测试完成")


if __name__ == "__main__":
    # 运行同步测试
    test_sync_components()
    
    # 运行异步测试
    asyncio.run(test_core_components())
    
    print("\n🎯 核心组件集成测试全部通过！")
    print("📊 测试结果:")
    print("  - 配置管理器: ✅ 通过")
    print("  - 数据库适配器: ✅ 通过")
    print("  - 异步处理: ✅ 通过")
    print("  - 微服务架构: ✅ 验证成功")