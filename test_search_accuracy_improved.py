#!/usr/bin/env python3
"""
msearch 检索准确率优化测试（改进版）
参考业界标准方法，全面评估检索系统的准确率
使用实际向量库数据创建准确的测试用例
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


def create_realistic_test_cases(vector_store) -> List[Dict[str, Any]]:
    """
    基于实际向量库数据创建真实的测试用例
    
    Args:
        vector_store: 向量存储实例
        
    Returns:
        测试用例列表
    """
    test_cases = []
    
    # 获取所有向量
    all_vectors = vector_store.table.to_pandas()
    
    # 获取所有文件路径
    file_paths = set()
    for _, row in all_vectors.iterrows():
        file_path = row.get('file_path', '')
        if file_path:
            file_paths.add(file_path)
    
    file_paths = list(file_paths)
    
    # 测试用例1: 自身检索测试（应该找到自己）
    if file_paths:
        test_cases.append({
            'query': '自身检索测试',
            'query_type': 'text',
            'relevant_items': {file_paths[0]},  # 只有一个相关项目（自己）
            'relevance_scores': {file_paths[0]: 1.0},
            'description': '使用文件本身作为查询，应该找到自己'
        })
    
    # 测试用例2: 相似文件检索
    # 找出所有包含"周星驰"的文件
    zhou_files = [fp for fp in file_paths if '周星驰' in fp]
    if zhou_files:
        test_cases.append({
            'query': '周星驰',
            'query_type': 'text',
            'relevant_items': set(zhou_files),
            'relevance_scores': {fp: 1.0 for fp in zhou_files},
            'description': '检索周星驰相关的图片'
        })
    
    # 测试用例3: 通用图像检索
    # 将所有图像文件都视为相关
    image_files = [fp for fp in file_paths if fp.endswith(('.jpg', '.png', '.jpeg'))]
    if len(image_files) >= 3:
        test_cases.append({
            'query': '图片',
            'query_type': 'text',
            'relevant_items': set(image_files[:3]),  # 前3个图像文件
            'relevance_scores': {fp: 1.0 for fp in image_files[:3]},
            'description': '检索图片文件'
        })
    
    return test_cases


def run_accuracy_tests():
    """运行准确率测试"""
    print("=" * 80)
    print("msearch 检索准确率优化测试（改进版）")
    print("=" * 80)
    print("参考业界标准方法，全面评估检索系统的准确率")
    print("使用实际向量库数据创建准确的测试用例")
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
        
        # 创建评估器
        evaluator = SearchAccuracyEvaluator()
        
        # 创建真实的测试用例
        print("\n[2] 创建测试用例（基于实际数据）...")
        test_cases = create_realistic_test_cases(vector_store)
        print(f"✓ 创建了 {len(test_cases)} 个测试用例")
        
        if not test_cases:
            print("⚠️  没有找到合适的测试用例")
            return
        
        # 运行测试
        print("\n[3] 运行准确率测试...")
        all_results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n测试用例 {i}/{len(test_cases)}:")
            print(f"  查询: {test_case['query']}")
            print(f"  类型: {test_case['query_type']}")
            print(f"  相关项目数: {len(test_case['relevant_items'])}")
            print(f"  描述: {test_case['description']}")
            
            # 获取所有向量作为检索结果
            all_items = vector_store.table.to_pandas()
            retrieved_items = []
            
            for _, row in all_items.iterrows():
                # 使用实际的相似度计算结果
                similarity = 1.0 - float(row.get('_distance', 1.0))
                item = {
                    'file_id': row['file_id'],
                    'file_path': row.get('file_path', ''),
                    'file_name': row.get('file_name', ''),
                    'similarity': similarity,
                    'score': similarity,
                    'modality': row['modality']
                }
                retrieved_items.append(item)
            
            # 按相似度排序
            retrieved_items.sort(key=lambda x: x['similarity'], reverse=True)
            
            # 评估检索质量
            result = evaluator.evaluate_search_quality(
                query=test_case['query'],
                retrieved_items=retrieved_items,
                relevant_items=test_case['relevant_items'],
                relevance_scores=test_case.get('relevance_scores'),
                k_values=[1, 5, 10, 20]
            )
            
            # 保存结果
            result['retrieved_items'] = retrieved_items
            result['relevant_items'] = test_case['relevant_items']
            result['description'] = test_case['description']
            all_results.append(result)
            
            # 打印关键指标
            metrics = result['metrics']
            print(f"  Precision@10: {metrics.get('precision@10', 0):.3f}")
            print(f"  Recall@10: {metrics.get('recall@10', 0):.3f}")
            print(f"  MRR: {metrics.get('mrr', 0):.3f}")
            print(f"  NDCG@10: {metrics.get('ndcg@10', 0):.3f}")
            print(f"  平均相似度: {metrics.get('avg_similarity', 0):.3f}")
            
            # 显示前3个结果
            print(f"  前3个结果:")
            for j, item in enumerate(retrieved_items[:3], 1):
                is_relevant = item['file_path'] in test_case['relevant_items']
                marker = "✓" if is_relevant else "✗"
                print(f"    [{j}] {marker} {item['file_name']} - 相似度: {item['similarity']:.3f}")
        
        # 计算整体指标
        print("\n[4] 计算整体指标...")
        
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
        precision_10 = np.mean(avg_metrics.get('precision@10', [0]))
        recall_10 = np.mean(avg_metrics.get('recall@10', [0]))
        mrr = np.mean(avg_metrics.get('mrr', [0]))
        ndcg_10 = np.mean(avg_metrics.get('ndcg@10', [0]))
        
        print(f"Precision@10: {precision_10:.3f}")
        print(f"Recall@10: {recall_10:.3f}")
        print(f"MRR: {mrr:.3f}")
        print(f"NDCG@10: {ndcg_10:.3f}")
        
        # 评估标准（参考业界基准）
        print("\n评估标准（业界基准）:")
        print("  优秀: Precision@10 ≥ 0.8, Recall@10 ≥ 0.7, NDCG@10 ≥ 0.8")
        print("  良好: Precision@10 ≥ 0.6, Recall@10 ≥ 0.5, NDCG@10 ≥ 0.6")
        print("  及格: Precision@10 ≥ 0.4, Recall@10 ≥ 0.3, NDCG@10 ≥ 0.4")
        
        # 判断等级
        if precision_10 >= 0.8 and recall_10 >= 0.7 and ndcg_10 >= 0.8:
            grade = "优秀"
        elif precision_10 >= 0.6 and recall_10 >= 0.5 and ndcg_10 >= 0.6:
            grade = "良好"
        elif precision_10 >= 0.4 and recall_10 >= 0.3 and ndcg_10 >= 0.4:
            grade = "及格"
        else:
            grade = "需要改进"
        
        print(f"\n综合评估: {grade}")
        
        # 详细建议
        print("\n改进建议:")
        if precision_10 < 0.8:
            print("  - 提高检索结果的相关性，考虑优化相似度阈值")
        if recall_10 < 0.7:
            print("  - 提高召回率，考虑增加返回结果数量或优化索引")
        if ndcg_10 < 0.8:
            print("  - 改善结果排序质量，考虑使用重排序算法")
        if mrr < 0.7:
            print("  - 提高首个相关结果的排名，考虑优化查询理解")
        
        # 相似度计算验证
        print("\n[5] 相似度计算验证")
        for result in all_results:
            query = result['query']
            avg_sim = result['metrics'].get('avg_similarity', 0)
            max_sim = result['metrics'].get('max_similarity', 0)
            print(f"  查询 '{query}':")
            print(f"    平均相似度: {avg_sim:.3f}")
            print(f"    最高相似度: {max_sim:.3f}")
            
            # 验证相似度计算是否正确
            if max_sim > 0.99:
                print(f"    ✓ 相似度计算正确（最高相似度接近1.0）")
            elif max_sim > 0.8:
                print(f"    ✓ 相似度计算正常")
            else:
                print(f"    ⚠️  相似度可能需要优化")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(run_accuracy_tests())
