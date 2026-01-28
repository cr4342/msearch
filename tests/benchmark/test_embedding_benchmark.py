"""
性能基准测试：向量化性能
测试图像、文本、音频向量化性能
"""

import pytest
import tempfile
import shutil
import time
import json
from pathlib import Path
from PIL import Image

from src.core.config.config_manager import ConfigManager
from src.core.embedding.embedding_engine import EmbeddingEngine


@pytest.fixture(scope="module")
def temp_dir():
    """创建临时目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="module")
def test_images_dir(temp_dir):
    """创建测试图像目录"""
    images_dir = Path(temp_dir) / "test_images"
    images_dir.mkdir(exist_ok=True)
    
    # 创建不同尺寸的测试图像
    sizes = [(100, 100), (500, 500), (1000, 1000), (1920, 1080)]
    for idx, (width, height) in enumerate(sizes):
        img = Image.new('RGB', (width, height), color=(idx * 50, 100, 255 - idx * 50))
        img.save(images_dir / f"test_image_{width}x{height}.jpg")
    
    return images_dir


@pytest.fixture(scope="module")
def config_manager():
    """创建配置管理器（使用默认配置）"""
    return ConfigManager()


@pytest.fixture(scope="module")
def embedding_engine(config_manager):
    """创建向量化引擎"""
    engine = EmbeddingEngine(config=config_manager.config)
    engine.initialize()
    return engine


@pytest.fixture(scope="module")
def benchmark_results(temp_dir):
    """基准测试结果"""
    return {
        "image_embedding": [],
        "text_embedding": [],
        "batch_embedding": []
    }


class TestEmbeddingBenchmark:
    """向量化性能基准测试"""
    
    def test_single_image_embedding_performance(self, test_images_dir, embedding_engine, benchmark_results):
        """测试单图像向量化性能"""
        image_files = list(test_images_dir.glob("*.jpg"))
        
        for image_file in image_files:
            # 预热
            embedding_engine.embed_image(str(image_file))
            
            # 测量性能
            start_time = time.time()
            vector = embedding_engine.embed_image(str(image_file))
            end_time = time.time()
            
            embedding_time = end_time - start_time
            
            result = {
                "image_file": image_file.name,
                "image_size": f"{image_file.stat().st_size / 1024:.2f}KB",
                "embedding_time": f"{embedding_time:.4f}s",
                "vector_dim": len(vector) if vector else 0
            }
            
            benchmark_results["image_embedding"].append(result)
            print(f"{image_file.name}: {embedding_time:.4f}s")
            
            # 验证结果
            assert vector is not None, "向量不应为None"
            assert len(vector) > 0, "向量维度应该>0"
    
    def test_text_embedding_performance(self, embedding_engine, benchmark_results):
        """测试文本向量化性能"""
        test_texts = [
            "短文本",
            "这是一个中等长度的测试文本，用于测试文本向量化性能。",
            "这是一个较长的测试文本，包含更多的内容和信息，用于测试文本向量化性能。这个文本应该能够提供更全面的测试结果，帮助我们评估文本向量化的性能表现。"
        ]
        
        for idx, text in enumerate(test_texts):
            # 预热
            embedding_engine.embed_text(text)
            
            # 测量性能
            start_time = time.time()
            vector = embedding_engine.embed_text(text)
            end_time = time.time()
            
            embedding_time = end_time - start_time
            
            result = {
                "text_index": idx,
                "text_length": len(text),
                "embedding_time": f"{embedding_time:.4f}s",
                "vector_dim": len(vector) if vector else 0
            }
            
            benchmark_results["text_embedding"].append(result)
            print(f"文本{idx} (长度{len(text)}): {embedding_time:.4f}s")
            
            # 验证结果
            assert vector is not None, "向量不应为None"
            assert len(vector) > 0, "向量维度应该>0"
    
    def test_batch_image_embedding_performance(self, test_images_dir, embedding_engine, benchmark_results):
        """测试批量图像向量化性能"""
        image_files = list(test_images_dir.glob("*.jpg"))
        
        # 测试不同批量大小
        batch_sizes = [1, 2, 4]
        
        for batch_size in batch_sizes:
            # 预热
            for image_file in image_files[:batch_size]:
                embedding_engine.embed_image(str(image_file))
                
                # 测量批量嵌入性能
                start_time = time.time()
                vectors = []
                for image_file in batch:
                    vector = embedding_engine.embed_image(str(image_file))
                    vectors.append(vector)
            end_time = time.time()
            
            total_time = end_time - start_time
            avg_time = total_time / batch_size
            
            result = {
                "batch_size": batch_size,
                "total_time": f"{total_time:.4f}s",
                "avg_time": f"{avg_time:.4f}s",
                "throughput": f"{batch_size / total_time:.2f} images/s"
            }
            
            benchmark_results["batch_embedding"].append(result)
            print(f"批量大小{batch_size}: {total_time:.4f}s (平均{avg_time:.4f}s/图像)")
            
            # 验证结果
            assert len(vectors) == batch_size, f"应该返回{batch_size}个向量"
            for vector in vectors:
                assert vector is not None, "向量不应为None"
                assert len(vector) > 0, "向量维度应该>0"
    
    def test_save_benchmark_results(self, temp_dir, benchmark_results):
        """保存基准测试结果"""
        results_file = Path(temp_dir) / "embedding_benchmark.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(benchmark_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n基准测试结果已保存到: {results_file}")
        
        # 生成摘要报告
        summary = self._generate_summary(benchmark_results)
        summary_file = Path(temp_dir) / "embedding_benchmark.md"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"基准测试摘要已保存到: {summary_file}")
    
    def _generate_summary(self, results):
        """生成基准测试摘要"""
        summary = "# 向量化性能基准测试报告\n\n"
        
        # 图像向量化结果
        summary += "## 图像向量化性能\n\n"
        summary += "| 图像文件 | 文件大小 | 向量化时间 | 向量维度 |\n"
        summary += "|---------|---------|-----------|---------|\n"
        
        for result in results["image_embedding"]:
            summary += f"| {result['image_file']} | {result['image_size']} | {result['embedding_time']} | {result['vector_dim']} |\n"
        
        # 文本向量化结果
        summary += "\n## 文本向量化性能\n\n"
        summary += "| 文本索引 | 文本长度 | 向量化时间 | 向量维度 |\n"
        summary += "|---------|---------|-----------|---------|\n"
        
        for result in results["text_embedding"]:
            summary += f"| {result['text_index']} | {result['text_length']} | {result['embedding_time']} | {result['vector_dim']} |\n"
        
        # 批量向量化结果
        summary += "\n## 批量向量化性能\n\n"
        summary += "| 批量大小 | 总时间 | 平均时间 | 吞吐量 |\n"
        summary += "|---------|-------|---------|--------|\n"
        
        for result in results["batch_embedding"]:
            summary += f"| {result['batch_size']} | {result['total_time']} | {result['avg_time']} | {result['throughput']} |\n"
        
        return summary
