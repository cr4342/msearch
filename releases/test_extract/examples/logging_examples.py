"""
日志系统使用示例
展示如何在不同组件中正确使用多级别日志系统
"""

import time
import asyncio
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.logger_manager import get_logger


class VideoProcessorExample:
    """视频处理器日志使用示例"""
    
    def __init__(self):
        self.logger = get_logger('msearch.processors.video_processor')
        self.performance_logger = get_logger('msearch.performance')
    
    async def process_video(self, video_path: str) -> dict:
        """处理视频文件 - 展示完整的日志记录流程"""
        
        # INFO级别：记录关键操作开始
        self.logger.info(f"开始处理视频: {video_path}")
        
        try:
            # DEBUG级别：详细执行流程
            self.logger.debug(f"检查视频文件存在性: {video_path}")
            
            if not Path(video_path).exists():
                # ERROR级别：文件不存在错误
                self.logger.error(f"视频文件不存在: {video_path}")
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
            # 获取文件信息
            file_size = Path(video_path).stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            self.logger.debug(f"视频文件大小: {file_size_mb:.1f}MB")
            
            # WARNING级别：大文件警告
            if file_size_mb > 500:
                self.logger.warning(f"处理大视频文件: {video_path}, 大小: {file_size_mb:.1f}MB")
            
            # 模拟处理过程
            start_time = time.time()
            
            # 1. 格式转换阶段
            self.logger.info("开始格式转换: 4K -> 720p")
            await self._simulate_format_conversion(file_size_mb)
            
            conversion_time = time.time() - start_time
            self.performance_logger.info(f"格式转换完成: 耗时 {conversion_time:.2f}s")
            
            # 2. 关键帧提取阶段
            self.logger.info("开始关键帧提取")
            frame_start = time.time()
            
            frame_count = await self._simulate_frame_extraction()
            
            frame_time = time.time() - frame_start
            self.performance_logger.info(f"关键帧提取完成: {frame_count}帧, 耗时 {frame_time:.2f}s")
            
            # 3. 向量化阶段
            self.logger.info("开始CLIP向量化")
            vector_start = time.time()
            
            vectors = await self._simulate_vectorization(frame_count)
            
            vector_time = time.time() - vector_start
            self.performance_logger.info(f"向量化完成: {len(vectors)}个向量, 耗时 {vector_time:.2f}s")
            
            total_time = time.time() - start_time
            
            # INFO级别：处理完成
            self.logger.info(f"视频处理完成: {video_path}, 总耗时: {total_time:.2f}s")
            
            return {
                "status": "success",
                "frame_count": frame_count,
                "vector_count": len(vectors),
                "processing_time": total_time
            }
            
        except Exception as e:
            # ERROR级别：处理失败
            self.logger.error(f"视频处理失败: {video_path}, 错误: {e}", exc_info=True)
            raise
    
    async def _simulate_format_conversion(self, file_size_mb: float):
        """模拟格式转换"""
        self.logger.debug("开始4K到720p转换")
        
        # 模拟转换时间（大文件需要更长时间）
        conversion_time = min(file_size_mb / 100, 5.0)  # 最多5秒
        await asyncio.sleep(conversion_time)
        
        self.logger.debug(f"格式转换完成，压缩率: 75%")
    
    async def _simulate_frame_extraction(self) -> int:
        """模拟关键帧提取"""
        self.logger.debug("使用场景检测算法提取关键帧")
        
        await asyncio.sleep(1.0)  # 模拟提取时间
        
        frame_count = 45  # 模拟提取的帧数
        self.logger.debug(f"提取了 {frame_count} 个关键帧")
        
        return frame_count
    
    async def _simulate_vectorization(self, frame_count: int) -> list:
        """模拟向量化过程"""
        self.logger.debug(f"对 {frame_count} 帧进行CLIP向量化")
        
        vectors = []
        batch_size = 16
        
        for i in range(0, frame_count, batch_size):
            batch_end = min(i + batch_size, frame_count)
            batch_frames = batch_end - i
            
            self.logger.debug(f"处理批次: 帧 {i+1}-{batch_end}")
            
            # 模拟批处理时间
            await asyncio.sleep(0.5)
            
            # 模拟生成向量
            batch_vectors = [f"vector_{j}" for j in range(i, batch_end)]
            vectors.extend(batch_vectors)
        
        self.logger.debug(f"向量化完成，生成 {len(vectors)} 个向量")
        return vectors


