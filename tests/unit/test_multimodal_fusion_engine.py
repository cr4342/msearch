"""
多模态融合引擎单元测试
测试MultiModalFusionEngine的核心功能
"""
import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.business.multimodal_fusion_engine import MultiModalFusionEngine


class TestMultiModalFusionEngine:
    """多模态融合引擎核心功能测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            'fusion': {
                'default_weights': {
                    'text': 0.25,
                    'image': 0.25,
                    'audio_music': 0.25,
                    'audio_speech': 0.25
                }
            }
        }
    
    @pytest.fixture
    def fusion_engine(self, mock_config):
        """多模态融合引擎实例"""
        engine = MultiModalFusionEngine(mock_config)
        return engine
    
    def test_init_success(self, mock_config):
        """测试初始化成功"""
        engine = MultiModalFusionEngine(mock_config)
        
        # 验证组件是否正确初始化
        assert engine.config == mock_config
        assert engine.default_weights == mock_config['fusion']['default_weights']
    
    def test_fuse_results_success(self, fusion_engine):
        """测试成功融合多模态结果"""
        # 创建测试数据
        modality_results = {
            'text': [
                {'file_id': 'file1', 'score': 0.8, 'content': '相关内容'},
                {'file_id': 'file2', 'score': 0.6, 'content': '相关内容'}
            ],
            'image': [
                {'file_id': 'file1', 'score': 0.9, 'content': '相关图片'},
                {'file_id': 'file3', 'score': 0.7, 'content': '相关图片'}
            ]
        }
        
        # 执行测试
        result = fusion_engine.fuse_results(modality_results)
        
        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 3  # file1, file2, file3
        
        # 验证file1的得分（来自两个模态）
        file1_result = next(r for r in result if r['file_id'] == 'file1')
        expected_score = (0.8 * 0.25 + 0.9 * 0.25)  # 平均得分
        assert abs(file1_result['score'] - expected_score) < 1e-6
        
        # 验证结果按得分排序
        scores = [r['score'] for r in result]
        assert scores == sorted(scores, reverse=True)
    
    def test_fuse_results_with_custom_weights(self, fusion_engine):
        """测试使用自定义权重融合多模态结果"""
        # 创建测试数据
        modality_results = {
            'text': [
                {'file_id': 'file1', 'score': 0.8}
            ],
            'image': [
                {'file_id': 'file1', 'score': 0.9}
            ]
        }
        
        # 自定义权重
        custom_weights = {
            'text': 0.3,
            'image': 0.7,
            'audio_music': 0.0,
            'audio_speech': 0.0
        }
        
        # 执行测试
        result = fusion_engine.fuse_results(modality_results, custom_weights)
        
        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 1
        
        # 验证使用了自定义权重
        expected_score = (0.8 * 0.3 + 0.9 * 0.7)
        assert abs(result[0]['score'] - expected_score) < 1e-6
    
    def test_fuse_results_empty_input(self, fusion_engine):
        """测试融合空输入"""
        # 执行测试
        result = fusion_engine.fuse_results({})
        
        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_fuse_results_with_exception(self, fusion_engine):
        """测试融合过程中出现异常"""
        # 创建无效的输入数据
        modality_results = {
            'text': [
                {'file_id': 'file1', 'score': 'invalid_score'}  # 无效的分数类型
            ]
        }
        
        # 执行测试
        result = fusion_engine.fuse_results(modality_results)
        
        # 验证返回空列表而不是抛出异常
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_dynamic_weight_adjustment_person_query(self, fusion_engine):
        """测试人名查询的动态权重调整"""
        # 执行测试
        result = fusion_engine.dynamic_weight_adjustment("张三的照片", "person")
        
        # 验证结果
        assert isinstance(result, dict)
        assert result['text'] == 0.2
        assert result['image'] == 0.5
        assert result['audio_music'] == 0.15
        assert result['audio_speech'] == 0.15
    
    def test_dynamic_weight_adjustment_audio_query(self, fusion_engine):
        """测试音频查询的动态权重调整"""
        # 执行测试
        result = fusion_engine.dynamic_weight_adjustment("搜索音乐", "audio")
        
        # 验证结果
        assert isinstance(result, dict)
        assert result['text'] == 0.3
        assert result['image'] == 0.2
        assert result['audio_music'] == 0.3
        assert result['audio_speech'] == 0.2
    
    def test_dynamic_weight_adjustment_visual_query(self, fusion_engine):
        """测试视觉查询的动态权重调整"""
        # 执行测试
        result = fusion_engine.dynamic_weight_adjustment("查找图片", "visual")
        
        # 验证结果
        assert isinstance(result, dict)
        assert result['text'] == 0.2
        assert result['image'] == 0.5
        assert result['audio_music'] == 0.15
        assert result['audio_speech'] == 0.15
    
    def test_dynamic_weight_adjustment_generic_query(self, fusion_engine):
        """测试通用查询的动态权重调整"""
        # 执行测试
        result = fusion_engine.dynamic_weight_adjustment("查找相关文件", "generic")
        
        # 验证结果使用默认权重
        assert result == fusion_engine.default_weights
    
    def test_reorder_results_success(self, fusion_engine):
        """测试成功重排序结果"""
        # 创建测试数据
        results = [
            {'file_id': 'file1', 'score': 0.6},
            {'file_id': 'file2', 'score': 0.9},
            {'file_id': 'file3', 'score': 0.3}
        ]
        
        # 执行测试
        result = fusion_engine.reorder_results(results)
        
        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 3
        # 验证按得分降序排列
        scores = [r['score'] for r in result]
        assert scores == sorted(scores, reverse=True)
        # 验证最高分的文件在第一位
        assert result[0]['file_id'] == 'file2'
        assert result[0]['score'] == 0.9
    
    def test_reorder_results_empty_input(self, fusion_engine):
        """测试重排序空输入"""
        # 执行测试
        result = fusion_engine.reorder_results([])
        
        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_reorder_results_with_exception(self, fusion_engine):
        """测试重排序过程中出现异常"""
        # 创建无效的输入数据
        results = [
            {'file_id': 'file1', 'score': 'invalid_score'}  # 无效的分数类型
        ]
        
        # 执行测试
        result = fusion_engine.reorder_results(results)
        
        # 验证返回原始结果而不是抛出异常
        assert result == results


if __name__ == '__main__':
    pytest.main([__file__])