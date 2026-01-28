"""
视频时间轴展示模块单元测试
"""

import pytest
from src.services.search.timeline import (
    VideoTimelineItem,
    VideoTimelineResult,
    VideoTimelineGenerator
)


class TestVideoTimelineItem:
    """视频时间轴条目测试"""
    
    @pytest.fixture
    def item(self):
        """创建时间轴条目实例"""
        return VideoTimelineItem(
            video_uuid="test-uuid-001",
            video_name="test_video.mp4",
            video_path="/path/to/test_video.mp4",
            start_time=10.0,
            end_time=20.0,
            duration=10.0,
            relevance_score=0.85,
            thumbnail_path="/path/to/thumbnail.jpg",
            preview_path="/path/to/preview.mp4",
            scene_info={"scene_type": "action"},
            frame_count=240,
            metadata={"key": "value"}
        )
    
    def test_formatted_duration(self, item):
        """测试格式化时长"""
        assert item.formatted_duration == "00:10"
        
        item.duration = 3665.0  # 1小时1分5秒
        assert item.formatted_duration == "01:01:05"
    
    def test_formatted_start_time(self, item):
        """测试格式化开始时间"""
        assert item.formatted_start_time == "00:10"
        
        item.start_time = 3665.0
        assert item.formatted_start_time == "01:01:05"
    
    def test_formatted_end_time(self, item):
        """测试格式化结束时间"""
        assert item.formatted_end_time == "00:20"
        
        item.end_time = 3675.0
        assert item.formatted_end_time == "01:01:15"
    
    def test_auto_duration_calculation(self):
        """测试自动计算时长"""
        item = VideoTimelineItem(
            video_uuid="test-uuid",
            video_name="test.mp4",
            video_path="/path/to/test.mp4",
            start_time=5.0,
            end_time=15.0,
            duration=0.0,  # 设置为0，应该自动计算
            relevance_score=0.9
        )
        assert item.duration == 10.0
    
    def test_to_dict(self, item):
        """测试转换为字典"""
        item_dict = item.to_dict()
        assert item_dict["video_uuid"] == "test-uuid-001"
        assert item_dict["video_name"] == "test_video.mp4"
        assert item_dict["start_time"] == 10.0
        assert item_dict["end_time"] == 20.0
        assert item_dict["duration"] == 10.0
        assert "formatted_duration" in item_dict
        assert "formatted_start_time" in item_dict
        assert "formatted_end_time" in item_dict


class TestVideoTimelineResult:
    """视频时间轴结果测试"""
    
    @pytest.fixture
    def result(self):
        """创建时间轴结果实例"""
        return VideoTimelineResult(
            query="test query",
            total_results=0
        )
    
    @pytest.fixture
    def item1(self):
        """创建测试条目1"""
        return VideoTimelineItem(
            video_uuid="video-001",
            video_name="video1.mp4",
            video_path="/path/to/video1.mp4",
            start_time=10.0,
            end_time=20.0,
            duration=10.0,
            relevance_score=0.9
        )
    
    @pytest.fixture
    def item2(self):
        """创建测试条目2"""
        return VideoTimelineItem(
            video_uuid="video-001",
            video_name="video1.mp4",
            video_path="/path/to/video1.mp4",
            start_time=30.0,
            end_time=40.0,
            duration=10.0,
            relevance_score=0.8
        )
    
    @pytest.fixture
    def item3(self):
        """创建测试条目3"""
        return VideoTimelineItem(
            video_uuid="video-002",
            video_name="video2.mp4",
            video_path="/path/to/video2.mp4",
            start_time=5.0,
            end_time=15.0,
            duration=10.0,
            relevance_score=0.95
        )
    
    def test_add_item(self, result, item1):
        """测试添加条目"""
        result.add_item(item1)
        assert result.total_results == 1
        assert len(result.timeline_items) == 1
        assert "video-001" in result.grouped_by_video
    
    def test_add_multiple_items_same_video(self, result, item1, item2):
        """测试添加同一视频的多个条目"""
        result.add_item(item1)
        result.add_item(item2)
        assert result.total_results == 2
        assert len(result.grouped_by_video["video-001"]) == 2
    
    def test_add_multiple_items_different_videos(self, result, item1, item3):
        """测试添加不同视频的条目"""
        result.add_item(item1)
        result.add_item(item3)
        assert result.total_results == 2
        assert result.get_video_count() == 2
    
    def test_sort_by_time(self, result, item1, item2, item3):
        """测试按时间排序"""
        result.add_item(item3)  # start_time=5.0
        result.add_item(item1)  # start_time=10.0
        result.add_item(item2)  # start_time=30.0
        
        sorted_items = result.sort_by_time(ascending=True)
        assert sorted_items[0].start_time == 5.0
        assert sorted_items[1].start_time == 10.0
        assert sorted_items[2].start_time == 30.0
    
    def test_sort_by_time_descending(self, result, item1, item2, item3):
        """测试按时间降序排序"""
        result.add_item(item3)
        result.add_item(item1)
        result.add_item(item2)
        
        sorted_items = result.sort_by_time(ascending=False)
        assert sorted_items[0].start_time == 30.0
        assert sorted_items[1].start_time == 10.0
        assert sorted_items[2].start_time == 5.0
    
    def test_sort_by_relevance(self, result, item1, item2, item3):
        """测试按相关性排序"""
        result.add_item(item1)  # relevance=0.9
        result.add_item(item2)  # relevance=0.8
        result.add_item(item3)  # relevance=0.95
        
        sorted_items = result.sort_by_relevance(descending=True)
        assert sorted_items[0].relevance_score == 0.95
        assert sorted_items[1].relevance_score == 0.9
        assert sorted_items[2].relevance_score == 0.8
    
    def test_get_video_count(self, result, item1, item2, item3):
        """测试获取视频数量"""
        result.add_item(item1)
        result.add_item(item2)
        result.add_item(item3)
        assert result.get_video_count() == 2
    
    def test_get_items_by_video(self, result, item1, item2, item3):
        """测试获取指定视频的所有条目"""
        result.add_item(item1)
        result.add_item(item2)
        result.add_item(item3)
        
        items = result.get_items_by_video("video-001")
        assert len(items) == 2
        assert items[0].video_uuid == "video-001"
        assert items[1].video_uuid == "video-001"
    
    def test_get_total_duration(self, result, item1, item2, item3):
        """测试获取总时长"""
        result.add_item(item1)  # 10秒
        result.add_item(item2)  # 10秒
        result.add_item(item3)  # 10秒
        
        total_duration = result.get_total_duration()
        assert total_duration == 30.0
    
    def test_get_formatted_total_duration(self, result, item1, item2):
        """测试获取格式化总时长"""
        result.add_item(item1)  # 10秒
        result.add_item(item2)  # 10秒
        
        formatted_duration = result.get_formatted_total_duration()
        assert formatted_duration == "00:20"
    
    def test_to_dict(self, result, item1):
        """测试转换为字典"""
        result.add_item(item1)
        result_dict = result.to_dict()
        
        assert result_dict["query"] == "test query"
        assert result_dict["total_results"] == 1
        assert result_dict["video_count"] == 1
        assert len(result_dict["timeline_items"]) == 1
        assert "total_duration" in result_dict
        assert "formatted_total_duration" in result_dict


