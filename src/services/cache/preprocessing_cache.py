"""
预处理缓存管理器
负责管理预处理过程中产生的中间文件和缓存
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PreprocessingCache:
    """
    预处理缓存管理器

    负责管理预处理过程中产生的中间文件和缓存
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化预处理缓存管理器

        Args:
            config: 配置字典
        """
        self.config = config

        # 缓存目录配置
        cache_dir = config.get("cache_dir", "data/cache")
        self.cache_dir = Path(cache_dir) / "preprocessing"

        # 预处理缓存配置
        preprocessing_config = config.get("preprocessing", {})
        self.max_cache_size = preprocessing_config.get(
            "max_cache_size", 5 * 1024 * 1024 * 1024
        )  # 5GB
        self.cache_ttl = preprocessing_config.get("cache_ttl", 7 * 24 * 3600)  # 7天
        self.enable_cache = preprocessing_config.get("enable_cache", True)

        # 临时文件目录
        self.tmp_dir = Path(cache_dir) / "tmp"

        # 创建必要的目录
        self._create_directories()

        logger.info(f"预处理缓存管理器初始化完成，缓存目录: {self.cache_dir}")

    def _create_directories(self) -> None:
        """
        创建必要的目录结构
        """
        # 创建主缓存目录和子目录
        # 注意：由于所有模型都支持直接视频处理，无需抽帧，移除frame_extraction缓存目录
        cache_subdirs = [
            self.cache_dir / "audio_segments",
            self.cache_dir / "video_slices",
            self.cache_dir / "text_embeddings",
            self.cache_dir / "image_preprocessing",  # 新增：图像预处理缓存
        ]

        for dir_path in cache_subdirs:
            dir_path.mkdir(parents=True, exist_ok=True)

        # 创建临时文件目录
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_path(self, file_id: str, cache_type: str) -> str:
        """
        获取缓存文件路径

        Args:
            file_id: 文件ID（UUID v4）
            cache_type: 缓存类型（image_preprocessing, audio_segments, video_slices, text_embeddings）

        Returns:
            缓存文件路径
        """
        cache_subdir = self.cache_dir / cache_type
        cache_subdir.mkdir(parents=True, exist_ok=True)
        return str(cache_subdir / f"{file_id}.json")

    def save_cache(self, file_id: str, cache_type: str, data: Any) -> bool:
        """
        保存缓存数据

        Args:
            file_id: 文件ID（UUID v4）
            cache_type: 缓存类型
            data: 缓存数据

        Returns:
            是否保存成功
        """
        if not self.enable_cache:
            return False

        try:
            cache_path = self.get_cache_path(file_id, cache_type)
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
            return False

    def load_cache(self, file_id: str, cache_type: str) -> Optional[Any]:
        """
        加载缓存数据

        Args:
            file_id: 文件ID（UUID v4）
            cache_type: 缓存类型

        Returns:
            缓存数据，如不存在或过期则返回None
        """
        if not self.enable_cache:
            return None

        try:
            cache_path = self.get_cache_path(file_id, cache_type)
            if not os.path.exists(cache_path):
                return None

            # 检查缓存是否过期
            if time.time() - os.path.getmtime(cache_path) > self.cache_ttl:
                self.delete_cache(file_id, cache_type)
                return None

            with open(cache_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
            return None

    def delete_cache(self, file_id: str, cache_type: Optional[str] = None) -> bool:
        """
        删除缓存数据

        Args:
            file_id: 文件ID（UUID v4）
            cache_type: 缓存类型（None表示删除所有类型）

        Returns:
            是否删除成功
        """
        try:
            if cache_type:
                # 删除特定类型的缓存
                cache_path = self.get_cache_path(file_id, cache_type)
                if os.path.exists(cache_path):
                    os.remove(cache_path)
            else:
                # 删除所有类型的缓存
                for cache_type in [
                    "frame_extraction",
                    "audio_segments",
                    "video_slices",
                    "text_embeddings",
                ]:
                    cache_path = self.get_cache_path(file_id, cache_type)
                    if os.path.exists(cache_path):
                        os.remove(cache_path)
            return True
        except Exception as e:
            logger.error(f"删除缓存失败: {e}")
            return False

    def cleanup_expired_cache(self) -> int:
        """
        清理过期缓存

        Returns:
            清理的缓存文件数量
        """
        try:
            count = 0
            current_time = time.time()

            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if current_time - os.path.getmtime(file_path) > self.cache_ttl:
                        os.remove(file_path)
                        count += 1

            logger.info(f"清理过期缓存完成，共清理 {count} 个文件")
            return count
        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
            return 0

    def cleanup_by_size(self) -> int:
        """
        按大小清理缓存

        Returns:
            清理的缓存文件数量
        """
        try:
            # 计算当前缓存大小
            total_size = 0
            cache_files = []

            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    cache_files.append(
                        (file_path, file_size, os.path.getmtime(file_path))
                    )

            # 如果缓存大小超过限制，按时间排序并删除最旧的文件
            count = 0
            if total_size > self.max_cache_size:
                logger.info(
                    f"缓存大小超过限制（当前: {total_size/1024/1024:.2f}MB, 限制: {self.max_cache_size/1024/1024:.2f}MB），开始清理"
                )

                # 按修改时间排序（最旧的先删除）
                cache_files.sort(key=lambda x: x[2])

                while total_size > self.max_cache_size and cache_files:
                    file_path, file_size, mtime = cache_files.pop(0)
                    os.remove(file_path)
                    total_size -= file_size
                    count += 1

            if count > 0:
                logger.info(f"按大小清理缓存完成，共清理 {count} 个文件")

            return count
        except Exception as e:
            logger.error(f"按大小清理缓存失败: {e}")
            return 0

    def cleanup_tmp_files(self) -> int:
        """
        清理临时文件

        Returns:
            清理的临时文件数量
        """
        try:
            count = 0
            current_time = time.time()

            for root, dirs, files in os.walk(self.tmp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 删除超过24小时的临时文件
                    if current_time - os.path.getmtime(file_path) > 24 * 3600:
                        os.remove(file_path)
                        count += 1

            logger.info(f"清理临时文件完成，共清理 {count} 个文件")
            return count
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
            return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计信息
        """
        try:
            total_size = 0
            file_count = 0
            type_counts = {}

            for root, dirs, files in os.walk(self.cache_dir):
                cache_type = os.path.basename(root)
                if cache_type == "preprocessing":
                    continue

                type_counts[cache_type] = len(files)
                file_count += len(files)

                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)

            return {
                "total_size": total_size,
                "file_count": file_count,
                "type_counts": type_counts,
                "max_cache_size": self.max_cache_size,
                "cache_ttl": self.cache_ttl,
                "enable_cache": self.enable_cache,
            }
        except Exception as e:
            logger.error(f"获取缓存统计信息失败: {e}")
            return {}

    def create_tmp_file(self, suffix: str = "") -> str:
        """
        创建临时文件

        Args:
            suffix: 文件后缀

        Returns:
            临时文件路径
        """
        # 使用当前时间和随机字符串生成唯一文件名
        timestamp = int(time.time() * 1000)
        random_str = os.urandom(8).hex()
        tmp_filename = f"tmp_{timestamp}_{random_str}{suffix}"
        tmp_file_path = self.tmp_dir / tmp_filename

        return str(tmp_file_path)

    def delete_tmp_file(self, file_path: str) -> bool:
        """
        删除临时文件

        Args:
            file_path: 临时文件路径

        Returns:
            是否删除成功
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"删除临时文件失败: {file_path}, {e}")
            return False

    def validate_cache_integrity(self) -> int:
        """
        验证缓存文件完整性

        Returns:
            无效缓存文件数量
        """
        try:
            invalid_count = 0

            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)

                    # 验证文件是否为有效的JSON文件
                    try:
                        with open(file_path, "r") as f:
                            json.load(f)
                    except json.JSONDecodeError:
                        logger.warning(f"无效的JSON缓存文件: {file_path}")
                        os.remove(file_path)
                        invalid_count += 1

            logger.info(f"缓存完整性验证完成，共清理 {invalid_count} 个无效文件")
            return invalid_count
        except Exception as e:
            logger.error(f"验证缓存完整性失败: {e}")
            return 0

    def cleanup_all(self) -> Dict[str, int]:
        """
        执行所有清理操作

        Returns:
            清理结果统计
        """
        stats = {
            "expired_cache": self.cleanup_expired_cache(),
            "size_cleanup": self.cleanup_by_size(),
            "tmp_files": self.cleanup_tmp_files(),
            "invalid_files": self.validate_cache_integrity(),
        }

        logger.info(f"所有清理操作完成: {stats}")
        return stats

    def get_tmp_dir(self) -> str:
        """
        获取临时文件目录

        Returns:
            临时文件目录路径
        """
        return str(self.tmp_dir)

    def enable(self) -> None:
        """
        启用缓存
        """
        self.enable_cache = True
        logger.info("预处理缓存已启用")

    def disable(self) -> None:
        """
        禁用缓存
        """
        self.enable_cache = False
        logger.info("预处理缓存已禁用")
