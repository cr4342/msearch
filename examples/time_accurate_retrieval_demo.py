#!/usr/bin/env python3
"""
时间戳精确检索演示脚本
展示±2秒精度的视频时间戳检索和多模态流处理功能
"""
import os
import sys
import asyncio
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.business.time_accurate_retrieval import (
    TimeAccurateRetrievalEngine, RetrievalQuery, VideoTimelineGenerator
)
from src.processors.timestamp_processor import TimestampProcessor, TimestampInfo, ModalityType
from src.processors.video_audio_stream_processor import VideoAudioStreamProcessor
from src.storage.timestamp_database import TimestampDatabase
from src.core.config_manager import ConfigManager


class TimeAccurateRetrievalDemo:
    """时间戳精确检索演示类"""
    
    def __init__(self):
        """初始化演示环境"""
        # 加载配置
        self.config_manager = ConfigManager()
        self.config = {
            'search': {
                'timestamp_retrieval': {
                    'accuracy_requirement': 2.0,
                    'enable_segment_merging': True,
                    'merge_threshold': 2.0,
                    'continuity_detection': True,
                    'max_gap_tolerance': 4.0
                }
            },
            'processing': {
                'stream': {
                    'enable_audio_extraction': True,
                    'enable_stream_sync': True,
                    'sync_tolerance': 0.1,
                    'max_drift_correction': 1.0
                }
            }
        }
        
        # 创建临时数据库
        self.db_path = "demo_timestamps.db"
        self.timestamp_db = TimestampDatabase(self.db_path)
        
        # 创建处理器
        self.timestamp_processor = TimestampProcessor(self.config)
        self.stream_processor = VideoAudioStreamProcessor(self.config)
        
        # 创建模拟向量存储
        self.mock_vector_store = self._create_mock_vector_store()
        
        # 创建检索引擎
        self.retrieval_engine = TimeAccurateRetrievalEngine(
            self.config, self.mock_vector_store, self.timestamp_db
        )
        
        # 创建时间线生成器
        self.timeline_generator = VideoTimelineGenerator(self.retrieval_engine)
        
        print("时间戳精确检索演示环境初始化完成")
    
    def _create_mock_vector_store(self):
        """创建模拟向量存储"""
        class MockVectorStore:
            async def search_vectors(self, collection_name, query_vector, top_k, score_threshold=0.0):
                # 模拟向量搜索结果
                results = []
                for i in range(min(top_k, 10)):
                    results.append({
                        'vector_id': f'vector_demo_{i}',
                        'score': 0.9 - i * 0.05,
                        'payload': {'segment_id': f'demo_segment_{i}'}
                    })
                return results
        
        return MockVectorStore()
    
    def create_demo_timestamps(self):
        """创建演示用的时间戳数据"""
        print("\n创建演示时间戳数据...")
        
        # 创建视频时间戳
        video_timestamps = []
        for i in range(20):
            start_time = i * 3.0  # 每3秒一个段
            end_time = start_time + 2.0  # 每段2秒，有1秒间隔
            
            timestamp_info = TimestampInfo(
                file_id="demo_video.mp4",
                segment_id=f"video_segment_{i}",
                modality=ModalityType.VISUAL,
                start_time=start_time,
                end_time=end_time,
                duration=2.0,
                frame_index=int(start_time * 30),
                vector_id=f"vector_demo_{i}",
                confidence=0.8 + (i % 3) * 0.1,
                scene_boundary=(i % 5 == 0)  # 每5个段标记一个场景边界
            )
            video_timestamps.append(timestamp_info)
        
        # 创建音频时间戳
        audio_timestamps = []
        for i in range(15):
            start_time = i * 4.0  # 每4秒一个音频段
            end_time = start_time + 3.0  # 每段3秒
            
            modality = ModalityType.AUDIO_MUSIC if i % 2 == 0 else ModalityType.AUDIO_SPEECH
            
            timestamp_info = TimestampInfo(
                file_id="demo_video.mp4",
                segment_id=f"audio_segment_{i}",
                modality=modality,
                start_time=start_time,
                end_time=end_time,
                duration=3.0,
                vector_id=f"vector_audio_{i}",
                confidence=0.7 + (i % 4) * 0.1
            )
            audio_timestamps.append(timestamp_info)
        
        # 批量插入时间戳
        all_timestamps = video_timestamps + audio_timestamps
        self.timestamp_db.batch_insert_timestamp_infos(all_timestamps)
        
        print(f"创建了 {len(video_timestamps)} 个视频时间戳和 {len(audio_timestamps)} 个音频时间戳")
        return video_timestamps, audio_timestamps
    
    async def demo_basic_retrieval(self):
        """演示基本的时间戳检索"""
        print("\n=== 基本时间戳检索演示 ===")
        
        # 创建查询
        query_vector = np.random.rand(512)
        query = RetrievalQuery(
            query_vector=query_vector,
            target_modality=ModalityType.VISUAL,
            top_k=5
        )
        
        # 执行检索
        results = await self.retrieval_engine.retrieve_with_timestamp(query)
        
        print(f"检索到 {len(results)} 个结果:")
        for i, result in enumerate(results):
            print(f"  {i+1}. 段ID: {result.segment_id}")
            print(f"     时间: {result.start_time:.1f}s - {result.end_time:.1f}s (时长: {result.duration:.1f}s)")
            print(f"     得分: {result.score:.3f}, 置信度: {result.confidence:.3f}")
            print(f"     时间精度: {result.time_accuracy}")
            print(f"     是否合并: {result.is_merged} (合并数: {result.merged_count})")
            print()
    
    def demo_precise_video_segment(self):
        """演示精确视频段定位"""
        print("\n=== 精确视频段定位演示 ===")
        
        target_times = [5.5, 12.3, 25.8, 45.2]
        
        for target_time in target_times:
            result = self.retrieval_engine.get_precise_video_segment(
                "demo_video.mp4", target_time, context_window=10.0
            )
            
            if result:
                center_time = result.start_time + result.duration / 2
                time_diff = abs(center_time - target_time)
                
                print(f"目标时间: {target_time:.1f}s")
                print(f"  找到段: {result.segment_id}")
                print(f"  段时间: {result.start_time:.1f}s - {result.end_time:.1f}s")
                print(f"  段中心: {center_time:.1f}s")
                print(f"  时间差: {time_diff:.3f}s")
                print(f"  精度满足: {'✓' if time_diff <= 2.0 else '✗'}")
            else:
                print(f"目标时间: {target_time:.1f}s - 未找到匹配段")
            print()
    
    def demo_continuous_timeline(self):
        """演示连续时间线获取"""
        print("\n=== 连续时间线演示 ===")
        
        timeline = self.retrieval_engine.get_continuous_video_timeline("demo_video.mp4")
        
        print(f"时间线包含 {len(timeline)} 个段:")
        
        # 检测时间间隙
        gaps = []
        for i in range(len(timeline) - 1):
            current_end = timeline[i].end_time
            next_start = timeline[i + 1].start_time
            gap_duration = next_start - current_end
            
            if gap_duration > 0.1:  # 100ms以上的间隙
                gaps.append({
                    'after_segment': timeline[i].segment_id,
                    'before_segment': timeline[i + 1].segment_id,
                    'gap_start': current_end,
                    'gap_end': next_start,
                    'gap_duration': gap_duration
                })
        
        print(f"检测到 {len(gaps)} 个时间间隙:")
        for gap in gaps[:5]:  # 只显示前5个间隙
            print(f"  间隙: {gap['gap_start']:.1f}s - {gap['gap_end']:.1f}s (时长: {gap['gap_duration']:.1f}s)")
            print(f"  位置: {gap['after_segment']} -> {gap['before_segment']}")
        
        # 显示时间线覆盖率
        total_duration = timeline[-1].end_time - timeline[0].start_time
        covered_duration = sum(segment.duration for segment in timeline)
        coverage_rate = covered_duration / total_duration if total_duration > 0 else 0
        
        print(f"\n时间线统计:")
        print(f"  总时长: {total_duration:.1f}s")
        print(f"  覆盖时长: {covered_duration:.1f}s")
        print(f"  覆盖率: {coverage_rate:.1%}")
    
    def demo_multimodal_sync(self):
        """演示多模态同步结果"""
        print("\n=== 多模态同步演示 ===")
        
        target_timestamps = [10.0, 25.0, 40.0]
        
        for target_time in target_timestamps:
            results = self.retrieval_engine.get_multimodal_synchronized_results(
                "demo_video.mp4", target_time, time_window=8.0
            )
            
            print(f"目标时间: {target_time:.1f}s (±4s窗口)")
            
            for modality, modality_results in results.items():
                print(f"  {modality}: {len(modality_results)} 个段")
                
                for result in modality_results[:2]:  # 只显示前2个结果
                    sync_diff = abs(result.start_time + result.duration/2 - target_time)
                    print(f"    段: {result.segment_id}")
                    print(f"    时间: {result.start_time:.1f}s - {result.end_time:.1f}s")
                    print(f"    同步差异: {sync_diff:.3f}s")
            print()
    
    def demo_timeline_generation(self):
        """演示时间线生成"""
        print("\n=== 视频时间线生成演示 ===")
        
        timeline_data = self.timeline_generator.generate_timeline(
            "demo_video.mp4", resolution=20
        )
        
        if 'error' in timeline_data:
            print(f"时间线生成失败: {timeline_data['error']}")
            return
        
        print("时间线生成成功:")
        print(f"  文件: {timeline_data['file_id']}")
        print(f"  时长: {timeline_data['duration']:.1f}s")
        print(f"  分辨率: {timeline_data['resolution']} 个时间点")
        print(f"  场景边界: {len(timeline_data['scene_boundaries'])} 个")
        
        # 显示统计信息
        stats = timeline_data['statistics']
        print(f"\n统计信息:")
        print(f"  总段数: {stats['total_segments']}")
        print(f"  视觉段: {stats['visual_segments']}")
        print(f"  音频段: {stats['audio_segments']}")
        print(f"  场景数: {stats['scene_count']}")
        print(f"  平均置信度: {stats['avg_confidence']:.3f}")
        
        # 显示活动强度最高的时间点
        time_points = timeline_data['time_points']
        top_activity_points = sorted(time_points, key=lambda x: x['activity_score'], reverse=True)[:5]
        
        print(f"\n活动强度最高的时间点:")
        for i, point in enumerate(top_activity_points):
            print(f"  {i+1}. 时间: {point['time']:.1f}s")
            print(f"     活动强度: {point['activity_score']:.2f}")
            print(f"     段数: {point['segment_count']}")
            print(f"     模态: {', '.join(point['modalities'])}")
    
    def demo_accuracy_validation(self):
        """演示检索精度验证"""
        print("\n=== 检索精度验证演示 ===")
        
        # 获取一些检索结果进行验证
        query_vector = np.random.rand(512)
        query = RetrievalQuery(
            query_vector=query_vector,
            target_modality=ModalityType.VISUAL,
            top_k=10
        )
        
        # 执行检索
        results = asyncio.run(self.retrieval_engine.retrieve_with_timestamp(query))
        
        # 验证精度
        validation_report = self.retrieval_engine.validate_retrieval_accuracy(results)
        
        print("精度验证报告:")
        print(f"  总结果数: {validation_report['total_results']}")
        print(f"  精度合规: {validation_report['accuracy_compliant']}")
        print(f"  精度违规: {validation_report['accuracy_violations']}")
        print(f"  合规率: {validation_report['accuracy_rate']:.1%}")
        print(f"  平均时长: {validation_report['avg_duration']:.2f}s")
        print(f"  最大时长: {validation_report['max_duration']:.2f}s")
        print(f"  最小时长: {validation_report['min_duration']:.2f}s")
        
        if validation_report['violations']:
            print(f"\n精度违规详情:")
            for violation in validation_report['violations'][:3]:  # 只显示前3个
                print(f"  段ID: {violation['segment_id']}")
                print(f"  实际时长: {violation['duration']:.2f}s")
                print(f"  要求最大: {violation['required_max']:.2f}s")
    
    def demo_stream_processing(self):
        """演示视频音频流处理"""
        print("\n=== 视频音频流处理演示 ===")
        
        # 模拟媒体流信息
        from src.processors.video_audio_stream_processor import StreamInfo
        
        video_stream = StreamInfo(
            stream_type='video',
            codec='h264',
            duration=60.0,
            fps=30.0,
            width=1920,
            height=1080
        )
        
        audio_stream = StreamInfo(
            stream_type='audio',
            codec='aac',
            duration=60.0,
            sample_rate=16000,
            channels=1
        )
        
        print("媒体流信息:")
        print(f"  视频: {video_stream.codec}, {video_stream.fps}fps, {video_stream.width}x{video_stream.height}")
        print(f"  音频: {audio_stream.codec}, {audio_stream.sample_rate}Hz, {audio_stream.channels}声道")
        
        # 模拟场景信息
        scenes = [
            {'start_time': 0.0, 'end_time': 20.0, 'confidence': 0.9, 'scene_id': 0},
            {'start_time': 20.0, 'end_time': 40.0, 'confidence': 0.8, 'scene_id': 1},
            {'start_time': 40.0, 'end_time': 60.0, 'confidence': 0.85, 'scene_id': 2}
        ]
        
        # 模拟音频分类段
        audio_segments = [
            {'type': 'music', 'start_time': 0.0, 'end_time': 30.0, 'confidence': 0.9},
            {'type': 'speech', 'start_time': 30.0, 'end_time': 60.0, 'confidence': 0.8}
        ]
        
        # 处理视频流
        video_timestamps = self.stream_processor.process_video_stream(
            "demo_video.mp4", video_stream, scenes
        )
        
        # 处理音频流
        audio_timestamps = self.stream_processor.process_audio_stream(
            "demo_audio.wav", audio_stream, audio_segments
        )
        
        print(f"\n流处理结果:")
        print(f"  视频时间戳: {len(video_timestamps)} 个")
        print(f"  音频时间戳: {len(audio_timestamps)} 个")
        
        # 同步多模态流
        synchronized_stream = self.stream_processor.synchronize_video_audio_streams(
            video_timestamps, audio_timestamps
        )
        
        print(f"\n流同步结果:")
        print(f"  同步质量: {synchronized_stream.sync_quality:.3f}")
        print(f"  时间漂移: {synchronized_stream.time_drift:.3f}s")
        print(f"  同步点数: {len(synchronized_stream.sync_points)}")
        
        # 验证同步质量
        validation_report = self.stream_processor.validate_stream_synchronization(synchronized_stream)
        
        print(f"\n同步质量验证:")
        print(f"  质量等级: {validation_report['quality_grade']}")
        print(f"  视频段数: {validation_report['video_segments']}")
        print(f"  音频段数: {validation_report['audio_segments']}")
        
        if validation_report['recommendations']:
            print(f"  建议:")
            for rec in validation_report['recommendations']:
                print(f"    - {rec}")
    
    async def run_all_demos(self):
        """运行所有演示"""
        print("开始时间戳精确检索功能演示")
        print("=" * 50)
        
        # 创建演示数据
        self.create_demo_timestamps()
        
        # 运行各种演示
        await self.demo_basic_retrieval()
        self.demo_precise_video_segment()
        self.demo_continuous_timeline()
        self.demo_multimodal_sync()
        self.demo_timeline_generation()
        self.demo_accuracy_validation()
        self.demo_stream_processing()
        
        print("\n" + "=" * 50)
        print("所有演示完成！")
    
    def cleanup(self):
        """清理演示环境"""
        try:
            self.timestamp_db.close()
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            print("演示环境清理完成")
        except Exception as e:
            print(f"清理演示环境时出错: {e}")


async def main():
    """主函数"""
    demo = TimeAccurateRetrievalDemo()
    
    try:
        await demo.run_all_demos()
    except KeyboardInterrupt:
        print("\n演示被用户中断")
    except Exception as e:
        print(f"\n演示过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        demo.cleanup()


if __name__ == "__main__":
    asyncio.run(main())