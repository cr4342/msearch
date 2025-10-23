"""
多模态处理流水线集成测试
测试CLIP、CLAP、Whisper模型协同工作和时间戳同步
"""
import pytest
import asyncio
import numpy as np
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch

from src.business.processing_orchestrator import ProcessingOrchestrator
from src.business.media_processor import MediaProcessor
from src.business.embedding_engine import EmbeddingEngine
from src.processors.timestamp_processor import TimestampProcessor
from src.core.config_manager import ConfigManager


class TestMultimodalProcessingPipeline:
    """多模态处理流水线集成测试"""
    
    @pytest.fixture
    def integration_config(self):
        """集成测试配置"""
        config = Mock(spec=ConfigManager)
        config.get.side_effect = lambda key, default=None: {
            # 基础配置
            'general.data_dir': './test_data',
            'processing.batch_size': 8,
            'processing.max_concurrent_tasks': 2,
            
            # 模型配置
            'embedding.models_dir': './data/models',
            'embedding.models.clip': 'clip',
            'embedding.models.clap': 'clap',
            'embedding.models.whisper': 'whisper',
            
            # 处理策略配置
            'processing.video.frame_interval': 2,
            'processing.video.max_resolution': [1280, 720],
            'processing.audio.sample_rate': 16000,
            'processing.audio.segment_duration': 10,
            
            # 时间戳配置
            'processing.timestamp.accuracy_requirement': 2.0,
            'processing.timestamp.overlap_buffer': 1.0,
            
            # 设备配置
            'device': 'cpu'
        }.get(key, default)
        return config
    
    @pytest.fixture
    def mock_infinity_engines(self):
        """模拟infinity引擎"""
        with patch('src.business.embedding_engine.AsyncEngineArray') as mock_engine_array:
            # 创建不同模型的mock引擎
            clip_engine = AsyncMock()
            clap_engine = AsyncMock()
            whisper_engine = AsyncMock()
            
            # 设置不同模型的返回值
            clip_engine.embed.return_value = [np.random.rand(512).tolist()]
            clap_engine.embed.return_value = [np.random.rand(512).tolist()]
            whisper_engine.embed.return_value = [np.random.rand(512).tolist()]
            
            # 模拟引擎数组
            mock_engine_array.from_args.return_value = Mock(
                clip=clip_engine,
                clap=clap_engine,
                whisper=whisper_engine
            )
            
            yield {
                'clip': clip_engine,
                'clap': clap_engine,
                'whisper': whisper_engine
            }
    
    @pytest.fixture
    def processing_pipeline(self, integration_config, mock_infinity_engines):
        """处理流水线实例"""
        orchestrator = ProcessingOrchestrator(config=integration_config)
        
        # 注入模拟的组件
        orchestrator.media_processor = MediaProcessor(config=integration_config)
        orchestrator.embedding_engine = EmbeddingEngine(config=integration_config)
        orchestrator.timestamp_processor = TimestampProcessor(config=integration_config)
        
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_video_multimodal_processing(self, processing_pipeline, mock_infinity_engines):
        """测试视频多模态处理流程"""
        # 创建模拟视频文件
        test_video_path = "test_video.mp4"
        
        # 模拟视频元数据
        video_metadata = {
            'duration': 60.0,  # 60秒视频
            'fps': 30.0,
            'resolution': '1920x1080',
            'has_audio': True
        }
        
        # 模拟媒体处理器返回
        with patch.object(processing_pipeline.media_processor, 'process_video') as mock_process_video:
            mock_process_video.return_value = {
                'visual_frames': [
                    {'frame_data': np.random.rand(224, 224, 3), 'timestamp': 2.0},
                    {'frame_data': np.random.rand(224, 224, 3), 'timestamp': 4.0},
                    {'frame_data': np.random.rand(224, 224, 3), 'timestamp': 6.0},
                ],
                'audio_segments': [
                    {'audio_data': np.random.rand(16000), 'start_time': 0.0, 'end_time': 10.0, 'type': 'music'},
                    {'audio_data': np.random.rand(16000), 'start_time': 10.0, 'end_time': 20.0, 'type': 'speech'},
                ],
                'metadata': video_metadata
            }
            
            # 执行多模态处理
            result = await processing_pipeline.process_file(test_video_path)
            
            # 验证处理结果
            assert result['status'] == 'success'
            assert 'visual_vectors' in result
            assert 'audio_vectors' in result
            assert 'timestamps' in result
            
            # 验证视觉向量
            visual_vectors = result['visual_vectors']
            assert len(visual_vectors) == 3  # 3个视频帧
            for vector_data in visual_vectors:
                assert len(vector_data['vector']) == 512
                assert 'timestamp' in vector_data
                assert vector_data['modality'] == 'visual'
            
            # 验证音频向量
            audio_vectors = result['audio_vectors']
            assert len(audio_vectors) == 2  # 2个音频片段
            for vector_data in audio_vectors:
                assert len(vector_data['vector']) == 512
                assert 'start_time' in vector_data
                assert 'end_time' in vector_data
                assert vector_data['modality'] in ['audio_music', 'audio_speech']
    
    @pytest.mark.asyncio
    async def test_timestamp_synchronization(self, processing_pipeline, mock_infinity_engines):
        """测试多模态时间戳同步"""
        test_video_path = "sync_test_video.mp4"
        
        # 模拟有时间戳偏差的处理结果
        with patch.object(processing_pipeline.media_processor, 'process_video') as mock_process_video:
            mock_process_video.return_value = {
                'visual_frames': [
                    {'frame_data': np.random.rand(224, 224, 3), 'timestamp': 10.0},
                ],
                'audio_segments': [
                    {'audio_data': np.random.rand(16000), 'start_time': 10.05, 'end_time': 12.05, 'type': 'music'},  # 50ms偏差
                ],
                'metadata': {'duration': 30.0, 'fps': 30.0}
            }
            
            # 执行处理
            result = await processing_pipeline.process_file(test_video_path)
            
            # 验证时间戳同步
            visual_timestamp = result['visual_vectors'][0]['timestamp']
            audio_start_time = result['audio_vectors'][0]['start_time']
            
            # 时间戳差异应该在同步容差范围内
            time_diff = abs(visual_timestamp - audio_start_time)
            assert time_diff <= 0.1, f"时间戳同步偏差过大: {time_diff}s"
            
            # 验证时间戳精度满足±2秒要求
            for vector_data in result['visual_vectors']:
                if 'duration' in vector_data:
                    assert vector_data['duration'] <= 4.0  # ±2秒 = 4秒总时长
            
            for vector_data in result['audio_vectors']:
                duration = vector_data['end_time'] - vector_data['start_time']
                assert duration <= 4.0  # ±2秒精度要求
    
    @pytest.mark.asyncio
    async def test_scene_aware_processing(self, processing_pipeline, mock_infinity_engines):
        """测试场景感知处理"""
        test_long_video_path = "long_video.mp4"
        
        # 模拟长视频场景检测结果
        with patch.object(processing_pipeline.media_processor, 'process_video') as mock_process_video:
            mock_process_video.return_value = {
                'scenes': [
                    {
                        'scene_id': 'scene_1',
                        'start_time': 0.0,
                        'end_time': 30.0,
                        'frames': [
                            {'frame_data': np.random.rand(224, 224, 3), 'timestamp': 5.0},
                            {'frame_data': np.random.rand(224, 224, 3), 'timestamp': 15.0},
                            {'frame_data': np.random.rand(224, 224, 3), 'timestamp': 25.0},
                        ]
                    },
                    {
                        'scene_id': 'scene_2',
                        'start_time': 30.0,
                        'end_time': 60.0,
                        'frames': [
                            {'frame_data': np.random.rand(224, 224, 3), 'timestamp': 35.0},
                            {'frame_data': np.random.rand(224, 224, 3), 'timestamp': 45.0},
                            {'frame_data': np.random.rand(224, 224, 3), 'timestamp': 55.0},
                        ]
                    }
                ],
                'audio_segments': [
                    {'audio_data': np.random.rand(16000), 'start_time': 0.0, 'end_time': 30.0, 'scene_id': 'scene_1'},
                    {'audio_data': np.random.rand(16000), 'start_time': 30.0, 'end_time': 60.0, 'scene_id': 'scene_2'},
                ],
                'metadata': {'duration': 120.0, 'fps': 30.0}
            }
            
            # 执行场景感知处理
            result = await processing_pipeline.process_file(test_long_video_path)
            
            # 验证场景边界保持完整
            visual_vectors = result['visual_vectors']
            scene_1_vectors = [v for v in visual_vectors if v.get('scene_id') == 'scene_1']
            scene_2_vectors = [v for v in visual_vectors if v.get('scene_id') == 'scene_2']
            
            assert len(scene_1_vectors) == 3
            assert len(scene_2_vectors) == 3
            
            # 验证场景内时间戳连续性
            for scene_vectors in [scene_1_vectors, scene_2_vectors]:
                timestamps = [v['timestamp'] for v in scene_vectors]
                timestamps.sort()
                
                # 场景内时间戳应该连续
                for i in range(len(timestamps) - 1):
                    time_gap = timestamps[i + 1] - timestamps[i]
                    assert time_gap <= 20.0  # 合理的时间间隔
    
    @pytest.mark.asyncio
    async def test_batch_processing_optimization(self, processing_pipeline, mock_infinity_engines):
        """测试批处理优化"""
        # 模拟大批量数据
        large_batch_data = {
            'visual_frames': [
                {'frame_data': np.random.rand(224, 224, 3), 'timestamp': i * 2.0}
                for i in range(32)  # 32帧
            ],
            'audio_segments': [
                {'audio_data': np.random.rand(16000), 'start_time': i * 10.0, 'end_time': (i + 1) * 10.0}
                for i in range(16)  # 16个音频片段
            ]
        }
        
        with patch.object(processing_pipeline.media_processor, 'process_video') as mock_process_video:
            mock_process_video.return_value = large_batch_data
            
            # 测试批处理性能
            import time
            start_time = time.time()
            
            result = await processing_pipeline.process_file("large_video.mp4")
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 验证批处理效果
            assert len(result['visual_vectors']) == 32
            assert len(result['audio_vectors']) == 16
            
            # 批处理应该提升处理效率
            assert processing_time < 5.0  # 应该在5秒内完成
            
            # 验证所有向量都是512维
            for vector_data in result['visual_vectors']:
                assert len(vector_data['vector']) == 512
            
            for vector_data in result['audio_vectors']:
                assert len(vector_data['vector']) == 512
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, processing_pipeline, mock_infinity_engines):
        """测试错误处理和恢复"""
        test_video_path = "error_test_video.mp4"
        
        # 模拟处理过程中的错误
        with patch.object(processing_pipeline.media_processor, 'process_video') as mock_process_video:
            # 第一次调用失败
            mock_process_video.side_effect = [
                Exception("处理失败"),
                {  # 重试成功
                    'visual_frames': [
                        {'frame_data': np.random.rand(224, 224, 3), 'timestamp': 5.0},
                    ],
                    'audio_segments': [
                        {'audio_data': np.random.rand(16000), 'start_time': 0.0, 'end_time': 10.0},
                    ],
                    'metadata': {'duration': 30.0, 'fps': 30.0}
                }
            ]
            
            # 执行处理（应该自动重试）
            result = await processing_pipeline.process_file_with_retry(test_video_path, max_retries=2)
            
            # 验证重试机制工作
            assert result['status'] == 'success'
            assert len(result['visual_vectors']) == 1
            assert len(result['audio_vectors']) == 1
            
            # 验证调用了两次（第一次失败，第二次成功）
            assert mock_process_video.call_count == 2
    
    @pytest.mark.asyncio
    async def test_memory_efficient_processing(self, processing_pipeline, mock_infinity_engines):
        """测试内存高效处理"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        # 模拟大文件处理
        large_video_data = {
            'visual_frames': [
                {'frame_data': np.random.rand(224, 224, 3), 'timestamp': i * 1.0}
                for i in range(100)  # 100帧
            ],
            'audio_segments': [
                {'audio_data': np.random.rand(16000), 'start_time': i * 5.0, 'end_time': (i + 1) * 5.0}
                for i in range(50)  # 50个音频片段
            ]
        }
        
        with patch.object(processing_pipeline.media_processor, 'process_video') as mock_process_video:
            mock_process_video.return_value = large_video_data
            
            # 执行大文件处理
            result = await processing_pipeline.process_file("large_file.mp4")
            
            final_memory = process.memory_info().rss / (1024 * 1024)  # MB
            memory_increase = final_memory - initial_memory
            
            # 验证内存使用在合理范围内
            assert memory_increase < 200, f"内存增长过多: {memory_increase}MB"
            
            # 验证处理结果完整
            assert len(result['visual_vectors']) == 100
            assert len(result['audio_vectors']) == 50


class TestMultimodalIntegrationPerformance:
    """多模态集成性能测试"""
    
    @pytest.mark.asyncio
    async def test_processing_speed_benchmarks(self):
        """测试处理速度基准"""
        config = Mock(spec=ConfigManager)
        config.get.side_effect = lambda key, default=None: {
            'processing.batch_size': 16,
            'device': 'cpu'
        }.get(key, default)
        
        orchestrator = ProcessingOrchestrator(config=config)
        
        # 模拟不同大小的文件处理
        test_cases = [
            {'duration': 30, 'expected_time': 10},   # 30秒视频应在10秒内处理完
            {'duration': 60, 'expected_time': 20},   # 60秒视频应在20秒内处理完
            {'duration': 120, 'expected_time': 40},  # 120秒视频应在40秒内处理完
        ]
        
        for test_case in test_cases:
            with patch.object(orchestrator, 'media_processor') as mock_processor:
                # 模拟处理结果
                mock_processor.process_video.return_value = {
                    'visual_frames': [
                        {'frame_data': np.random.rand(224, 224, 3), 'timestamp': i * 2.0}
                        for i in range(test_case['duration'] // 2)
                    ],
                    'audio_segments': [
                        {'audio_data': np.random.rand(16000), 'start_time': i * 10.0, 'end_time': (i + 1) * 10.0}
                        for i in range(test_case['duration'] // 10)
                    ]
                }
                
                # 测试处理时间
                import time
                start_time = time.time()
                
                result = await orchestrator.process_file(f"test_{test_case['duration']}s.mp4")
                
                end_time = time.time()
                actual_time = end_time - start_time
                
                # 验证处理速度满足要求
                assert actual_time < test_case['expected_time'], \
                    f"{test_case['duration']}秒视频处理时间过长: {actual_time}s > {test_case['expected_time']}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self):
        """测试并发处理能力"""
        config = Mock(spec=ConfigManager)
        config.get.side_effect = lambda key, default=None: {
            'processing.max_concurrent_tasks': 4,
            'processing.batch_size': 8
        }.get(key, default)
        
        orchestrator = ProcessingOrchestrator(config=config)
        
        # 创建多个并发任务
        tasks = []
        for i in range(8):  # 8个并发任务
            task = orchestrator.process_file(f"concurrent_test_{i}.mp4")
            tasks.append(task)
        
        # 执行并发处理
        import time
        start_time = time.time()
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 验证并发处理效果
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 6  # 至少75%成功率
        
        # 并发处理应该比串行处理快
        assert total_time < 30  # 8个任务应该在30秒内完成