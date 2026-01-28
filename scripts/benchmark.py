#!/usr/bin/env python3
"""
性能测试脚本
用于测试系统性能和生成性能基准报告
"""

import os
import sys
import argparse
import logging
import time
import json
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.config.config_manager import ConfigManager
    from src.core.embedding.embedding_engine import EmbeddingEngine
    from src.core.search_engine import SearchEngine
    from PIL import Image
    import numpy as np
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保已安装所有依赖: pip install -r requirements.txt")
    sys.exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def print_info(message):
    """打印信息"""
    logger.info(message)


def print_success(message):
    """打印成功信息"""
    logger.info(f"✓ {message}")


def print_warning(message):
    """打印警告信息"""
    logger.warning(f"⚠️  {message}")


def print_error(message):
    """打印错误信息"""
    logger.error(f"✗ {message}")


class BenchmarkResult:
    """性能测试结果"""
    
    def __init__(self, name: str):
        self.name = name
        self.durations: List[float] = []
        self.results: Dict[str, Any] = {}
    
    def add_duration(self, duration: float):
        """添加持续时间"""
        self.durations.append(duration)
    
    def get_stats(self) -> Dict[str, float]:
        """获取统计信息"""
        if not self.durations:
            return {}
        
        return {
            "min": min(self.durations),
            "max": max(self.durations),
            "mean": sum(self.durations) / len(self.durations),
            "median": sorted(self.durations)[len(self.durations) // 2],
            "count": len(self.durations)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "stats": self.get_stats(),
            "results": self.results
        }


def benchmark_embedding(config: ConfigManager, embedding_engine: EmbeddingEngine) -> BenchmarkResult:
    """
    测试向量化性能
    
    Args:
        config: 配置管理器
        embedding_engine: 向量化引擎
        
    Returns:
        性能测试结果
    """
    print_info("开始向量化性能测试...")
    
    result = BenchmarkResult("embedding")
    
    # 测试文本向量化
    test_texts = [
        "这是一个测试文本",
        "测试图像检索功能",
        "视频片段搜索测试",
        "音频内容分析测试"
    ]
    
    for text in test_texts:
        start_time = time.time()
        embedding = embedding_engine.embed_text(text)
        duration = time.time() - start_time
        result.add_duration(duration)
        print_info(f"文本向量化耗时: {duration:.4f}秒")
    
    # 测试图像向量化
    test_image_path = "testdata/faces/test_image.jpg"
    if os.path.exists(test_image_path):
        start_time = time.time()
        embedding = embedding_engine.embed_image(test_image_path)
        duration = time.time() - start_time
        result.add_duration(duration)
        print_info(f"图像向量化耗时: {duration:.4f}秒")
    else:
        print_warning(f"测试图像不存在: {test_image_path}")
    
    stats = result.get_stats()
    print_success(f"向量化性能测试完成")
    print_info(f"  平均耗时: {stats.get('mean', 0):.4f}秒")
    print_info(f"  最小耗时: {stats.get('min', 0):.4f}秒")
    print_info(f"  最大耗时: {stats.get('max', 0):.4f}秒")
    
    return result


def benchmark_search(config: ConfigManager, search_engine: SearchEngine) -> BenchmarkResult:
    """
    测试搜索性能
    
    Args:
        config: 配置管理器
        search_engine: 搜索引擎
        
    Returns:
        性能测试结果
    """
    print_info("开始搜索性能测试...")
    
    result = BenchmarkResult("search")
    
    # 测试文本搜索
    test_queries = [
        "测试",
        "图像",
        "视频",
        "音频"
    ]
    
    for query in test_queries:
        start_time = time.time()
        results = search_engine.search(query, modality="text", top_k=10)
        duration = time.time() - start_time
        result.add_duration(duration)
        print_info(f"文本搜索耗时: {duration:.4f}秒，结果数: {len(results)}")
    
    stats = result.get_stats()
    print_success(f"搜索性能测试完成")
    print_info(f"  平均耗时: {stats.get('mean', 0):.4f}秒")
    print_info(f"  最小耗时: {stats.get('min', 0):.4f}秒")
    print_info(f"  最大耗时: {stats.get('max', 0):.4f}秒")
    
    return result


def benchmark_msearch(config: ConfigManager) -> BenchmarkResult:
    """
    测试msearch整体性能
    
    Args:
        config: 配置管理器
        
    Returns:
        性能测试结果
    """
    print_info("开始msearch整体性能测试...")
    
    result = BenchmarkResult("msearch")
    
    # 测试配置加载
    start_time = time.time()
    config2 = ConfigManager()
    duration = time.time() - start_time
    result.add_duration(duration)
    print_info(f"配置加载耗时: {duration:.4f}秒")
    
    # 测试向量化引擎初始化
    start_time = time.time()
    embedding_engine = EmbeddingEngine(config2)
    duration = time.time() - start_time
    result.add_duration(duration)
    print_info(f"向量化引擎初始化耗时: {duration:.4f}秒")
    
    # 测试搜索引擎初始化
    start_time = time.time()
    search_engine = SearchEngine(config2, embedding_engine)
    duration = time.time() - start_time
    result.add_duration(duration)
    print_info(f"搜索引擎初始化耗时: {duration:.4f}秒")
    
    stats = result.get_stats()
    print_success(f"msearch整体性能测试完成")
    print_info(f"  平均耗时: {stats.get('mean', 0):.4f}秒")
    print_info(f"  最小耗时: {stats.get('min', 0):.4f}秒")
    print_info(f"  最大耗时: {stats.get('max', 0):.4f}秒")
    
    return result


def save_benchmark_report(results: List[BenchmarkResult], output_dir: str = "tests/benchmark"):
    """
    保存性能测试报告
    
    Args:
        results: 性能测试结果列表
        output_dir: 输出目录
    """
    print_info("保存性能测试报告...")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存JSON报告
    json_report = {
        "timestamp": time.time(),
        "results": [result.to_dict() for result in results]
    }
    
    json_path = os.path.join(output_dir, "msearch.benchmark.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False)
    
    print_success(f"JSON报告已保存: {json_path}")
    
    # 保存Markdown报告
    md_path = os.path.join(output_dir, "msearch.benchmark.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# msearch 性能测试报告\n\n")
        f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for result in results:
            f.write(f"## {result.name}\n\n")
            stats = result.get_stats()
            
            if stats:
                f.write("### 统计信息\n\n")
                f.write(f"- 平均耗时: {stats.get('mean', 0):.4f}秒\n")
                f.write(f"- 最小耗时: {stats.get('min', 0):.4f}秒\n")
                f.write(f"- 最大耗时: {stats.get('max', 0):.4f}秒\n")
                f.write(f"- 中位数: {stats.get('median', 0):.4f}秒\n")
                f.write(f"- 测试次数: {stats.get('count', 0)}\n\n")
    
    print_success(f"Markdown报告已保存: {md_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="msearch性能测试脚本")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # run命令
    run_parser = subparsers.add_parser("run", help="运行性能测试")
    run_parser.add_argument(
        "--config-dir",
        default="config",
        help="配置目录（默认: config）"
    )
    run_parser.add_argument(
        "--config-file",
        default="config.yml",
        help="配置文件名（默认: config.yml）"
    )
    run_parser.add_argument(
        "--output-dir",
        default="tests/benchmark",
        help="输出目录（默认: tests/benchmark）"
    )
    run_parser.add_argument(
        "--embedding",
        action="store_true",
        help="测试向量化性能"
    )
    run_parser.add_argument(
        "--search",
        action="store_true",
        help="测试搜索性能"
    )
    run_parser.add_argument(
        "--msearch",
        action="store_true",
        help="测试msearch整体性能"
    )
    run_parser.add_argument(
        "--all",
        action="store_true",
        help="运行所有测试"
    )
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "run":
        # 加载配置
        print_info("加载配置...")
        config = ConfigManager(config_dir=args.config_dir, config_file=args.config_file)
        
        results = []
        
        if args.all or args.msearch:
            results.append(benchmark_msearch(config))
        
        if args.all or args.embedding:
            embedding_engine = EmbeddingEngine(config)
            results.append(benchmark_embedding(config, embedding_engine))
        
        if args.all or args.search:
            embedding_engine = EmbeddingEngine(config)
            search_engine = SearchEngine(config, embedding_engine)
            results.append(benchmark_search(config, search_engine))
        
        # 保存报告
        if results:
            save_benchmark_report(results, args.output_dir)
        
        print_success("所有性能测试完成")


if __name__ == "__main__":
    main()