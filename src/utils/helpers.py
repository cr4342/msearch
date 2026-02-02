"""
工具函数
提供常用的辅助函数
"""

import hashlib
import uuid
from typing import Any, Dict, List, Optional
from pathlib import Path


def generate_uuid() -> str:
    """
    生成UUID

    Returns:
        UUID字符串
    """
    return str(uuid.uuid4())


def calculate_file_hash(file_path: str) -> str:
    """
    计算文件哈希值

    Args:
        file_path: 文件路径

    Returns:
        文件SHA256哈希值
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_file_extension(file_path: str) -> str:
    """
    获取文件扩展名

    Args:
        file_path: 文件路径

    Returns:
        文件扩展名（小写，不带点）
    """
    return Path(file_path).suffix.lower().lstrip(".")


def get_file_size(file_path: str) -> int:
    """
    获取文件大小

    Args:
        file_path: 文件路径

    Returns:
        文件大小（字节）
    """
    return Path(file_path).stat().st_size


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        格式化的文件大小字符串
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def ensure_directory(directory: str) -> None:
    """
    确保目录存在

    Args:
        directory: 目录路径
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def safe_filename(filename: str) -> str:
    """
    生成安全的文件名

    Args:
        filename: 原始文件名

    Returns:
        安全的文件名
    """
    import re

    # 移除或替换不安全的字符
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", filename)
    # 限制文件名长度
    return safe_name[:255]


def deep_merge_dict(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    深度合并字典

    Args:
        base: 基础字典
        update: 更新字典

    Returns:
        合并后的字典
    """
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def flatten_dict(
    d: Dict[str, Any], parent_key: str = "", sep: str = "."
) -> Dict[str, Any]:
    """
    展平嵌套字典

    Args:
        d: 字典
        parent_key: 父键
        sep: 分隔符

    Returns:
        展平后的字典
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    将列表分块

    Args:
        lst: 列表
        chunk_size: 块大小

    Returns:
        分块后的列表
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """
    截断字符串

    Args:
        s: 字符串
        max_length: 最大长度
        suffix: 后缀

    Returns:
        截断后的字符串
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix
