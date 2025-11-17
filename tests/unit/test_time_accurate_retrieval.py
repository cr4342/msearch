"""
精确时间检索引擎单元测试
测试TimeAccurateRetrievalEngine的核心功能
"""
import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List

from src.business.time_accurate_retrieval import (
    TimeAccurateRetrievalEngine, 
    RetrievalQuery, 
    TimeAccurateResult,
    VideoTimelineGenerator
)
from src.processors.timestamp_processor import (
    TimestampInfo, ModalityType, TimeStampedResult, MergedTimeSegment
)


class TestTimeAccurateRetrievalEngine:
    """精确时间检索引擎核心功能测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            'search': {
                'timestamp_retrieval': {
                    'accuracy_requirement': 2.0,
                    'enable_segment_merging': True,
                    'merge_threshold': 2.0,
                    'continuity_detection': True,
                    'max_gap_tolerance': 4.0
                }
            }
        }
    
    @pytest.fixture
    def retrieval_engine(self, mock_config):
        """精确时间检索引擎实例"""
        # 创建mock对象
        mock_vector_store = AsyncMock()
        mock_timestamp_db = Mock()
        
        engine = TimeAccurateRetrievalEngine(mock_config, mock_vector_store, mock_timestamp_db)
        return engine
    
    def test_init_success(self, mock_config):
        """测试初始化成功"""
        # 创建mock对象
        mock_vector_store = AsyncMock()
        mock_timestamp_db = Mock()
        
        engine = TimeAccurateRetrievalEngine(mock_config, mock_vector_store, mock_timestamp_db)
        
        # 验证组件是否正确初始化
        assert engine.config == mock_config
        assert engine.vector_store == mock_vector_store
        assert engine.timestamp_db == mock_timestamp_db
        assert engine.accuracy_requirement == 2.0
        assert engine.enable_segment_merging is True
        assert engine.merge_threshold == 2.0
        assert engine.continuity_detection is True
        assert engine.max_gap_tolerance == 4.0
    
    @pytest.mark.asyncio
    async def test_retrieve_with_timestamp_success(self, retrieval_engine):
        """测试成功进行带时间戳的精确检索"""
        # 设置mock对象
        retrieval_engine._vector_search = AsyncMock(return_value=[
            {'vector_id': 'vector_1', 'score': 0.9},
            {'vector_id': 'vector_2', 'score': 0.8}
        ])
        
        # 模拟时间戳信息
        timestamp_info_1 = TimestampInfo(
            file_id='file_1',
            start_time=1.0,
            end_time=3.0,
            duration=2.0,
            confidence=0.9,
            modality=ModalityType.VISUAL,
            segment_id='segment_1',
            vector_id='vector_1'
        )
        timestamp_info_2 = TimestampInfo(
            file_id='file_1',
            start_time=5.0,
            end_time=7.0,
            duration=2.0,
            confidence=0.8,
            modality=ModalityType.VISUAL,
            segment_id='segment_2',
            vector_id='vector_2'
        )
        
        retrieval_engine.timestamp_db.get_timestamp_info_by_vector_id = Mock(side_effect=[
            timestamp_info_1,
            timestamp_info_2
        ])
        
        retrieval_engine._validate_time_accuracy = Mock(return_value=True)
        retrieval_engine._matches_query_filters = Mock(return_value=True)
        retrieval_engine._merge_overlapping_segments = Mock(return_value=[
            MergedTimeSegment(TimeStampedResult(
                file_id='file_1',
                start_time=1.0,
                end_time=3.0,
                score=0.9,
                vector_id='vector_1',
                modality=ModalityType.VISUAL,
                timestamp_info=timestamp_info_1
            ))
        ])
        retrieval_engine._sort_by_relevance_and_continuity = Mock(return_value=[
            MergedTimeSegment(TimeStampedResult(
                file_id='file_1',
                start_time=1.0,
                end_time=3.0,
                score=0.9,
                vector_id='vector_1',
                modality=ModalityType.VISUAL,
                timestamp_info=timestamp_info_1
            ))
        ])
        retrieval_engine._convert_to_accurate_results = Mock(return_value=[
            TimeAccurateResult(
                file_id='file_1',
                start_time=1.0,
                end_time=3.0,
                duration=2.0,
                score=0.9,
                confidence=0.9,
                modality=ModalityType.VISUAL,
                vector_id='vector_1',
                segment_id='segment_1',
                time_accuracy='±2.0s'
            )
        ])
        
        # 创建查询
        query_vector = np.array([0.1, 0.2, 0.3])
        query = RetrievalQuery(
            query_vector=query_vector,
            target_modality=ModalityType.VISUAL,
            top_k=10
        )
        
        # 执行测试
        result = await retrieval_engine.retrieve_with_timestamp(query)
        
        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TimeAccurateResult)
        assert result[0].file_id == 'file_1'
        assert result[0].score == 0.9
        
        # 验证调用了正确的处理步骤
        retrieval_engine._vector_search.assert_called_once()
        assert retrieval_engine.timestamp_db.get_timestamp_info_by_vector_id.call_count == 2
        retrieval_engine._merge_overlapping_segments.assert_called_once()
        retrieval_engine._sort_by_relevance_and_continuity.assert_called_once()
        retrieval_engine._convert_to_accurate_results.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_with_timestamp_no_results(self, retrieval_engine):
        """测试带时间戳的精确检索无结果"""
        # 设置mock对象，模拟无结果
        retrieval_engine._vector_search = AsyncMock(return_value=[])
        
        # 创建查询
        query_vector = np.array([0.1, 0.2, 0.3])
        query = RetrievalQuery(
            query_vector=query_vector,
            target_modality=ModalityType.VISUAL,
            top_k=10
        )
        
        # 执行测试
        result = await retrieval_engine.retrieve_with_timestamp(query)
        
        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_validate_time_accuracy(self, retrieval_engine):
        """测试验证时间戳精度"""
        engine = retrieval_engine
        
        # 创建时间戳信息
        timestamp_info = TimestampInfo(
            file_id='file_1',
            start_time=1.0,
            end_time=2.5,  # 1.5秒持续时间，在±2秒精度范围内
            duration=1.5,
            confidence=0.9,
            modality=ModalityType.VISUAL,
            segment_id='segment_1'
        )
        
        # 执行测试
        result = engine._validate_time_accuracy(timestamp_info)
        
        # 验证结果
        assert result is True
    
    def test_matches_query_filters(self, retrieval_engine):
        """测试匹配查询过滤条件"""
        engine = retrieval_engine
        
        # 创建时间戳信息
        timestamp_info = TimestampInfo(
            file_id='file_1',
            start_time=1.0,
            end_time=3.0,
            duration=2.0,
            confidence=0.9,
            modality=ModalityType.VISUAL,
            segment_id='segment_1'
        )
        
        # 创建查询
        query = RetrievalQuery(
            query_vector=np.array([0.1, 0.2, 0.3]),
            target_modality=ModalityType.VISUAL,
            file_id='file_1',
            time_range=(0.0, 5.0),
            min_confidence=0.5,
            top_k=10
        )
        
        # 执行测试
        result = engine._matches_query_filters(timestamp_info, query)
        
        # 验证结果
        assert result is True
    
    def test_matches_query_filters_file_id_mismatch(self, retrieval_engine):
        """测试文件ID不匹配的查询过滤"""
        engine = retrieval_engine
        
        # 创建时间戳信息
        timestamp_info = TimestampInfo(
            file_id='file_1',
            start_time=1.0,
            end_time=3.0,
            duration=2.0,
            confidence=0.9,
            modality=ModalityType.VISUAL,
            segment_id='segment_1'
        )
        
        # 创建查询，文件ID不匹配
        query = RetrievalQuery(
            query_vector=np.array([0.1, 0.2, 0.3]),
            target_modality=ModalityType.VISUAL,
            file_id='file_2',  # 不匹配
            top_k=10
        )
        
        # 执行测试
        result = engine._matches_query_filters(timestamp_info, query)
        
        # 验证结果
        assert result is False
    
    def test_is_time_continuous(self, retrieval_engine):
        """测试时间段连续性判断"""
        engine = retrieval_engine
        
        # 创建时间段
        segment = MergedTimeSegment(TimeStampedResult(
            file_id='file_1',
            start_time=1.0,
            end_time=3.0,
            score=0.9,
            vector_id='vector_1',
            modality=ModalityType.VISUAL,
            timestamp_info=TimestampInfo(
                file_id='file_1',
                start_time=1.0,
                end_time=3.0,
                duration=2.0,
                confidence=0.9,
                modality=ModalityType.VISUAL,
                segment_id='segment_1'
            )
        ))
        
        result = TimeStampedResult(
            file_id='file_1',
            start_time=4.0,  # 与前一段间隔1秒，在连续性阈值内
            end_time=6.0,
            score=0.8,
            vector_id='vector_2',
            modality=ModalityType.VISUAL,
            timestamp_info=TimestampInfo(
                file_id='file_1',
                start_time=4.0,
                end_time=6.0,
                duration=2.0,
                confidence=0.8,
                modality=ModalityType.VISUAL,
                segment_id='segment_2'
            )
        )
        
        # 执行测试
        result_value = engine._is_time_continuous(segment, result)
        
        # 验证结果
        assert result_value is True
    
    @pytest.mark.asyncio
    async def test_vector_search_success(self, retrieval_engine):
        """测试向量搜索成功"""
        engine = retrieval_engine
        
        # 设置mock对象
        engine.vector_store.search_vectors = AsyncMock(return_value=[
            {'vector_id': 'vector_1', 'score': 0.9},
            {'vector_id': 'vector_2', 'score': 0.8}
        ])
        
        # 创建查询向量
        query_vector = np.array([0.1, 0.2, 0.3])
        
        # 执行测试
        result = await engine._vector_search(query_vector, ModalityType.VISUAL, 10)
        
        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]['vector_id'] == 'vector_1'
        assert result[0]['score'] == 0.9
        
        # 验证调用了正确的向量存储方法
        engine.vector_store.search_vectors.assert_called_once()
    
    def test_get_video_segments_by_time_range(self, retrieval_engine):
        """测试获取指定时间范围内的视频段"""
        engine = retrieval_engine
        
        # 设置mock对象
        mock_query_builder = Mock()
        mock_query_builder.filter_by_file_id = Mock(return_value=mock_query_builder)
        mock_query_builder.filter_by_time_range = Mock(return_value=mock_query_builder)
        mock_query_builder.order_by_time = Mock(return_value=mock_query_builder)
        mock_query_builder.execute = Mock(return_value=[
            TimestampInfo(
                file_id='file_1',
                start_time=1.0,
                end_time=3.0,
                duration=2.0,
                confidence=0.9,
                modality=ModalityType.VISUAL,
                segment_id='segment_1'
            )
        ])
        
        with patch('src.business.time_accurate_retrieval.TimestampQueryBuilder', return_value=mock_query_builder):
            # 执行测试
            result = engine.get_video_segments_by_time_range('file_1', 0.0, 5.0)
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], TimeAccurateResult)
            assert result[0].file_id == 'file_1'
            assert result[0].start_time == 1.0
            assert result[0].end_time == 3.0


class TestVideoTimelineGenerator:
    """视频时间线生成器测试"""
    
    @pytest.fixture
    def mock_retrieval_engine(self):
        """模拟检索引擎"""
        mock_engine = Mock()
        mock_engine.timestamp_db = Mock()
        return mock_engine
    
    @pytest.fixture
    def timeline_generator(self, mock_retrieval_engine):
        """时间线生成器实例"""
        generator = VideoTimelineGenerator(mock_retrieval_engine)
        return generator
    
    def test_generate_timeline_success(self, timeline_generator, mock_retrieval_engine):
        """测试成功生成时间线"""
        # 设置mock对象
        mock_retrieval_engine.timestamp_db.get_timestamp_infos_by_file_id = Mock(return_value=[
            TimestampInfo(
                file_id='file_1',
                start_time=1.0,
                end_time=3.0,
                duration=2.0,
                confidence=0.9,
                modality=ModalityType.VISUAL,
                segment_id='segment_1'
            ),
            TimestampInfo(
                file_id='file_1',
                start_time=5.0,
                end_time=7.0,
                duration=2.0,
                confidence=0.8,
                modality=ModalityType.VISUAL,
                segment_id='segment_2'
            )
        ])
        
        timeline_generator.retrieval_engine.get_scene_boundaries = Mock(return_value=[
            TimeAccurateResult(
                file_id='file_1',
                start_time=1.0,
                end_time=3.0,
                duration=2.0,
                score=0.9,
                confidence=0.9,
                modality=ModalityType.VISUAL,
                vector_id='vector_1',
                segment_id='segment_1',
                time_accuracy='±2.0s'
            )
        ])
        
        # 执行测试
        result = timeline_generator.generate_timeline('file_1', resolution=10)
        
        # 验证结果
        assert isinstance(result, dict)
        assert 'file_id' in result
        assert 'time_points' in result
        assert 'scene_boundaries' in result
        assert 'statistics' in result
        assert result['file_id'] == 'file_1'
        assert len(result['time_points']) == 10  # 分辨率10
        assert len(result['scene_boundaries']) == 1


if __name__ == '__main__':
    pytest.main([__file__])