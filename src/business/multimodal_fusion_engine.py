"""
多模态融合引擎 - 融合多模态向量搜索结果，提供统一的排序和重排机制
"""
import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class MultiModalFusionEngine:
    """多模态融合引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化多模态融合引擎
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.default_weights = config.get('fusion.default_weights', {
            'text': 0.25,
            'image': 0.25,
            'audio_music': 0.25,
            'audio_speech': 0.25
        })
        
        logger.info("多模态融合引擎初始化完成")
    
    def fuse_results(self, modality_results: Dict[str, List[Dict[str, Any]]], 
                     weights: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """
        融合多模态结果
        
        Args:
            modality_results: 各模态的搜索结果
            weights: 各模态的权重
            
        Returns:
            融合后的结果列表
        """
        try:
            if weights is None:
                weights = self.default_weights
            
            logger.debug(f"融合多模态结果: 模态数={len(modality_results)}, 权重={weights}")
            
            # 1. 收集所有结果
            all_results = []
            for modality, results in modality_results.items():
                for result in results:
                    result_copy = result.copy()
                    result_copy['modality'] = modality
                    all_results.append(result_copy)
            
            # 2. 按文件ID分组
            file_groups = {}
            for result in all_results:
                file_id = result.get('file_id') or result.get('id', 'unknown')
                if file_id not in file_groups:
                    file_groups[file_id] = []
                file_groups[file_id].append(result)
            
            # 3. 为每个文件组计算综合得分
            fused_results = []
            for file_id, results in file_groups.items():
                # 计算加权得分
                weighted_scores = []
                modalities = []
                
                for result in results:
                    modality = result['modality']
                    score = result.get('score', 0)
                    weight = weights.get(modality, 0)
                    
                    weighted_score = score * weight
                    weighted_scores.append(weighted_score)
                    modalities.append(modality)
                
                # 计算综合得分
                if weighted_scores:
                    total_score = sum(weighted_scores)
                    avg_score = total_score / len(weighted_scores)
                else:
                    total_score = 0
                    avg_score = 0
                
                # 使用第一个结果作为基础信息
                base_result = results[0].copy()
                base_result['score'] = float(avg_score)
                base_result['total_score'] = float(total_score)
                base_result['modalities'] = modalities
                base_result['modality_count'] = len(results)
                base_result['file_id'] = file_id
                
                fused_results.append(base_result)
            
            # 4. 按得分排序
            fused_results.sort(key=lambda x: x['score'], reverse=True)
            
            logger.debug(f"结果融合完成: 原始{len(all_results)}个结果 -> 融合后{len(fused_results)}个结果")
            
            return fused_results
            
        except Exception as e:
            logger.error(f"多模态结果融合失败: {e}")
            # 返回空列表而不是抛出异常
            return []
    
    def dynamic_weight_adjustment(self, query: str, query_type: str) -> Dict[str, float]:
        """
        动态权重调整
        
        Args:
            query: 查询字符串
            query_type: 查询类型
            
        Returns:
            调整后的权重字典
        """
        # 基于查询类型调整权重
        if query_type == "person":
            # 人名查询，提升图像和人脸相关权重
            return {
                'text': 0.2,
                'image': 0.5,
                'audio_music': 0.15,
                'audio_speech': 0.15
            }
        elif query_type == "audio":
            # 音频查询，提升音频相关权重
            return {
                'text': 0.3,
                'image': 0.2,
                'audio_music': 0.3,
                'audio_speech': 0.2
            }
        elif query_type == "visual":
            # 视觉查询，提升图像相关权重
            return {
                'text': 0.2,
                'image': 0.5,
                'audio_music': 0.15,
                'audio_speech': 0.15
            }
        else:
            # 默认权重
            return self.default_weights.copy()
    
    def reorder_results(self, results: List[Dict[str, Any]], 
                       query: str = None) -> List[Dict[str, Any]]:
        """
        重排序结果
        
        Args:
            results: 搜索结果列表
            query: 查询字符串(可选)
            
        Returns:
            重排序后的结果列表
        """
        try:
            if not results:
                return results
            
            # 可以实现更复杂的重排序逻辑
            # 例如：基于时间戳、文件类型、置信度等进行重排序
            
            # 简单按得分排序
            reordered = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
            
            logger.debug(f"结果重排序完成: {len(reordered)}个结果")
            return reordered
            
        except Exception as e:
            logger.error(f"结果重排序失败: {e}")
            return results


# 示例使用
if __name__ == "__main__":
    # 配置示例
    config = {
        'fusion': {
            'default_weights': {
                'text': 0.25,
                'image': 0.25,
                'audio_music': 0.25,
                'audio_speech': 0.25
            }
        }
    }
    
    # 创建引擎实例
    engine = MultiModalFusionEngine(config)
    
    # 示例模态结果
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
    
    # 融合结果
    # fused = engine.fuse_results(modality_results)
    # print(fused)
    # 
    # # 动态权重调整
    # weights = engine.dynamic_weight_adjustment("张三的照片", "person")
    # print(weights)