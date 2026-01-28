#!/usr/bin/env python3
"""
msearch 检索准确率优化测试（真实版本）
执行实际的向量搜索，评估检索准确率
"""

import sys
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Set
from collections import defaultdict

sys.path.insert(0, 'src')


class SearchAccuracyEvaluator:
    """检索准确率评估器"""
    
    def __init__(self):
        self.evaluation_results = {}
    
    def calculate_precision_at_k(self, retrieved_items: List[Dict], relevant_items: Set[str], k: int) -> float:
        """计算Precision@K"""
        if k == 0:
            return 0.0
        
        relevant_count = 0
        for i in range(min(k, len(retrieved_items))):
            item = retrieved_items[i]
            # 优先使用file_id，如果没有则使用file_path
            item_id = item.get('file_id') or item.get('file_path', '')
            if item_id in relevant_items:
                relevant_count += 1
        
        return relevant_count / k
    
    def calculate_recall_at_k(self, retrieved_items: List[Dict], relevant_items: Set[str], k: int) -> float:
        """计算Recall@K"""
        if len(relevant_items) == 0:
            return 0.0
        
        relevant_count = 0
        for i in range(min(k, len(retrieved_items))):
            item = retrieved_items[i]
            item_id = item.get('file_id') or item.get('file_path', '')
            if item_id in relevant_items:
                relevant_count += 1
        
        return relevant_count / len(relevant_items)
    
    def calculate_mrr(self, retrieved_items: List[Dict], relevant_items: Set[str]) -> float:
        """计算Mean Reciprocal Rank (MRR)"""
        if len(relevant_items) == 0:
            return 0.0
        
        for i, item in enumerate(retrieved_items, start=1):
            item_id = item.get('file_id') or item.get('file_path', '')
            if item_id in relevant_items:
                return 1.0 / i
        
        return 0.0
    
    def calculate_ndcg_at_k(self, retrieved_items: List[Dict], relevance_scores: Dict[str, float], k: int) -> float:
        """计算Normalized Discounted Cumulative Gain (NDCG@K)"""
        if k == 0:
            return 0.0
        
        # 计算DCG@K
        dcg = 0.0
        for i in range(min(k, len(retrieved_items))):
            item = retrieved_items[i]
            item_id = item.get('file_id') or item.get('file_path', '')
            relevance = relevance_scores.get(item_id, 0.0)
            dcg += relevance / np.log2(i + 2)
        
        # 计算IDCG@K
        sorted_relevance = sorted(relevance_scores.values(), reverse=True)
        idcg = 0.0
        for i in range(min(k, len(sorted_relevance))):
            idcg += sorted_relevance[i] / np.log2(i + 2)
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    def evaluate_search_quality(self, query: str, retrieved_items: List[Dict], 
                               relevant_items: Set[str], relevance_scores: Dict[str, float] = None,
                               k_values: List[int] = [1, 5, 10, 20]) -> Dict[str, Any]:
        """综合评估检索质量"""
        results = {
            'query': query,
            'retrieved_count': len(retrieved_items),
            'relevant_count': len(relevant_items),
            'metrics': {}
        }
        
        # 计算不同K值的Precision和Recall
        for k in k_values:
            precision = self.calculate_precision_at_k(retrieved_items, relevant_items, k)
            recall = self.calculate_recall_at_k(retrieved_items, relevant_items, k)
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            results['metrics'][f'precision@{k}'] = precision
            results['metrics'][f'recall@{k}'] = recall
            results['metrics'][f'f1@{k}'] = f1
        
        # 计算MRR
        mrr = self.calculate_mrr(retrieved_items, relevant_items)
        results['metrics']['mrr'] = mrr
        
        # 计算NDCG（如果提供了相关性评分）
        if relevance_scores:
            for k in k_values:
                ndcg = self.calculate_ndcg_at_k(retrieved_items, relevance_scores, k)
                results['metrics'][f'ndcg@{k}'] = ndcg
        
        # 计算平均相似度
        similarities = [item.get('similarity', item.get('score', 0)) for item in retrieved_items]
        if similarities:
            results['metrics']['avg_similarity'] = np.mean(similarities)
            results['metrics']['max_similarity'] = np.max(similarities)
            results['metrics']['min_similarity'] = np.min(similarities)
        
        return results


