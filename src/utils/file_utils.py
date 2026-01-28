"""
文件工具
提供文件操作相关的工具函数
"""

import os
import shutil
from typing import List, Optional
from pathlib import Path


def get_files_by_extension(directory: str, extensions: List[str], recursive: bool = True) -> List[str]:
    """
    根据扩展名获取文件列表

    Args:
        directory: 目录路径
        extensions: 扩展名列表（如 ['jpg', 'png']）
        recursive: 是否递归搜索

    Returns:
        文件路径列表
    """
    extensions = [ext.lower().lstrip('.') for ext in extensions]
    files = []

    if recursive:
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if any(filename.lower().endswith(f'.{ext}') for ext in extensions):
                    files.append(os.path.join(root, filename))
    else:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                if any(filename.lower().endswith(f'.{ext}') for ext in extensions):
                    files.append(filepath)

    return files


def is_image_file(file_path: str) -> bool:
    """
    判断是否为图像文件

    Args:
        file_path: 文件路径

    Returns:
        是否为图像文件
    """
    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff']
    return Path(file_path).suffix.lower().lstrip('.') in image_extensions


def is_video_file(file_path: str) -> bool:
    """
    判断是否为视频文件

    Args:
        file_path: 文件路径

    Returns:
        是否为视频文件
    """
    video_extensions = ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm', 'm4v']
    return Path(file_path).suffix.lower().lstrip('.') in video_extensions


def is_audio_file(file_path: str) -> bool:
    """
    判断是否为音频文件

    Args:
        file_path: 文件路径

    Returns:
        是否为音频文件
    """
    audio_extensions = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma']
    return Path(file_path).suffix.lower().lstrip('.') in audio_extensions


def ensure_directory_exists(directory: str) -> None:
    """
    确保目录存在

    Args:
        directory: 目录路径
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def safe_delete_file(file_path: str) -> bool:
    """
    安全删除文件

    Args:
        file_path: 文件路径

    Returns:
        是否成功删除
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as e:
        print(f"删除文件失败: {file_path}, 错误: {e}")
        return False


def safe_delete_directory(directory: str) -> bool:
    """
    安全删除目录

    Args:
        directory: 目录路径

    Returns:
        是否成功删除
    """
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        return True
    except Exception as e:
        print(f"删除目录失败: {directory}, 错误: {e}")
        return False


def copy_file_with_progress(src: str, dst: str, progress_callback: Optional[callable] = None) -> bool:
    """
    带进度回调的文件复制

    Args:
        src: 源文件路径
        dst: 目标文件路径
        progress_callback: 进度回调函数

    Returns:
        是否成功复制
    """
    try:
        file_size = os.path.getsize(src)
        copied = 0

        with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
            while True:
                chunk = fsrc.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                fdst.write(chunk)
                copied += len(chunk)
                if progress_callback:
                    progress_callback(copied, file_size)

        return True
    except Exception as e:
        print(f"复制文件失败: {src} -> {dst}, 错误: {e}")
        return False


def get_relative_path(file_path: str, base_path: str) -> str:
    """
    获取相对路径

    Args:
        file_path: 文件路径
        base_path: 基础路径

    Returns:
        相对路径
    """
    return os.path.relpath(file_path, base_path)


def is_hidden_file(file_path: str) -> bool:
    """
    判断是否为隐藏文件

    Args:
        file_path: 文件路径

    Returns:
        是否为隐藏文件
    """
    filename = os.path.basename(file_path)
    return filename.startswith('.')