class TimestampProcessorExample:
    """时间戳处理器日志使用示例"""
    
    def __init__(self):
        self.logger = get_logger('msearch.processors.timestamp_processor')
    
    def calculate_frame_timestamp(self, frame_index: int, fps: float) -> float:
        """计算帧时间戳 - 展示精确的调试日志"""
        
        self.logger.debug(f"计算帧时间戳: frame_index={frame_index}, fps={fps}")
        
        # 参数验证
        if fps <= 0:
            self.logger.error(f"无效的帧率: {fps}")
            raise ValueError(f"帧率必须大于0: {fps}")
        
        if frame_index < 0:
            self.logger.error(f"无效的帧索引: {frame_index}")
            raise ValueError(f"帧索引必须非负: {frame_index}")
        
        # 计算时间戳
        timestamp = frame_index / fps
        
        # 精度检查
        if abs(timestamp - round(timestamp, 3)) > 0.001:
            self.logger.warning(f"时间戳精度可能不足: {timestamp:.6f}s")
        
        self.logger.debug(f"帧时间戳计算完成: {timestamp:.3f}s")
        return timestamp
    
    def validate_timestamp_accuracy(self, timestamp: float, duration: float) -> bool:
        """验证时间戳精度 - 展示业务逻辑日志"""
        
        self.logger.debug(f"验证时间戳精度: timestamp={timestamp:.3f}s, duration={duration:.3f}s")
        
        accuracy_requirement = 2.0  # ±2秒精度要求
        is_valid = duration <= (accuracy_requirement * 2)
        
        if not is_valid:
            self.logger.warning(
                f"时间戳精度不满足要求: duration={duration:.3f}s > {accuracy_requirement*2}s"
            )
        else:
            self.logger.debug(f"时间戳精度验证通过: duration={duration:.3f}s")
        
        return is_valid


class SearchEngineExample:
    """搜索引擎日志使用示例"""
    
    def __init__(self):
        self.logger = get_logger('msearch.business.search_engine')
        self.performance_logger = get_logger('msearch.performance')
    
    async def search(self, query: str, top_k: int = 10) -> list:
        """执行搜索 - 展示搜索过程的日志记录"""
        
        self.logger.info(f"执行搜索: query='{query}', top_k={top_k}")
        
        try:
            search_start = time.time()
            
            # 1. 查询预处理
            self.logger.debug("开始查询预处理")
            processed_query = self._preprocess_query(query)
            self.logger.debug(f"查询预处理完成: '{processed_query}'")
            
            # 2. 查询类型识别
            query_type = self._detect_query_type(processed_query)
            self.logger.info(f"识别查询类型: {query_type}")
            
            # 3. 向量化
            self.logger.debug(f"使用 {query_type} 模型进行文本向量化")
            query_vector = await self._vectorize_query(processed_query, query_type)
            
            # 4. 向量搜索
            self.logger.debug("开始向量相似度搜索")
            vector_results = await self._vector_search(query_vector, top_k * 2)
            
            # 5. 时间戳查询
            self.logger.debug("查询时间戳信息")
            timestamped_results = await self._get_timestamps(vector_results)
            
            # 6. 结果排序和过滤
            self.logger.debug("结果排序和过滤")
            final_results = self._rank_and_filter(timestamped_results, top_k)
            
            search_time = time.time() - search_start
            
            self.logger.info(f"搜索完成: 返回 {len(final_results)} 个结果, 耗时: {search_time:.3f}s")
            self.performance_logger.info(f"搜索性能: query='{query}', results={len(final_results)}, time={search_time:.3f}s")
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"搜索失败: query='{query}', 错误: {e}", exc_info=True)
            raise
    
    def _preprocess_query(self, query: str) -> str:
        """查询预处理"""
        # 模拟预处理
        processed = query.strip().lower()
        return processed
    
    def _detect_query_type(self, query: str) -> str:
        """检测查询类型"""
        visual_keywords = ["图片", "照片", "视频", "画面"]
        audio_keywords = ["音乐", "歌曲", "音频", "声音"]
        
        if any(keyword in query for keyword in visual_keywords):
            return "visual"
        elif any(keyword in query for keyword in audio_keywords):
            return "audio"
        else:
            return "general"
    
    async def _vectorize_query(self, query: str, query_type: str) -> list:
        """查询向量化"""
        await asyncio.sleep(0.1)  # 模拟向量化时间
        return [0.1] * 512  # 模拟512维向量
    
    async def _vector_search(self, query_vector: list, top_k: int) -> list:
        """向量搜索"""
        await asyncio.sleep(0.2)  # 模拟搜索时间
        
        # 模拟搜索结果
        results = []
        for i in range(top_k):
            results.append({
                "vector_id": f"vec_{i}",
                "similarity": 0.9 - i * 0.05,
                "file_id": f"file_{i}"
            })
        
        return results
    
    async def _get_timestamps(self, vector_results: list) -> list:
        """获取时间戳信息"""
        await asyncio.sleep(0.05)  # 模拟时间戳查询
        
        for result in vector_results:
            result["timestamp"] = {
                "start_time": 10.0 + len(vector_results) * 2,
                "end_time": 12.0 + len(vector_results) * 2,
                "duration": 2.0
            }
        
        return vector_results
    
    def _rank_and_filter(self, results: list, top_k: int) -> list:
        """结果排序和过滤"""
        # 按相似度排序
        sorted_results = sorted(results, key=lambda x: x["similarity"], reverse=True)
        return sorted_results[:top_k]


