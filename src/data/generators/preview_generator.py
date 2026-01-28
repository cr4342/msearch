"""
预览生成器

职责：为媒体文件生成预览视频
不包含业务逻辑，只负责数据生成
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Any, List, Dict

from ..constants import PreviewType

logger = logging.getLogger(__name__)


class PreviewGenerator:
    """
    预览生成器
    
    职责：为媒体文件生成预览视频
    
    支持的生成方式：
    - 从视频生成预览（快速播放）
    - 从图像序列生成预览
    - 从音频生成可视化预览
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化预览生成器
        
        Args:
            config: 配置字典，包含以下可选键:
                - output_dir: 预览输出目录，如果为None则使用临时目录
                - width: 预览宽度（默认320）
                - height: 预览高度（默认240）
                - duration: 预览时长（秒，默认10）
                - fps: 预览帧率（默认10）
        """
        if config is None:
            config = {}
        
        # 支持两种配置格式：直接参数或嵌套在preview键下
        if isinstance(config, dict) and 'preview' in config:
            config = config['preview']
        elif isinstance(config, dict) and 'preview_generator' in config:
            config = config['preview_generator']
        
        self.output_dir = config.get('output_dir', config.get('preview_dir', None))
        self.width = config.get('width', config.get('preview_width', 320))
        self.height = config.get('height', config.get('preview_height', 240))
        self.duration = config.get('duration', config.get('preview_duration', 10))
        self.fps = config.get('fps', config.get('preview_fps', 10))
        self.temp_dir = None
        
        if self.output_dir is None:
            self.temp_dir = tempfile.TemporaryDirectory()
            self.output_dir = self.temp_dir.name
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"预览生成器初始化完成，输出目录: {self.output_dir}, 尺寸: {self.width}x{self.height}, 时长: {self.duration}秒, 帧率: {self.fps}")
    
    def __del__(self):
        """
        清理临时目录
        """
        if self.temp_dir:
            try:
                self.temp_dir.cleanup()
            except Exception as e:
                logger.warning(f"清理临时目录失败: {e}")
    
    def generate(self, media_path: str,
                output_format: str = 'mp4') -> Optional[Tuple[str, int, int, int]]:
        """
        为媒体文件生成预览
        
        Args:
            media_path: 媒体文件路径
            output_format: 输出格式（mp4/webm/avi）
            
        Returns:
            预览信息：(预览文件路径, 宽度, 高度, 时长)，如果生成失败则返回None
            
        Raises:
            FileNotFoundError: 媒体文件不存在
            ValueError: 参数无效
            RuntimeError: 生成失败
        """
        if not media_path:
            raise ValueError("媒体路径不能为空")
        
        if not os.path.exists(media_path):
            raise FileNotFoundError(f"媒体文件不存在: {media_path}")
        
        if output_format not in ['mp4', 'webm', 'avi']:
            raise ValueError(f"不支持的输出格式: {output_format}")
        
        try:
            # 判断文件类型
            file_type = self._get_file_type(media_path)
            
            if file_type == 'image':
                return self._generate_from_image(media_path, output_format)
            elif file_type == 'video':
                return self._generate_from_video(media_path, output_format)
            elif file_type == 'audio':
                return self._generate_from_audio(media_path, output_format)
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
                
        except Exception as e:
            logger.error(f"生成预览失败: {media_path}, 错误: {e}")
            raise
    
    def _get_file_type(self, file_path: str) -> str:
        """
        根据文件扩展名判断文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件类型（image/video/audio/unknown）
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic'}
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.mpeg', '.mpg'}
        audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}
        
        if ext in image_extensions:
            return 'image'
        elif ext in video_extensions:
            return 'video'
        elif ext in audio_extensions:
            return 'audio'
        else:
            return 'unknown'
    
    def _generate_from_image(self, image_path: str, output_format: str) -> Optional[Tuple[str, int, int, int]]:
        """
        从图像生成预览（简单的幻灯片效果）
        
        Args:
            image_path: 图像文件路径
            output_format: 输出格式
            
        Returns:
            预览信息：(预览文件路径, 宽度, 高度, 时长)
        """
        try:
            # 生成输出文件名
            image_name = os.path.splitext(os.path.basename(image_path))[0]
            preview_filename = f"{image_name}_preview.{output_format}"
            preview_path = os.path.join(self.output_dir, preview_filename)
            
            # 使用ffmpeg生成预览
            import subprocess
            
            cmd = [
                'ffmpeg',
                '-v', 'error',
                '-loop', '1',
                '-i', image_path,
                '-t', str(self.duration),
                '-vf', f'scale={self.width}:{self.height}',
                '-r', str(self.fps),
                '-y',
                preview_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg生成预览失败: {result.stderr}")
            
            logger.info(f"成功生成预览: {preview_path}")
            
            return (preview_path, self.width, self.height, self.duration)
            
        except Exception as e:
            logger.error(f"从图像生成预览失败: {image_path}, 错误: {e}")
            return None
    
    def _generate_from_video(self, video_path: str, output_format: str) -> Optional[Tuple[str, int, int, int]]:
        """
        从视频生成预览（快速播放）
        
        Args:
            video_path: 视频文件路径
            output_format: 输出格式
            
        Returns:
            预览信息：(预览文件路径, 宽度, 高度, 时长)
        """
        try:
            # 获取视频时长
            duration = self._get_video_duration(video_path)
            
            # 计算播放速度
            speed = duration / self.duration if self.duration > 0 else 1
            
            if speed < 1:
                speed = 1
            
            # 生成输出文件名
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            preview_filename = f"{video_name}_preview.{output_format}"
            preview_path = os.path.join(self.output_dir, preview_filename)
            
            # 使用ffmpeg生成预览
            import subprocess
            
            cmd = [
                'ffmpeg',
                '-v', 'error',
                '-i', video_path,
                '-vf', f'scale={self.width}:{self.height},setpts={1/speed}*PTS',
                '-r', str(self.fps),
                '-t', str(self.duration),
                '-y',
                preview_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg生成预览失败: {result.stderr}")
            
            logger.info(f"成功生成预览: {preview_path}, 播放速度: {speed:.2f}x")
            
            return (preview_path, self.width, self.height, self.duration)
            
        except Exception as e:
            logger.error(f"从视频生成预览失败: {video_path}, 错误: {e}")
            return None
    
    def _generate_from_audio(self, audio_path: str, output_format: str) -> Optional[Tuple[str, int, int, int]]:
        """
        从音频生成预览（可视化音频波形）
        
        Args:
            audio_path: 音频文件路径
            output_format: 输出格式
            
        Returns:
            预览信息：(预览文件路径, 宽度, 高度, 时长)
        """
        try:
            # 生成输出文件名
            audio_name = os.path.splitext(os.path.basename(audio_path))[0]
            preview_filename = f"{audio_name}_preview.{output_format}"
            preview_path = os.path.join(self.output_dir, preview_filename)
            
            # 使用ffmpeg生成预览（音频可视化）
            import subprocess
            
            cmd = [
                'ffmpeg',
                '-v', 'error',
                '-i', audio_path,
                '-t', str(self.duration),
                '-filter_complex', \
                f"showwavespic=s={self.width}x{self.height}:colors=blue",
                '-r', str(self.fps),
                '-y',
                preview_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg生成预览失败: {result.stderr}")
            
            logger.info(f"成功生成预览: {preview_path}")
            
            return (preview_path, self.width, self.height, self.duration)
            
        except Exception as e:
            logger.error(f"从音频生成预览失败: {audio_path}, 错误: {e}")
            return None
    
    def _get_video_duration(self, video_path: str) -> float:
        """
        获取视频时长
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频时长（秒）
        """
        try:
            import subprocess
            
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries',
                 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
                 video_path],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"无法获取视频时长: {result.stderr}")
            
            duration = float(result.stdout.strip())
            
            return duration
            
        except Exception as e:
            logger.error(f"获取视频时长失败: {video_path}, 错误: {e}")
            raise
    
    def generate_from_frames(self, frames: List[str],
                           output_format: str = 'mp4') -> Optional[Tuple[str, int, int, int]]:
        """
        从帧序列生成预览
        
        Args:
            frames: 帧文件路径列表
            output_format: 输出格式
            
        Returns:
            预览信息：(预览文件路径, 宽度, 高度, 时长)
        """
        if not frames:
            raise ValueError("帧列表不能为空")
        
        try:
            # 生成临时文件列表
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for frame in frames:
                    f.write(f"file '{frame}'\n")
                    f.write(f"duration {1/self.fps}\n")
                
                # 最后一帧的持续时间
                f.write(f"file '{frames[-1]}'\n")
                f.write(f"duration {1/self.fps}\n")
                
                filelist_path = f.name
            
            # 生成输出文件名
            preview_filename = f"frames_preview.{output_format}"
            preview_path = os.path.join(self.output_dir, preview_filename)
            
            # 使用ffmpeg生成预览
            import subprocess
            
            cmd = [
                'ffmpeg',
                '-v', 'error',
                '-f', 'concat',
                '-safe', '0',
                '-i', filelist_path,
                '-vf', f'scale={self.width}:{self.height}',
                '-r', str(self.fps),
                '-y',
                preview_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 清理临时文件
            os.unlink(filelist_path)
            
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg生成预览失败: {result.stderr}")
            
            # 计算预览时长
            duration = len(frames) / self.fps
            
            logger.info(f"成功从 {len(frames)} 帧生成预览: {preview_path}, 时长: {duration:.2f}秒")
            
            return (preview_path, self.width, self.height, int(duration))
            
        except Exception as e:
            logger.error(f"从帧序列生成预览失败, 错误: {e}")
            return None
    
    def get_preview_filename(self, file_id: str, preview_type: PreviewType) -> str:
        """
        获取预览文件名
        
        Args:
            file_id: 文件ID
            preview_type: 预览类型
            
        Returns:
            预览文件名
        """
        # 根据预览类型确定文件扩展名
        if preview_type == PreviewType.THUMBNAIL:
            return f"{file_id}.jpg"
        elif preview_type == PreviewType.VIDEO_PREVIEW:
            return f"{file_id}.mp4"
        elif preview_type == PreviewType.GIF_PREVIEW:
            return f"{file_id}.gif"
        elif preview_type == PreviewType.AUDIO_WAVEFORM:
            return f"{file_id}.png"
        elif preview_type in [PreviewType.SMALL_PREVIEW, PreviewType.MEDIUM_PREVIEW, PreviewType.LARGE_PREVIEW]:
            return f"{file_id}.jpg"
        else:
            return f"{file_id}.jpg"
    
    def get_preview_path(self, file_id: str, preview_type: PreviewType) -> str:
        """
        获取预览文件路径
        
        Args:
            file_id: 文件ID
            preview_type: 预览类型
            
        Returns:
            预览文件路径
        """
        filename = self.get_preview_filename(file_id, preview_type)
        return os.path.join(self.output_dir, preview_type.value, filename)
    
    def has_preview(self, file_id: str, preview_type: PreviewType) -> bool:
        """
        检查预览是否存在
        
        Args:
            file_id: 文件ID
            preview_type: 预览类型
            
        Returns:
            预览是否存在
        """
        preview_path = self.get_preview_path(file_id, preview_type)
        return os.path.exists(preview_path)
    
    def get_cache_usage(self) -> dict:
        """
        获取缓存使用情况
        
        Returns:
            缓存使用情况字典
        """
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(self.output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                except OSError:
                    continue
        
        return {
            'total_size': total_size,
            'file_count': file_count
        }
    
    def clear_preview_cache(self) -> None:
        """
        清理预览缓存
        """
        import shutil
        
        # 删除预览目录下的所有文件
        if os.path.exists(self.output_dir):
            for root, dirs, files in os.walk(self.output_dir, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    try:
                        os.rmdir(dir_path)
                    except OSError:
                        pass
