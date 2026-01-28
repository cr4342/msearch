# -*- coding: utf-8 -*-
"""
文件扫描器模块

提供目录文件扫描功能，支持递归扫描、文件过滤和增量扫描。
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from ...data.constants import SUPPORTED_FORMATS, SUPPORTED_IMAGE_FORMATS, SUPPORTED_VIDEO_FORMATS, SUPPORTED_AUDIO_FORMATS


class FileScanner:
    """文件扫描器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化文件扫描器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = None
        
        # 扫描配置
        self.recursive = self.config.get("recursive", True)
        self.max_depth = self.config.get("max_depth", 10)
        self.ignore_dirs = self.config.get("ignore_dirs", {".git", ".venv", "__pycache__", "node_modules"})
        self.ignore_files = self.config.get("ignore_files", {".DS_Store", "Thumbs.db"})
        
        # 文件类型过滤
        self.scan_images = self.config.get("scan_images", True)
        self.scan_videos = self.config.get("scan_videos", True)
        self.scan_audio = self.config.get("scan_audio", True)
    
    def scan_directory(self, directory: str) -> List[str]:
        """
        扫描目录，返回所有支持的文件路径
        
        Args:
            directory: 目录路径
            
        Returns:
            文件路径列表
        """
        try:
            dir_path = Path(directory)
            
            if not dir_path.exists() or not dir_path.is_dir():
                if self.logger:
                    self.logger.error(f"目录不存在或不是目录: {directory}")
                return []
            
            files = []
            
            if self.recursive:
                files = self._scan_recursive(dir_path, 0)
            else:
                files = self._scan_flat(dir_path)
            
            return files
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"扫描目录失败: {directory}, 错误: {e}")
            return []
    
    def _scan_recursive(self, directory: Path, depth: int) -> List[str]:
        """
        递归扫描目录
        
        Args:
            directory: 目录路径
            depth: 当前深度
            
        Returns:
            文件路径列表
        """
        if depth > self.max_depth:
            return []
        
        files = []
        
        try:
            for item in directory.iterdir():
                # 跳过忽略的目录
                if item.is_dir() and item.name in self.ignore_dirs:
                    continue
                
                # 递归扫描子目录
                if item.is_dir():
                    files.extend(self._scan_recursive(item, depth + 1))
                # 处理文件
                elif item.is_file():
                    if self._is_supported_file(item):
                        files.append(str(item.absolute()))
        
        except PermissionError as e:
            if self.logger:
                self.logger.warning(f"无权限访问目录: {directory}, 错误: {e}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"扫描目录失败: {directory}, 错误: {e}")
        
        return files
    
    def _scan_flat(self, directory: Path) -> List[str]:
        """
        扫描目录（非递归）
        
        Args:
            directory: 目录路径
            
        Returns:
            文件路径列表
        """
        files = []
        
        try:
            for item in directory.iterdir():
                if item.is_file() and self._is_supported_file(item):
                    files.append(str(item.absolute()))
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"扫描目录失败: {directory}, 错误: {e}")
        
        return files
    
    def _is_supported_file(self, file_path: Path) -> bool:
        """
        检查文件是否支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持
        """
        # 跳过忽略的文件
        if file_path.name in self.ignore_files:
            return False
        
        # 检查文件扩展名
        ext = file_path.suffix.lower()
        
        if ext in SUPPORTED_IMAGE_FORMATS and self.scan_images:
            return True
        elif ext in SUPPORTED_VIDEO_FORMATS and self.scan_videos:
            return True
        elif ext in SUPPORTED_AUDIO_FORMATS and self.scan_audio:
            return True
        
        return False
    
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """
        计算文件的SHA256哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            SHA256哈希值，如果计算失败返回None
        """
        try:
            import hashlib
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            if self.logger:
                self.logger.error(f"计算文件哈希失败: {file_path}, 错误: {e}")
            return None
    
    def scan_directory_with_hashes(self, directory: str) -> List[Dict[str, str]]:
        """
        扫描目录，返回所有支持的文件路径和对应的SHA256哈希值
        
        Args:
            directory: 目录路径
            
        Returns:
            文件路径和哈希值的列表
        """
        file_paths = self.scan_directory(directory)
        
        # 计算每个文件的哈希值
        files_with_hashes = []
        for file_path in file_paths:
            file_hash = self.calculate_file_hash(file_path)
            if file_hash:
                files_with_hashes.append({
                    "file_path": file_path,
                    "file_hash": file_hash
                })
        
        return files_with_hashes
    
    def scan_multiple_directories(self, directories: List[str]) -> List[str]:
        """
        扫描多个目录
        
        Args:
            directories: 目录路径列表
            
        Returns:
            文件路径列表
        """
        all_files = []
        
        for directory in directories:
            files = self.scan_directory(directory)
            all_files.extend(files)
        
        # 去重
        all_files = list(set(all_files))
        
        return all_files
    
    def get_new_files(self, directories: List[str], known_files: Set[str]) -> List[str]:
        """
        获取新增文件
        
        Args:
            directories: 目录路径列表
            known_files: 已知文件集合
            
        Returns:
            新增文件列表
        """
        all_files = self.scan_multiple_directories(directories)
        
        # 过滤出新增文件
        new_files = [f for f in all_files if f not in known_files]
        
        return new_files
    
    def get_deleted_files(self, directories: List[str], known_files: Set[str]) -> List[str]:
        """
        获取已删除文件
        
        Args:
            directories: 目录路径列表
            known_files: 已知文件集合
            
        Returns:
            已删除文件列表
        """
        current_files = set(self.scan_multiple_directories(directories))
        
        # 找出已删除的文件
        deleted_files = [f for f in known_files if f not in current_files]
        
        return deleted_files
    
    def get_modified_files(self, directories: List[str], known_files: Dict[str, float]) -> List[str]:
        """
        获取已修改的文件
        
        Args:
            directories: 目录路径列表
            known_files: 已知文件字典（文件路径 -> 修改时间）
            
        Returns:
            已修改文件列表
        """
        modified_files = []
        
        for file_path, old_mtime in known_files.items():
            try:
                current_mtime = os.path.getmtime(file_path)
                if current_mtime > old_mtime:
                    modified_files.append(file_path)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"检查文件修改时间失败: {file_path}, 错误: {e}")
        
        return modified_files
    
    def get_file_stats(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        获取文件统计信息
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            统计信息字典
        """
        stats = {
            "total_files": len(file_paths),
            "image_files": 0,
            "video_files": 0,
            "audio_files": 0,
            "total_size": 0,
            "by_extension": {}
        }
        
        for file_path in file_paths:
            try:
                path = Path(file_path)
                ext = path.suffix.lower()
                
                # 统计文件类型
                if ext in SUPPORTED_IMAGE_FORMATS:
                    stats["image_files"] += 1
                elif ext in SUPPORTED_VIDEO_FORMATS:
                    stats["video_files"] += 1
                elif ext in SUPPORTED_AUDIO_FORMATS:
                    stats["audio_files"] += 1
                
                # 统计文件大小
                file_size = path.stat().st_size
                stats["total_size"] += file_size
                
                # 按扩展名统计
                stats["by_extension"][ext] = stats["by_extension"].get(ext, 0) + 1
            
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"获取文件统计失败: {file_path}, 错误: {e}")
        
        return stats
    
    def filter_by_size(self, file_paths: List[str], min_size: int = 0, max_size: int = None) -> List[str]:
        """
        按文件大小过滤
        
        Args:
            file_paths: 文件路径列表
            min_size: 最小文件大小（字节）
            max_size: 最大文件大小（字节）
            
        Returns:
            过滤后的文件列表
        """
        filtered_files = []
        
        for file_path in file_paths:
            try:
                file_size = Path(file_path).stat().st_size
                
                if file_size >= min_size:
                    if max_size is None or file_size <= max_size:
                        filtered_files.append(file_path)
            
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"检查文件大小失败: {file_path}, 错误: {e}")
        
        return filtered_files
    
    def filter_by_extension(self, file_paths: List[str], extensions: Set[str]) -> List[str]:
        """
        按文件扩展名过滤
        
        Args:
            file_paths: 文件路径列表
            extensions: 扩展名集合
            
        Returns:
            过滤后的文件列表
        """
        extensions_lower = {ext.lower() for ext in extensions}
        
        filtered_files = [
            f for f in file_paths 
            if Path(f).suffix.lower() in extensions_lower
        ]
        
        return filtered_files