async def demonstrate_logging_levels():
    """演示不同日志级别的使用"""
    
    print("=== 日志级别演示 ===")
    
    # 创建不同组件的日志器
    core_logger = get_logger('msearch.core.demo')
    processor_logger = get_logger('msearch.processors.demo')
    model_logger = get_logger('msearch.models.demo')
    
    print("\n1. DEBUG级别日志（开发调试）:")
    core_logger.debug("这是核心组件的调试信息")
    processor_logger.debug("这是处理器的详细执行流程")
    model_logger.debug("这是模型调用的参数信息")
    
    print("\n2. INFO级别日志（正常运行）:")
    core_logger.info("系统启动完成")
    processor_logger.info("开始处理文件: example.mp4")
    model_logger.info("CLIP模型加载成功")
    
    print("\n3. WARNING级别日志（潜在问题）:")
    core_logger.warning("配置文件使用默认值")
    processor_logger.warning("处理大文件，可能需要较长时间")
    model_logger.warning("GPU内存使用率较高: 85%")
    
    print("\n4. ERROR级别日志（处理错误）:")
    core_logger.error("配置文件格式错误")
    processor_logger.error("文件处理失败: 不支持的格式")
    model_logger.error("模型推理失败: CUDA内存不足")
    
    print("\n5. CRITICAL级别日志（系统故障）:")
    core_logger.critical("数据库连接失败，系统无法正常工作")
    processor_logger.critical("处理器崩溃，需要重启服务")
    model_logger.critical("所有GPU设备不可用，系统停止服务")


async def demonstrate_performance_logging():
    """演示性能日志的使用"""
    
    print("\n=== 性能日志演示 ===")
    
    # 创建示例处理器
    video_processor = VideoProcessorExample()
    
    # 模拟处理不同大小的视频文件
    test_videos = [
        "small_video.mp4",    # 小文件
        "large_video.mp4",    # 大文件
    ]
    
    for video_path in test_videos:
        try:
            result = await video_processor.process_video(video_path)
            print(f"处理结果: {result}")
        except Exception as e:
            print(f"处理失败: {e}")


async def demonstrate_timestamp_logging():
    """演示时间戳处理日志"""
    
    print("\n=== 时间戳处理日志演示 ===")
    
    timestamp_processor = TimestampProcessorExample()
    
    # 测试正常情况
    try:
        timestamp = timestamp_processor.calculate_frame_timestamp(1800, 30.0)
        is_valid = timestamp_processor.validate_timestamp_accuracy(timestamp, 2.0)
        print(f"时间戳: {timestamp:.3f}s, 有效: {is_valid}")
    except Exception as e:
        print(f"时间戳计算失败: {e}")
    
    # 测试异常情况
    try:
        timestamp_processor.calculate_frame_timestamp(-1, 30.0)  # 无效帧索引
    except Exception as e:
        print(f"预期的错误: {e}")
    
    try:
        timestamp_processor.calculate_frame_timestamp(1800, 0)  # 无效帧率
    except Exception as e:
        print(f"预期的错误: {e}")


async def demonstrate_search_logging():
    """演示搜索日志"""
    
    print("\n=== 搜索日志演示 ===")
    
    search_engine = SearchEngineExample()
    
    # 测试不同类型的查询
    test_queries = [
        "美丽的风景照片",
        "轻松的背景音乐",
        "会议讨论录音"
    ]
    
    for query in test_queries:
        try:
            results = await search_engine.search(query, top_k=5)
            print(f"查询 '{query}' 返回 {len(results)} 个结果")
        except Exception as e:
            print(f"搜索失败: {e}")


async def main():
    """主演示函数"""
    print("多级别日志系统演示")
    print("=" * 50)
    
    # 演示不同日志级别
    await demonstrate_logging_levels()
    
    # 演示性能日志
    await demonstrate_performance_logging()
    
    # 演示时间戳处理日志
    await demonstrate_timestamp_logging()
    
    # 演示搜索日志
    await demonstrate_search_logging()
    
    print("\n=== 日志统计信息 ===")
    from src.core.logger_manager import get_logger_manager
    
    manager = get_logger_manager()
    stats = manager.get_log_stats()
    
    print(f"活跃日志器数量: {stats['active_loggers']}")
    print("日志文件信息:")
    for log_file in stats['log_files']:
        print(f"  - {log_file['name']}: {log_file['size_mb']}MB ({log_file['path']})")
    
    if 'disk_usage' in stats and 'total_gb' in stats['disk_usage']:
        disk = stats['disk_usage']
        print(f"磁盘使用: {disk['used_gb']:.1f}GB / {disk['total_gb']:.1f}GB ({disk['usage_percent']:.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())