"""
msearch 多模态检索功能测试
验证CLIP、CLAP、Whisper模型的协同工作和智能检索功能
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.business.multimodal_fusion_engine import MultiModalFusionEngine


class TestMultiModalFusion:
    """多模态融合引擎测试"""
    
    @pytest.fixture
    def fusion_config(self):
        """融合引擎配置"""
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
    
    def test_fusion_engine_initialization(self, fusion_config):
        """测试融合引擎初始化"""
        engine = MultiModalFusionEngine(fusion_config)
        assert engine.config == fusion_config
        assert engine.default_weights['text'] == 0.25
        assert engine.default_weights['image'] == 0.25
        assert engine.default_weights['audio_music'] == 0.25
        assert engine.default_weights['audio_speech'] == 0.25
    
    def test_basic_fusion(self, fusion_config):
        """测试基本融合功能"""
        engine = MultiModalFusionEngine(fusion_config)
        
        # 模拟多模态结果
        modality_results = {
            'text': [
                {'file_id': 'file1', 'score': 0.8, 'content': '相关文本内容'},
                {'file_id': 'file2', 'score': 0.6, 'content': '相关文本内容'}
            ],
            'image': [
                {'file_id': 'file1', 'score': 0.9, 'content': '相关图片内容'},
                {'file_id': 'file3', 'score': 0.7, 'content': '相关图片内容'}
            ],
            'audio_music': [
                {'file_id': 'file1', 'score': 0.7, 'content': '相关音乐内容'},
                {'file_id': 'file4', 'score': 0.5, 'content': '相关音乐内容'}
            ]
        }
        
        # 执行融合
        fused_results = engine.fuse_results(modality_results)
        
        # 验证融合结果
        assert len(fused_results) == 4  # 应该有4个不同的文件
        
        # 验证file1的多模态融合结果
        file1_result = next(r for r in fused_results if r['file_id'] == 'file1')
        assert file1_result['modality_count'] == 3  # file1在3个模态中都有结果
        assert set(file1_result['modalities']) == {'text', 'image', 'audio_music'}
        
        # 验证得分计算
        # file1的加权得分: (0.8*0.25 + 0.9*0.25 + 0.7*0.25) / 3 = 0.2
        expected_score = (0.8*0.25 + 0.9*0.25 + 0.7*0.25) / 3
        assert abs(file1_result['score'] - expected_score) < 0.001
    
    def test_custom_weights_fusion(self, fusion_config):
        """测试自定义权重融合"""
        engine = MultiModalFusionEngine(fusion_config)
        
        # 模拟多模态结果
        modality_results = {
            'text': [
                {'file_id': 'file1', 'score': 0.8}
            ],
            'image': [
                {'file_id': 'file1', 'score': 0.9}
            ]
        }
        
        # 使用自定义权重
        custom_weights = {
            'text': 0.3,
            'image': 0.7,
            'audio_music': 0.0,
            'audio_speech': 0.0
        }
        
        # 执行融合
        fused_results = engine.fuse_results(modality_results, custom_weights)
        
        # 验证结果
        assert len(fused_results) == 1
        file1_result = fused_results[0]
        
        # 验证自定义权重计算: (0.8*0.3 + 0.9*0.7) / 2 = 0.415
        expected_score = (0.8*0.3 + 0.9*0.7) / 2
        assert abs(file1_result['score'] - expected_score) < 0.001
    
    def test_dynamic_weight_adjustment(self, fusion_config):
        """测试动态权重调整"""
        engine = MultiModalFusionEngine(fusion_config)
        
        # 测试人名查询权重调整
        person_weights = engine.dynamic_weight_adjustment("张三的照片", "person")
        assert person_weights['image'] == 0.5  # 图像权重最高
        assert person_weights['text'] == 0.2
        assert person_weights['audio_music'] == 0.15
        assert person_weights['audio_speech'] == 0.15
        
        # 测试音频查询权重调整
        audio_weights = engine.dynamic_weight_adjustment("动听的音乐", "audio")
        assert audio_weights['audio_music'] == 0.3  # 音乐权重最高
        assert audio_weights['text'] == 0.3
        assert audio_weights['image'] == 0.2
        assert audio_weights['audio_speech'] == 0.2
        
        # 测试视觉查询权重调整
        visual_weights = engine.dynamic_weight_adjustment("美丽的风景", "visual")
        assert visual_weights['image'] == 0.5  # 图像权重最高
        assert visual_weights['text'] == 0.2
        assert visual_weights['audio_music'] == 0.15
        assert visual_weights['audio_speech'] == 0.15
        
        # 测试默认权重
        default_weights = engine.dynamic_weight_adjustment("普通查询", "generic")
        assert default_weights['text'] == 0.25
        assert default_weights['image'] == 0.25
        assert default_weights['audio_music'] == 0.25
        assert default_weights['audio_speech'] == 0.25
    
    def test_empty_results_fusion(self, fusion_config):
        """测试空结果融合"""
        engine = MultiModalFusionEngine(fusion_config)
        
        # 测试空模态结果
        empty_results = engine.fuse_results({})
        assert empty_results == []
        
        # 测试部分空模态结果
        partial_results = engine.fuse_results({
            'text': [],
            'image': [{'file_id': 'file1', 'score': 0.9}]
        })
        
        assert len(partial_results) == 1
        assert partial_results[0]['file_id'] == 'file1'
    
    def test_result_reordering(self, fusion_config):
        """测试结果重排序"""
        engine = MultiModalFusionEngine(fusion_config)
        
        # 创建未排序的结果
        unsorted_results = [
            {'file_id': 'file3', 'score': 0.6},
            {'file_id': 'file1', 'score': 0.9},
            {'file_id': 'file2', 'score': 0.7}
        ]
        
        # 执行重排序
        reordered_results = engine.reorder_results(unsorted_results)
        
        # 验证排序结果
        assert reordered_results[0]['file_id'] == 'file1'
        assert reordered_results[1]['file_id'] == 'file2'
        assert reordered_results[2]['file_id'] == 'file3'
        
        # 验证得分递减
        scores = [r['score'] for r in reordered_results]
        assert scores == sorted(scores, reverse=True)
    
    def test_fusion_with_missing_scores(self, fusion_config):
        """测试缺少得分的情况"""
        engine = MultiModalFusionEngine(fusion_config)
        
        # 模拟部分结果缺少得分的情况
        modality_results = {
            'text': [
                {'file_id': 'file1', 'score': 0.8},
                {'file_id': 'file2'}  # 缺少得分
            ],
            'image': [
                {'file_id': 'file1', 'score': 0.9}
            ]
        }
        
        # 执行融合
        fused_results = engine.fuse_results(modality_results)
        
        # 验证结果
        assert len(fused_results) == 2
        
        # file2应该有默认得分0
        file2_result = next(r for r in fused_results if r['file_id'] == 'file2')
        assert file2_result['score'] == 0.0


class TestMultiModalIntegration:
    """多模态集成测试"""
    
    def test_cross_modal_consistency(self):
        """测试跨模态一致性"""
        # 这个测试验证不同模态对同一内容的一致性理解
        # 例如：文本"猫"和猫的图片应该在语义空间中相近
        
        # 模拟跨模态结果
        cross_modal_results = {
            'text': [
                {'file_id': 'cat_video', 'score': 0.85, 'content': '猫在玩耍'},
                {'file_id': 'dog_video', 'score': 0.45, 'content': '狗在奔跑'}
            ],
            'image': [
                {'file_id': 'cat_video', 'score': 0.90, 'content': '猫的图片'},
                {'file_id': 'dog_video', 'score': 0.50, 'content': '狗的图片'}
            ]
        }
        
        fusion_config = {
            'fusion': {
                'default_weights': {
                    'text': 0.5,
                    'image': 0.5,
                    'audio_music': 0.0,
                    'audio_speech': 0.0
                }
            }
        }
        
        engine = MultiModalFusionEngine(fusion_config)
        fused_results = engine.fuse_results(cross_modal_results)
        
        # 验证跨模态一致性
        cat_result = next(r for r in fused_results if r['file_id'] == 'cat_video')
        dog_result = next(r for r in fused_results if r['file_id'] == 'dog_video')
        
        # 猫的跨模态一致性应该更高（两个模态得分都较高）
        assert cat_result['score'] > dog_result['score']
        
        # 猫应该在多模态中都表现良好
        assert cat_result['modality_count'] == 2
        assert set(cat_result['modalities']) == {'text', 'image'}
    
    def test_multimodal_query_understanding(self):
        """测试多模态查询理解"""
        fusion_config = {
            'fusion': {
                'default_weights': {
                    'text': 0.25,
                    'image': 0.25,
                    'audio_music': 0.25,
                    'audio_speech': 0.25
                }
            }
        }
        
        engine = MultiModalFusionEngine(fusion_config)
        
        # 测试不同类型查询的权重调整
        test_queries = [
            ("张三的照片", "person"),
            ("动听的音乐", "audio"),
            ("美丽的风景", "visual"),
            ("普通查询", "generic")
        ]
        
        for query, query_type in test_queries:
            weights = engine.dynamic_weight_adjustment(query, query_type)
            
            # 验证权重总和为1.0
            total_weight = sum(weights.values())
            assert abs(total_weight - 1.0) < 0.001, f"权重总和不为1.0: {total_weight}"
            
            # 验证权重值在合理范围内
            for weight in weights.values():
                assert 0.0 <= weight <= 1.0, f"权重超出范围: {weight}"
    
    def test_multimodal_performance(self):
        """测试多模态性能"""
        fusion_config = {
            'fusion': {
                'default_weights': {
                    'text': 0.25,
                    'image': 0.25,
                    'audio_music': 0.25,
                    'audio_speech': 0.25
                }
            }
        }
        
        engine = MultiModalFusionEngine(fusion_config)
        
        # 创建大量模态结果测试性能
        large_modality_results = {}
        modalities = ['text', 'image', 'audio_music', 'audio_speech']
        
        for modality in modalities:
            results = []
            for i in range(1000):  # 每个模态1000个结果
                results.append({
                    'file_id': f'file_{modality}_{i}',
                    'score': np.random.random(),
                    'content': f'内容_{i}'
                })
            large_modality_results[modality] = results
        
        import time
        
        # 测试融合性能
        start_time = time.time()
        fused_results = engine.fuse_results(large_modality_results)
        fusion_time = time.time() - start_time
        
        # 验证性能要求：4000个结果的融合应在1秒内完成
        assert fusion_time < 1.0, f"融合性能过慢: {fusion_time}秒"
        
        # 验证结果正确性
        assert len(fused_results) > 0, "融合结果不应为空"
        
        # 验证结果按得分排序
        scores = [r['score'] for r in fused_results[:100]]  # 检查前100个结果
        assert scores == sorted(scores, reverse=True), "结果未正确排序"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])