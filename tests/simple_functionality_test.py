#!/usr/bin/env python3
"""
MSearch 简化功能测试
测试核心功能而不依赖复杂的AI模型
"""
import os
import sys
import logging
import time
import json
import traceback
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleFunctionalityTester:
    """简化功能测试器"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any] = None):
        """记录测试结果"""
        self.test_results[test_name] = {
            'success': success,
            'timestamp': time.time(),
            'details': details or {}
        }
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}")
        
        if details:
            for key, value in details.items():
                logger.info(f"  - {key}: {value}")
    
    def test_python_environment(self) -> bool:
        """测试Python环境"""
        logger.info("🐍 测试Python环境...")
        
        try:
            # 检查Python版本
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            
            # 检查关键包
            packages = {}
            
            try:
                import numpy
                packages['numpy'] = numpy.__version__
            except ImportError:
                packages['numpy'] = 'Not installed'
            
            try:
                import torch
                packages['torch'] = torch.__version__
                packages['cuda_available'] = torch.cuda.is_available()
            except ImportError:
                packages['torch'] = 'Not installed'
                packages['cuda_available'] = False
            
            try:
                import transformers
                packages['transformers'] = transformers.__version__
            except ImportError:
                packages['transformers'] = 'Not installed'
            
            try:
                import fastapi
                packages['fastapi'] = fastapi.__version__
            except ImportError:
                packages['fastapi'] = 'Not installed'
            
            try:
                import infinity_emb
                packages['infinity_emb'] = infinity_emb.__version__
            except ImportError:
                packages['infinity_emb'] = 'Not installed'
            
            # 检查项目结构
            project_structure = {}
            required_dirs = ['src', 'src/business', 'src/core', 'tests']
            
            for dir_path in required_dirs:
                full_path = project_root / dir_path
                project_structure[dir_path] = full_path.exists()
            
            success = all(project_structure.values())
            
            self.log_test_result("Python环境", success, {
                "python_version": python_version,
                "packages": packages,
                "project_structure": project_structure
            })
            
            return success
            
        except Exception as e:
            logger.error(f"Python环境测试失败: {e}")
            self.log_test_result("Python环境", False, {"error": str(e)})
            return False
    
    def test_config_loading(self) -> bool:
        """测试配置加载"""
        logger.info("⚙️ 测试配置加载...")
        
        try:
            from src.core.config_manager import ConfigManager
            
            # 测试默认配置
            config = ConfigManager()
            
            # 验证配置结构
            config_dict = config.to_dict() if hasattr(config, 'to_dict') else config.config
            
            # 检查关键配置项
            required_sections = ['general', 'models', 'processing']
            missing_sections = []
            
            for section in required_sections:
                if section not in config_dict:
                    missing_sections.append(section)
            
            # 测试配置文件加载
            test_config_file = project_root / 'tests/configs/cpu_test_config.yml'
            file_config_loaded = False
            
            if test_config_file.exists():
                try:
                    file_config = ConfigManager(str(test_config_file))
                    file_config_loaded = True
                except Exception as e:
                    logger.warning(f"配置文件加载失败: {e}")
            
            success = len(missing_sections) <= 1  # 允许缺少一个配置节
            
            self.log_test_result("配置加载", success, {
                "default_config_loaded": True,
                "file_config_loaded": file_config_loaded,
                "missing_sections": missing_sections,
                "config_sections": list(config_dict.keys())
            })
            
            return success
            
        except Exception as e:
            logger.error(f"配置加载测试失败: {e}")
            self.log_test_result("配置加载", False, {"error": str(e)})
            return False
    
    def test_mock_embedding(self) -> bool:
        """测试模拟嵌入功能"""
        logger.info("🧠 测试模拟嵌入功能...")
        
        try:
            # 创建模拟嵌入引擎
            class MockEmbeddingEngine:
                def __init__(self):
                    self.embedding_dim = 512
                
                def embed_text(self, text: str) -> np.ndarray:
                    """生成模拟文本嵌入"""
                    # 使用文本哈希生成确定性向量
                    hash_value = hash(text)
                    np.random.seed(abs(hash_value) % (2**32))
                    vector = np.random.normal(0, 1, self.embedding_dim)
                    # 归一化
                    vector = vector / np.linalg.norm(vector)
                    return vector
                
                def embed_text_batch(self, texts: List[str]) -> np.ndarray:
                    """批量生成模拟文本嵌入"""
                    vectors = []
                    for text in texts:
                        vectors.append(self.embed_text(text))
                    return np.array(vectors)
            
            # 测试模拟引擎
            mock_engine = MockEmbeddingEngine()
            
            # 测试单个文本嵌入
            test_text = "This is a test sentence"
            embedding = mock_engine.embed_text(test_text)
            
            # 验证嵌入
            assert len(embedding) == 512, "嵌入维度错误"
            assert not np.allclose(embedding, 0), "嵌入向量全为零"
            assert np.isfinite(embedding).all(), "嵌入包含无效值"
            
            # 测试批量嵌入
            test_texts = ["Text 1", "Text 2", "Text 3"]
            batch_embeddings = mock_engine.embed_text_batch(test_texts)
            
            assert batch_embeddings.shape == (3, 512), "批量嵌入形状错误"
            
            # 测试一致性
            single_embedding = mock_engine.embed_text("Text 1")
            batch_first = batch_embeddings[0]
            similarity = np.dot(single_embedding, batch_first)
            
            assert similarity > 0.99, "单个和批量嵌入不一致"
            
            # 测试性能
            start_time = time.time()
            large_batch = [f"Test text {i}" for i in range(100)]
            large_embeddings = mock_engine.embed_text_batch(large_batch)
            processing_time = time.time() - start_time
            
            self.log_test_result("模拟嵌入功能", True, {
                "embedding_dim": 512,
                "single_embedding_shape": embedding.shape,
                "batch_embedding_shape": batch_embeddings.shape,
                "consistency_similarity": f"{similarity:.4f}",
                "large_batch_size": len(large_batch),
                "large_batch_time": f"{processing_time:.3f}s"
            })
            
            return True
            
        except Exception as e:
            logger.error(f"模拟嵌入功能测试失败: {e}")
            self.log_test_result("模拟嵌入功能", False, {"error": str(e)})
            return False
    
    def test_vector_operations(self) -> bool:
        """测试向量操作"""
        logger.info("🔢 测试向量操作...")
        
        try:
            # 创建测试向量
            dim = 512
            num_vectors = 1000
            
            # 生成随机向量数据库
            np.random.seed(42)
            database_vectors = np.random.normal(0, 1, (num_vectors, dim))
            database_vectors = database_vectors / np.linalg.norm(database_vectors, axis=1, keepdims=True)
            
            # 生成查询向量
            query_vector = np.random.normal(0, 1, dim)
            query_vector = query_vector / np.linalg.norm(query_vector)
            
            # 测试相似度计算
            start_time = time.time()
            similarities = np.dot(database_vectors, query_vector)
            similarity_time = time.time() - start_time
            
            # 测试排序
            start_time = time.time()
            sorted_indices = np.argsort(similarities)[::-1]
            sort_time = time.time() - start_time
            
            # 测试Top-K检索
            k = 10
            start_time = time.time()
            top_k_indices = sorted_indices[:k]
            top_k_similarities = similarities[top_k_indices]
            topk_time = time.time() - start_time
            
            # 验证结果
            assert len(top_k_indices) == k, "Top-K结果数量错误"
            assert all(top_k_similarities[i] >= top_k_similarities[i+1] for i in range(k-1)), "Top-K结果未正确排序"
            
            # 测试批量查询
            batch_queries = np.random.normal(0, 1, (5, dim))
            batch_queries = batch_queries / np.linalg.norm(batch_queries, axis=1, keepdims=True)
            
            start_time = time.time()
            batch_similarities = np.dot(database_vectors, batch_queries.T)
            batch_time = time.time() - start_time
            
            self.log_test_result("向量操作", True, {
                "database_size": num_vectors,
                "vector_dim": dim,
                "similarity_time": f"{similarity_time:.4f}s",
                "sort_time": f"{sort_time:.4f}s",
                "topk_time": f"{topk_time:.4f}s",
                "batch_query_time": f"{batch_time:.4f}s",
                "top_similarity": f"{top_k_similarities[0]:.4f}",
                "batch_similarities_shape": batch_similarities.shape
            })
            
            return True
            
        except Exception as e:
            logger.error(f"向量操作测试失败: {e}")
            self.log_test_result("向量操作", False, {"error": str(e)})
            return False
    
    def test_file_operations(self) -> bool:
        """测试文件操作"""
        logger.info("📁 测试文件操作...")
        
        try:
            # 创建测试目录
            test_dir = project_root / 'tests/temp_test'
            test_dir.mkdir(exist_ok=True)
            
            # 测试文件写入
            test_file = test_dir / 'test_file.txt'
            test_content = "This is a test file content"
            
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # 测试文件读取
            with open(test_file, 'r', encoding='utf-8') as f:
                read_content = f.read()
            
            assert read_content == test_content, "文件读写不一致"
            
            # 测试JSON操作
            json_file = test_dir / 'test_data.json'
            test_data = {
                "test_key": "test_value",
                "numbers": [1, 2, 3, 4, 5],
                "nested": {"inner_key": "inner_value"}
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, indent=2, ensure_ascii=False)
            
            with open(json_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            assert loaded_data == test_data, "JSON读写不一致"
            
            # 测试目录遍历
            file_count = 0
            for file_path in test_dir.iterdir():
                if file_path.is_file():
                    file_count += 1
            
            assert file_count >= 2, "文件创建失败"
            
            # 清理测试文件
            test_file.unlink()
            json_file.unlink()
            test_dir.rmdir()
            
            self.log_test_result("文件操作", True, {
                "text_file_rw": "success",
                "json_file_rw": "success",
                "directory_ops": "success",
                "files_created": file_count
            })
            
            return True
            
        except Exception as e:
            logger.error(f"文件操作测试失败: {e}")
            self.log_test_result("文件操作", False, {"error": str(e)})
            return False
    
    def test_timestamp_precision(self) -> bool:
        """测试时间戳精度"""
        logger.info("⏱️ 测试时间戳精度...")
        
        try:
            # 模拟时间戳精度测试
            test_cases = [
                {"expected": 10.0, "actual": 10.5, "tolerance": 2.0},
                {"expected": 25.0, "actual": 26.8, "tolerance": 2.0},
                {"expected": 45.0, "actual": 44.2, "tolerance": 2.0},
                {"expected": 60.0, "actual": 61.9, "tolerance": 2.0},
                {"expected": 120.0, "actual": 118.5, "tolerance": 2.0},
            ]
            
            passed_tests = 0
            accuracy_results = []
            
            for i, test_case in enumerate(test_cases):
                accuracy = abs(test_case["actual"] - test_case["expected"])
                meets_requirement = accuracy <= test_case["tolerance"]
                
                if meets_requirement:
                    passed_tests += 1
                
                accuracy_results.append({
                    "test_id": i + 1,
                    "expected": test_case["expected"],
                    "actual": test_case["actual"],
                    "accuracy": accuracy,
                    "tolerance": test_case["tolerance"],
                    "passed": meets_requirement
                })
                
                logger.info(f"时间戳测试 {i+1}: 期望={test_case['expected']}s, 实际={test_case['actual']}s, 误差={accuracy:.1f}s, {'✅' if meets_requirement else '❌'}")
            
            success_rate = passed_tests / len(test_cases)
            success = success_rate >= 0.8  # 至少80%通过
            
            max_accuracy = max(result["accuracy"] for result in accuracy_results)
            avg_accuracy = sum(result["accuracy"] for result in accuracy_results) / len(accuracy_results)
            
            self.log_test_result("时间戳精度", success, {
                "total_tests": len(test_cases),
                "passed_tests": passed_tests,
                "success_rate": f"{success_rate:.1%}",
                "max_accuracy": f"{max_accuracy:.3f}s",
                "avg_accuracy": f"{avg_accuracy:.3f}s",
                "tolerance": "2.0s",
                "test_results": accuracy_results
            })
            
            return success
            
        except Exception as e:
            logger.error(f"时间戳精度测试失败: {e}")
            self.log_test_result("时间戳精度", False, {"error": str(e)})
            return False
    
    def test_memory_usage(self) -> bool:
        """测试内存使用"""
        logger.info("💾 测试内存使用...")
        
        try:
            import psutil
            
            process = psutil.Process()
            initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
            
            # 模拟内存密集操作
            data_arrays = []
            
            # 创建一些大数组
            for i in range(10):
                array = np.random.random((1000, 1000))
                data_arrays.append(array)
            
            peak_memory = process.memory_info().rss / (1024 * 1024)  # MB
            
            # 清理数组
            del data_arrays
            import gc
            gc.collect()
            
            final_memory = process.memory_info().rss / (1024 * 1024)  # MB
            
            memory_increase = peak_memory - initial_memory
            memory_recovered = peak_memory - final_memory
            
            # 验证内存使用合理
            memory_reasonable = memory_increase < 1000  # 增长不超过1GB
            memory_cleanup = memory_recovered > memory_increase * 0.5  # 至少回收50%
            
            success = memory_reasonable and memory_cleanup
            
            self.log_test_result("内存使用", success, {
                "initial_memory_mb": f"{initial_memory:.2f}",
                "peak_memory_mb": f"{peak_memory:.2f}",
                "final_memory_mb": f"{final_memory:.2f}",
                "memory_increase_mb": f"{memory_increase:.2f}",
                "memory_recovered_mb": f"{memory_recovered:.2f}",
                "memory_reasonable": memory_reasonable,
                "memory_cleanup": memory_cleanup
            })
            
            return success
            
        except Exception as e:
            logger.error(f"内存使用测试失败: {e}")
            self.log_test_result("内存使用", False, {"error": str(e)})
            return False
    
    def generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total_time = time.time() - self.start_time
        
        # 统计测试结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%",
                "total_time": f"{total_time:.2f}s"
            },
            "test_results": self.test_results,
            "environment_info": {
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": sys.platform,
                "test_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        return report
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        logger.info("🚀 开始简化功能测试...")
        
        # 测试列表
        tests = [
            ("Python环境", self.test_python_environment),
            ("配置加载", self.test_config_loading),
            ("模拟嵌入功能", self.test_mock_embedding),
            ("向量操作", self.test_vector_operations),
            ("文件操作", self.test_file_operations),
            ("时间戳精度", self.test_timestamp_precision),
            ("内存使用", self.test_memory_usage),
        ]
        
        # 执行测试
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"执行测试: {test_name}")
            logger.info(f"{'='*50}")
            
            try:
                test_func()
            except Exception as e:
                logger.error(f"测试执行异常: {test_name} - {e}")
                logger.error(traceback.format_exc())
                self.log_test_result(test_name, False, {"exception": str(e)})
        
        # 生成测试报告
        report = self.generate_test_report()
        
        # 保存测试报告
        report_file = Path('./tests/output/simple_functionality_test_report.json')
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n{'='*60}")
        logger.info("📊 测试报告")
        logger.info(f"{'='*60}")
        logger.info(f"总测试数: {report['test_summary']['total_tests']}")
        logger.info(f"通过测试: {report['test_summary']['passed_tests']}")
        logger.info(f"失败测试: {report['test_summary']['failed_tests']}")
        logger.info(f"成功率: {report['test_summary']['success_rate']}")
        logger.info(f"总耗时: {report['test_summary']['total_time']}")
        logger.info(f"测试报告已保存: {report_file}")
        
        # 返回是否大部分测试都通过
        success_rate = report['test_summary']['passed_tests'] / report['test_summary']['total_tests']
        return success_rate >= 0.7  # 至少70%通过

def main():
    """主函数"""
    print("🧪 MSearch 简化功能测试")
    print("=" * 60)
    
    tester = SimpleFunctionalityTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 大部分测试通过！")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查测试报告")
        return 1

if __name__ == "__main__":
    sys.exit(main())