import pytest
import sqlite3
from pathlib import Path
from typing import Dict, Any, List

from tests.fixtures.path_factory import PathFactory
from tests.fixtures.data_factory import DataFactory


class TestDatabaseManager:
    """
    DatabaseManager单元测试
    
    测试数据库管理器的连接、查询、更新等功能
    """
    
    def test_database_manager_initialize_success(self, path_factory: PathFactory):
        """
        测试数据库管理器初始化成功
        
        Arrange:
            - 创建临时数据库目录
        
        Act:
            - 初始化数据库管理器
            - 连接数据库
        
        Assert:
            - 数据库管理器初始化成功
            - 数据库连接成功
            - 数据库文件创建成功
        """
        # Arrange
        database_dir = path_factory.get_database_dir()
        database_file = database_dir / "msearch.db"
        
        # Act
        from msearch.core.database_manager import DatabaseManager
        db_manager = DatabaseManager(str(database_dir))
        db_manager.initialize()
        db_manager.connect()
        
        # Assert
        assert database_file.exists()
        assert db_manager.is_connected()
    
    def test_database_manager_connect_disconnect(self, path_factory: PathFactory):
        """
        测试数据库连接和断开
        
        Arrange:
            - 创建临时数据库目录
            - 初始化数据库管理器
        
        Act:
            - 连接数据库
            - 断开数据库连接
        
        Assert:
            - 连接状态正确
        """
        # Arrange
        database_dir = path_factory.get_database_dir()
        
        from msearch.core.database_manager import DatabaseManager
        db_manager = DatabaseManager(str(database_dir))
        db_manager.initialize()
        
        # Act
        db_manager.connect()
        is_connected_after_connect = db_manager.is_connected()
        
        db_manager.disconnect()
        is_connected_after_disconnect = db_manager.is_connected()
        
        # Assert
        assert is_connected_after_connect == True
        assert is_connected_after_disconnect == False
    
    def test_database_manager_save_file_metadata_success(self, path_factory: PathFactory, data_factory: DataFactory):
        """
        测试保存文件元数据成功
        
        Arrange:
            - 创建临时数据库目录
            - 初始化数据库管理器并连接
            - 准备测试文件元数据
        
        Act:
            - 保存文件元数据
        
        Assert:
            - 保存成功
            - 数据可以正确查询
        """
        # Arrange
        database_dir = path_factory.get_database_dir()
        
        from msearch.core.database_manager import DatabaseManager
        db_manager = DatabaseManager(str(database_dir))
        db_manager.initialize()
        db_manager.connect()
        
        file_metadata = data_factory.create_file_metadata(file_type="image", file_size=1024)
        
        # Act
        db_manager.save_file_metadata(file_metadata)
        
        # Assert
        saved_metadata = db_manager.get_file_metadata(file_metadata["id"])
        assert saved_metadata is not None
        assert saved_metadata["id"] == file_metadata["id"]
        assert saved_metadata["file_type"] == "image"
        assert saved_metadata["file_size"] == 1024
    
    def test_database_manager_get_file_metadata_success(self, path_factory: PathFactory, data_factory: DataFactory):
        """
        测试获取文件元数据成功
        
        Arrange:
            - 创建临时数据库目录
            - 初始化数据库管理器并连接
            - 保存测试文件元数据
        
        Act:
            - 获取文件元数据
        
        Assert:
            - 返回正确的元数据
        """
        # Arrange
        database_dir = path_factory.get_database_dir()
        
        from msearch.core.database_manager import DatabaseManager
        db_manager = DatabaseManager(str(database_dir))
        db_manager.initialize()
        db_manager.connect()
        
        file_metadata = data_factory.create_file_metadata(file_type="video", file_size=2048)
        db_manager.save_file_metadata(file_metadata)
        
        # Act
        retrieved_metadata = db_manager.get_file_metadata(file_metadata["id"])
        
        # Assert
        assert retrieved_metadata is not None
        assert retrieved_metadata["id"] == file_metadata["id"]
        assert retrieved_metadata["file_type"] == "video"
        assert retrieved_metadata["file_size"] == 2048
    
    def test_database_manager_get_file_metadata_not_found(self, path_factory: PathFactory):
        """
        测试获取不存在的文件元数据
        
        Arrange:
            - 创建临时数据库目录
            - 初始化数据库管理器并连接
        
        Act:
            - 获取不存在的文件元数据
        
        Assert:
            - 返回None
        """
        # Arrange
        database_dir = path_factory.get_database_dir()
        
        from msearch.core.database_manager import DatabaseManager
        db_manager = DatabaseManager(str(database_dir))
        db_manager.initialize()
        db_manager.connect()
        
        # Act
        retrieved_metadata = db_manager.get_file_metadata("nonexistent_id")
        
        # Assert
        assert retrieved_metadata is None
    
    def test_database_manager_update_file_metadata_success(self, path_factory: PathFactory, data_factory: DataFactory):
        """
        测试更新文件元数据成功
        
        Arrange:
            - 创建临时数据库目录
            - 初始化数据库管理器并连接
            - 保存测试文件元数据
        
        Act:
            - 更新文件元数据
        
        Assert:
            - 更新成功
            - 更新后的值正确
        """
        # Arrange
        database_dir = path_factory.get_database_dir()
        
        from msearch.core.database_manager import DatabaseManager
        db_manager = DatabaseManager(str(database_dir))
        db_manager.initialize()
        db_manager.connect()
        
        file_metadata = data_factory.create_file_metadata(file_type="image", file_size=1024)
        db_manager.save_file_metadata(file_metadata)
        
        # Act
        file_metadata["processing_status"] = "completed"
        file_metadata["file_size"] = 2048
        db_manager.update_file_metadata(file_metadata["id"], file_metadata)
        
        # Assert
        updated_metadata = db_manager.get_file_metadata(file_metadata["id"])
        assert updated_metadata["processing_status"] == "completed"
        assert updated_metadata["file_size"] == 2048
    
    def test_database_manager_delete_file_metadata_success(self, path_factory: PathFactory, data_factory: DataFactory):
        """
        测试删除文件元数据成功
        
        Arrange:
            - 创建临时数据库目录
            - 初始化数据库管理器并连接
            - 保存测试文件元数据
        
        Act:
            - 删除文件元数据
        
        Assert:
            - 删除成功
            - 无法再查询到该元数据
        """
        # Arrange
        database_dir = path_factory.get_database_dir()
        
        from msearch.core.database_manager import DatabaseManager
        db_manager = DatabaseManager(str(database_dir))
        db_manager.initialize()
        db_manager.connect()
        
        file_metadata = data_factory.create_file_metadata(file_type="image", file_size=1024)
        db_manager.save_file_metadata(file_metadata)
        
        # Act
        db_manager.delete_file_metadata(file_metadata["id"])
        
        # Assert
        deleted_metadata = db_manager.get_file_metadata(file_metadata["id"])
        assert deleted_metadata is None
    
    def test_database_manager_save_vector_data_success(self, path_factory: PathFactory, data_factory: DataFactory):
        """
        测试保存向量数据成功
        
        Arrange:
            - 创建临时数据库目录
            - 初始化数据库管理器并连接
            - 准备测试向量数据
        
        Act:
            - 保存向量数据
        
        Assert:
            - 保存成功
            - 数据可以正确查询
        """
        # Arrange
        database_dir = path_factory.get_database_dir()
        
        from msearch.core.database_manager import DatabaseManager
        db_manager = DatabaseManager(str(database_dir))
        db_manager.initialize()
        db_manager.connect()
        
        vector_data = data_factory.create_vector_data(modality="image", dimension=512)
        
        # Act
        db_manager.save_vector_data(vector_data)
        
        # Assert
        saved_vector = db_manager.get_vector_data(vector_data["id"])
        assert saved_vector is not None
        assert saved_vector["id"] == vector_data["id"]
        assert saved_vector["modality"] == "image"
        assert len(saved_vector["vector"]) == 512
    
    def test_database_manager_get_vector_data_success(self, path_factory: PathFactory, data_factory: DataFactory):
        """
        测试获取向量数据成功
        
        Arrange:
            - 创建临时数据库目录
            - 初始化数据库管理器并连接
            - 保存测试向量数据
        
        Act:
            - 获取向量数据
        
        Assert:
            - 返回正确的向量数据
        """
        # Arrange
        database_dir = path_factory.get_database_dir()
        
        from msearch.core.database_manager import DatabaseManager
        db_manager = DatabaseManager(str(database_dir))
        db_manager.initialize()
        db_manager.connect()
        
        vector_data = data_factory.create_vector_data(modality="video", dimension=512)
        db_manager.save_vector_data(vector_data)
        
        # Act
        retrieved_vector = db_manager.get_vector_data(vector_data["id"])
        
        # Assert
        assert retrieved_vector is not None
        assert retrieved_vector["id"] == vector_data["id"]
        assert retrieved_vector["modality"] == "video"
        assert len(retrieved_vector["vector"]) == 512
    
    def test_database_manager_get_vectors_by_file_id_success(self, path_factory: PathFactory, data_factory: DataFactory):
        """
        测试根据文件ID获取向量数据成功
        
        Arrange:
            - 创建临时数据库目录
            - 初始化数据库管理器并连接
            - 保存多个向量数据
        
        Act:
            - 根据文件ID获取向量数据
        
        Assert:
            - 返回正确的向量列表
        """
        # Arrange
        database_dir = path_factory.get_database_dir()
        
        from msearch.core.database_manager import DatabaseManager
        db_manager = DatabaseManager(str(database_dir))
        db_manager.initialize()
        db_manager.connect()
        
        file_id = data_factory.generate_uuid()
        vector1 = data_factory.create_vector_data(modality="image", dimension=512, file_id=file_id)
        vector2 = data_factory.create_vector_data(modality="video", dimension=512, file_id=file_id)
        vector3 = data_factory.create_vector_data(modality="audio", dimension=512, file_id=data_factory.generate_uuid())
        
        db_manager.save_vector_data(vector1)
        db_manager.save_vector_data(vector2)
        db_manager.save_vector_data(vector3)
        
        # Act
        vectors = db_manager.get_vectors_by_file_id(file_id)
        
        # Assert
        assert len(vectors) == 2
        vector_ids = [v["id"] for v in vectors]
        assert vector1["id"] in vector_ids
        assert vector2["id"] in vector_ids
        assert vector3["id"] not in vector_ids
    
    def test_database_manager_delete_vector_data_success(self, path_factory: PathFactory, data_factory: DataFactory):
        """
        测试删除向量数据成功
        
        Arrange:
            - 创建临时数据库目录
            - 初始化数据库管理器并连接
            - 保存测试向量数据
        
        Act:
            - 删除向量数据
        
        Assert:
            - 删除成功
            - 无法再查询到该向量数据
        """
        # Arrange
        database_dir = path_factory.get_database_dir()
        
        from msearch.core.database_manager import DatabaseManager
        db_manager = DatabaseManager(str(database_dir))
        db_manager.initialize()
        db_manager.connect()
        
        vector_data = data_factory.create_vector_data(modality="image", dimension=512)
        db_manager.save_vector_data(vector_data)
        
        # Act
        db_manager.delete_vector_data(vector_data["id"])
        
        # Assert
        deleted_vector = db_manager.get_vector_data(vector_data["id"])
        assert deleted_vector is None
    
    def test_database_manager_execute_query_success(self, path_factory: PathFactory, data_factory: DataFactory):
        """
        测试执行查询成功
        
        Arrange:
            - 创建临时数据库目录
            - 初始化数据库管理器并连接
            - 保存测试数据
        
        Act:
            - 执行自定义查询
        
        Assert:
            - 查询结果正确
        """
        # Arrange
        database_dir = path_factory.get_database_dir()
        
        from msearch.core.database_manager import DatabaseManager
        db_manager = DatabaseManager(str(database_dir))
        db_manager.initialize()
        db_manager.connect()
        
        file1 = data_factory.create_file_metadata(file_type="image", file_size=1024)
        file2 = data_factory.create_file_metadata(file_type="video", file_size=2048)
        file3 = data_factory.create_file_metadata(file_type="image", file_size=4096)
        
        db_manager.save_file_metadata(file1)
        db_manager.save_file_metadata(file2)
        db_manager.save_file_metadata(file3)
        
        # Act
        query = "SELECT * FROM files WHERE file_type = ?"
        results = db_manager.execute_query(query, ("image",))
        
        # Assert
        assert len(results) == 2
        file_types = [r["file_type"] for r in results]
        assert all(ft == "image" for ft in file_types)
    
    def test_database_manager_transaction_commit_success(self, path_factory: PathFactory, data_factory: DataFactory):
        """
        测试事务提交成功
        
        Arrange:
            - 创建临时数据库目录
            - 初始化数据库管理器并连接
        
        Act:
            - 开始事务
            - 执行多个操作
            - 提交事务
        
        Assert:
            - 所有操作成功
            - 数据持久化
        """
        # Arrange
        database_dir = path_factory.get_database_dir()
        
        from msearch.core.database_manager import DatabaseManager
        db_manager = DatabaseManager(str(database_dir))
        db_manager.initialize()
        db_manager.connect()
        
        # Act
        db_manager.begin_transaction()
        
        file1 = data_factory.create_file_metadata(file_type="image", file_size=1024)
        file2 = data_factory.create_file_metadata(file_type="video", file_size=2048)
        
        db_manager.save_file_metadata(file1)
        db_manager.save_file_data(file2)
        
        db_manager.commit_transaction()
        
        # Assert
        retrieved_file1 = db_manager.get_file_metadata(file1["id"])
        retrieved_file2 = db_manager.get_file_metadata(file2["id"])
        
        assert retrieved_file1 is not None
        assert retrieved_file2 is not None
    
    def test_database_manager_transaction_rollback_success(self, path_factory: PathFactory, data_factory: DataFactory):
        """
        测试事务回滚成功
        
        Arrange:
            - 创建临时数据库目录
            - 初始化数据库管理器并连接
        
        Act:
            - 开始事务
            - 执行多个操作
            - 回滚事务
        
        Assert:
            - 所有操作被撤销
            - 数据未持久化
        """
        # Arrange
        database_dir = path_factory.get_database_dir()
        
        from msearch.core.database_manager import DatabaseManager
        db_manager = DatabaseManager(str(database_dir))
        db_manager.initialize()
        db_manager.connect()
        
        # Act
        db_manager.begin_transaction()
        
        file1 = data_factory.create_file_metadata(file_type="image", file_size=1024)
        file2 = data_factory.create_file_metadata(file_type="video", file_size=2048)
        
        db_manager.save_file_metadata(file1)
        db_manager.save_file_metadata(file2)
        
        db_manager.rollback_transaction()
        
        # Assert
        retrieved_file1 = db_manager.get_file_metadata(file1["id"])
        retrieved_file2 = db_manager.get_file_metadata(file2["id"])
        
        assert retrieved_file1 is None
        assert retrieved_file2 is None
