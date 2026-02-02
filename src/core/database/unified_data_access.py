"""
统一数据访问层
协调向量检索和元数据查询，提供统一的数据访问接口
"""

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class UnifiedDataAccess:
    """统一数据访问层"""

    def __init__(
        self, database_manager, vector_store, config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化统一数据访问层

        Args:
            database_manager: 数据库管理器实例
            vector_store: 向量存储实例
            config: 配置参数
        """
        self.database_manager = database_manager
        self.vector_store = vector_store
        self.config = config or {}

    async def search_with_metadata(
        self,
        query_vector: List[float],
        modality: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索并返回包含元数据的结果

        Args:
            query_vector: 查询向量
            modality: 模态类型 (image/video/audio)
            top_k: 返回结果数量
            filters: 过滤条件

        Returns:
            包含元数据的搜索结果列表
        """
        vector_results = await self.vector_store.search(
            query_vector=query_vector, modality=modality, top_k=top_k, filters=filters
        )

        results = []
        for item in vector_results:
            file_id = item.get("file_id")
            metadata = await self.database_manager.get_metadata(file_id)

            if metadata:
                result = {**item, "metadata": metadata}
                results.append(result)

        return results

    async def get_file_with_vectors(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文件及其向量数据

        Args:
            file_id: 文件ID

        Returns:
            文件及向量数据字典
        """
        metadata = await self.database_manager.get_metadata(file_id)
        if not metadata:
            return None

        vectors = await self.vector_store.get_vectors_by_file_id(file_id)

        return {"metadata": metadata, "vectors": vectors}

    async def delete_file_data(
        self, file_id: str, delete_from_disk: bool = False
    ) -> bool:
        """
        删除文件及其相关数据

        Args:
            file_id: 文件ID
            delete_from_disk: 是否同时删除磁盘文件

        Returns:
            是否成功
        """
        await self.vector_store.delete_by_file_id(file_id)
        await self.database_manager.delete_metadata(file_id)

        if delete_from_disk:
            metadata = await self.database_manager.get_metadata(file_id)
            if metadata:
                file_path = Path(metadata.get("file_path", ""))
                if file_path.exists():
                    file_path.unlink()

        return True

    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据统计信息

        Returns:
            统计信息字典
        """
        db_stats = await self.database_manager.get_statistics()
        vector_stats = await self.vector_store.get_statistics()

        return {"database": db_stats, "vector_store": vector_stats}
