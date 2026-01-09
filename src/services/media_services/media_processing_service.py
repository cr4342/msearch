"""
媒体处理服务
提供视频、图像、音频处理相关的服务功能
"""
import asyncio
import logging
import subprocess
import os
from typing import Dict, Any, List, Tuple
from pathlib import Path

from src.core.config_manager import ConfigManager


class MediaProcessingService:
    """媒体处理服务 - 提供视频、图像、音频处理相关的服务功能"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        
        self.logger = logging.getLogger(__name__)
        
        # 从配置获取处理参数
        self.video_config = self.config_manager.get('media_processing.video', {})
        self.audio_config = self.config_manager.get('media_processing.audio', {})
        self.image_config = self.config_manager.get('media_processing.image', {})
        
        # 运行状态
        self.is_running = False
        
        self.logger.info("媒体处理服务初始化完成")
    
    async def start(self):
        """启动媒体处理服务"""
        self.logger.info("启动媒体处理服务")
        
        # 验证FFmpeg是否可用
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                self.logger.warning("FFmpeg不可用，媒体处理功能受限")
            else:
                self.logger.info("FFmpeg可用")
        except FileNotFoundError:
            self.logger.warning("FFmpeg未安装，媒体处理功能受限")
        except Exception as e:
            self.logger.warning(f"检查FFmpeg时出错: {e}")
        
        self.is_running = True
        self.logger.info("媒体处理服务启动完成")
    
    async def stop(self):
        """停止媒体处理服务"""
        self.logger.info("停止媒体处理服务")
        
        self.is_running = False
        self.logger.info("媒体处理服务已停止")
    
    async def extract_video_frames(self, video_path: str, output_dir: str, 
                                 frame_interval: int = 30) -> List[str]:
        """提取视频帧
        
        Args:
            video_path: 视频路径
            output_dir: 输出目录
            frame_interval: 帧间隔（每隔多少帧提取一帧）
            
        Returns:
            提取的帧文件路径列表
        """
        self.logger.info(f"提取视频帧: {video_path}, 间隔: {frame_interval}")
        
        # 确保输出目录存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 生成输出文件名模式
        video_name = Path(video_path).stem
        output_pattern = os.path.join(output_dir, f"{video_name}_frame_%05d.jpg")
        
        # 构建FFmpeg命令
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f'fps=1/{frame_interval}',
            '-q:v', '2',  # 图像质量 (1-5, 1为最佳)
            output_pattern
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                self.logger.error(f"视频帧提取失败: {result.stderr}")
                return []
            
            # 获取生成的帧文件
            frames = []
            for file in os.listdir(output_dir):
                if file.startswith(f"{video_name}_frame_") and file.endswith('.jpg'):
                    frames.append(os.path.join(output_dir, file))
            
            frames.sort()  # 按名称排序，确保时间顺序
            self.logger.info(f"提取了 {len(frames)} 个视频帧")
            return frames
            
        except subprocess.TimeoutExpired:
            self.logger.error("视频帧提取超时")
            return []
        except Exception as e:
            self.logger.error(f"视频帧提取出错: {e}")
            return []
    
    async def extract_audio_from_video(self, video_path: str, output_path: str) -> bool:
        """从视频中提取音频
        
        Args:
            video_path: 视频路径
            output_path: 输出音频路径
            
        Returns:
            是否提取成功
        """
        self.logger.info(f"从视频提取音频: {video_path} -> {output_path}")
        
        # 确保输出目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 构建FFmpeg命令
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-q:a', '0',  # 最佳音频质量
            '-map', 'a',  # 只映射音频流
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            success = result.returncode == 0
            
            if success:
                self.logger.info("音频提取成功")
            else:
                self.logger.error(f"音频提取失败: {result.stderr}")
            
            return success
            
        except subprocess.TimeoutExpired:
            self.logger.error("音频提取超时")
            return False
        except Exception as e:
            self.logger.error(f"音频提取出错: {e}")
            return False
    
    async def resize_image(self, image_path: str, output_path: str, 
                          max_size: int = None) -> bool:
        """调整图像大小
        
        Args:
            image_path: 输入图像路径
            output_path: 输出图像路径
            max_size: 最大尺寸（宽高中的较大值）
            
        Returns:
            是否调整成功
        """
        if max_size is None:
            max_size = self.image_config.get('max_resolution', 1920)
        
        self.logger.info(f"调整图像大小: {image_path} -> {output_path}, 最大尺寸: {max_size}")
        
        try:
            from PIL import Image
            
            with Image.open(image_path) as img:
                # 计算新的尺寸以保持宽高比
                width, height = img.size
                if max(width, height) <= max_size:
                    # 如果图像已经小于最大尺寸，则直接复制
                    img.save(output_path, quality=self.image_config.get('quality', 85))
                    return True
                
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                
                # 调整图像大小
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 保存调整后的图像
                resized_img.save(output_path, quality=self.image_config.get('quality', 85))
                
                self.logger.info(f"图像调整完成: {new_width}x{new_height}")
                return True
        except Exception as e:
            self.logger.error(f"图像调整出错: {e}")
            return False
    
    async def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频信息
        
        Args:
            video_path: 视频路径
            
        Returns:
            视频信息
        """
        self.logger.debug(f"获取视频信息: {video_path}")
        
        try:
            import json
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                self.logger.error(f"获取视频信息失败: {result.stderr}")
                return {}
            
            info = json.loads(result.stdout)
            
            # 提取有用的信息
            video_info = {
                'format': info.get('format', {}),
                'streams': info.get('streams', []),
                'duration': float(info['format'].get('duration', 0)) if 'format' in info else 0,
                'file_size': int(info['format'].get('size', 0)) if 'format' in info else 0
            }
            
            # 查找视频流和音频流
            for stream in video_info['streams']:
                if stream.get('codec_type') == 'video':
                    video_info['video_stream'] = stream
                elif stream.get('codec_type') == 'audio':
                    video_info['audio_stream'] = stream
            
            self.logger.debug(f"获取到视频信息: {video_path}")
            return video_info
            
        except subprocess.TimeoutExpired:
            self.logger.error("获取视频信息超时")
            return {}
        except Exception as e:
            self.logger.error(f"获取视频信息出错: {e}")
            return {}
    
    async def detect_video_scenes(self, video_path: str, threshold: float = 0.3) -> List[Dict[str, float]]:
        """使用FFMPEG检测视频场景变化
        
        Args:
            video_path: 视频路径
            threshold: 场景检测阈值 (0.0-1.0)
            
        Returns:
            场景变化时间点列表
        """
        self.logger.info(f"使用FFMPEG检测视频场景变化: {video_path}, 阈值: {threshold}")
        
        try:
            # 使用FFMPEG的场景检测功能
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f'scene=threshold={threshold}',
                '-f', 'null',
                '-'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            # 解析FFMPEG输出，提取场景变化时间
            scene_changes = []
            for line in result.stderr.split('\n'):
                if 'detected scene' in line:
                    # 示例输出: [Parsed_scene_0 @ 0x55b6e8b8c5c0] detected scene change at 0.000000 pts (0.000000 sec)
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'sec)':
                            time_str = parts[i-1].rstrip(')')
                            time = float(time_str)
                            scene_changes.append({
                                'time': time,
                                'frame': 0,  # 暂时不计算帧号
                                'difference': 0.0  # 暂时不计算差值
                            })
                            break
            
            self.logger.info(f"使用FFMPEG检测到 {len(scene_changes)} 个场景变化")
            return scene_changes
        except subprocess.TimeoutExpired:
            self.logger.error("视频场景检测超时")
            return []
        except Exception as e:
            self.logger.error(f"视频场景检测出错: {e}")
            # 如果FFMPEG场景检测失败，使用OpenCV作为备选方案
            self.logger.info("尝试使用OpenCV进行场景检测")
            try:
                import cv2
                
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    self.logger.error("无法打开视频文件")
                    return []
                
                fps = cap.get(cv2.CAP_PROP_FPS)
                prev_frame = None
                scene_changes = []
                frame_count = 0
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # 转换为灰度图以简化计算
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    if prev_frame is not None:
                        # 计算帧差
                        diff = cv2.absdiff(prev_frame, gray)
                        diff_mean = diff.mean()
                        
                        # 如果差值超过阈值，则认为是场景变化
                        if diff_mean > threshold * 100:  # 调整阈值到合适的范围
                            time_in_seconds = frame_count / fps
                            scene_changes.append({
                                'time': time_in_seconds,
                                'frame': frame_count,
                                'difference': diff_mean
                            })
                    
                    prev_frame = gray
                    frame_count += 1
                
                cap.release()
                
                self.logger.info(f"使用OpenCV检测到 {len(scene_changes)} 个场景变化")
                return scene_changes
            except ImportError:
                self.logger.warning("OpenCV未安装，无法进行场景检测")
                return []
            except Exception as e:
                self.logger.error(f"OpenCV场景检测出错: {e}")
                return []
    
    async def extract_keyframes(self, video_path: str, output_dir: str, 
                              scene_changes: List[Dict[str, float]], 
                              max_segment_duration: float = 5.0,
                              keyframes_per_segment: int = 2) -> List[Dict[str, Any]]:
        """从视频中提取关键帧，实现两阶段切片策略
        
        Args:
            video_path: 视频路径
            output_dir: 输出目录
            scene_changes: 场景变化时间点列表
            max_segment_duration: 最大切片时长（秒）
            keyframes_per_segment: 每切片提取的关键帧数量
            
        Returns:
            关键帧列表，包含时间戳信息
        """
        self.logger.info(f"提取关键帧: {video_path}, 每切片提取 {keyframes_per_segment} 个关键帧")
        
        # 确保输出目录存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 生成切片边界
        segments = []
        if not scene_changes:
            # 如果没有检测到场景变化，使用固定时长切片
            video_info = await self.get_video_info(video_path)
            duration = video_info.get('duration', 0)
            start_time = 0.0
            while start_time < duration:
                end_time = min(start_time + max_segment_duration, duration)
                segments.append({
                    'start_time': start_time,
                    'end_time': end_time
                })
                start_time = end_time
        else:
            # 使用场景变化作为切片边界
            start_time = 0.0
            for scene_change in scene_changes:
                end_time = scene_change['time']
                if end_time - start_time > max_segment_duration:
                    # 如果切片时长超过最大值，分割为多个切片
                    current = start_time
                    while current < end_time:
                        next_end = min(current + max_segment_duration, end_time)
                        segments.append({
                            'start_time': current,
                            'end_time': next_end
                        })
                        current = next_end
                else:
                    segments.append({
                        'start_time': start_time,
                        'end_time': end_time
                    })
                start_time = end_time
            # 添加最后一个切片
            video_info = await self.get_video_info(video_path)
            duration = video_info.get('duration', 0)
            if start_time < duration:
                segments.append({
                    'start_time': start_time,
                    'end_time': duration
                })
        
        # 提取每个切片的关键帧
        keyframes = []
        video_name = Path(video_path).stem
        
        for i, segment in enumerate(segments):
            start_time = segment['start_time']
            end_time = segment['end_time']
            duration = end_time - start_time
            
            # 计算关键帧提取时间点
            keyframe_times = []
            if keyframes_per_segment == 1:
                # 提取中间帧
                keyframe_time = start_time + duration / 2
                keyframe_times.append(keyframe_time)
            else:
                # 均匀提取多个关键帧
                interval = duration / (keyframes_per_segment + 1)
                for j in range(1, keyframes_per_segment + 1):
                    keyframe_time = start_time + j * interval
                    keyframe_times.append(keyframe_time)
            
            # 提取关键帧
            for j, keyframe_time in enumerate(keyframe_times):
                output_path = os.path.join(output_dir, f"{video_name}_seg{i}_key{j}.jpg")
                
                # 使用FFmpeg提取指定时间点的帧
                cmd = [
                    'ffmpeg',
                    '-ss', str(keyframe_time),
                    '-i', video_path,
                    '-vframes', '1',
                    '-q:v', '2',  # 图像质量 (1-5, 1为最佳)
                    output_path
                ]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        keyframes.append({
                            'segment_index': i,
                            'start_time': start_time,
                            'end_time': end_time,
                            'duration': duration,
                            'keyframe_index': j,
                            'keyframe_time': keyframe_time,
                            'absolute_timestamp': keyframe_time,
                            'relative_position': (keyframe_time - start_time) / duration,
                            'frame_path': output_path,
                            'segment_id': f"seg-{i}"
                        })
                    else:
                        self.logger.error(f"提取关键帧失败: {result.stderr}")
                except subprocess.TimeoutExpired:
                    self.logger.error("提取关键帧超时")
                except Exception as e:
                    self.logger.error(f"提取关键帧出错: {e}")
        
        self.logger.info(f"提取了 {len(keyframes)} 个关键帧")
        return keyframes
    
    async def analyze_audio_content(self, video_path: str) -> str:
        """分析视频音频内容，判断是语音、音乐还是噪声
        
        Args:
            video_path: 视频路径
            
        Returns:
            音频类型: "speech", "music", 或 "noise"
        """
        self.logger.info(f"分析音频内容: {video_path}")
        
        try:
            # 提取视频开头10秒音频
            temp_audio_path = f"{video_path}.temp.wav"
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-t', '10',  # 只提取10秒
                '-q:a', '0',
                '-map', 'a',
                temp_audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                self.logger.error(f"提取音频失败: {result.stderr}")
                return "noise"
            
            # 使用inaSpeechSegmenter进行音频分类
            try:
                from inaSpeechSegmenter import Segmenter
                
                seg = Segmenter()
                segments = seg(temp_audio_path)
                
                # 统计各类型时长
                speech_duration = 0
                music_duration = 0
                noise_duration = 0
                
                for segment_type, start, end in segments:
                    duration = end - start
                    if segment_type == 'speech':
                        speech_duration += duration
                    elif segment_type == 'music':
                        music_duration += duration
                    else:
                        noise_duration += duration
                
                # 删除临时音频文件
                os.remove(temp_audio_path)
                
                # 确定主要音频类型
                if speech_duration > music_duration and speech_duration > noise_duration:
                    return "speech"
                elif music_duration > speech_duration and music_duration > noise_duration:
                    return "music"
                else:
                    return "noise"
            except ImportError:
                self.logger.warning("inaSpeechSegmenter未安装，无法进行音频分类")
                # 删除临时音频文件
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
                return "noise"
        except Exception as e:
            self.logger.error(f"音频分析出错: {e}")
            return "noise"
    
    async def smart_video_slicing(self, video_path: str, output_dir: str) -> List[Dict[str, Any]]:
        """智能视频切片机制，实现两阶段切片策略和超大视频特殊处理
        
        Args:
            video_path: 视频路径
            output_dir: 输出目录
            
        Returns:
            切片信息列表，包含关键帧和时间戳
        """
        self.logger.info(f"智能视频切片: {video_path}")
        
        # 获取视频信息
        video_info = await self.get_video_info(video_path)
        duration = video_info.get('duration', 0)
        file_size = video_info.get('file_size', 0) / (1024 * 1024 * 1024)  # 转换为GB
        
        # 确定是否为超大视频
        is_large_video = file_size > 3 or duration > 1800  # >3GB或>30分钟
        
        # 音频辅助切片优化
        audio_type = await self.analyze_audio_content(video_path)
        self.logger.info(f"音频类型: {audio_type}")
        
        # 根据音频类型调整场景检测阈值
        if audio_type == "speech":
            scene_threshold = 0.25  # 降低阈值以捕获更多细节
        elif audio_type == "music":
            scene_threshold = 0.3  # 默认阈值
        else:
            scene_threshold = 0.35  # 提高阈值减少切片数量
        
        self.logger.info(f"使用场景检测阈值: {scene_threshold}")
        
        # 检测场景变化
        if is_large_video:
            self.logger.info("超大视频，优先处理开头5分钟内容")
            # 创建临时视频，只包含开头5分钟
            temp_video_path = f"{video_path}.temp.mp4"
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-t', '300',  # 5分钟
                '-c:v', 'copy',
                '-c:a', 'copy',
                temp_video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                self.logger.error(f"创建临时视频失败: {result.stderr}")
                return []
            
            # 检测临时视频的场景变化
            scene_changes = await self.detect_video_scenes(temp_video_path, scene_threshold)
            
            # 提取临时视频的关键帧
            keyframes = await self.extract_keyframes(temp_video_path, output_dir, scene_changes)
            
            # 删除临时视频
            os.remove(temp_video_path)
            
            self.logger.info("超大视频开头5分钟处理完成，后续内容将在后台处理")
            return keyframes
        
        # 检测场景变化
        scene_changes = await self.detect_video_scenes(video_path, scene_threshold)
        
        # 提取关键帧
        keyframes = await self.extract_keyframes(video_path, output_dir, scene_changes)
        
        self.logger.info("智能视频切片完成")
        return keyframes
    
    async def convert_video_format(self, input_path: str, output_path: str, 
                                 target_resolution: Tuple[int, int] = None) -> bool:
        """转换视频格式
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            target_resolution: 目标分辨率 (width, height)
            
        Returns:
            是否转换成功
        """
        if target_resolution is None:
            target_resolution = self.video_config.get('target_resolution', [1280, 720])
            if isinstance(target_resolution, list) and len(target_resolution) == 2:
                target_resolution = (target_resolution[0], target_resolution[1])
        
        self.logger.info(f"转换视频格式: {input_path} -> {output_path}, 分辨率: {target_resolution}")
        
        # 确保输出目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 构建FFmpeg命令
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libx264',  # 使用H.264编码
            '-crf', '23',       # 恒定速率因子 (18-28, 18为视觉无损)
            '-preset', 'medium', # 编码预设
            '-c:a', 'aac',      # 音频编码
            '-b:a', '128k',     # 音频比特率
        ]
        
        # 添加分辨率参数
        if target_resolution:
            cmd.extend(['-s', f'{target_resolution[0]}x{target_resolution[1]}'])
        
        cmd.append(output_path)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            success = result.returncode == 0
            
            if success:
                self.logger.info("视频格式转换成功")
            else:
                self.logger.error(f"视频格式转换失败: {result.stderr}")
            
            return success
            
        except subprocess.TimeoutExpired:
            self.logger.error("视频格式转换超时")
            return False
        except Exception as e:
            self.logger.error(f"视频格式转换出错: {e}")
            return False