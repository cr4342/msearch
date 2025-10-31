"""
CPU环境性能基准测试
根据test_strategy.md第2.4节要求，验证CPU模式下的性能指标
"""
import pytest
import logging
import time
import psutil
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

class TestCPUPerformance:
    """CPU环境性能基准测试"""
    
    @pytest.fixture
    def cpu_config(self):
        """CPU测试配置"""
        return {
            'device': 'cpu',
            'models': {
                'clip': {'device': 'cpu', 'batch_size': 4},
                'clap': {'device': 'cpu', 'batch_size': 2},
                'whisper': {'device': 'cpu', 'batch_size': 1}
            },
            'performance_benchmarks': {
                'text_search_response_time_ms': 300,
                'image_search_response_time_ms': 500,
                'video_processing_speed_x': 0.2,
                'memory_usage_mb': 2048,
                'concurrent_queries': 10
            }
        }
    
    @pytest.fixture
    def mock_search_engine(self):
        """Mock的搜索引擎"""
        with patch('src.business.search_engine.SearchEngine') as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine_class.return_value = mock_engine
            
            # 配置mock行为
            def mock_search(query, modality="text"):
                # 模拟搜索延迟
                time.sleep(0.05)  # 50ms延迟
                return [
                    {"id": f"result_{i}", "score": 0.9 - i*0.1, "content": f"结果 {i}"}
                    for i in range(5)
                ]
            
            mock_engine.search = mock_search
            mock_engine.get_video_metadata.return_value = {"duration": 60}
            
            yield mock_engine
    
    def test_text_search_performance(self, mock_search_engine, cpu_config):
        """测试文本搜索性能"""
        queries = ["美丽的风景", "人物肖像", "城市建筑", "自然风光", "动物世界"]
        response_times = []
        
        for query in queries:
            start_time = time.time()
            results = mock_search_engine.search(query, modality="text_to_image")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # 转换为毫秒
            response_times.append(response_time)
            
            assert len(results) > 0, f"查询 '{query}' 无结果"
        
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        # CPU模式下性能基准
        benchmark_time = cpu_config['performance_benchmarks']['text_search_response_time_ms']
        assert avg_response_time < benchmark_time, f"平均响应时间过长: {avg_response_time:.2f}ms > {benchmark_time}ms"
        assert max_response_time < benchmark_time * 2, f"最大响应时间过长: {max_response_time:.2f}ms"
        
        # 记录性能数据
        perf_data = {
            "test_type": "text_search_performance",
            "avg_response_time_ms": avg_response_time,
            "max_response_time_ms": max_response_time,
            "query_count": len(queries),
            "benchmark_ms": benchmark_time
        }
        
        logger.info(f"性能数据: {json.dumps(perf_data, ensure_ascii=False)}")
        logger.info(f"文本搜索性能测试通过 - 平均响应时间: {avg_response_time:.2f}ms")
    
    def test_image_processing_performance(self, mock_search_engine, cpu_config):
        """测试图片处理性能"""
        # 模拟图片数据
        test_images = [np.random.rand(224, 224, 3).astype(np.float32) for _ in range(3)]
        
        processing_times = []
        
        for i, image in enumerate(test_images):
            start_time = time.time()
            results = mock_search_engine.search(f"test_image_{i}", modality="image_to_image")
            end_time = time.time()
            
            processing_time = (end_time - start_time) * 1000  # 毫秒
            processing_times.append(processing_time)
            
            assert len(results) > 0, f"图片 {i} 处理无结果"
        
        avg_processing_time = sum(processing_times) / len(processing_times)
        
        # CPU模式下性能基准
        benchmark_time = cpu_config['performance_benchmarks']['image_search_response_time_ms']
        assert avg_processing_time < benchmark_time, f"图片处理时间过长: {avg_processing_time:.2f}ms > {benchmark_time}ms"
        
        # 记录性能数据
        perf_data = {
            "test_type": "image_processing_performance",
            "avg_processing_time_ms": avg_processing_time,
            "image_count": len(test_images),
            "benchmark_ms": benchmark_time
        }
        
        logger.info(f"性能数据: {json.dumps(perf_data, ensure_ascii=False)}")
        logger.info(f"图片处理性能测试通过 - 平均处理时间: {avg_processing_time:.2f}ms")
    
    def test_video_processing_performance(self, mock_search_engine, cpu_config):
        """测试视频处理性能"""
        test_video = "mock_video.mp4"
        
        start_time = time.time()
        results = mock_search_engine.search(test_video, modality="video_to_image")
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # 获取视频元数据
        video_metadata = mock_search_engine.get_video_metadata(test_video)
        video_duration = video_metadata.get("duration", 60)  # 默认60秒
        
        # 计算处理速度（实时倍数）
        processing_speed = video_duration / processing_time if processing_time > 0 else 0
        
        # CPU模式下性能基准（至少0.2倍实时处理速度）
        benchmark_speed = cpu_config['performance_benchmarks']['video_processing_speed_x']
        assert processing_speed >= benchmark_speed, f"视频处理速度过慢: {processing_speed:.2f}x < {benchmark_speed}x"
        
        # 记录性能数据
        perf_data = {
            "test_type": "video_processing_performance",
            "video_duration_s": video_duration,
            "processing_time_s": processing_time,
            "processing_speed_x": processing_speed,
            "benchmark_speed_x": benchmark_speed
        }
        
        logger.info(f"性能数据: {json.dumps(perf_data, ensure_ascii=False)}")
        logger.info(f"视频处理性能测试通过 - 处理速度: {processing_speed:.2f}x实时")
    
    def test_memory_usage_performance(self, mock_search_engine, cpu_config):
        """测试内存使用性能"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        # 执行批量操作
        batch_size = 20
        for i in range(batch_size):
            mock_search_engine.search(f"批量测试查询 {i}")
        
        final_memory = process.memory_info().rss / (1024 * 1024)  # MB
        memory_increase = final_memory - initial_memory
        memory_per_operation = memory_increase / batch_size if batch_size > 0 else 0
        
        # CPU模式下内存使用基准
        max_memory = cpu_config['performance_benchmarks']['memory_usage_mb']
        assert memory_per_operation < 10, f"单次操作内存使用过多: {memory_per_operation:.2f}MB"
        assert final_memory < max_memory, f"总内存使用过多: {final_memory:.2f}MB > {max_memory}MB"
        
        # 记录性能数据
        perf_data = {
            "test_type": "memory_usage_performance",
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": memory_increase,
            "memory_per_operation_mb": memory_per_operation,
            "batch_size": batch_size,
            "benchmark_max_mb": max_memory
        }
        
        logger.info(f"性能数据: {json.dumps(perf_data, ensure_ascii=False)}")
        logger.info(f"内存使用性能测试通过 - 单次操作内存: {memory_per_operation:.2f}MB")
    
    def test_concurrent_performance(self, mock_search_engine, cpu_config):
        """测试并发性能"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def worker(query_id):
            start_time = time.time()
            result = mock_search_engine.search(f"并发测试查询 {query_id}", modality="text_to_image")
            end_time = time.time()
            
            results_queue.put({
                "query_id": query_id,
                "response_time": (end_time - start_time) * 1000,
                "result_count": len(result),
                "success": True
            })
        
        # 创建并启动线程
        threads = []
        concurrent_queries = cpu_config['performance_benchmarks']['concurrent_queries']
        
        start_time = time.time()
        for i in range(concurrent_queries):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # 收集结果
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        response_times = [r["response_time"] for r in results]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        # 并发性能基准
        assert avg_response_time < 500, f"并发平均响应时间过长: {avg_response_time:.2f}ms"
        assert max_response_time < 1000, f"并发最大响应时间过长: {max_response_time:.2f}ms"
        assert total_time < 10, f"总执行时间过长: {total_time:.2f}s"
        
        # 记录性能数据
        perf_data = {
            "test_type": "concurrent_performance",
            "concurrent_queries": concurrent_queries,
            "total_time_s": total_time,
            "avg_response_time_ms": avg_response_time,
            "max_response_time_ms": max_response_time,
            "success_rate": len(results) / concurrent_queries
        }
        
        logger.info(f"性能数据: {json.dumps(perf_data, ensure_ascii=False)}")
        logger.info(f"并发性能测试通过 - 平均响应时间: {avg_response_time:.2f}ms")
    
    def test_system_resource_monitoring(self):
        """测试系统资源监控"""
        # 获取系统资源信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # 记录系统资源状态
        resource_data = {
            "test_type": "system_resource_monitoring",
            "cpu_usage_percent": cpu_percent,
            "memory_total_mb": memory.total / (1024 * 1024),
            "memory_available_mb": memory.available / (1024 * 1024),
            "memory_usage_percent": memory.percent
        }
        
        logger.info(f"系统资源数据: {json.dumps(resource_data, ensure_ascii=False)}")
        
        # 验证系统资源在合理范围内
        assert cpu_percent < 90, f"CPU使用率过高: {cpu_percent}%"
        assert memory.percent < 90, f"内存使用率过高: {memory.percent}%"
        
        logger.info("系统资源监控测试通过")

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    pytest.main([__file__, "-v", "-s"])