"""
数据库适配器单元测试
"""

import sys
import os
import tempfile
import sqlite3
import uuid
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.common.storage.database_adapter import DatabaseAdapter


def test_database_adapter_initialization():
    """测试数据库适配器初始化"""
    print("测试数据库适配器初始化...")
    
    # 使用临时数据库文件
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # 创建数据库适配器实例
        db_adapter = DatabaseAdapter()
        db_adapter.db_path = db_path  # 使用临时数据库路径
        
        # 重新初始化数据库
        db_adapter._initialize_database()
        
        # 验证数据库文件创建
        assert os.path.exists(db_path), "数据库文件应该被创建"
        
        # 验证数据库连接
        conn = db_adapter.get_connection()
        assert conn is not None, "数据库连接应该成功"
        conn.close()
        
        print("✓ 数据库适配器初始化测试通过")
        
    finally:
        # 清理临时文件
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_database_schema_creation():
    """测试数据库表结构创建"""
    print("测试数据库表结构创建...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db_adapter = DatabaseAdapter()
        db_adapter.db_path = db_path
        db_adapter._initialize_database()
        
        # 检查表是否存在
        conn = db_adapter.get_connection()
        cursor = conn.cursor()
        
        # 检查files表
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='files'
        """)
        assert cursor.fetchone() is not None, "files表应该存在"
        
        # 检查tasks表
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tasks'
        """)
        assert cursor.fetchone() is not None, "tasks表应该存在"
        
        # 检查media_segments表
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='media_segments'
        """)
        assert cursor.fetchone() is not None, "media_segments表应该存在"
        
        # 检查vectors表
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='vectors'
        """)
        assert cursor.fetchone() is not None, "vectors表应该存在"
        
        conn.close()
        
        print("✓ 数据库表结构创建测试通过")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_file_operations():
    """测试文件操作功能"""
    print("测试文件操作功能...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db_adapter = DatabaseAdapter()
        db_adapter.db_path = db_path
        db_adapter._initialize_database()
        
        # 模拟文件信息
        test_file = {
            'id': str(uuid.uuid4()),
            'file_path': '/test/path/image.jpg',
            'file_name': 'image.jpg',
            'file_type': '.jpg',
            'file_size': 1024,
            'file_hash': 'abc123',
            'created_at': datetime.now().timestamp(),
            'modified_at': datetime.now().timestamp()
        }
        
        # 插入文件记录
        db_adapter.insert_file(test_file)
        
        # 验证插入成功
        result = db_adapter.get_file(test_file['id'])
        assert result is not None, "应该能找到插入的文件"
        assert result['file_path'] == test_file['file_path'], "文件路径应该匹配"
        assert result['file_name'] == test_file['file_name'], "文件名称应该匹配"
        
        # 测试更新文件状态
        db_adapter.update_file_status(test_file['id'], 'processing')
        
        # 验证状态更新
        updated_result = db_adapter.get_file(test_file['id'])
        assert updated_result['status'] == 'processing', "文件状态应该更新为processing"
        
        print("✓ 文件操作功能测试通过")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_task_operations():
    """测试任务操作功能"""
    print("测试任务操作功能...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db_adapter = DatabaseAdapter()
        db_adapter.db_path = db_path
        db_adapter._initialize_database()
        
        # 先插入一个文件记录
        test_file = {
            'id': str(uuid.uuid4()),
            'file_path': '/test/path/video.mp4',
            'file_name': 'video.mp4',
            'file_type': '.mp4',
            'file_size': 1024000,
            'file_hash': 'def456',
            'created_at': datetime.now().timestamp(),
            'modified_at': datetime.now().timestamp()
        }
        db_adapter.insert_file(test_file)
        
        # 创建任务
        task_id = db_adapter.create_task(
            file_id=test_file['id'],
            task_type='processing',
            status='pending'
        )
        
        assert task_id is not None, "任务ID应该生成"
        
        # 验证任务创建
        task = db_adapter.get_task(task_id)
        assert task is not None, "应该能找到创建的任务"
        assert task['task_type'] == 'processing', "任务类型应该正确"
        assert task['status'] == 'pending', "任务状态应该是pending"
        
        # 测试更新任务状态
        db_adapter.update_task_status(task_id, 'processing')
        
        # 验证状态更新
        updated_task = db_adapter.get_task(task_id)
        assert updated_task['status'] == 'processing', "任务状态应该更新为processing"
        
        print("✓ 任务操作功能测试通过")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_get_connection():
    """测试数据库连接获取"""
    print("测试数据库连接获取...")
    
    # 使用内存数据库进行测试
    db_adapter = DatabaseAdapter()
    original_path = db_adapter.db_path
    db_adapter.db_path = ':memory:'
    db_adapter._initialize_database()
    
    try:
        # 测试连接获取
        conn1 = db_adapter.get_connection()
        conn2 = db_adapter.get_connection()
        
        assert conn1 is not None, "应该能获取数据库连接"
        assert conn2 is not None, "应该能获取第二个数据库连接"
        assert conn1 != conn2, "应该返回不同的连接对象"
        
        # 验证连接可以执行SQL
        cursor = conn1.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1, "应该能执行简单查询"
        
        conn1.close()
        conn2.close()
        
        print("✓ 数据库连接获取测试通过")
        
    finally:
        db_adapter.db_path = original_path


def test_get_pending_files():
    """测试获取待处理文件"""
    print("测试获取待处理文件...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db_adapter = DatabaseAdapter()
        db_adapter.db_path = db_path
        db_adapter._initialize_database()
        
        # 插入不同状态的文件
        files_data = [
            {
                'id': str(uuid.uuid4()),
                'file_path': '/test/file1.jpg',
                'file_name': 'file1.jpg',
                'file_type': '.jpg',
                'file_size': 1024,
                'file_hash': 'hash1',
                'created_at': datetime.now().timestamp(),
                'modified_at': datetime.now().timestamp(),
                'status': 'pending'
            },
            {
                'id': str(uuid.uuid4()),
                'file_path': '/test/file2.mp4',
                'file_name': 'file2.mp4',
                'file_type': '.mp4',
                'file_size': 2048,
                'file_hash': 'hash2',
                'created_at': datetime.now().timestamp(),
                'modified_at': datetime.now().timestamp(),
                'status': 'processing'
            },
            {
                'id': str(uuid.uuid4()),
                'file_path': '/test/file3.wav',
                'file_name': 'file3.wav',
                'file_type': '.wav',
                'file_size': 4096,
                'file_hash': 'hash3',
                'created_at': datetime.now().timestamp(),
                'modified_at': datetime.now().timestamp(),
                'status': 'completed'
            }
        ]
        
        for file_data in files_data:
            db_adapter.insert_file(file_data)
        
        # 获取待处理文件
        pending_files = db_adapter.get_pending_files(limit=10)
        
        assert len(pending_files) == 1, "应该只有1个待处理文件"
        assert pending_files[0]['file_type'] == '.jpg', "待处理文件应该是jpg文件"
        
        # 测试限制数量
        limited_pending_files = db_adapter.get_pending_files(limit=1)
        assert len(limited_pending_files) == 1, "应该只返回1个文件"
        
        print("✓ 获取待处理文件测试通过")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    print("开始数据库适配器单元测试...\n")
    
    test_database_adapter_initialization()
    test_database_schema_creation()
    test_file_operations()
    test_task_operations()
    test_get_connection()
    test_get_pending_files()
    
    print("\n🎉 所有数据库适配器测试通过!")