class TestVideoTimelineGenerator:
    """视频时间轴生成器测试"""
    
    @pytest.fixture
    def generator(self):
        """创建时间轴生成器实例"""
        return VideoTimelineGenerator()
    
    @pytest.fixture
    def search_results(self):
        """创建模拟搜索结果"""
        return [
            {
                "video_uuid": "video-001",
                "video_name": "video1.mp4",
                "video_path": "/path/to/video1.mp4",
                "start_time": 10.0,
                "end_time": 20.0,
                "relevance_score": 0.9,
                "scene_info": {"scene_type": "action"},
                "frame_count": 240,
                "metadata": {"key": "value"}
            },
            {
                "video_uuid": "video-002",
                "video_name": "video2.mp4",
                "video_path": "/path/to/video2.mp4",
                "start_time": 5.0,
                "end_time": 15.0,
                "relevance_score": 0.85,
                "scene_info": {"scene_type": "dialogue"},
                "frame_count": 200,
                "metadata": {}
            }
        ]
    
    @pytest.fixture
    def metadata_map(self):
        """创建模拟元数据映射"""
        return {
            "video-001": {
                "thumbnail_path": "/path/to/thumb1.jpg",
                "preview_path": "/path/to/preview1.mp4"
            },
            "video-002": {
                "thumbnail_path": "/path/to/thumb2.jpg",
                "preview_path": "/path/to/preview2.mp4"
            }
        }
    
    def test_from_search_results(self, generator, search_results, metadata_map):
        """测试从搜索结果生成时间轴"""
        result = generator.from_search_results(
            query="test query",
            search_results=search_results,
            metadata_map=metadata_map
        )
        
        assert result.query == "test query"
        assert result.total_results == 2
        assert result.get_video_count() == 2
        assert len(result.timeline_items) == 2
        assert result.timeline_items[0].video_uuid == "video-001"
        assert result.timeline_items[1].video_uuid == "video-002"
        assert result.timeline_items[0].thumbnail_path == "/path/to/thumb1.jpg"
        assert result.timeline_items[1].thumbnail_path == "/path/to/thumb2.jpg"
    
    def test_from_search_results_without_metadata(self, generator, search_results):
        """测试从搜索结果生成时间轴（无元数据）"""
        result = generator.from_search_results(
            query="test query",
            search_results=search_results,
            metadata_map=None
        )
        
        assert result.total_results == 2
        assert result.timeline_items[0].thumbnail_path is None
        assert result.timeline_items[1].thumbnail_path is None
    
    def test_merge_timeline_results_union(self, generator):
        """测试合并时间轴结果（并集策略）"""
        result1 = VideoTimelineResult(query="query1", total_results=0)
        item1 = VideoTimelineItem(
            video_uuid="video-001",
            video_name="video1.mp4",
            video_path="/path/to/video1.mp4",
            start_time=10.0,
            end_time=20.0,
            duration=10.0,
            relevance_score=0.9
        )
        result1.add_item(item1)
        
        result2 = VideoTimelineResult(query="query2", total_results=0)
        item2 = VideoTimelineItem(
            video_uuid="video-002",
            video_name="video2.mp4",
            video_path="/path/to/video2.mp4",
            start_time=5.0,
            end_time=15.0,
            duration=10.0,
            relevance_score=0.85
        )
        result2.add_item(item2)
        
        merged = generator.merge_timeline_results([result1, result2], merge_strategy="union")
        
        assert merged.total_results == 2
        assert merged.get_video_count() == 2
    
    def test_merge_timeline_results_intersection(self, generator):
        """测试合并时间轴结果（交集策略）"""
        result1 = VideoTimelineResult(query="query1", total_results=0)
        item1 = VideoTimelineItem(
            video_uuid="video-001",
            video_name="video1.mp4",
            video_path="/path/to/video1.mp4",
            start_time=10.0,
            end_time=20.0,
            duration=10.0,
            relevance_score=0.9
        )
        result1.add_item(item1)
        
        result2 = VideoTimelineResult(query="query2", total_results=0)
        item2 = VideoTimelineItem(
            video_uuid="video-001",
            video_name="video1.mp4",
            video_path="/path/to/video1.mp4",
            start_time=10.0,
            end_time=20.0,
            duration=10.0,
            relevance_score=0.85
        )
        result2.add_item(item2)
        
        merged = generator.merge_timeline_results([result1, result2], merge_strategy="intersection")
        
        assert merged.total_results == 1
        assert merged.get_video_count() == 1
    
    def test_merge_timeline_results_empty(self, generator):
        """测试合并空结果列表"""
        merged = generator.merge_timeline_results([], merge_strategy="union")
        assert merged.total_results == 0
    
    def test_merge_timeline_results_single(self, generator):
        """测试合并单个结果"""
        result1 = VideoTimelineResult(query="query1", total_results=0)
        item1 = VideoTimelineItem(
            video_uuid="video-001",
            video_name="video1.mp4",
            video_path="/path/to/video1.mp4",
            start_time=10.0,
            end_time=20.0,
            duration=10.0,
            relevance_score=0.9
        )
        result1.add_item(item1)
        
        merged = generator.merge_timeline_results([result1], merge_strategy="union")
        
        assert merged.total_results == 1
        assert merged.get_video_count() == 1