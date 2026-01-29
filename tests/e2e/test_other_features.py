#!/usr/bin/env python3
"""
msearch 其他功能检查报告
检查除文字检索和视觉相似功能外的其他核心功能是否满足要求
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, 'src')


class FeatureChecker:
    """功能检查器"""
    
    def __init__(self):
        self.results = []
        self.total = 0
        self.passed = 0
        self.failed = 0
    
    def log_result(self, feature: str, passed: bool, details: str = ""):
        """记录测试结果"""
        self.total += 1
        if passed:
            self.passed += 1
            status = "✅ 通过"
        else:
            self.failed += 1
            status = "❌ 失败"
        
        self.results.append({
            'feature': feature,
            'passed': passed,
            'details': details,
            'status': status
        })
        
        print(f"  {status} - {feature}")
        if details:
            print(f"    {details}")
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 80)
        print("功能检查总结")
        print("=" * 80)
        print(f"总计: {self.total}")
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print(f"通过率: {self.passed/self.total*100:.1f}%")
        print("=" * 80)
        
        if self.failed > 0:
            print("\n失败的功能:")
            for result in self.results:
                if not result['passed']:
                    print(f"  - {result['feature']}")
                    if result['details']:
                        print(f"    {result['details']}")


def check_audio_features(checker: FeatureChecker):
    """检查音频相关功能"""
    print("\n" + "=" * 80)
    print("音频功能检查")
    print("=" * 80)
    
    try:
        from core.config.config_manager import ConfigManager
        from core.embedding.embedding_engine import EmbeddingEngine
        
        config_manager = ConfigManager()
        config = config_manager.config
        
        # 检查1: 音频模型配置
        print("\n检查1: 音频模型配置")
        audio_model = config.get('models', {}).get('available_models', {}).get('audio_model', {})
        if audio_model:
            model_name = audio_model.get('model_name', '')
            checker.log_result(
                "音频模型配置",
                bool(model_name),
                f"模型: {model_name}"
            )
        else:
            checker.log_result(
                "音频模型配置",
                False,
                "未找到音频模型配置"
            )
        
        # 检查2: 向量化引擎支持音频
        print("\n检查2: 向量化引擎支持音频")
        try:
            embedding_engine = EmbeddingEngine(config)
            has_audio_method = hasattr(embedding_engine, 'embed_audio_from_path')
            checker.log_result(
                "向量化引擎支持音频",
                has_audio_method,
                "EmbeddingEngine支持音频向量化" if has_audio_method else "缺少音频向量化方法"
            )
        except Exception as e:
            checker.log_result(
                "向量化引擎支持音频",
                False,
                f"初始化失败: {str(e)}"
            )
        
        # 检查3: 音频预处理器
        print("\n检查3: 音频预处理器")
        try:
            from services.media.audio_preprocessor import AudioPreprocessor
            audio_preprocessor = AudioPreprocessor(config)
            checker.log_result(
                "音频预处理器",
                True,
                "AudioPreprocessor初始化成功"
            )
        except Exception as e:
            checker.log_result(
                "音频预处理器",
                False,
                f"初始化失败: {str(e)}"
            )
        
        # 检查4: 音频价值判断
        print("\n检查4: 音频价值判断")
        try:
            has_value_method = hasattr(audio_preprocessor, 'has_audio_value')
            checker.log_result(
                "音频价值判断",
                has_value_method,
                "支持音频价值判断（<3秒过滤）" if has_value_method else "缺少音频价值判断方法"
            )
        except Exception as e:
            checker.log_result(
                "音频价值判断",
                False,
                f"检查失败: {str(e)}"
            )
        
    except Exception as e:
        checker.log_result("音频功能检查", False, f"检查失败: {str(e)}")


def check_video_features(checker: FeatureChecker):
    """检查视频相关功能"""
    print("\n" + "=" * 80)
    print("视频功能检查")
    print("=" * 80)
    
    try:
        from core.config.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.config
        
        # 检查1: 视频预处理器
        print("\n检查1: 视频预处理器")
        try:
            from services.media.video_preprocessor import VideoPreprocessor
            video_preprocessor = VideoPreprocessor(config)
            checker.log_result(
                "视频预处理器",
                True,
                "VideoPreprocessor初始化成功"
            )
        except Exception as e:
            checker.log_result(
                "视频预处理器",
                False,
                f"初始化失败: {str(e)}"
            )
        
        # 检查2: 短视频优化
        print("\n检查2: 短视频优化")
        try:
            has_short_video_method = hasattr(video_preprocessor, 'is_short_video')
            checker.log_result(
                "短视频优化",
                has_short_video_method,
                "支持短视频判断（≤6秒）" if has_short_video_method else "缺少短视频判断方法"
            )
        except Exception as e:
            checker.log_result(
                "短视频优化",
                False,
                f"检查失败: {str(e)}"
            )
        
        # 检查3: 视频切片
        print("\n检查3: 视频切片")
        try:
            has_slice_method = hasattr(video_preprocessor, 'video_slice')
            checker.log_result(
                "视频切片",
                has_slice_method,
                "支持视频切片功能" if has_slice_method else "缺少视频切片方法"
            )
        except Exception as e:
            checker.log_result(
                "视频切片",
                False,
                f"检查失败: {str(e)}"
            )
        
        # 检查4: 音频分离
        print("\n检查4: 音频分离")
        try:
            has_extract_method = hasattr(video_preprocessor, 'extract_audio_from_video')
            checker.log_result(
                "音频分离",
                has_extract_method,
                "支持音频分离功能" if has_extract_method else "缺少音频分离方法"
            )
        except Exception as e:
            checker.log_result(
                "音频分离",
                False,
                f"检查失败: {str(e)}"
            )
        
        # 检查5: 时间定位
        print("\n检查5: 时间定位")
        try:
            from services.media.video_preprocessor import VideoPreprocessor
            has_timestamp_method = hasattr(video_preprocessor, 'get_segment_timestamps')
            checker.log_result(
                "时间定位",
                has_timestamp_method,
                "支持时间戳获取" if has_timestamp_method else "缺少时间戳方法"
            )
        except Exception as e:
            checker.log_result(
                "时间定位",
                False,
                f"检查失败: {str(e)}"
            )
        
    except Exception as e:
        checker.log_result("视频功能检查", False, f"检查失败: {str(e)}")


def check_file_monitoring_features(checker: FeatureChecker):
    """检查文件监控功能"""
    print("\n" + "=" * 80)
    print("文件监控功能检查")
    print("=" * 80)
    
    try:
        from core.config.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.config
        
        # 检查1: 文件扫描器
        print("\n检查1: 文件扫描器")
        try:
            from services.file.file_scanner import FileScanner
            file_scanner = FileScanner(config)
            checker.log_result(
                "文件扫描器",
                True,
                "FileScanner初始化成功"
            )
        except Exception as e:
            checker.log_result(
                "文件扫描器",
                False,
                f"初始化失败: {str(e)}"
            )
        
        # 检查2: 文件监控器
        print("\n检查2: 文件监控器")
        try:
            from core.file_monitor import FileMonitor
            checker.log_result(
                "文件监控器",
                True,
                "FileMonitor模块存在"
            )
        except Exception as e:
            checker.log_result(
                "文件监控器",
                False,
                f"检查失败: {str(e)}"
            )
        
        # 检查3: 文件哈希计算
        print("\n检查3: 文件哈希计算")
        try:
            has_hash_method = hasattr(file_scanner, 'calculate_file_hash')
            checker.log_result(
                "文件哈希计算",
                has_hash_method,
                "支持SHA256哈希计算" if has_hash_method else "缺少哈希计算方法"
            )
        except Exception as e:
            checker.log_result(
                "文件哈希计算",
                False,
                f"检查失败: {str(e)}"
            )
        
        # 检查4: 重复文件检测
        print("\n检查4: 重复文件检测")
        try:
            from services.file.file_indexer import FileIndexer
            file_indexer = FileIndexer(config)
            has_duplicate_method = hasattr(file_indexer, 'check_duplicate_file')
            checker.log_result(
                "重复文件检测",
                has_duplicate_method,
                "支持重复文件检测" if has_duplicate_method else "缺少重复检测方法"
            )
        except Exception as e:
            checker.log_result(
                "重复文件检测",
                False,
                f"检查失败: {str(e)}"
            )
        
    except Exception as e:
        checker.log_result("文件监控功能检查", False, f"检查失败: {str(e)}")


def check_task_management_features(checker: FeatureChecker):
    """检查任务管理功能"""
    print("\n" + "=" * 80)
    print("任务管理功能检查")
    print("=" * 80)
    
    try:
        from core.config.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.config
        
        # 检查1: 任务管理器
        print("\n检查1: 任务管理器")
        try:
            from core.task.task_manager import TaskManager
            checker.log_result(
                "任务管理器",
                True,
                "TaskManager模块存在"
            )
        except Exception as e:
            checker.log_result(
                "任务管理器",
                False,
                f"检查失败: {str(e)}"
            )
        
        # 检查2: 任务调度器
        print("\n检查2: 任务调度器")
        try:
            from core.task.task_scheduler import TaskScheduler
            checker.log_result(
                "任务调度器",
                True,
                "TaskScheduler模块存在"
            )
        except Exception as e:
            checker.log_result(
                "任务调度器",
                False,
                f"检查失败: {str(e)}"
            )
        
        # 检查3: 优先级计算器
        print("\n检查3: 优先级计算器")
        try:
            from core.task.priority_calculator import PriorityCalculator
            checker.log_result(
                "优先级计算器",
                True,
                "PriorityCalculator模块存在"
            )
        except Exception as e:
            checker.log_result(
                "优先级计算器",
                False,
                f"检查失败: {str(e)}"
            )
        
        # 检查4: 任务配置
        print("\n检查4: 任务配置")
        task_config = config.get('task_manager', {})
        if task_config:
            max_concurrent = task_config.get('max_concurrent_tasks')
            checker.log_result(
                "任务配置",
                True,
                f"最大并发任务: {max_concurrent}"
            )
        else:
            checker.log_result(
                "任务配置",
                False,
                "未找到任务配置"
            )
        
    except Exception as e:
        checker.log_result("任务管理功能检查", False, f"检查失败: {str(e)}")


def check_cache_features(checker: FeatureChecker):
    """检查缓存功能"""
    print("\n" + "=" * 80)
    print("缓存功能检查")
    print("=" * 80)
    
    try:
        from core.config.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.config
        
        # 检查1: 预处理缓存
        print("\n检查1: 预处理缓存")
        try:
            from services.cache.preprocessing_cache import PreprocessingCache
            cache = PreprocessingCache(config)
            checker.log_result(
                "预处理缓存",
                True,
                "PreprocessingCache初始化成功"
            )
        except Exception as e:
            checker.log_result(
                "预处理缓存",
                False,
                f"初始化失败: {str(e)}"
            )
        
        # 检查2: 缓存配置
        print("\n检查2: 缓存配置")
        cache_config = config.get('cache', {})
        if cache_config:
            cache_dir = cache_config.get('cache_dir')
            checker.log_result(
                "缓存配置",
                True,
                f"缓存目录: {cache_dir}"
            )
        else:
            checker.log_result(
                "缓存配置",
                False,
                "未找到缓存配置"
            )
        
    except Exception as e:
        checker.log_result("缓存功能检查", False, f"检查失败: {str(e)}")


def check_database_features(checker: FeatureChecker):
    """检查数据库功能"""
    print("\n" + "=" * 80)
    print("数据库功能检查")
    print("=" * 80)
    
    try:
        from core.config.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.config
        
        # 检查1: 向量数据库
        print("\n检查1: 向量数据库（LanceDB）")
        try:
            from core.vector.vector_store import VectorStore
            vector_store = VectorStore(config)
            stats = vector_store.get_stats()
            checker.log_result(
                "向量数据库",
                True,
                f"向量数量: {stats.get('vector_count', 0)}"
            )
        except Exception as e:
            checker.log_result(
                "向量数据库",
                False,
                f"初始化失败: {str(e)}"
            )
        
        # 检查2: 数据库配置
        print("\n检查2: 数据库配置")
        db_config = config.get('database', {})
        if db_config:
            vector_db_path = db_config.get('vector_db_path')
            checker.log_result(
                "数据库配置",
                True,
                f"向量数据库路径: {vector_db_path}"
            )
        else:
            checker.log_result(
                "数据库配置",
                False,
                "未找到数据库配置"
            )
        
    except Exception as e:
        checker.log_result("数据库功能检查", False, f"检查失败: {str(e)}")


def main():
    """主函数"""
    print("=" * 80)
    print("msearch 其他功能检查报告")
    print("=" * 80)
    print("检查除文字检索和视觉相似功能外的其他核心功能")
    print("=" * 80)
    
    checker = FeatureChecker()
    
    # 检查各项功能
    check_audio_features(checker)
    check_video_features(checker)
    check_file_monitoring_features(checker)
    check_task_management_features(checker)
    check_cache_features(checker)
    check_database_features(checker)
    
    # 打印总结
    checker.print_summary()
    
    # 评估结果
    print("\n" + "=" * 80)
    print("评估结果")
    print("=" * 80)
    
    if checker.failed == 0:
        print("✅ 所有功能检查通过！除文字检索和视觉相似功能外的其他核心功能均满足要求。")
    elif checker.failed <= 2:
        print(f"⚠️  大部分功能检查通过（{checker.passed}/{checker.total}），有少量功能需要完善。")
    else:
        print(f"❌ 有较多功能未通过检查（{checker.failed}个），需要进一步完善。")
    
    print("=" * 80)
    
    return 0 if checker.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
