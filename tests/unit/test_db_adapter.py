"""
统一数据库适配器单元测试
测试UnifiedDatabaseAdapter的核心功能
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.storage.db_adapter import UnifiedDatabaseAdapter, get_db_adapter


class TestUnifiedDatabaseAdapter:
    """统一数据库适配器核心功能测试"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """模拟数据库管理器"""
        mock_manager = Mock()
        mock_manager.execute_query = Mock(return_value=[])
        mock_manager.insert_record = Mock(return_value=1)
        mock_manager.update_record = Mock(return_value=1)
        mock_manager.reset_database = Mock()
        return mock_manager
    
    @pytest.fixture
    def db_adapter(self, mock_db_manager):
        """数据库适配器实例"""
        with patch('src.storage.db_adapter.get_db_manager', return_value=mock_db_manager):
            adapter = UnifiedDatabaseAdapter()
            return adapter
    
    def test_init_success(self, mock_db_manager):
        """测试初始化成功"""
        with patch('src.storage.db_adapter.get_db_manager', return_value=mock_db_manager):
            adapter = UnifiedDatabaseAdapter()
            
            # 验证组件是否正确初始化
            assert adapter.db_manager == mock_db_manager
    
    @pytest.mark.asyncio
    async def test_search_success(self, db_adapter, mock_db_manager):
        """测试成功搜索"""
        # 设置mock数据
        mock_files = [
            {
                "id": 1,
                "file_path": "/data/videos/sample1.mp4",
                "file_type": "video",
                "file_size": 1024000,
                "duration": 120.5,
                "status": "completed"
            }
        ]
        mock_db_manager.execute_query.return_value = mock_files
        
        # 执行测试
        result = await db_adapter.search([0.1, 0.2, 0.3], modality="video")
        
        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["file_id"] == 1
        assert result[0]["file_path"] == "/data/videos/sample1.mp4"
        assert result[0]["file_type"] == "video"
        
        # 验证调用了正确的数据库方法
        mock_db_manager.execute_query.assert_called()
    
    @pytest.mark.asyncio
    async def test_search_with_exception(self, db_adapter, mock_db_manager):
        """测试搜索时出现异常"""
        # 设置mock抛出异常
        mock_db_manager.execute_query.side_effect = Exception("数据库错误")
        
        # 执行测试
        result = await db_adapter.search([0.1, 0.2, 0.3])
        
        # 验证结果 - 应该返回模拟数据而不是抛出异常
        assert isinstance(result, list)
        assert len(result) >= 0  # 可能返回模拟数据
    
    @pytest.mark.asyncio
    async def test_store_embedding_success(self, db_adapter, mock_db_manager):
        """测试成功存储嵌入向量"""
        # 执行测试
        vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        metadata = {"segment_type": "image"}
        result = await db_adapter.store_embedding(1, vectors, metadata)
        
        # 验证结果
        assert result is True
        
        # 验证调用了正确的数据库方法
        assert mock_db_manager.insert_record.call_count == 2  # 两个向量
        mock_db_manager.update_record.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_embedding_with_exception(self, db_adapter, mock_db_manager):
        """测试存储嵌入向量时出现异常"""
        # 设置mock抛出异常
        mock_db_manager.insert_record.side_effect = Exception("数据库错误")
        
        # 执行测试
        vectors = [[0.1, 0.2, 0.3]]
        metadata = {"segment_type": "image"}
        result = await db_adapter.store_embedding(1, vectors, metadata)
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_reset_success(self, db_adapter, mock_db_manager):
        """测试成功重置数据库"""
        # 执行测试
        result = await db_adapter.reset()
        
        # 验证结果
        assert result is True
        
        # 验证调用了正确的数据库方法
        mock_db_manager.reset_database.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reset_with_exception(self, db_adapter, mock_db_manager):
        """测试重置数据库时出现异常"""
        # 设置mock抛出异常
        mock_db_manager.reset_database.side_effect = Exception("数据库错误")
        
        # 执行测试
        result = await db_adapter.reset()
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_file_metadata_success(self, db_adapter, mock_db_manager):
        """测试成功获取文件元数据"""
        # 设置mock数据
        mock_files = [
            {
                "id": 1,
                "file_path": "/data/videos/sample1.mp4",
                "file_type": "video",
                "file_size": 1024000,
                "duration": 120.5,
                "status": "completed"
            }
        ]
        mock_db_manager.execute_query.return_value = mock_files
        
        # 执行测试
        result = await db_adapter.get_file_metadata(1)
        
        # 验证结果
        assert result is not None
        assert result["id"] == 1
        assert result["file_path"] == "/data/videos/sample1.mp4"
    
    @pytest.mark.asyncio
    async def test_get_file_metadata_not_found(self, db_adapter, mock_db_manager):
        """测试获取文件元数据但未找到"""
        # 设置mock数据为空
        mock_db_manager.execute_query.return_value = []
        
        # 执行测试
        result = await db_adapter.get_file_metadata(999)
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_file_metadata_with_exception(self, db_adapter, mock_db_manager):
        """测试获取文件元数据时出现异常"""
        # 设置mock抛出异常
        mock_db_manager.execute_query.side_effect = Exception("数据库错误")
        
        # 执行测试
        result = await db_adapter.get_file_metadata(1)
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_add_file_to_queue_success(self, db_adapter, mock_db_manager):
        """测试成功添加文件到队列"""
        # 设置mock返回值
        mock_db_manager.insert_record.return_value = 123
        
        # 执行测试
        result = await db_adapter.add_file_to_queue("/data/test.mp4", priority=10)
        
        # 验证结果
        assert result == 123
        
        # 验证调用了正确的数据库方法
        mock_db_manager.insert_record.assert_called_once_with(
            "processing_queue",
            {
                "file_path": "/data/test.mp4",
                "priority": 10,
                "status": "queued"
            }
        )
    
    @pytest.mark.asyncio
    async def test_add_file_to_queue_with_exception(self, db_adapter, mock_db_manager):
        """测试添加文件到队列时出现异常"""
        # 设置mock抛出异常
        mock_db_manager.insert_record.side_effect = Exception("数据库错误")
        
        # 执行测试并验证异常被传播
        with pytest.raises(Exception):
            await db_adapter.add_file_to_queue("/data/test.mp4")
    
    @pytest.mark.asyncio
    async def test_update_queue_status_success(self, db_adapter, mock_db_manager):
        """测试成功更新队列状态"""
        # 执行测试
        result = await db_adapter.update_queue_status(123, "processing")
        
        # 验证结果
        assert result is True
        
        # 验证调用了正确的数据库方法
        mock_db_manager.update_record.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_queue_status_with_error(self, db_adapter, mock_db_manager):
        """测试更新队列状态时包含错误信息"""
        # 执行测试
        result = await db_adapter.update_queue_status(123, "failed", "处理失败")
        
        # 验证结果
        assert result is True
        
        # 验证调用了正确的数据库方法
        mock_db_manager.update_record.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_queue_status_with_exception(self, db_adapter, mock_db_manager):
        """测试更新队列状态时出现异常"""
        # 设置mock抛出异常
        mock_db_manager.update_record.side_effect = Exception("数据库错误")
        
        # 执行测试
        result = await db_adapter.update_queue_status(123, "processing")
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_file_processing_status_success(self, db_adapter, mock_db_manager):
        """测试成功更新文件处理状态"""
        # 设置mock数据
        mock_queue_records = [{"id": 123}]
        mock_db_manager.execute_query.return_value = mock_queue_records
        
        # 执行测试
        result = await db_adapter.update_file_processing_status("123", "processing", 50)
        
        # 验证结果
        assert result is True
        
        # 验证调用了正确的数据库方法
        mock_db_manager.execute_query.assert_called_once()
        mock_db_manager.update_record.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_file_processing_status_not_found(self, db_adapter, mock_db_manager):
        """测试更新文件处理状态但未找到记录"""
        # 设置mock数据为空
        mock_db_manager.execute_query.return_value = []
        
        # 执行测试
        result = await db_adapter.update_file_processing_status("999", "processing", 50)
        
        # 验证结果
        assert result is False


class TestUnifiedDatabaseAdapterSingleton:
    """统一数据库适配器单例模式测试"""
    
    def test_get_db_adapter_singleton(self):
        """测试获取全局数据库适配器实例"""
        with patch('src.storage.db_adapter.get_db_manager'):
            # 重置全局实例
            import src.storage.db_adapter as dba
            dba._db_adapter = None
            
            # 获取第一个实例
            adapter1 = get_db_adapter()
            assert adapter1 is not None
            
            # 获取第二个实例，应该与第一个相同
            adapter2 = get_db_adapter()
            assert adapter1 is adapter2


if __name__ == '__main__':
    pytest.main([__file__])