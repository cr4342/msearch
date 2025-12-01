#!/usr/bin/env python3
"""
msearch 多模态检索系统端到端测试
轻量级测试系统的核心功能：文件监控、数据库操作和系统组件集成
"""

import os
import shutil
import tempfile
import sys
from pathlib import Path
import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.config_manager import ConfigManager
from src.common.storage.database_adapter import DatabaseAdapter


class TestEndToEndSystem:
    """轻量级端到端系统测试 - 使用同步测试模式避免pytest-asyncio问题"""
    
    def setup_method(self):
        """设置测试环境（使用同步方法代替async fixture）"""
        print("\n=== 设置测试环境 ===")
        # 创建临时目录
        self.base_dir = tempfile.mkdtemp(prefix="msearch_e2e_test_")
        self.test_files_dir = os.path.join(self.base_dir, "test_files")
        self.db_path = os.path.join(self.base_dir, "test_database.db")
        
        # 创建必要的目录
        os.makedirs(self.test_files_dir, exist_ok=True)
        
        # 设置配置
        self.config_manager = ConfigManager()
        self.config_manager.set("system.monitored_directories", [self.test_files_dir])
        self.config_manager.set("system.supported_extensions", ['.jpg', '.jpeg', '.png', '.mp3', '.mp4', '.txt'])
        self.config_manager.set("system.debounce_delay", 0.1)
        self.config_manager.set("system.log_level", "ERROR")  # 使用ERROR级别减少日志输出
        self.config_manager.set("database.sqlite.path", self.db_path)
        self.config_manager.set("features.enable_clip", False)  # 禁用需要外部依赖的功能
        self.config_manager.set("features.enable_clap", False)
        self.config_manager.set("features.enable_whisper", False)
        
        # 初始化数据库（使用同步方式，使用reset_database方法）
        self.db_adapter = DatabaseAdapter(self.config_manager)
        import asyncio
        asyncio.run(self.db_adapter.reset_database())
        
        print(f"测试环境设置完成: {self.base_dir}")
    
    def teardown_method(self):
        """清理测试环境（使用同步方法）"""
        # 删除临时目录
        if hasattr(self, 'base_dir') and os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir, ignore_errors=True)
            print(f"测试环境清理完成: {self.base_dir}")
    
    def create_test_file(self, content="Test content", filename="test_file.txt"):
        """创建测试文件"""
        file_path = os.path.join(self.test_files_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def run_async(self, coro):
        """辅助方法：运行异步函数"""
        import asyncio
        return asyncio.run(coro)
    
    def test_database_operations(self):
        """测试数据库基本操作"""
        print("\n=== 测试数据库基本操作 ===")
        
        # 1. 创建测试文件
        test_file_path = self.create_test_file("这是端到端测试文件", "e2e_test_file.txt")
        print(f"创建测试文件: {test_file_path}")
        
        # 2. 测试添加文件记录 - 使用正确的字段名
        import uuid
        file_id_value = str(uuid.uuid4())
        file_id = self.run_async(self.db_adapter.insert_file({
            "id": file_id_value,
            "file_path": test_file_path,
            "file_name": "e2e_test_file.txt",
            "file_type": "text",
            "file_size": os.path.getsize(test_file_path),
            "file_hash": "test_hash",  # 模拟哈希值
            "created_at": os.path.getctime(test_file_path),
            "modified_at": os.path.getmtime(test_file_path),
            "status": "pending"
        }))
        assert file_id is not None, "应该成功添加文件记录"
        print(f"成功添加文件记录，ID: {file_id}")
        
        # 3. 测试查询文件记录
        file_records = self.run_async(self.db_adapter.get_files_by_path(test_file_path))
        assert len(file_records) >= 1, "应该能查询到文件记录"
        print(f"成功查询到文件记录，数量: {len(file_records)}")
        
        file_record = file_records[0]
        # 检查记录中的关键字段
        assert 'id' in file_record, "文件记录应该有id字段"
        assert 'file_path' in file_record, "文件记录应该有file_path字段"
        assert 'status' in file_record, "文件记录应该有status字段"
        assert 'created_at' in file_record, "文件记录应该有created_at字段"
        assert 'file_name' in file_record, "文件记录应该有file_name字段"
        
        # 4. 测试数据库统计功能 - 手动查询
        def get_file_count():
            try:
                import sqlite3
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM files")
                    return cursor.fetchone()[0]
            except Exception as e:
                print(f"获取文件统计失败: {e}")
                return 0
        
        file_count = get_file_count()
        assert file_count >= 1, "数据库统计应该显示至少有一个文件"
        print(f"数据库统计: 文件数量 = {file_count}")
        
        # 5. 测试文件删除功能 - 需要先获取file_id
        file_id = file_record["id"]
        deleted = self.run_async(self.db_adapter.delete_file(file_id))
        assert deleted is True, "文件应该被成功删除"
        
        # 验证文件已被删除
        file_records_after_delete = self.run_async(self.db_adapter.get_files_by_path(test_file_path))
        assert len(file_records_after_delete) == 0, "删除后不应该有文件记录"
        
        print("文件删除测试通过")
    
    def test_database_schema_compliance(self):
        """测试数据库模式兼容性"""
        print("\n=== 测试数据库模式兼容性 ===")
        
        # 1. 手动测试数据库表结构
        def check_tables_exist():
            try:
                import sqlite3
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    required_tables = ['files', 'tasks', 'media_segments', 'vectors', 'video_segments']
                    
                    # 检查所有必需的表是否存在
                    for table in required_tables:
                        assert table in tables, f"表 {table} 不存在"
                    
                    return True
            except Exception as e:
                print(f"检查数据库表结构失败: {e}")
                return False
        
        tables_check = check_tables_exist()
        assert tables_check is True, "数据库表结构检查失败"
        print("数据库表结构检查通过")
        
        # 2. 测试多文件添加和批量查询
        file_paths = []
        for i in range(3):
            file_path = self.create_test_file(f"测试文件内容 {i}", f"test_file_{i}.txt")
            # 使用正确的字段名
            import uuid
            file_id_value = str(uuid.uuid4())
            self.run_async(self.db_adapter.insert_file({
                "id": file_id_value,
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_type": "text",
                "file_size": os.path.getsize(file_path),
                "file_hash": f"test_hash_{i}",  # 模拟哈希值
                "created_at": os.path.getctime(file_path),
                "modified_at": os.path.getmtime(file_path),
                "status": "pending"
            }))
            file_paths.append(file_path)
        
        # 使用文件ID直接查询每个文件，确保它们都存在
        for file_path in file_paths:
            # 使用文件路径查询，确保文件记录存在
            file_records = self.run_async(self.db_adapter.get_files_by_path(file_path))
            assert len(file_records) >= 1, f"应该能找到文件记录: {file_path}"
            print(f"成功找到文件记录: {file_path}")
        
        # 手动查询数据库验证总记录数
        def get_file_count():
            try:
                import sqlite3
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM files")
                    return cursor.fetchone()[0]
            except Exception as e:
                print(f"获取文件统计失败: {e}")
                return 0
        
        file_count = get_file_count()
        assert file_count >= len(file_paths), f"数据库中应该至少有 {len(file_paths)} 个文件"
        print(f"多文件添加测试通过，数据库中共有 {file_count} 个文件记录")
        
        # 3. 手动验证数据库统计
        def get_file_count():
            try:
                import sqlite3
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM files")
                    return cursor.fetchone()[0]
            except Exception as e:
                print(f"获取文件统计失败: {e}")
                return 0
        
        file_count = get_file_count()
        assert file_count >= len(file_paths), f"数据库中应该至少有 {len(file_paths)} 个文件"
        print(f"数据库统计验证通过，文件数量: {file_count}")


if __name__ == "__main__":
    # 直接运行测试的入口点
    test_instance = TestEndToEndSystem()
    
    try:
        test_instance.setup_method()
        test_instance.test_database_operations()
        test_instance.test_database_schema_compliance()
        print("\n✅ 所有轻量级端到端测试通过!")
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
    finally:
        test_instance.teardown_method()
