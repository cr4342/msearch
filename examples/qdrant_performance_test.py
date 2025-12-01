"""
Qdrant向量存储性能测试
测试Qdrant向量存储的性能指标
"""

import asyncio
import numpy as np
import time
import sys
from pathlib import Path
import statistics

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.common.storage.vector_storage_manager import (
    VectorStorageManager, VectorType, VectorMetadata
)
from src.core.config_manager import get_config_manager


class PerformanceTest:
    """性能测试类"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.storage_manager = VectorStorageManager(self.config_manager)
        self.results = {}
    
    async def setup(self):
        """设置测试环境"""
        print("🔧 设置测试环境...")
        success = await self.storage_manager.initialize()
        if not success:
            raise RuntimeError("向量存储初始化失败")
        print("✅ 测试环境设置完成")
    
    async def cleanup(self):
        """清理测试环境"""
        print("🧹 清理测试环境...")
        await self.storage_manager.cleanup()
        print("✅ 测试环境清理完成")
    
    async def test_single_vector_storage_performance(self, num_vectors=1000):
        """测试单个向量存储性能"""
        print(f"\n📊 测试单个向量存储性能 ({num_vectors} 个向量)")
        print("-" * 50)
        
        times = []
        
        for i in range(num_vectors):
            # 创建测试向量
            vector_data = np.random.rand(512).astype(np.float32)
            metadata = VectorMetadata(
                file_id=f"perf_test_{i:06d}",
                file_path=f"/test/path/image_{i:06d}.jpg",
                file_name=f"image_{i:06d}.jpg",
                file_type=".jpg",
                file_size=1024 * 1024,
                created_at=time.time()
            )
            
            # 测量存储时间
            start_time = time.time()
            await self.storage_manager.store_vector(
                vector_type=VectorType.VISUAL,
                vector_data=vector_data,
                metadata=metadata
            )
            end_time = time.time()
            
            times.append(end_time - start_time)
            
            if (i + 1) % 100 == 0:
                print(f"   进度: {i + 1}/{num_vectors} ({(i + 1)/num_vectors*100:.1f}%)")
        
        # 计算性能指标
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        p95_time = np.percentile(times, 95)
        
        throughput = num_vectors / sum(times)
        
        self.results['single_storage'] = {
            'num_vectors': num_vectors,
            'avg_time_ms': avg_time * 1000,
            'min_time_ms': min_time * 1000,
            'max_time_ms': max_time * 1000,
            'median_time_ms': median_time * 1000,
            'p95_time_ms': p95_time * 1000,
            'throughput_ops_per_sec': throughput
        }
        
        print(f"✅ 单个向量存储性能测试完成")
        print(f"   平均时间: {avg_time*1000:.2f}ms")
        print(f"   吞吐量: {throughput:.2f} ops/sec")
        print(f"   P95延迟: {p95_time*1000:.2f}ms")
    
    async def test_batch_storage_performance(self, batch_sizes=[10, 50, 100, 500]):
        """测试批量存储性能"""
        print(f"\n📦 测试批量存储性能")
        print("-" * 50)
        
        for batch_size in batch_sizes:
            print(f"\n🔢 批量大小: {batch_size}")
            
            # 准备批量数据
            vectors_data = []
            for i in range(batch_size):
                vector_data = np.random.rand(512).astype(np.float32)
                metadata = VectorMetadata(
                    file_id=f"batch_test_{batch_size}_{i:03d}",
                    file_path=f"/test/path/batch_{batch_size}_{i:03d}.jpg",
                    file_name=f"batch_{batch_size}_{i:03d}.jpg",
                    file_type=".jpg",
                    file_size=1024 * 1024,
                    created_at=time.time()
                )
                vectors_data.append((VectorType.VISUAL, vector_data, metadata))
            
            # 测量批量存储时间
            start_time = time.time()
            await self.storage_manager.batch_store_vectors(vectors_data)
            end_time = time.time()
            
            batch_time = end_time - start_time
            throughput = batch_size / batch_time
            
            print(f"   批量时间: {batch_time*1000:.2f}ms")
            print(f"   批量吞吐量: {throughput:.2f} ops/sec")
            print(f"   平均每个向量: {batch_time*1000/batch_size:.2f}ms")
            
            self.results[f'batch_{batch_size}'] = {
                'batch_size': batch_size,
                'batch_time_ms': batch_time * 1000,
                'throughput_ops_per_sec': throughput,
                'avg_per_vector_ms': batch_time * 1000 / batch_size
            }
    
    async def test_search_performance(self, search_sizes=[10, 50, 100, 500]):
        """测试搜索性能"""
        print(f"\n🔍 测试搜索性能")
        print("-" * 50)
        
        # 先存储一些测试向量
        print("📦 准备测试数据...")
        test_vectors = []
        for i in range(1000):
            vector_data = np.random.rand(512).astype(np.float32)
            metadata = VectorMetadata(
                file_id=f"search_test_{i:04d}",
                file_path=f"/test/path/search_{i:04d}.jpg",
                file_name=f"search_{i:04d}.jpg",
                file_type=".jpg",
                file_size=1024 * 1024,
                created_at=time.time()
            )
            vector_id = await self.storage_manager.store_vector(
                vector_type=VectorType.VISUAL,
                vector_data=vector_data,
                metadata=metadata
            )
            test_vectors.append((vector_data, vector_id))
        
        print(f"✅ 准备了 {len(test_vectors)} 个测试向量")
        
        for search_size in search_sizes:
            print(f"\n🔍 搜索数量: {search_size}")
            
            # 随机选择查询向量
            query_vector, _ = test_vectors[np.random.randint(len(test_vectors))]
            
            # 测量搜索时间
            start_time = time.time()
            results = await self.storage_manager.search_vectors(
                vector_type=VectorType.VISUAL,
                query_vector=query_vector,
                limit=search_size,
                score_threshold=0.5
            )
            end_time = time.time()
            
            search_time = end_time - start_time
            throughput = search_size / search_time
            
            print(f"   搜索时间: {search_time*1000:.2f}ms")
            print(f"   搜索吞吐量: {throughput:.2f} queries/sec")
            print(f"   返回结果: {len(results)}")
            
            self.results[f'search_{search_size}'] = {
                'search_size': search_size,
                'search_time_ms': search_time * 1000,
                'throughput_queries_per_sec': throughput,
                'results_count': len(results)
            }
    
    async def test_hybrid_search_performance(self):
        """测试混合搜索性能"""
        print(f"\n🔄 测试混合搜索性能")
        print("-" * 50)
        
        # 准备不同类型的测试向量
        visual_vectors = []
        audio_vectors = []
        
        for i in range(500):
            # 视觉向量
            visual_vector = np.random.rand(512).astype(np.float32)
            visual_metadata = VectorMetadata(
                file_id=f"visual_test_{i:04d}",
                file_path=f"/test/path/visual_{i:04d}.jpg",
                file_name=f"visual_{i:04d}.jpg",
                file_type=".jpg",
                file_size=1024 * 1024,
                created_at=time.time()
            )
            visual_id = await self.storage_manager.store_vector(
                vector_type=VectorType.VISUAL,
                vector_data=visual_vector,
                metadata=visual_metadata
            )
            visual_vectors.append((visual_vector, visual_id))
            
            # 音频向量
            audio_vector = np.random.rand(512).astype(np.float32)
            audio_metadata = VectorMetadata(
                file_id=f"audio_test_{i:04d}",
                file_path=f"/test/path/audio_{i:04d}.mp3",
                file_name=f"audio_{i:04d}.mp3",
                file_type=".mp3",
                file_size=512 * 1024,
                created_at=time.time()
            )
            audio_id = await self.storage_manager.store_vector(
                vector_type=VectorType.AUDIO_MUSIC,
                vector_data=audio_vector,
                metadata=audio_metadata
            )
            audio_vectors.append((audio_vector, audio_id))
        
        print(f"✅ 准备了 {len(visual_vectors)} 个视觉向量和 {len(audio_vectors)} 个音频向量")
        
        # 测试不同权重配置
        weight_configs = [
            {'visual': 0.8, 'audio_music': 0.2},
            {'visual': 0.5, 'audio_music': 0.5},
            {'visual': 0.2, 'audio_music': 0.8}
        ]
        
        for i, weights in enumerate(weight_configs):
            print(f"\n⚖️ 权重配置 {i+1}: {weights}")
            
            # 随机选择查询向量
            visual_query, _ = visual_vectors[np.random.randint(len(visual_vectors))]
            audio_query, _ = audio_vectors[np.random.randint(len(audio_vectors))]
            
            query_vectors = {
                VectorType.VISUAL: visual_query,
                VectorType.AUDIO_MUSIC: audio_query
            }
            
            # 测量混合搜索时间
            start_time = time.time()
            results = await self.storage_manager.hybrid_search(
                query_vectors=query_vectors,
                weights=weights,
                limit=100,
                score_threshold=0.4
            )
            end_time = time.time()
            
            search_time = end_time - start_time
            throughput = len(results) / search_time if search_time > 0 else 0
            
            print(f"   搜索时间: {search_time*1000:.2f}ms")
            print(f"   返回结果: {len(results)}")
            print(f"   吞吐量: {throughput:.2f} results/sec")
            
            self.results[f'hybrid_weights_{i+1}'] = {
                'weights': weights,
                'search_time_ms': search_time * 1000,
                'results_count': len(results),
                'throughput_results_per_sec': throughput
            }
    
    def print_performance_summary(self):
        """打印性能测试摘要"""
        print("\n" + "="*60)
        print("📊 性能测试摘要")
        print("="*60)
        
        # 单个向量存储性能
        if 'single_storage' in self.results:
            single = self.results['single_storage']
            print(f"\n📝 单个向量存储 ({single['num_vectors']} 个向量):")
            print(f"   平均延迟: {single['avg_time_ms']:.2f}ms")
            print(f"   P95延迟: {single['p95_time_ms']:.2f}ms")
            print(f"   吞吐量: {single['throughput_ops_per_sec']:.2f} ops/sec")
        
        # 批量存储性能
        print(f"\n📦 批量存储性能:")
        for key, result in self.results.items():
            if key.startswith('batch_'):
                print(f"   {result['batch_size']} 个向量: {result['throughput_ops_per_sec']:.2f} ops/sec")
        
        # 搜索性能
        print(f"\n🔍 搜索性能:")
        for key, result in self.results.items():
            if key.startswith('search_'):
                print(f"   {result['search_size']} 个结果: {result['throughput_queries_per_sec']:.2f} queries/sec")
        
        # 混合搜索性能
        print(f"\n🔄 混合搜索性能:")
        for key, result in self.results.items():
            if key.startswith('hybrid_'):
                weights = result['weights']
                print(f"   权重配置 {key.split('_')[-1]}: {weights}")
                print(f"   吞吐量: {result['throughput_results_per_sec']:.2f} results/sec")
        
        print("\n" + "="*60)


async def main():
    """主函数"""
    print("🚀 Qdrant向量存储性能测试")
    print("="*60)
    
    perf_test = PerformanceTest()
    
    try:
        # 设置测试环境
        await perf_test.setup()
        
        # 运行性能测试
        await perf_test.test_single_vector_storage_performance(1000)
        await perf_test.test_batch_storage_performance([10, 50, 100, 500])
        await perf_test.test_search_performance([10, 50, 100, 500])
        await perf_test.test_hybrid_search_performance()
        
        # 打印性能摘要
        perf_test.print_performance_summary()
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试环境
        await perf_test.cleanup()


if __name__ == "__main__":
    # 运行性能测试
    asyncio.run(main())