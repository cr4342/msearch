"""
媒体处理器
负责具体处理媒体预处理的worker模块
"""

import asyncio
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import subprocess

from src.core.config_manager import get_config_manager


class MediaProcessor:
    """媒体处理器"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # 处理配置
        self.video_config = self.config_manager.get("media_processing.video", {})
        self.audio_config = self.config_manager.get("media_processing.audio", {})
        
        # 支持的文件类型
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif', '.svg', '.heic', '.heif'}
        self.video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.mpeg', '.mpg', '.3gp', '.webm', '.m4v', '.mts', '.m2ts'}
        self.audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus', '.amr', '.aiff', '.au'}
        self.logger.info("媒体处理器初始化完成")
    
    async def process(self, file_path: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理媒体文件
        
        Args:
            file_path: 文件路径
            strategy: 处理策略
            
        Returns:
            处理结果数据
        """
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext in self.image_extensions:
                return await self._process_image(file_path, strategy)
            elif file_ext in self.video_extensions:
                return await self._process_video(file_path, strategy)
            elif file_ext in self.audio_extensions:
                return await self._process_audio(file_path, strategy)
            else:
                raise ValueError(f"不支持的文件类型: {file_ext}")
        
        except Exception as e:
            self.logger.error(f"媒体处理失败: {file_path}, 错误: {e}")
            raise
    
    async def _process_image(self, file_path: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """处理图像文件"""
        self.logger.debug(f"处理图像文件: {file_path}")
        
        preprocessing = strategy.get('preprocessing', {})
        
        result = {
            'segments': [],
            'metadata': {}
        }
        
        try:
            # 读取图像数据
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            # 图像预处理
            if preprocessing.get('resize', False):
                target_resolution = preprocessing.get('target_resolution', 720)
                image_data = await self._resize_image(image_data, target_resolution)
            
            # 获取图像元数据
            image_metadata = await self._extract_image_metadata(file_path)
            
            # 创建图像片段
            segment = {
                'id': str(uuid.uuid4()),
                'segment_type': 'image',
                'data_path': file_path,
                'metadata': {
                    'width': image_metadata.get('width'),
                    'height': image_metadata.get('height'),
                    'format': Path(file_path).suffix[1:],
                    'size_bytes': len(image_data),
                    'color_mode': image_metadata.get('color_mode', 'RGB')
                }
            }
            
            result['segments'].append(segment)
            result['metadata']['total_segments'] = 1
            
            self.logger.debug(f"图像处理完成: {file_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"图像处理失败: {file_path}, 错误: {e}")
            raise
    
    async def _process_video(self, file_path: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """处理视频文件"""
        self.logger.debug(f"处理视频文件: {file_path}")
        
        preprocessing = strategy.get('preprocessing', {})
        
        result = {
            'segments': [],
            'metadata': {}
        }
        
        try:
            # 获取视频元数据
            video_metadata = await self._extract_video_metadata(file_path)
            result['metadata'] = video_metadata
            
            # 场景检测和切片
            if preprocessing.get('scene_detection', True):
                max_segment_duration = preprocessing.get('max_segment_duration', 5)
                target_fps = preprocessing.get('target_fps', 8)
                
                segments = await self._detect_video_scenes(
                    file_path, 
                    max_segment_duration,
                    target_fps
                )
                
                result['segments'].extend(segments)
            
            # 音频分离
            if preprocessing.get('audio_separation', False) and video_metadata.get('has_audio', False):
                audio_path = await self._extract_audio_from_video(file_path)
                
                # 创建音频片段
                audio_segment = {
                    'id': str(uuid.uuid4()),
                    'segment_type': 'audio',
                    'data_path': audio_path,
                    'metadata': {
                        'source': 'video',
                        'sample_rate': self.audio_config.get('sample_rate', 16000),
                        'channels': self.audio_config.get('channels', 1),
                        'duration': video_metadata.get('duration', 0)
                    }
                }
                
                result['segments'].append(audio_segment)
            
            result['metadata']['total_segments'] = len(result['segments'])
            
            self.logger.debug(f"视频处理完成: {file_path}, 片段数: {len(result['segments'])}")
            return result
            
        except Exception as e:
            self.logger.error(f"视频处理失败: {file_path}, 错误: {e}")
            raise
    
    async def _process_audio(self, file_path: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """处理音频文件"""
        self.logger.debug(f"处理音频文件: {file_path}")
        
        preprocessing = strategy.get('preprocessing', {})
        
        result = {
            'segments': [],
            'metadata': {}
        }
        
        try:
            # 获取音频元数据
            audio_metadata = await self._extract_audio_metadata(file_path)
            result['metadata'] = audio_metadata
            
            # 格式转换
            if preprocessing.get('format_conversion', False):
                sample_rate = preprocessing.get('sample_rate', 16000)
                channels = preprocessing.get('channels', 1)
                
                converted_path = await self._convert_audio_format(
                    file_path, 
                    sample_rate, 
                    channels
                )
                
                # 创建音频片段
                segment = {
                    'id': str(uuid.uuid4()),
                    'segment_type': 'audio',
                    'data_path': converted_path,
                    'metadata': {
                        'sample_rate': sample_rate,
                        'channels': channels,
                        'duration': audio_metadata.get('duration', 0),
                        'format': 'wav'
                    }
                }
                
                result['segments'].append(segment)
            else:
                # 使用原始文件
                segment = {
                    'id': str(uuid.uuid4()),
                    'segment_type': 'audio',
                    'data_path': file_path,
                    'metadata': audio_metadata
                }
                
                result['segments'].append(segment)
            
            result['metadata']['total_segments'] = 1
            
            self.logger.debug(f"音频处理完成: {file_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"音频处理失败: {file_path}, 错误: {e}")
            raise
    
    async def _resize_image(self, image_data: bytes, target_resolution: int) -> bytes:
        """使用ffmpeg调整图像分辨率"""
        try:
            # 创建临时文件保存输入图像
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_in:
                tmp_in.write(image_data)
                tmp_in_path = tmp_in.name
            
            # 创建临时文件保存输出图像
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_out:
                tmp_out_path = tmp_out.name
            
            # 使用ffmpeg调整分辨率
            cmd = [
                'ffmpeg',
                '-i', tmp_in_path,
                '-vf', f'scale=-1:{target_resolution}',  # 保持宽高比，高度为目标分辨率
                '-y',
                tmp_out_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"ffmpeg图像缩放失败: {stderr.decode()}")
                return image_data
            
            # 读取调整后的图像数据
            with open(tmp_out_path, 'rb') as f:
                resized_data = f.read()
            
            # 清理临时文件
            os.unlink(tmp_in_path)
            os.unlink(tmp_out_path)
            
            return resized_data
            
        except Exception as e:
            self.logger.error(f"图像分辨率调整失败: {e}")
            return image_data
    
    async def _extract_video_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取视频元数据"""
        try:
            # 使用ffprobe获取视频信息
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"ffprobe执行失败: {stderr.decode()}")
                return {}
            
            import json
            probe_data = json.loads(stdout.decode())
            
            # 提取视频流信息
            video_stream = None
            audio_stream = None
            
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                elif stream.get('codec_type') == 'audio':
                    audio_stream = stream
            
            metadata = {
                'duration': float(probe_data['format'].get('duration', 0)),
                'size': int(probe_data['format'].get('size', 0)),
                'has_audio': audio_stream is not None,
                'width': int(video_stream.get('width', 0)) if video_stream else 0,
                'height': int(video_stream.get('height', 0)) if video_stream else 0,
                'fps': self._parse_fps(video_stream.get('r_frame_rate', '0/1')) if video_stream else 0
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"提取视频元数据失败: {e}")
            return {}
    
    def _parse_fps(self, fps_str: str) -> float:
        """解析帧率字符串"""
        try:
            if '/' in fps_str:
                num, den = fps_str.split('/')
                return float(num) / float(den)
            return float(fps_str)
        except:
            return 0.0
    
    async def _detect_video_scenes(self, file_path: str, max_duration: float, target_fps: int) -> List[Dict[str, Any]]:
        """检测视频场景并切片"""
        try:
            # 使用ffmpeg进行场景检测
            temp_dir = tempfile.mkdtemp()
            scenes_file = os.path.join(temp_dir, 'scenes.txt')
            
            # 场景检测命令
            cmd = [
                'ffmpeg',
                '-i', file_path,
                '-vf', f"select='gt(scene,0.15)',showinfo",
                '-f', 'null',
                '-'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # 解析场景时间点
            scene_times = self._parse_scene_times(stderr.decode())
            
            # 生成切片
            segments = []
            video_metadata = await self._extract_video_metadata(file_path)
            total_duration = video_metadata.get('duration', 0)
            
            current_time = 0.0
            segment_index = 0
            
            for scene_time in scene_times + [total_duration]:
                # 如果场景过长，按最大时长切分
                while scene_time - current_time > max_duration:
                    segment_end = current_time + max_duration
                    
                    segment = await self._extract_video_frame(
                        file_path, 
                        current_time, 
                        segment_end,
                        segment_index
                    )
                    
                    if segment:
                        segments.append(segment)
                        segment_index += 1
                    
                    current_time = segment_end
                
                # 场景边界切片
                if scene_time > current_time:
                    segment = await self._extract_video_frame(
                        file_path,
                        current_time,
                        scene_time,
                        segment_index
                    )
                    
                    if segment:
                        segments.append(segment)
                        segment_index += 1
                    
                    current_time = scene_time
            
            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir)
            
            return segments
            
        except Exception as e:
            self.logger.error(f"视频场景检测失败: {e}")
            return []
    
    def _parse_scene_times(self, ffmpeg_output: str) -> List[float]:
        """解析ffmpeg场景检测输出"""
        scene_times = []
        
        for line in ffmpeg_output.split('\n'):
            if 'pts_time:' in line:
                try:
                    # 提取时间戳
                    start = line.find('pts_time:') + 9
                    end = line.find(' ', start)
                    time_str = line[start:end]
                    scene_times.append(float(time_str))
                except:
                    continue
        
        return scene_times
    
    async def _extract_video_frame(self, file_path: str, start_time: float, end_time: float, segment_index: int) -> Optional[Dict[str, Any]]:
        """提取视频帧"""
        try:
            # 计算中间时间点
            mid_time = (start_time + end_time) / 2
            
            # 创建临时文件
            temp_dir = tempfile.mkdtemp()
            frame_path = os.path.join(temp_dir, f'frame_{segment_index}.jpg')
            
            # 提取帧命令
            cmd = [
                'ffmpeg',
                '-ss', str(mid_time),
                '-i', file_path,
                '-vframes', '1',
                '-q:v', '2',
                '-y',
                frame_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"提取视频帧失败: {stderr.decode()}")
                return None
            
            # 读取帧数据
            with open(frame_path, 'rb') as f:
                frame_data = f.read()
            
            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir)
            
            # 创建片段
            segment = {
                'id': str(uuid.uuid4()),
                'segment_type': 'video_frame',
                'data_path': frame_path,
                'metadata': {
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'frame_time': mid_time,
                    'segment_index': segment_index,
                    'size_bytes': len(frame_data)
                }
            }
            
            return segment
            
        except Exception as e:
            self.logger.error(f"提取视频帧失败: {e}")
            return None
    
    async def _extract_audio_from_video(self, file_path: str) -> str:
        """从视频中提取音频"""
        try:
            # 创建临时文件
            temp_dir = tempfile.mkdtemp()
            audio_path = os.path.join(temp_dir, 'extracted_audio.wav')
            
            # 音频提取命令
            cmd = [
                'ffmpeg',
                '-i', file_path,
                '-vn',  # 不处理视频
                '-acodec', 'pcm_s16le',  # PCM 16位编码
                '-ar', str(self.audio_config.get('sample_rate', 16000)),
                '-ac', str(self.audio_config.get('channels', 1)),
                '-y',
                audio_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"音频提取失败: {stderr.decode()}")
                return ""
            
            return audio_path
            
        except Exception as e:
            self.logger.error(f"音频提取失败: {e}")
            return ""
    
    async def _extract_audio_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取音频元数据"""
        try:
            # 使用ffprobe获取音频信息
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"ffprobe执行失败: {stderr.decode()}")
                return {}
            
            import json
            probe_data = json.loads(stdout.decode())
            
            # 提取音频流信息
            audio_stream = None
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                return {}
            
            metadata = {
                'duration': float(probe_data['format'].get('duration', 0)),
                'size': int(probe_data['format'].get('size', 0)),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'codec': audio_stream.get('codec_name', 'unknown'),
                'bit_rate': int(audio_stream.get('bit_rate', 0))
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"提取音频元数据失败: {e}")
            return {}
    
    async def _convert_audio_format(self, file_path: str, sample_rate: int, channels: int) -> str:
        """转换音频格式"""
        try:
            # 创建临时文件
            temp_dir = tempfile.mkdtemp()
            output_path = os.path.join(temp_dir, 'converted_audio.wav')
            
            # 格式转换命令
            cmd = [
                'ffmpeg',
                '-i', file_path,
                '-ar', str(sample_rate),
                '-ac', str(channels),
                '-acodec', 'pcm_s16le',
                '-y',
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"音频格式转换失败: {stderr.decode()}")
                return file_path
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"音频格式转换失败: {e}")
            return file_path
    
    async def _extract_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取图像元数据"""
        try:
            # 使用PIL库获取图像元数据
            from PIL import Image
            
            with Image.open(file_path) as img:
                metadata = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'color_mode': img.mode,
                    'has_transparency': img.mode in ('RGBA', 'LA', 'P'),
                }
                
                # 获取更多详细信息
                if hasattr(img, 'info'):
                    metadata.update(img.info)
                
                return metadata
                
        except ImportError:
            # 如果PIL不可用，使用基础方法
            try:
                with open(file_path, 'rb') as f:
                    # 简单的文件信息
                    import os
                    stat = os.stat(file_path)
                    
                    return {
                        'width': None,
                        'height': None,
                        'format': Path(file_path).suffix[1:].upper(),
                        'size_bytes': stat.st_size,
                        'color_mode': 'Unknown'
                    }
            except Exception as e:
                self.logger.error(f"获取图像元数据失败: {e}")
                return {
                    'width': None,
                    'height': None,
                    'format': Path(file_path).suffix[1:].upper(),
                    'color_mode': 'Unknown'
                }
        except Exception as e:
            self.logger.error(f"提取图像元数据失败: {e}")
            return {
                'width': None,
                'height': None,
                'format': Path(file_path).suffix[1:].upper(),
                'color_mode': 'Unknown'
            }
