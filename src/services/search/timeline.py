"""
视频检索结果时间轴展示模块
用于生成视频检索结果的时间轴数据结构
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class VideoTimelineItem:
    """视频时间轴条目"""

    video_uuid: str  # 视频文件唯一标识
    video_name: str  # 视频文件名
    video_path: str  # 视频文件路径
    start_time: float  # 片段开始时间（秒）
    end_time: float  # 片段结束时间（秒）
    duration: float  # 片段时长（秒）
    relevance_score: float  # 相关性评分
    thumbnail_path: Optional[str] = None  # 片段缩略图路径
    preview_path: Optional[str] = None  # 片段预览路径
    scene_info: Optional[Dict[str, Any]] = None  # 场景信息
    frame_count: int = 0  # 包含的帧数
    metadata: Optional[Dict[str, Any]] = None  # 其他元数据

    def __post_init__(self):
        """初始化后处理"""
        if self.duration == 0:
            self.duration = self.end_time - self.start_time
        if self.scene_info is None:
            self.scene_info = {}
        if self.metadata is None:
            self.metadata = {}

    @property
    def formatted_duration(self) -> str:
        """格式化时长"""
        td = timedelta(seconds=self.duration)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    @property
    def formatted_start_time(self) -> str:
        """格式化开始时间"""
        td = timedelta(seconds=self.start_time)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    @property
    def formatted_end_time(self) -> str:
        """格式化结束时间"""
        td = timedelta(seconds=self.end_time)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "video_uuid": self.video_uuid,
            "video_name": self.video_name,
            "video_path": self.video_path,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "formatted_duration": self.formatted_duration,
            "formatted_start_time": self.formatted_start_time,
            "formatted_end_time": self.formatted_end_time,
            "relevance_score": self.relevance_score,
            "thumbnail_path": self.thumbnail_path,
            "preview_path": self.preview_path,
            "scene_info": self.scene_info,
            "frame_count": self.frame_count,
            "metadata": self.metadata,
        }


@dataclass
class VideoTimelineResult:
    """视频时间轴结果"""

    query: str  # 用户查询
    total_results: int  # 总结果数
    timeline_items: List[VideoTimelineItem] = field(
        default_factory=list
    )  # 时间轴条目列表
    grouped_by_video: Optional[Dict[str, List[VideoTimelineItem]]] = (
        None  # 按视频分组的条目
    )
    sorted_by_time: Optional[List[VideoTimelineItem]] = None  # 按时间排序的条目
    sorted_by_relevance: Optional[List[VideoTimelineItem]] = None  # 按相关性排序的条目
    metadata: Optional[Dict[str, Any]] = None  # 其他元数据

    def __post_init__(self):
        """初始化后处理"""
        if self.grouped_by_video is None:
            self.grouped_by_video = {}
        if self.sorted_by_time is None:
            self.sorted_by_time = []
        if self.sorted_by_relevance is None:
            self.sorted_by_relevance = []
        if self.metadata is None:
            self.metadata = {}

    def add_item(self, item: VideoTimelineItem) -> None:
        """添加时间轴条目"""
        self.timeline_items.append(item)
        self.total_results = len(self.timeline_items)

        # 更新按视频分组的条目
        if item.video_uuid not in self.grouped_by_video:
            self.grouped_by_video[item.video_uuid] = []
        self.grouped_by_video[item.video_uuid].append(item)

    def sort_by_time(self, ascending: bool = True) -> List[VideoTimelineItem]:
        """按时间排序"""
        self.sorted_by_time = sorted(
            self.timeline_items, key=lambda x: x.start_time, reverse=not ascending
        )
        return self.sorted_by_time

    def sort_by_relevance(self, descending: bool = True) -> List[VideoTimelineItem]:
        """按相关性排序"""
        self.sorted_by_relevance = sorted(
            self.timeline_items, key=lambda x: x.relevance_score, reverse=descending
        )
        return self.sorted_by_relevance

    def get_video_count(self) -> int:
        """获取视频数量"""
        return len(self.grouped_by_video)

    def get_items_by_video(self, video_uuid: str) -> List[VideoTimelineItem]:
        """获取指定视频的所有条目"""
        return self.grouped_by_video.get(video_uuid, [])

    def get_total_duration(self) -> float:
        """获取总时长"""
        return sum(item.duration for item in self.timeline_items)

    def get_formatted_total_duration(self) -> str:
        """获取格式化总时长"""
        td = timedelta(seconds=self.get_total_duration())
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "total_results": self.total_results,
            "video_count": self.get_video_count(),
            "total_duration": self.get_total_duration(),
            "formatted_total_duration": self.get_formatted_total_duration(),
            "timeline_items": [item.to_dict() for item in self.timeline_items],
            "grouped_by_video": {
                uuid: [item.to_dict() for item in items]
                for uuid, items in self.grouped_by_video.items()
            },
            "sorted_by_time": [item.to_dict() for item in self.sorted_by_time],
            "sorted_by_relevance": [
                item.to_dict() for item in self.sorted_by_relevance
            ],
            "metadata": self.metadata,
        }


class VideoTimelineGenerator:
    """视频时间轴生成器"""

    def __init__(self):
        """初始化时间轴生成器"""
        logger.info("视频时间轴生成器初始化完成")

    def from_search_results(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        metadata_map: Optional[Dict[str, Any]] = None,
    ) -> VideoTimelineResult:
        """从搜索结果生成时间轴

        Args:
            query: 用户查询
            search_results: 搜索结果列表
            metadata_map: 元数据映射（video_uuid -> video_metadata）

        Returns:
            视频时间轴结果
        """
        if metadata_map is None:
            metadata_map = {}

        result = VideoTimelineResult(query=query, total_results=0)

        for idx, search_result in enumerate(search_results):
            try:
                # 提取基本信息
                video_uuid = search_result.get("video_uuid", "")
                video_name = search_result.get("video_name", "")
                video_path = search_result.get("video_path", "")
                start_time = search_result.get("start_time", 0.0)
                end_time = search_result.get("end_time", 0.0)
                relevance_score = search_result.get("relevance_score", 0.0)

                # 从元数据映射获取额外信息
                video_metadata = metadata_map.get(video_uuid, {})
                thumbnail_path = video_metadata.get("thumbnail_path")
                preview_path = video_metadata.get("preview_path")

                # 创建时间轴条目
                item = VideoTimelineItem(
                    video_uuid=video_uuid,
                    video_name=video_name,
                    video_path=video_path,
                    start_time=start_time,
                    end_time=end_time,
                    duration=end_time - start_time,
                    relevance_score=relevance_score,
                    thumbnail_path=thumbnail_path,
                    preview_path=preview_path,
                    scene_info=search_result.get("scene_info"),
                    frame_count=search_result.get("frame_count", 0),
                    metadata=search_result.get("metadata", {}),
                )

                result.add_item(item)

            except Exception as e:
                logger.error(f"处理搜索结果 {idx} 时出错: {e}")
                continue

        # 自动排序
        result.sort_by_time()
        result.sort_by_relevance()

        logger.info(
            f"生成时间轴结果: {result.total_results} 个片段, {result.get_video_count()} 个视频"
        )

        return result

    def from_database_results(
        self, query: str, vector_results: List[Dict[str, Any]], db_manager
    ) -> VideoTimelineResult:
        """从数据库结果生成时间轴

        Args:
            query: 用户查询
            vector_results: 向量检索结果列表
            db_manager: 数据库管理器实例

        Returns:
            视频时间轴结果
        """
        result = VideoTimelineResult(query=query, total_results=0)

        # 收集所有视频UUID
        video_uuids = set()
        for vector_result in vector_results:
            video_uuid = vector_result.get("video_uuid")
            if video_uuid:
                video_uuids.add(video_uuid)

        # 批量获取视频元数据
        metadata_map = {}
        if db_manager and video_uuids:
            try:
                # 这里需要根据实际的数据库管理器接口进行调整
                # metadata_map = db_manager.get_video_metadata_batch(list(video_uuids))
                pass
            except Exception as e:
                logger.error(f"批量获取视频元数据时出错: {e}")

        # 转换为时间轴条目
        for idx, vector_result in enumerate(vector_results):
            try:
                video_uuid = vector_result.get("video_uuid", "")
                segment_id = vector_result.get("segment_id", "")
                start_time = vector_result.get("start_time", 0.0)
                end_time = vector_result.get("end_time", 0.0)
                relevance_score = vector_result.get("score", 0.0)

                # 从元数据获取视频信息
                video_metadata = metadata_map.get(video_uuid, {})
                video_name = video_metadata.get("video_name", "")
                video_path = video_metadata.get("video_path", "")
                thumbnail_path = video_metadata.get("thumbnail_path")
                preview_path = video_metadata.get("preview_path")

                # 创建时间轴条目
                item = VideoTimelineItem(
                    video_uuid=video_uuid,
                    video_name=video_name,
                    video_path=video_path,
                    start_time=start_time,
                    end_time=end_time,
                    duration=end_time - start_time,
                    relevance_score=relevance_score,
                    thumbnail_path=thumbnail_path,
                    preview_path=preview_path,
                    scene_info=vector_result.get("scene_info"),
                    frame_count=vector_result.get("frame_count", 0),
                    metadata={"segment_id": segment_id},
                )

                result.add_item(item)

            except Exception as e:
                logger.error(f"处理向量结果 {idx} 时出错: {e}")
                continue

        # 自动排序
        result.sort_by_time()
        result.sort_by_relevance()

        logger.info(
            f"从数据库生成时间轴结果: {result.total_results} 个片段, {result.get_video_count()} 个视频"
        )

        return result

    def merge_timeline_results(
        self, results: List[VideoTimelineResult], merge_strategy: str = "union"
    ) -> VideoTimelineResult:
        """合并多个时间轴结果

        Args:
            results: 时间轴结果列表
            merge_strategy: 合并策略（union: 并集, intersection: 交集）

        Returns:
            合并后的时间轴结果
        """
        if not results:
            return VideoTimelineResult(query="", total_results=0)

        # 使用第一个结果的查询作为合并结果的查询
        merged = VideoTimelineResult(query=results[0].query, total_results=0)

        if merge_strategy == "union":
            # 并集策略：合并所有结果
            for result in results:
                for item in result.timeline_items:
                    # 检查是否已存在相同的条目
                    exists = any(
                        existing.video_uuid == item.video_uuid
                        and existing.start_time == item.start_time
                        and existing.end_time == item.end_time
                        for existing in merged.timeline_items
                    )
                    if not exists:
                        merged.add_item(item)

        elif merge_strategy == "intersection":
            # 交集策略：只保留所有结果中都存在的条目
            if len(results) < 2:
                # 只有一个结果，直接复制
                for item in results[0].timeline_items:
                    merged.add_item(item)
            else:
                # 查找所有结果中都存在的条目
                first_result = results[0]
                for item in first_result.timeline_items:
                    # 检查是否在所有结果中都存在
                    exists_in_all = all(
                        any(
                            other_item.video_uuid == item.video_uuid
                            and other_item.start_time == item.start_time
                            and other_item.end_time == item.end_time
                            for other_item in result.timeline_items
                        )
                        for result in results[1:]
                    )
                    if exists_in_all:
                        merged.add_item(item)

        # 自动排序
        merged.sort_by_time()
        merged.sort_by_relevance()

        logger.info(
            f"合并时间轴结果: {len(results)} 个结果 -> {merged.total_results} 个片段"
        )

        return merged