def run_accuracy_tests():
    """运行准确率测试"""
    print("=" * 80)
    print("msearch 检索准确率优化测试（真实版本）")
    print("=" * 80)
    print("参考业界标准方法，执行实际的向量搜索，评估检索准确率")
    print("=" * 80)
    
    try:
        from core.config.config_manager import ConfigManager
        from core.vector.vector_store import VectorStore
        
        # 初始化
        print("\n[1] 初始化系统...")
        config_manager = ConfigManager()
        config = config_manager.config
        
        vector_store = VectorStore(config)
        stats = vector_store.get_stats()
        print(f"✓ 向量存储初始化成功")
        print(f"  向量数量: {stats.get('vector_count', 0)}")
        print(f"  向量维度: {stats.get('vector_dimension', 'N/A')}")
        
        # 创建评估器
        evaluator = SearchAccuracyEvaluator()
        
        # 获取所有向量作为查询向量
        all_vectors = vector_store.table.to_pandas()
        
        print("\n[2] 执行向量搜索测试...")
        
        # 测试用例：使用每个向量作为查询，搜索最相似的向量
        all_results = []
        
        # 限制测试数量（避免过多）
        test_limit = min(5, len(all_vectors))
        
        for i in range(test_limit):
            query_row = all_vectors.iloc[i]
            query_vector = query_row['vector']
            query_file = query_row['file_name']
            query_path = query_row['file_path']
            
            print(f"\n测试 {i+1}/{test_limit}:")
            print(f"  查询文件: {query_file}")
            print(f"  查询路径: {query_path}")
            
            # 执行向量搜索（搜索最相似的向量）
            search_results = vector_store.search_vectors(
                query_vector=query_vector.tolist(),
                limit=10,
                similarity_threshold=None  # 不使用阈值，获取所有结果
            )
            
            # 评估检索质量
            # 相关项目：查询文件本身（使用file_id）
            query_file_id = query_row['file_id']
            relevant_items = {query_file_id}
            relevance_scores = {query_file_id: 1.0}
            
            result = evaluator.evaluate_search_quality(
                query=query_file,
                retrieved_items=search_results,
                relevant_items=relevant_items,
                relevance_scores=relevance_scores,
                k_values=[1, 5, 10]
            )
            
            # 打印关键指标
            metrics = result['metrics']
            print(f"  Precision@1: {metrics.get('precision@1', 0):.3f}")
            print(f"  Recall@1: {metrics.get('recall@1', 0):.3f}")
            print(f"  MRR: {metrics.get('mrr', 0):.3f}")
            print(f"  平均相似度: {metrics.get('avg_similarity', 0):.3f}")
            print(f"  最高相似度: {metrics.get('max_similarity', 0):.3f}")
            
            # 显示前5个结果
            print(f"  前5个结果:")
            for j, item in enumerate(search_results[:5], 1):
                is_relevant = item['file_path'] in relevant_items
                marker = "✓" if is_relevant else "✗"
                print(f"    [{j}] {marker} {item['file_name']} - 相似度: {item['similarity']:.3f}")
            
            all_results.append(result)
        
        # 计算整体指标
        print("\n[3] 计算整体指标...")
        
        # 计算平均指标
        avg_metrics = defaultdict(list)
        for result in all_results:
            for key, value in result['metrics'].items():
                avg_metrics[key].append(value)
        
        print("\n平均指标:")
        for key in sorted(avg_metrics.keys()):
            avg_value = np.mean(avg_metrics[key])
            std_value = np.std(avg_metrics[key])
            print(f"  {key}: {avg_value:.3f} ± {std_value:.3f}")
        
        # 评估结果
        print("\n" + "=" * 80)
        print("评估结果")
        print("=" * 80)
        
        # 根据业界标准评估
        precision_1 = np.mean(avg_metrics.get('precision@1', [0]))
        recall_1 = np.mean(avg_metrics.get('recall@1', [0]))
        mrr = np.mean(avg_metrics.get('mrr', [0]))
        ndcg_1 = np.mean(avg_metrics.get('ndcg@1', [0]))
        
        print(f"Precision@1: {precision_1:.3f}")
        print(f"Recall@1: {recall_1:.3f}")
        print(f"MRR: {mrr:.3f}")
        print(f"NDCG@1: {ndcg_1:.3f}")
        
        # 评估标准（参考业界基准）
        print("\n评估标准（业界基准）:")
        print("  优秀: Precision@1 ≥ 0.9, Recall@1 ≥ 0.9, MRR ≥ 0.9")
        print("  良好: Precision@1 ≥ 0.7, Recall@1 ≥ 0.7, MRR ≥ 0.7")
        print("  及格: Precision@1 ≥ 0.5, Recall@1 ≥ 0.5, MRR ≥ 0.5")
        
        # 判断等级
        if precision_1 >= 0.9 and recall_1 >= 0.9 and mrr >= 0.9:
            grade = "优秀"
        elif precision_1 >= 0.7 and recall_1 >= 0.7 and mrr >= 0.7:
            grade = "良好"
        elif precision_1 >= 0.5 and recall_1 >= 0.5 and mrr >= 0.5:
            grade = "及格"
        else:
            grade = "需要改进"
        
        print(f"\n综合评估: {grade}")
        
        # 详细建议
        print("\n改进建议:")
        if precision_1 < 0.9:
            print("  - 提高检索结果的相关性，检查相似度计算公式")
        if recall_1 < 0.9:
            print("  - 提高召回率，检查索引配置")
        if mrr < 0.9:
            print("  - 提高首个相关结果的排名，检查相似度排序")
        
        # 相似度计算验证
        print("\n[4] 相似度计算验证")
        for result in all_results:
            query = result['query']
            avg_sim = result['metrics'].get('avg_similarity', 0)
            max_sim = result['metrics'].get('max_similarity', 0)
            min_sim = result['metrics'].get('min_similarity', 0)
            print(f"  查询 '{query}':")
            print(f"    平均相似度: {avg_sim:.3f}")
            print(f"    最高相似度: {max_sim:.3f}")
            print(f"    最低相似度: {min_sim:.3f}")
            
            # 验证相似度计算是否正确
            if max_sim > 0.95:
                print(f"    ✓ 相似度计算正确（最高相似度>0.95）")
            elif max_sim > 0.8:
                print(f"    ✓ 相似度计算正常")
            else:
                print(f"    ⚠️  相似度可能需要优化")
        
        print("\n[5] 相似度计算正确性验证")
        print("  理论预期：自己检索自己，相似度应该接近1.0")
        print("  实际结果：")
        for result in all_results:
            first_result_similarity = result['metrics'].get('precision@1', 0)  # Precision@1 = 自己在第一个结果的概率
            print(f"    {result['query']}: Precision@1 = {first_result_similarity:.3f}")
            if first_result_similarity == 1.0:
                print(f"      ✓ 完美匹配")
            elif first_result_similarity > 0.8:
                print(f"      ✓ 匹配良好")
            else:
                print(f"      ⚠️  需要优化")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(run_accuracy_tests())
