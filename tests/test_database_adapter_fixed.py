import pytest
from src.common.storage.database_adapter import DatabaseAdapter


class TestDatabaseAdapterFixed:
    """测试修复后的DatabaseAdapter类"""
    
    def test_database_adapter_initialization(self):
        """测试数据库适配器初始化"""
        adapter = DatabaseAdapter()
        assert adapter is not None
        assert isinstance(adapter, DatabaseAdapter)
    
    def test_missing_methods_exist(self):
        """测试修复后所有必要方法都存在"""
        adapter = DatabaseAdapter()
        
        # 检查新增的方法是否存在
        required_methods = [
            'get_file_by_category',
            'create_file_relationship',
            'get_file_relationships',
            'insert_video_segment',
            'get_video_segments_by_file',
            'get_deletable_files',
            'get_database_stats',
            'get_schema_version'
        ]
        
        for method in required_methods:
            assert hasattr(adapter, method), f"方法 {method} 不存在于 DatabaseAdapter 中"
    
    @pytest.mark.asyncio
    async def test_get_schema_version(self):
        """测试获取Schema版本"""
        adapter = DatabaseAdapter()
        version = await adapter.get_schema_version()
        assert isinstance(version, dict)
        assert 'version' in version
        assert isinstance(version['version'], str)
    
    @pytest.mark.asyncio
    async def test_get_database_stats(self):
        """测试获取数据库统计信息"""
        adapter = DatabaseAdapter()
        stats = await adapter.get_database_stats()
        assert isinstance(stats, dict)
        assert 'total_files' in stats
        assert 'completed_files' in stats
        assert 'total_tasks' in stats
        assert 'total_vectors' in stats
        assert 'total_segments' in stats
    
    @pytest.mark.asyncio
    async def test_get_deletable_files(self):
        """测试获取可删除文件"""
        adapter = DatabaseAdapter()
        deletable_files = await adapter.get_deletable_files()
        assert isinstance(deletable_files, list)
    
    @pytest.mark.asyncio
    async def test_get_file_relationships(self):
        """测试获取文件关系"""
        adapter = DatabaseAdapter()
        relationships = await adapter.get_file_relationships('test_file_id')
        assert isinstance(relationships, list)
    
    @pytest.mark.asyncio
    async def test_get_video_segments_by_file(self):
        """测试获取视频片段"""
        adapter = DatabaseAdapter()
        segments = await adapter.get_video_segments_by_file('test_file_id')
        assert isinstance(segments, list)
