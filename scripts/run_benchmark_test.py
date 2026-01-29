#!/usr/bin/env python3
"""
运行基准测试
使用现有的测试数据评估检索准确性
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
src_root = project_root / "src"
sys.path.insert(0, str(src_root))
sys.path.insert(0, str(project_root))

# 设置离线环境变量
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

from core.config.config_manager import ConfigManager
from core.vector.vector_store import VectorStore
from core.embedding.embedding_engine import EmbeddingEngine


class BenchmarkTester:
    """基准测试器"""
    
    def __init__(self):
        self.config = None
        self.vector_store = None
        self.embedding_engine = None
        self.test_data_dir = Path("testdata")
        
    async def initialize(self):
        """初始化组件"""
        logger.info("初始化测试环境...")
        
        # 加载配置
        config_manager = ConfigManager()
        self.config = config_manager.get_all()
        
        # 初始化向量存储
        vector_db_path = self.config.get('database', {}).get('vector_db_path', 'data/database/lancedb')
        vector_store_config = {
            'data_dir': vector_db_path,
            'collection_name': 'unified_vectors',
            'index_type': 'ivf_pq',
            'num_partitions': 128,
            'vector_dimension': 512
        }
        self.vector_store = VectorStore(vector_store_config)
        self.vector_store.initialize()
        logger.info("✓ 向量存储初始化完成")
        
        # 初始化向量化引擎
        self.embedding_engine = EmbeddingEngine(self.config)
        await self.embedding_engine.initialize()
        logger.info("✓ 向量化引擎初始化完成")
        
    def get_test_images(self) -> List[Path]:
        """获取测试图像列表"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
        images = []
        for ext in image_extensions:
            images.extend(self.test_data_dir.glob(f'*{ext}'))
        return images
    
    async def test_text_to_image_retrieval(self) -> Dict:
        """
        测试文本到图像检索
        使用预定义的查询测试是否能正确检索到对应的图像
        """
        logger.info("\n" + "="*70)
        logger.info("测试1: 文本到图像检索")
        logger.info("="*70)
        
        # 定义测试用例：(查询文本, 期望的图像文件名, 描述)
        test_cases = [
            ("周星驰", "周星驰.jpg", "人物名称"),
            ("人物肖像", "周星驰.jpg", "人物描述"),
            ("自然风景", "8_3.jpg", "风景描述"),
            ("建筑物", "18.jpg", "建筑描述"),
            ("小猫", "OIP-C (5).jpg", "动物描述"),
            ("可爱动物", "OIP-C (5).jpg", "动物描述2"),
            ("城市夜景", "OIP-C (6).jpg", "夜景描述"),
            ("美食", "OIP-C (6).jpg", "食物描述"),
        ]
        
        results = {
            'total': len(test_cases),
            'correct_at_1': 0,
            'correct_at_3': 0,
            'correct_at_5': 0,
            'details': []
        }
        
        for query, expected_file, description in test_cases:
            logger.info(f"\n查询: '{query}' ({description})")
            logger.info(f"  期望文件: {expected_file}")
            
            # 生成查询向量
            query_embedding = await self.embedding_engine.embed_text(query)
            
            # 执行搜索
            search_results = self.vector_store.search(query_embedding, limit=5)
            
            if search_results:
                # 获取返回的文件名
                returned_files = [Path(r.get('file_path', '')).name for r in search_results]
                similarities = [r.get('similarity', 0) for r in search_results]
                
                logger.info(f"  返回文件: {returned_files}")
                logger.info(f"  相似度: {[f'{s:.4f}' for s in similarities]}")
                
                # 检查是否找到期望文件
                found_at = None
                for i, fname in enumerate(returned_files):
                    if fname == expected_file:
                        found_at = i + 1
                        break
                
                if found_at:
                    logger.info(f"  ✓ 期望文件排名第 {found_at}")
                    if found_at == 1:
                        results['correct_at_1'] += 1
                    if found_at <= 3:
                        results['correct_at_3'] += 1
                    if found_at <= 5:
                        results['correct_at_5'] += 1
                else:
                    logger.info(f"  ✗ 未找到期望文件")
                
                results['details'].append({
                    'query': query,
                    'expected': expected_file,
                    'found_at': found_at,
                    'returned_files': returned_files,
                    'similarities': similarities
                })
            else:
                logger.info(f"  ✗ 无返回结果")
                results['details'].append({
                    'query': query,
                    'expected': expected_file,
                    'found_at': None,
                    'returned_files': [],
                    'similarities': []
                })
        
        # 计算Recall@K
        results['recall_at_1'] = results['correct_at_1'] / results['total']
        results['recall_at_3'] = results['correct_at_3'] / results['total']
        results['recall_at_5'] = results['correct_at_5'] / results['total']
        results['mean_recall'] = (results['recall_at_1'] + results['recall_at_3'] + results['recall_at_5']) / 3
        
        return results
    
    async def test_image_to_text_retrieval(self) -> Dict:
        """
        测试图像到文本检索
        使用图像搜索，检查是否能找到相似的图像
        """
        logger.info("\n" + "="*70)
        logger.info("测试2: 图像到文本检索 (图像相似度)")
        logger.info("="*70)
        
        # 获取测试图像
        test_images = self.get_test_images()[:5]  # 测试前5张图像
        
        results = {
            'total': len(test_images),
            'correct_at_1': 0,
            'correct_at_3': 0,
            'correct_at_5': 0,
            'details': []
        }
        
        for test_image in test_images:
            logger.info(f"\n查询图像: {test_image.name}")
            
            # 生成图像向量
            query_embedding = await self.embedding_engine.embed_image(str(test_image))
            
            # 执行搜索
            search_results = self.vector_store.search(query_embedding, limit=5)
            
            if search_results:
                returned_files = [Path(r.get('file_path', '')).name for r in search_results]
                similarities = [r.get('similarity', 0) for r in search_results]
                
                logger.info(f"  返回文件: {returned_files}")
                logger.info(f"  相似度: {[f'{s:.4f}' for s in similarities]}")
                
                # 检查是否找到自身（排名第1且相似度接近1.0）
                found_at = None
                for i, fname in enumerate(returned_files):
                    if fname == test_image.name:
                        found_at = i + 1
                        break
                
                if found_at:
                    logger.info(f"  ✓ 自身文件排名第 {found_at}")
                    if found_at == 1:
                        results['correct_at_1'] += 1
                    if found_at <= 3:
                        results['correct_at_3'] += 1
                    if found_at <= 5:
                        results['correct_at_5'] += 1
                else:
                    logger.info(f"  ✗ 未找到自身文件")
                
                results['details'].append({
                    'query_image': test_image.name,
                    'found_at': found_at,
                    'top_similarity': similarities[0] if similarities else 0,
                    'returned_files': returned_files
                })
            else:
                logger.info(f"  ✗ 无返回结果")
                results['details'].append({
                    'query_image': test_image.name,
                    'found_at': None,
                    'top_similarity': 0,
                    'returned_files': []
                })
        
        # 计算Recall@K
        results['recall_at_1'] = results['correct_at_1'] / results['total'] if results['total'] > 0 else 0
        results['recall_at_3'] = results['correct_at_3'] / results['total'] if results['total'] > 0 else 0
        results['recall_at_5'] = results['correct_at_5'] / results['total'] if results['total'] > 0 else 0
        results['mean_recall'] = (results['recall_at_1'] + results['recall_at_3'] + results['recall_at_5']) / 3
        
        return results
    
    async def test_similarity_distribution(self) -> Dict:
        """
        测试相似度分布
        检查相似度分数的分布情况
        """
        logger.info("\n" + "="*70)
        logger.info("测试3: 相似度分布分析")
        logger.info("="*70)
        
        # 使用几个标准查询进行测试
        test_queries = ["人物", "风景", "建筑", "动物", "食物"]
        all_similarities = []
        
        for query in test_queries:
            query_embedding = await self.embedding_engine.embed_text(query)
            search_results = self.vector_store.search(query_embedding, limit=10)
            
            similarities = [r.get('similarity', 0) for r in search_results]
            all_similarities.extend(similarities)
            
            logger.info(f"查询 '{query}': 平均相似度 = {sum(similarities)/len(similarities):.4f}" if similarities else "无结果")
        
        if all_similarities:
            import statistics
            results = {
                'count': len(all_similarities),
                'mean': statistics.mean(all_similarities),
                'median': statistics.median(all_similarities),
                'min': min(all_similarities),
                'max': max(all_similarities),
                'stdev': statistics.stdev(all_similarities) if len(all_similarities) > 1 else 0
            }
            
            logger.info(f"\n相似度统计:")
            logger.info(f"  样本数: {results['count']}")
            logger.info(f"  平均值: {results['mean']:.4f}")
            logger.info(f"  中位数: {results['median']:.4f}")
            logger.info(f"  最小值: {results['min']:.4f}")
            logger.info(f"  最大值: {results['max']:.4f}")
            logger.info(f"  标准差: {results['stdev']:.4f}")
        else:
            results = {'error': '无相似度数据'}
        
        return results
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("\n" + "="*70)
        logger.info("开始基准测试")
        logger.info("="*70)
        
        # 初始化
        await self.initialize()
        
        # 获取数据库统计
        all_records = self.vector_store.table.to_pandas()
        unique_files = all_records[all_records['file_path'] != '']['file_path'].nunique()
        logger.info(f"\n向量数据库统计:")
        logger.info(f"  总记录数: {len(all_records)}")
        logger.info(f"  唯一文件数: {unique_files}")
        
        # 运行测试
        t2i_results = await self.test_text_to_image_retrieval()
        i2t_results = await self.test_image_to_text_retrieval()
        sim_dist = await self.test_similarity_distribution()
        
        # 汇总结果
        final_results = {
            'test_info': {
                'total_vectors': len(all_records),
                'unique_files': int(unique_files),
                'test_date': str(Path().stat().st_mtime)
            },
            'text_to_image_retrieval': t2i_results,
            'image_to_text_retrieval': i2t_results,
            'similarity_distribution': sim_dist
        }
        
        # 打印总结
        logger.info("\n" + "="*70)
        logger.info("基准测试结果总结")
        logger.info("="*70)
        
        logger.info("\n【文本到图像检索】")
        logger.info(f"  测试用例数: {t2i_results['total']}")
        logger.info(f"  Recall@1: {t2i_results['recall_at_1']:.4f} ({t2i_results['recall_at_1']*100:.2f}%)")
        logger.info(f"  Recall@3: {t2i_results['recall_at_3']:.4f} ({t2i_results['recall_at_3']*100:.2f}%)")
        logger.info(f"  Recall@5: {t2i_results['recall_at_5']:.4f} ({t2i_results['recall_at_5']*100:.2f}%)")
        logger.info(f"  Mean Recall: {t2i_results['mean_recall']:.4f} ({t2i_results['mean_recall']*100:.2f}%)")
        
        logger.info("\n【图像到文本检索】")
        logger.info(f"  测试图像数: {i2t_results['total']}")
        logger.info(f"  Recall@1: {i2t_results['recall_at_1']:.4f} ({i2t_results['recall_at_1']*100:.2f}%)")
        logger.info(f"  Recall@3: {i2t_results['recall_at_3']:.4f} ({i2t_results['recall_at_3']*100:.2f}%)")
        logger.info(f"  Recall@5: {i2t_results['recall_at_5']:.4f} ({i2t_results['recall_at_5']*100:.2f}%)")
        logger.info(f"  Mean Recall: {i2t_results['mean_recall']:.4f} ({i2t_results['mean_recall']*100:.2f}%)")
        
        logger.info("\n【相似度分布】")
        if 'mean' in sim_dist:
            logger.info(f"  平均相似度: {sim_dist['mean']:.4f}")
            logger.info(f"  相似度范围: [{sim_dist['min']:.4f}, {sim_dist['max']:.4f}]")
        
        # 保存结果
        output_dir = Path("testdata/benchmark_results")
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / 'benchmark_results.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n✓ 测试结果保存到: {output_path}")
        
        # 关闭组件
        self.vector_store.close()
        await self.embedding_engine.shutdown()
        
        logger.info("\n" + "="*70)
        logger.info("基准测试完成")
        logger.info("="*70)
        
        return final_results


async def main():
    """主函数"""
    tester = BenchmarkTester()
    await tester.run_all_tests()


if __name__ == '__main__':
    asyncio.run(main())
