"""
结果排序器 - 实现多种结果排序算法
"""
import asyncio
import logging
from typing import Dict, Any, List, Tuple
from enum import Enum
import numpy as np


class RankingStrategy(Enum):
    SIMILARITY = "similarity"
    RELEVANCE = "relevance"
    POPULARITY = "popularity"
    RECENCY = "recency"
    HYBRID = "hybrid"
    PERSONALIZED = "personalized"


class ResultRanker:
    """结果排序器 - 实现多种结果排序算法"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def initialize(self) -> bool:
        """初始化结果排序器"""
        self.logger.info("初始化结果排序器")
        return True

    def rank_by_similarity(self, results: List[Dict[str, Any]], query_vector: List[float]) -> List[Dict[str, Any]]:
        """按相似度排序
        
        Args:
            results: 搜索结果列表
            query_vector: 查询向量
            
        Returns:
            排序后的结果列表
        """
        # 计算每个结果与查询的相似度（如果还没有计算的话）
        for result in results:
            if 'similarity_score' not in result:
                result['similarity_score'] = self._calculate_similarity_score(result, query_vector)
        
        # 按相似度分数降序排序
        sorted_results = sorted(results, key=lambda x: x['similarity_score'], reverse=True)
        return sorted_results

    def rank_by_relevance(self, results: List[Dict[str, Any]], query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """按相关性排序
        
        Args:
            results: 搜索结果列表
            query: 查询信息
            
        Returns:
            排序后的结果列表
        """
        for result in results:
            result['relevance_score'] = self._calculate_relevance_score(result, query)
        
        # 按相关性分数降序排序
        sorted_results = sorted(results, key=lambda x: x['relevance_score'], reverse=True)
        return sorted_results

    def rank_by_popularity(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按流行度排序
        
        Args:
            results: 搜索结果列表
            
        Returns:
            排序后的结果列表
        """
        for result in results:
            # 使用访问次数、点赞数等作为流行度指标
            popularity_score = result.get('access_count', 0) + result.get('like_count', 0) * 2
            result['popularity_score'] = popularity_score
        
        # 按流行度分数降序排序
        sorted_results = sorted(results, key=lambda x: x['popularity_score'], reverse=True)
        return sorted_results

    def rank_by_recency(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按时间排序
        
        Args:
            results: 搜索结果列表
            
        Returns:
            排序后的结果列表
        """
        # 按时间戳降序排序（最新的在前）
        sorted_results = sorted(results, key=lambda x: x.get('timestamp', 0), reverse=True)
        return sorted_results

    def personalized_ranking(self, results: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """个性化排序
        
        Args:
            results: 搜索结果列表
            user_profile: 用户画像
            
        Returns:
            排序后的结果列表
        """
        for result in results:
            result['personalized_score'] = self._calculate_personalized_score(result, user_profile)
        
        # 按个性化分数降序排序
        sorted_results = sorted(results, key=lambda x: x['personalized_score'], reverse=True)
        return sorted_results

    def learn_user_preferences(self, user_interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """学习用户偏好
        
        Args:
            user_interactions: 用户交互历史
            
        Returns:
            用户偏好模型
        """
        preferences = {
            'preferred_categories': {},
            'preferred_content_types': {},
            'time_preferences': {},
            'interaction_weights': {}
        }
        
        # 分析用户交互历史来学习偏好
        for interaction in user_interactions:
            content_type = interaction.get('content_type', 'unknown')
            category = interaction.get('category', 'unknown')
            timestamp = interaction.get('timestamp', 0)
            
            # 统计内容类型偏好
            if content_type in preferences['preferred_content_types']:
                preferences['preferred_content_types'][content_type] += 1
            else:
                preferences['preferred_content_types'][content_type] = 1
            
            # 统计类别偏好
            if category in preferences['preferred_categories']:
                preferences['preferred_categories'][category] += 1
            else:
                preferences['preferred_categories'][category] = 1
        
        return preferences

    def deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重结果
        
        Args:
            results: 搜索结果列表
            
        Returns:
            去重后的结果列表
        """
        seen_ids = set()
        unique_results = []
        
        for result in results:
            result_id = result.get('id') or result.get('file_path')
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        return unique_results

    def filter_results(self, results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """过滤结果
        
        Args:
            results: 搜索结果列表
            filters: 过滤条件
            
        Returns:
            过滤后的结果列表
        """
        filtered_results = []
        
        for result in results:
            include = True
            
            # 应用各种过滤条件
            if 'file_type' in filters:
                if result.get('file_type') not in filters['file_type']:
                    include = False
            
            if 'min_similarity' in filters:
                if result.get('similarity', 0) < filters['min_similarity']:
                    include = False
            
            if 'date_range' in filters:
                start_date, end_date = filters['date_range']
                if not (start_date <= result.get('created_at', 0) <= end_date):
                    include = False
            
            if include:
                filtered_results.append(result)
        
        return filtered_results

    def diversify_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """多样化结果
        
        Args:
            results: 搜索结果列表
            
        Returns:
            多样化后的结果列表
        """
        if not results:
            return results
        
        # 实现MMR (Maximal Marginal Relevance) 算法来多样化结果
        selected_results = [results[0]]  # 选择最相关的结果
        remaining_results = results[1:]
        
        lambda_param = 0.7  # 多样性和相关性的平衡参数
        
        while len(selected_results) < len(results) and len(selected_results) < self.config.get('search', {}).get('diversity_max_results', 20):
            best_score = float('-inf')
            best_result = None
            best_idx = -1
            
            for i, result in enumerate(remaining_results):
                # 计算MMR分数
                relevance_score = result.get('similarity_score', result.get('relevance_score', 0))
                
                # 计算与已选结果的相似度
                max_similarity = 0
                for selected in selected_results:
                    sim = self._calculate_result_similarity(result, selected)
                    max_similarity = max(max_similarity, sim)
                
                mmr_score = lambda_param * relevance_score - (1 - lambda_param) * max_similarity
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_result = result
                    best_idx = i
            
            if best_result:
                selected_results.append(best_result)
                del remaining_results[best_idx]
            else:
                break  # 没有更多结果可选
        
        return selected_results

    def calculate_relevance_score(self, result: Dict[str, Any], query: Dict[str, Any]) -> float:
        """计算相关性分数
        
        Args:
            result: 搜索结果
            query: 查询信息
            
        Returns:
            相关性分数
        """
        return self._calculate_relevance_score(result, query)

    def combine_scores(self, scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """组合多个分数
        
        Args:
            scores: 分数字典
            weights: 权重字典
            
        Returns:
            组合后的分数
        """
        total_score = 0.0
        total_weight = 0.0
        
        for score_type, score in scores.items():
            weight = weights.get(score_type, 1.0)
            total_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            return total_score / total_weight
        else:
            return 0.0

    def _calculate_similarity_score(self, result: Dict[str, Any], query_vector: List[float]) -> float:
        """计算相似度分数"""
        # 从结果中获取向量，计算与查询向量的相似度
        result_vector = result.get('vector')
        if result_vector and query_vector:
            # 计算余弦相似度
            dot_product = sum(a * b for a, b in zip(result_vector, query_vector))
            norm_a = sum(a * a for a in result_vector) ** 0.5
            norm_b = sum(b * b for b in query_vector) ** 0.5
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return dot_product / (norm_a * norm_b)
        else:
            # 如果没有向量，返回默认相似度
            return result.get('similarity', 0.0)

    def _calculate_relevance_score(self, result: Dict[str, Any], query: Dict[str, Any]) -> float:
        """计算相关性分数"""
        # 结合多个因素计算相关性
        similarity_score = result.get('similarity', 0.0)
        metadata_score = self._calculate_metadata_score(result, query)
        popularity_score = self._calculate_popularity_score(result)
        
        # 根据配置加权组合
        weights = self.config.get('search', {}).get('relevance_weights', {
            'similarity': 0.6,
            'metadata': 0.3,
            'popularity': 0.1
        })
        
        relevance_score = (
            similarity_score * weights.get('similarity', 0.6) +
            metadata_score * weights.get('metadata', 0.3) +
            popularity_score * weights.get('popularity', 0.1)
        )
        
        return relevance_score

    def _calculate_metadata_score(self, result: Dict[str, Any], query: Dict[str, Any]) -> float:
        """计算元数据相关性分数"""
        metadata = result.get('metadata', {})
        query_text = query.get('original_query', '').lower()
        
        score = 0.0
        
        # 检查文件名匹配
        if 'file_name' in metadata:
            file_name = metadata['file_name'].lower()
            if query_text in file_name:
                score += 0.3
            elif any(word in file_name for word in query_text.split()):
                score += 0.1
        
        # 检查描述或标签匹配
        if 'description' in metadata:
            desc = metadata['description'].lower()
            if query_text in desc:
                score += 0.2
            elif any(word in desc for word in query_text.split()):
                score += 0.1
        
        # 检查标签匹配
        if 'tags' in metadata:
            tags = [tag.lower() for tag in metadata['tags']]
            matching_tags = [tag for tag in tags if query_text in tag or query_text.split()[0] in tag if query_text.split()]
            score += min(0.2, len(matching_tags) * 0.1)
        
        return min(1.0, score)

    def _calculate_popularity_score(self, result: Dict[str, Any]) -> float:
        """计算流行度分数"""
        access_count = result.get('access_count', 0)
        like_count = result.get('like_count', 0)
        share_count = result.get('share_count', 0)
        
        # 归一化流行度分数
        total_interactions = access_count + like_count * 2 + share_count * 3
        max_expected_interactions = 1000  # 假设的最大交互数
        
        return min(1.0, total_interactions / max_expected_interactions)

    def _calculate_personalized_score(self, result: Dict[str, Any], user_profile: Dict[str, Any]) -> float:
        """计算个性化分数"""
        base_score = result.get('relevance_score', result.get('similarity', 0.0))
        
        # 根据用户偏好调整分数
        content_type = result.get('file_type', 'unknown')
        category = result.get('category', 'unknown')
        
        type_boost = user_profile.get('preferred_content_types', {}).get(content_type, 1.0)
        category_boost = user_profile.get('preferred_categories', {}).get(category, 1.0)
        
        # 时间偏好（如果结果与用户活跃时间匹配）
        time_boost = 1.0  # 简化实现
        
        personalized_score = base_score * type_boost * category_boost * time_boost
        
        return min(1.0, personalized_score)

    def _calculate_result_similarity(self, result1: Dict[str, Any], result2: Dict[str, Any]) -> float:
        """计算两个结果之间的相似度"""
        # 计算向量相似度
        vector1 = result1.get('vector')
        vector2 = result2.get('vector')
        
        if vector1 and vector2:
            # 计算余弦相似度
            dot_product = sum(a * b for a, b in zip(vector1, vector2))
            norm_a = sum(a * a for a in vector1) ** 0.5
            norm_b = sum(b * b for b in vector2) ** 0.5
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return dot_product / (norm_a * norm_b)
        else:
            # 如果没有向量，基于元数据计算相似度
            return self._metadata_similarity(result1, result2)

    def _metadata_similarity(self, result1: Dict[str, Any], result2: Dict[str, Any]) -> float:
        """基于元数据计算相似度"""
        meta1 = result1.get('metadata', {})
        meta2 = result2.get('metadata', {})
        
        similarity = 0.0
        
        # 比较文件类型
        if meta1.get('file_type') == meta2.get('file_type'):
            similarity += 0.2
        
        # 比较标签
        tags1 = set(meta1.get('tags', []))
        tags2 = set(meta2.get('tags', []))
        if tags1 and tags2:
            jaccard = len(tags1.intersection(tags2)) / len(tags1.union(tags2))
            similarity += jaccard * 0.3
        
        # 比较类别
        if meta1.get('category') == meta2.get('category'):
            similarity += 0.3
        
        return min(1.0, similarity)
    
    def aggregate_results_by_video(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按视频聚合结果，收集相似度分数和时间戳列
        
        Args:
            results: 搜索结果列表
            
        Returns:
            按视频聚合的结果列表
        """
        from collections import defaultdict
        
        # 按视频聚合结果
        aggregated_results = {}
        for result in results:
            # 获取视频唯一标识
            video_uuid = result.get('video_uuid') or result.get('file_uuid')
            if not video_uuid:
                continue
            
            if video_uuid not in aggregated_results:
                # 初始化视频聚合结果
                aggregated_results[video_uuid] = {
                    'video_uuid': video_uuid,
                    'file_path': result.get('file_path', ''),
                    'file_name': result.get('file_name', ''),
                    'file_type': result.get('file_type', ''),
                    'modality': result.get('modality', ''),
                    'processing_status': result.get('processing_status', ''),
                    'total_segments': result.get('total_segments', 0),
                    'indexed_segments': result.get('indexed_segments', 0),
                    'segments': []
                }
            
            # 添加切片信息
            aggregated_results[video_uuid]['segments'].append({
                'similarity_score': result.get('similarity_score', 0.0),
                'absolute_timestamp': result.get('absolute_timestamp', 0.0),
                'segment_id': result.get('segment_id', ''),
                'vector_id': result.get('vector_id', ''),
                'start_time': result.get('start_time', 0.0),
                'end_time': result.get('end_time', 0.0),
                'duration': result.get('duration', 0.0),
                'frame_path': result.get('frame_path', ''),
                'relative_position': result.get('relative_position', 0.0)
            })
        
        # 计算视频的最大相似度并构建最终结果
        final_results = []
        for video_uuid, agg_result in aggregated_results.items():
            segments = agg_result['segments']
            if segments:
                # 计算视频的最大相似度
                max_similarity = max(segment['similarity_score'] for segment in segments)
                
                # 获取最相似的切片
                most_similar_segment = max(segments, key=lambda x: x['similarity_score'])
                
                # 构建最终结果
                final_result = {
                    'result_id': f"video-{video_uuid}",
                    'video_uuid': video_uuid,
                    'file_path': agg_result['file_path'],
                    'file_name': agg_result['file_name'],
                    'file_type': agg_result['file_type'],
                    'modality': agg_result['modality'],
                    'similarity_score': max_similarity,
                    'best_match_timestamp': most_similar_segment['absolute_timestamp'],
                    'matched_segments': segments,
                    'matched_segment_count': len(segments),
                    'processing_status': agg_result['processing_status'],
                    'total_segments': agg_result['total_segments'],
                    'indexed_segments': agg_result['indexed_segments']
                }
                final_results.append(final_result)
        
        # 按视频聚合相似度排序
        final_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        self.logger.debug(f"按视频聚合结果: {len(final_results)} 个视频")
        return final_results