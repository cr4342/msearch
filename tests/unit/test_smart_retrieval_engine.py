"""
SmartRetrievalEngine单元测试
测试智能检索引擎的查询类型识别和动态权重分配
"""
import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from src.business.smart_retrieval import SmartRetrievalEngine
from src.core.config_manager import ConfigManager


class TestSmartRetrievalEngine:
    """智能检索引擎核心功能测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        config = Mock(spec=ConfigManager)
        config.get.side_effect = lambda key, default=None: {
            'retrieval.accuracy_requirement': 2.0,
            'retrieval.top_k': 50,
            'retrieval.similarity_threshold': 0.7,
            'retrieval.person_names': ['张三', '李四', '王五', '科比', '乔丹'],
            'retrieval.weights.default': {'visual': 0.4, 'audio': 0.3, 'text': 0.3},
            'retrieval.weights.person_query': {'face': 0.6, 'visual': 0.2, 'audio': 0.1, 'text': 0.1},
            'retrieval.weights.audio_query': {'audio': 0.6, 'visual': 0.2, 'text': 0.2},
            'retrieval.weights.visual_query': {'visual': 0.6, 'audio': 0.2, 'text': 0.2}
        }.get(key, default)
        return config
    
    @pytest.fixture
    def mock_face_manager(self):
        """模拟人脸管理器"""
        face_manager = AsyncMock()
        face_manager.search_person_files.return_value = ['file_1', 'file_2', 'file_3']
        face_manager.evaluate_face_coverage.return_value = 0.8
        return face_manager
    
    @pytest.fixture
    def mock_vector_search(self):
        """模拟向量搜索"""
        vector_search = AsyncMock()
        vector_search.search.return_value = [
            {'file_id': 'file_1', 'score': 0.95, 'timestamp': 10.5},
            {'file_id': 'file_2', 'score': 0.88, 'timestamp': 25.2},
            {'file_id': 'file_3', 'score': 0.82, 'timestamp': 45.8},
        ]
        return vector_search
    
    @pytest.fixture
    def smart_retrieval_engine(self, mock_config, mock_face_manager, mock_vector_search):
        """智能检索引擎实例"""
        engine = SmartRetrievalEngine(config=mock_config)
        engine.face_manager = mock_face_manager
        engine.vector_search = mock_vector_search
        return engine
    
    def test_query_type_recognition(self, smart_retrieval_engine):
        """测试查询类型识别"""
        # 测试人名查询识别
        person_queries = [
            "张三在做什么",
            "科比正在投篮",
            "李四的照片",
            "王五在哪里"
        ]
        
        for query in person_queries:
            query_type, extracted_info = smart_retrieval_engine.recognize_query_type(query)
            assert query_type == 'person_query'
            assert 'person_name' in extracted_info
            assert extracted_info['person_name'] in ['张三', '科比', '李四', '王五']
        
        # 测试音频查询识别
        audio_queries = [
            "播放音乐",
            "这首歌是什么",
            "音频内容",
            "声音很大"
        ]
        
        for query in audio_queries:
            query_type, extracted_info = smart_retrieval_engine.recognize_query_type(query)
            assert query_type == 'audio_query'
        
        # 测试视觉查询识别
        visual_queries = [
            "红色的汽车",
            "美丽的风景",
            "建筑物",
            "动物照片"
        ]
        
        for query in visual_queries:
            query_type, extracted_info = smart_retrieval_engine.recognize_query_type(query)
            assert query_type == 'visual_query'
        
        # 测试通用查询
        general_queries = [
            "搜索内容",
            "查找文件",
            "相关信息"
        ]
        
        for query in general_queries:
            query_type, extracted_info = smart_retrieval_engine.recognize_query_type(query)
            assert query_type == 'general_query'
    
    def test_dynamic_weight_calculation(self, smart_retrieval_engine):
        """测试动态权重计算"""
        # 测试人名查询权重
        person_weights = smart_retrieval_engine.calculate_dynamic_weights(
            'person_query', {'person_name': '科比'}
        )
        assert person_weights['face'] == 0.6
        assert person_weights['visual'] == 0.2
        assert sum(person_weights.values()) == pytest.approx(1.0)
        
        # 测试音频查询权重
        audio_weights = smart_retrieval_engine.calculate_dynamic_weights('audio_query', {})
        assert audio_weights['audio'] == 0.6
        assert audio_weights['visual'] == 0.2
        assert sum(audio_weights.values()) == pytest.approx(1.0)
        
        # 测试视觉查询权重
        visual_weights = smart_retrieval_engine.calculate_dynamic_weights('visual_query', {})
        assert visual_weights['visual'] == 0.6
        assert visual_weights['audio'] == 0.2
        assert sum(visual_weights.values()) == pytest.approx(1.0)
        
        # 测试默认权重
        default_weights = smart_retrieval_engine.calculate_dynamic_weights('general_query', {})
        assert default_weights['visual'] == 0.4
        assert default_weights['audio'] == 0.3
        assert default_weights['text'] == 0.3
        assert sum(default_weights.values()) == pytest.approx(1.0)
    
    @pytest.mark.asyncio
    async def test_layered_retrieval_strategy(self, smart_retrieval_engine):
        """测试分层检索策略"""
        # 测试人名查询的分层检索
        query = "科比正在投篮"
        
        # 执行分层检索
        results = await smart_retrieval_engine.layered_retrieval(query)
        
        # 验证分层检索流程
        # 1. 人脸预检索应该被调用
        smart_retrieval_engine.face_manager.search_person_files.assert_called_once()
        
        # 2. 应该生成文件白名单
        assert len(results) > 0
        
        # 3. 结果应该包含时间戳信息
        for result in results:
            assert 'timestamp' in result
            assert 'file_id' in result
            assert 'score' in result
    
    @pytest.mark.asyncio
    async def test_comprehensive_retrieval_strategy(self, smart_retrieval_engine):
        """测试全库检索策略"""
        # 模拟人脸覆盖率不足的情况
        smart_retrieval_engine.face_manager.evaluate_face_coverage.return_value = 0.3
        
        query = "科比正在投篮"
        
        # 执行全库检索
        results = await smart_retrieval_engine.comprehensive_retrieval(query)
        
        # 验证全库检索流程
        # 1. 向量搜索应该被调用
        smart_retrieval_engine.vector_search.search.assert_called()
        
        # 2. 应该返回搜索结果
        assert len(results) > 0
        
        # 3. 结果应该包含完整信息
        for result in results:
            assert 'file_id' in result
            assert 'score' in result
    
    @pytest.mark.asyncio
    async def test_adaptive_strategy_selection(self, smart_retrieval_engine):
        """测试自适应策略选择"""
        # 测试高人脸覆盖率情况（应选择分层检索）
        smart_retrieval_engine.face_manager.evaluate_face_coverage.return_value = 0.8
        
        query = "科比正在投篮"
        strategy = await smart_retrieval_engine.select_optimal_strategy(query)
        
        assert strategy == 'layered_retrieval'
        
        # 测试低人脸覆盖率情况（应选择全库检索）
        smart_retrieval_engine.face_manager.evaluate_face_coverage.return_value = 0.3
        
        strategy = await smart_retrieval_engine.select_optimal_strategy(query)
        
        assert strategy == 'comprehensive_retrieval'
    
    @pytest.mark.asyncio
    async def test_result_fusion_and_ranking(self, smart_retrieval_engine):
        """测试结果融合和排序"""
        # 模拟多模态搜索结果
        multimodal_results = {
            'visual': [
                {'file_id': 'file_1', 'score': 0.9, 'timestamp': 10.5},
                {'file_id': 'file_2', 'score': 0.8, 'timestamp': 25.2},
            ],
            'audio': [
                {'file_id': 'file_1', 'score': 0.7, 'timestamp': 10.5},
                {'file_id': 'file_3', 'score': 0.85, 'timestamp': 45.8},
            ],
            'face': [
                {'file_id': 'file_1', 'score': 0.95, 'timestamp': 10.5},
            ]
        }
        
        weights = {'visual': 0.4, 'audio': 0.3, 'face': 0.3}
        
        # 执行结果融合
        fused_results = smart_retrieval_engine.fuse_multimodal_results(
            multimodal_results, weights
        )
        
        # 验证融合结果
        assert len(fused_results) == 3  # 应该有3个不同的文件
        
        # 验证排序（按融合分数降序）
        for i in range(len(fused_results) - 1):
            assert fused_results[i]['fused_score'] >= fused_results[i + 1]['fused_score']
        
        # 验证file_1应该排在最前面（多模态都有高分）
        assert fused_results[0]['file_id'] == 'file_1'
    
    @pytest.mark.asyncio
    async def test_timestamp_accuracy_validation(self, smart_retrieval_engine):
        """测试时间戳精度验证"""
        # 创建包含时间戳的搜索结果
        search_results = [
            {'file_id': 'file_1', 'score': 0.9, 'timestamp': 10.5, 'duration': 2.0},
            {'file_id': 'file_2', 'score': 0.8, 'timestamp': 25.2, 'duration': 1.5},
            {'file_id': 'file_3', 'score': 0.7, 'timestamp': 45.8, 'duration': 5.0},  # 超过±2秒
        ]
        
        # 验证时间戳精度
        validated_results = smart_retrieval_engine.validate_timestamp_accuracy(search_results)
        
        # 应该过滤掉精度不满足要求的结果
        assert len(validated_results) == 2
        
        # 验证剩余结果都满足±2秒精度要求
        for result in validated_results:
            assert result['duration'] <= 4.0  # ±2秒 = 4秒总时长
    
    def test_person_name_extraction(self, smart_retrieval_engine):
        """测试人名提取功能"""
        # 测试简单人名提取
        test_cases = [
            ("张三在做什么", "张三"),
            ("科比正在投篮", "科比"),
            ("李四的照片在哪里", "李四"),
            ("王五今天来了吗", "王五"),
            ("没有人名的查询", None),
        ]
        
        for query, expected_name in test_cases:
            extracted_name = smart_retrieval_engine.extract_person_name(query)
            assert extracted_name == expected_name
    
    def test_query_context_analysis(self, smart_retrieval_engine):
        """测试查询上下文分析"""
        # 测试复杂查询的上下文分析
        complex_queries = [
            {
                'query': "科比在篮球场上投篮的视频",
                'expected_context': {
                    'person': '科比',
                    'action': '投篮',
                    'location': '篮球场',
                    'media_type': '视频'
                }
            },
            {
                'query': "张三唱歌的音频文件",
                'expected_context': {
                    'person': '张三',
                    'action': '唱歌',
                    'media_type': '音频'
                }
            }
        ]
        
        for test_case in complex_queries:
            context = smart_retrieval_engine.analyze_query_context(test_case['query'])
            
            # 验证上下文分析结果
            for key, expected_value in test_case['expected_context'].items():
                assert key in context
                assert context[key] == expected_value


class TestSmartRetrievalEngineIntegration:
    """智能检索引擎集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_retrieval_flow(self):
        """测试端到端检索流程"""
        # 创建完整的配置
        config = Mock(spec=ConfigManager)
        config.get.side_effect = lambda key, default=None: {
            'retrieval.accuracy_requirement': 2.0,
            'retrieval.top_k': 10,
            'retrieval.person_names': ['科比', '乔丹'],
            'retrieval.weights.person_query': {'face': 0.6, 'visual': 0.3, 'audio': 0.1}
        }.get(key, default)
        
        # 创建智能检索引擎
        engine = SmartRetrievalEngine(config=config)
        
        # 模拟依赖组件
        engine.face_manager = AsyncMock()
        engine.face_manager.evaluate_face_coverage.return_value = 0.8
        engine.face_manager.search_person_files.return_value = ['file_1', 'file_2']
        
        engine.vector_search = AsyncMock()
        engine.vector_search.search.return_value = [
            {'file_id': 'file_1', 'score': 0.95, 'timestamp': 10.5, 'duration': 2.0},
            {'file_id': 'file_2', 'score': 0.88, 'timestamp': 25.2, 'duration': 1.8},
        ]
        
        # 执行完整的检索流程
        query = "科比正在投篮"
        results = await engine.smart_search(query)
        
        # 验证检索结果
        assert len(results) > 0
        assert all('file_id' in result for result in results)
        assert all('score' in result for result in results)
        assert all('timestamp' in result for result in results)
        
        # 验证时间戳精度
        for result in results:
            if 'duration' in result:
                assert result['duration'] <= 4.0  # ±2秒精度要求
    
    @pytest.mark.asyncio
    async def test_performance_optimization(self):
        """测试性能优化效果"""
        config = Mock(spec=ConfigManager)
        config.get.side_effect = lambda key, default=None: {
            'retrieval.accuracy_requirement': 2.0,
            'retrieval.top_k': 50,
            'retrieval.person_names': ['科比']
        }.get(key, default)
        
        engine = SmartRetrievalEngine(config=config)
        
        # 模拟大规模数据集
        engine.face_manager = AsyncMock()
        engine.face_manager.evaluate_face_coverage.return_value = 0.8
        engine.face_manager.search_person_files.return_value = [f'file_{i}' for i in range(100)]
        
        engine.vector_search = AsyncMock()
        engine.vector_search.search.return_value = [
            {'file_id': f'file_{i}', 'score': 0.9 - i*0.01, 'timestamp': i*2.0}
            for i in range(100)
        ]
        
        # 测试分层检索性能
        import time
        start_time = time.time()
        
        results = await engine.smart_search("科比正在投篮")
        
        end_time = time.time()
        search_time = (end_time - start_time) * 1000  # 转换为毫秒
        
        # 分层检索应该提升30-50%效率
        assert search_time < 200  # 应该在200ms内完成
        assert len(results) <= 50  # 返回top_k结果