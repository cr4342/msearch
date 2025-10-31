#!/usr/bin/env python3
"""
MSearch 模拟模型测试
在网络受限环境下使用模拟模型进行功能测试
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

class MockModelTester:
    """模拟模型测试器"""
    
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
    
    def test_infinity_emb_import(self) -> bool:
        """测试infinity-emb导入"""
        logger.info("🔍 测试infinity-emb导入...")
        
        try:
            import infinity_emb
            version = infinity_emb.__version__
            logger.info(f"infinity-emb版本: {version}")
            
            self.log_test_result("infinity-emb导入", True, {
                "version": version
            })
            return True
            
        except ImportError as e:
            logger.error(f"infinity-emb导入失败: {e}")
            self.log_test_result("infinity-emb导入", False, {"error": str(e)})
            return False
    
    def test_infinity_engine_creation(self) -> bool:
        """测试infinity引擎创建"""
        logger.info("🧠 测试infinity引擎创建...")
        
        try:
            from infinity_emb import EngineArray
            
            # 使用小模型进行测试
            engine_args = [
                "--model-id", "sentence-transformers/all-MiniLM-L6-v2",
                "--device", "cpu",
                "--engine", "torch"
            ]
            
            start_time = time.time()
            engine = EngineArray.from_args(engine_args)
            init_time = time.time() - start_time
            
            logger.info(f"引擎创建成功，耗时: {init_time:.3f}s")
            
            self.log_test_result("infinity引擎创建", True, {
                "init_time": f"{init_time:.3f}s",
                "model": "sentence-transformers/all-MiniLM-L6-v2"
            })
            return True
            
        except Exception as e:
            logger.error(f"infinity引擎创建失败: {e}")
            self.log_test_result("infinity引擎创建", False, {"error": str(e)})
            return False
    
    def test_text_embedding(self) -> bool:
        """测试文本嵌入"""
        logger.info("📝 测试文本嵌入...")
        
        try:
            from infinity_emb import EngineArray
            
            # 创建引擎
            engine_args = [
                "--model-id", "sentence-transformers/all-MiniLM-L6-v2",
                "--device", "cpu",
                "--engine", "torch"
            ]
            
            engine = EngineArray.from_args(engine_args)
            
            # 测试文本
            test_texts = [
                "This is a test sentence",
                "Another test sentence",
                "A third test sentence"
            ]
            
            start_time = time.time()
            embeddings = engine.encode(test_texts)
            embed_time = time.time() - start_time
            
            # 验证结果
            if embeddings is not None and len(embeddings) == len(test_texts):
                logger.info(f"文本嵌入成功: {embeddings.shape}, 耗时: {embed_time:.3f}s")
                
                # 验证嵌入质量
                embedding_dim = embeddings.shape[1]
                avg_norm = np.mean([np.linalg.norm(emb) for emb in embeddings])
                
                self.log_test_result("文本嵌入", True, {
                    "embedding_shape": str(embeddings.shape),
                    "embedding_dim": embedding_dim,
                    "avg_norm": f"{avg_norm:.3f}",
                    "embed_time": f"{embed_time:.3f}s",
                    "texts_processed": len(test_texts)
                })
                return True
            else:
                raise ValueError("嵌入结果无效")
                
        except Exception as e:
            logger.error(f"文本嵌入测试失败: {e}")
            self.log_test_result("文本嵌入", False, {"error": str(e)})
            return False
    
    def test_batch_processing(self) -> bool:
        """测试批处理"""
        logger.info("📦 测试批处理...")
        
        try:
            from infinity_emb import EngineArray
            
            # 创建引擎
            engine_args = [
                "--model-id", "sentence-transformers/all-MiniLM-L6-v2",
                "--device", "cpu",
                "--engine", "torch"
            ]
            
            engine = EngineArray.from_args(engine_args)
            
            # 创建大批量文本
            batch_texts = [f"Test sentence number {i}" for i in range(20)]
            
            start_time = time.time()
            embeddings = engine.encode(batch_texts)
            batch_time = time.time() - start_time
            
            # 计算平均处理时间
            avg_time_per_text = batch_time / len(batch_texts)
            
            logger.info(f"批处理完成: {len(batch_texts)}个文本, 总耗时: {batch_time:.3f}s, 平均: {avg_time_per_text:.3f}s/文本")
            
            self.log_test_result("批处理", True, {
                "batch_size": len(batch_texts),
                "total_time": f"{batch_time:.3f}s",
                "avg_time_per_text": f"{avg_time_per_text:.3f}s",
                "embedding_shape": str(embeddings.shape)
            })
            return True
            
        except Exception as e:
            logger.error(f"批处理测试失败: {e}")
            self.log_test_result("批处理", False, {"error": str(e)})
            return False
    
    def test_performance_benchmarks(self) -> bool:
        """测试性能基准"""
        logger.info("⚡ 测试性能基准...")
        
        try:
            from infinity_emb import EngineArray
            import psutil
            
            # 监控系统资源
            process = psutil.Process()
            initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
            
            # 创建引擎
            engine_args = [
                "--model-id", "sentence-transformers/all-MiniLM-L6-v2",
                "--device", "cpu",
                "--engine", "torch"
            ]
            
            engine = EngineArray.from_args(engine_args)
            
            # 性能测试
            test_cases = [
                {"name": "单文本", "texts": ["Single text test"], "expected_time": 1.0},
                {"name": "小批量", "texts": [f"Small batch {i}" for i in range(5)], "expected_time": 2.0},
                {"name": "中批量", "texts": [f"Medium batch {i}" for i in range(10)], "expected_time": 3.0},
            ]
            
            results = []
            
            for test_case in test_cases:
                start_time = time.time()
                embeddings = engine.encode(test_case["texts"])
                processing_time = time.time() - start_time
                
                # 验证性能
                meets_benchmark = processing_time <= test_case["expected_time"]
                
                results.append({
                    "name": test_case["name"],
                    "processing_time": processing_time,
                    "expected_time": test_case["expected_time"],
                    "meets_benchmark": meets_benchmark,
                    "texts_count": len(test_case["texts"])
                })
                
                logger.info(f"{test_case['name']}: {processing_time:.3f}s (期望: <{test_case['expected_time']}s) {'✅' if meets_benchmark else '❌'}")
            
            # 检查内存使用
            final_memory = process.memory_info().rss / (1024 * 1024)  # MB
            memory_increase = final_memory - initial_memory
            
            # 统计结果
            passed_benchmarks = sum(1 for r in results if r["meets_benchmark"])
            total_benchmarks = len(results)
            
            success = passed_benchmarks >= total_benchmarks * 0.8  # 至少80%通过
            
            self.log_test_result("性能基准", success, {
                "passed_benchmarks": f"{passed_benchmarks}/{total_benchmarks}",
                "initial_memory_mb": f"{initial_memory:.2f}",
                "final_memory_mb": f"{final_memory:.2f}",
                "memory_increase_mb": f"{memory_increase:.2f}",
                "benchmark_results": results
            })
            
            return success
            
        except Exception as e:
            logger.error(f"性能基准测试失败: {e}")
            self.log_test_result("性能基准", False, {"error": str(e)})
            return False
    
    def test_error_handling(self) -> bool:
        """测试错误处理"""
        logger.info("🛡️ 测试错误处理...")
        
        try:
            from infinity_emb import EngineArray
            
            # 测试无效模型
            try:
                invalid_engine_args = [
                    "--model-id", "invalid/model/path",
                    "--device", "cpu",
                    "--engine", "torch"
                ]
                engine = EngineArray.from_args(invalid_engine_args)
                logger.warning("无效模型测试未按预期失败")
                invalid_model_handled = False
            except Exception as e:
                logger.info(f"无效模型正确处理: {type(e).__name__}")
                invalid_model_handled = True
            
            # 测试空文本处理
            valid_engine_args = [
                "--model-id", "sentence-transformers/all-MiniLM-L6-v2",
                "--device", "cpu",
                "--engine", "torch"
            ]
            engine = EngineArray.from_args(valid_engine_args)
            
            try:
                empty_result = engine.encode([])
                empty_text_handled = empty_result is not None and len(empty_result) == 0
                logger.info("空文本列表处理正确")
            except Exception as e:
                logger.info(f"空文本列表处理异常: {type(e).__name__}")
                empty_text_handled = True
            
            # 测试超长文本处理
            try:
                long_text = "Very long text " * 1000  # 创建超长文本
                long_result = engine.encode([long_text])
                long_text_handled = long_result is not None
                logger.info("超长文本处理正确")
            except Exception as e:
                logger.info(f"超长文本处理异常: {type(e).__name__}")
                long_text_handled = True
            
            success = invalid_model_handled and empty_text_handled and long_text_handled
            
            self.log_test_result("错误处理", success, {
                "invalid_model_handled": invalid_model_handled,
                "empty_text_handled": empty_text_handled,
                "long_text_handled": long_text_handled
            })
            
            return success
            
        except Exception as e:
            logger.error(f"错误处理测试失败: {e}")
            self.log_test_result("错误处理", False, {"error": str(e)})
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
        logger.info("🚀 开始模拟模型测试...")
        
        # 测试列表
        tests = [
            ("infinity-emb导入", self.test_infinity_emb_import),
            ("infinity引擎创建", self.test_infinity_engine_creation),
            ("文本嵌入", self.test_text_embedding),
            ("批处理", self.test_batch_processing),
            ("性能基准", self.test_performance_benchmarks),
            ("错误处理", self.test_error_handling),
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
        report_file = Path('./tests/output/mock_model_test_report.json')
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
        
        # 返回是否所有关键测试都通过
        critical_tests = ["infinity-emb导入", "infinity引擎创建", "文本嵌入"]
        critical_passed = all(
            self.test_results.get(test, {}).get('success', False) 
            for test in critical_tests
        )
        
        return critical_passed

def main():
    """主函数"""
    print("🧪 MSearch 模拟模型测试")
    print("=" * 60)
    
    tester = MockModelTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 关键测试全部通过！")
        return 0
    else:
        print("\n⚠️ 部分关键测试失败，请检查测试报告")
        return 1

if __name__ == "__main__":
    sys.exit(main())