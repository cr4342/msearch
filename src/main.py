"""
msearch主程序入口
"""

import sys
import os
import logging
import signal
import argparse
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import ConfigManager
from src.core.database_manager import DatabaseManager
from src.core.vector_store import VectorStore
from src.core.embedding_engine import EmbeddingEngine
from src.core.task_manager import TaskManager
from src.core.hardware_detector import HardwareDetector
from src.services.file_monitor import FileMonitor
from src.services.media_processor import MediaProcessor


class MSearchApp:
    """msearch应用主类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化应用
        
        Args:
            config_path: 配置文件路径
        """
        self.config: Optional[ConfigManager] = None
        self.database_manager: Optional[DatabaseManager] = None
        self.vector_store: Optional[VectorStore] = None
        self.embedding_engine: Optional[EmbeddingEngine] = None
        self.task_manager: Optional[TaskManager] = None
        self.hardware_detector: Optional[HardwareDetector] = None
        self.file_monitor: Optional[FileMonitor] = None
        self.media_processor: Optional[MediaProcessor] = None
        
        self.is_running = False
        
        # 初始化配置
        self._init_config(config_path)
        
        # 初始化日志
        self._init_logging()
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _init_config(self, config_path: Optional[str]) -> None:
        """初始化配置"""
        if config_path:
            self.config = ConfigManager(config_file=config_path)
        else:
            self.config = ConfigManager()
        
        logger.info(f"配置加载完成: {self.config.config_file}")
    
    def _init_logging(self) -> None:
        """初始化日志"""
        log_config = self.config.get('logging', {})
        
        log_level = log_config.get('level', 'INFO')
        log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_file = log_config.get('file')
        log_dir = log_config.get('dir', 'data/logs')
        
        # 创建日志目录
        log_dir_path = Path(log_dir)
        log_dir_path.mkdir(parents=True, exist_ok=True)
        
        # 配置根日志器
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format
        )
        
        # 添加文件处理器
        if log_file:
            log_file_path = log_dir_path / log_file
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(log_format))
            logging.getLogger().addHandler(file_handler)
        
        global logger
        logger = logging.getLogger(__name__)
    
    def _signal_handler(self, signum, frame) -> None:
        """信号处理"""
        logger.info(f"收到信号 {signum}, 正在关闭应用...")
        self.stop()
    
    def initialize(self) -> bool:
        """
        初始化应用
        
        Returns:
            是否成功
        """
        try:
            logger.info("开始初始化msearch应用...")
            
            # 检测硬件
            self.hardware_detector = HardwareDetector()
            hardware_info = self.hardware_detector.get_hardware_info()
            logger.info(f"硬件检测完成: CPU核心数={hardware_info['cpu']['physical_cores']}, "
                       f"内存={hardware_info['memory']['total']/1024:.1f}GB, "
                       f"GPU={'有' if hardware_info['gpu']['has_gpu'] else '无'}")
            
            # 初始化数据库管理器
            self.database_manager = DatabaseManager(self.config.config)
            if not self.database_manager.initialize():
                logger.error("数据库管理器初始化失败")
                return False
            logger.info("数据库管理器初始化完成")
            
            # 初始化向量存储
            self.vector_store = VectorStore(self.config.config)
            if not self.vector_store.initialize():
                logger.error("向量存储初始化失败")
                return False
            logger.info("向量存储初始化完成")
            
            # 初始化向量化引擎
            self.embedding_engine = EmbeddingEngine(self.config.config, self.hardware_detector)
            if not self.embedding_engine.initialize():
                logger.error("向量化引擎初始化失败")
                return False
            logger.info("向量化引擎初始化完成")
            
            # 初始化任务管理器
            self.task_manager = TaskManager(self.config.config)
            if not self.task_manager.initialize():
                logger.error("任务管理器初始化失败")
                return False
            logger.info("任务管理器初始化完成")
            
            # 初始化媒体处理器
            self.media_processor = MediaProcessor(self.config.config)
            logger.info("媒体处理器初始化完成")
            
            # 注册任务处理器
            self._register_task_handlers()
            
            # 初始化文件监控
            self._init_file_monitor()
            
            logger.info("msearch应用初始化完成")
            return True
        
        except Exception as e:
            logger.error(f"应用初始化失败: {e}", exc_info=True)
            return False
    
    def _register_task_handlers(self) -> None:
        """注册任务处理器"""
        # 文件扫描任务
        self.task_manager.register_task_handler(
            'file_scan',
            self._handle_file_scan_task
        )
        
        # 文件向量化任务
        self.task_manager.register_task_handler(
            'file_embed',
            self._handle_file_embed_task
        )
        
        # 视频切片任务
        self.task_manager.register_task_handler(
            'video_slice',
            self._handle_video_slice_task
        )
        
        # 音频分段任务
        self.task_manager.register_task_handler(
            'audio_segment',
            self._handle_audio_segment_task
        )
        
        logger.info("任务处理器注册完成")
    
    def _init_file_monitor(self) -> None:
        """初始化文件监控"""
        watch_config = self.config.get('file_monitor', {})
        
        if watch_config.get('enabled', True):
            self.file_monitor = FileMonitor(self.config.config)
            
            # 添加监控路径
            watch_paths = watch_config.get('paths', [])
            for path in watch_paths:
                if os.path.exists(path):
                    self.file_monitor.add_watch_path(path)
                    logger.info(f"添加监控路径: {path}")
            
            # 启动文件监控
            if self.file_monitor.start():
                logger.info("文件监控启动成功")
            else:
                logger.warning("文件监控启动失败")
    
    def start(self) -> None:
        """启动应用"""
        if not self.initialize():
            logger.error("应用初始化失败, 无法启动")
            return
        
        self.is_running = True
        logger.info("msearch应用启动成功")
        
        # 主循环
        try:
            while self.is_running:
                # 检查任务状态
                stats = self.task_manager.get_task_stats()
                if stats['total_count'] > 0:
                    logger.debug(f"任务状态: 待处理={stats['pending_count']}, "
                               f"运行中={stats['running_count']}, "
                               f"已完成={stats['completed_count']}, "
                               f"失败={stats['failed_count']}")
                
                # 短暂休眠
                import time
                time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("收到键盘中断, 正在关闭应用...")
            self.stop()
        except Exception as e:
            logger.error(f"应用运行错误: {e}", exc_info=True)
            self.stop()
    
    def stop(self) -> None:
        """停止应用"""
        if not self.is_running:
            return
        
        logger.info("正在停止msearch应用...")
        self.is_running = False
        
        # 停止文件监控
        if self.file_monitor:
            self.file_monitor.stop()
            logger.info("文件监控已停止")
        
        # 关闭任务管理器
        if self.task_manager:
            self.task_manager.shutdown()
            logger.info("任务管理器已关闭")
        
        # 关闭向量化引擎
        if self.embedding_engine:
            self.embedding_engine.shutdown()
            logger.info("向量化引擎已关闭")
        
        # 关闭向量存储
        if self.vector_store:
            self.vector_store.close()
            logger.info("向量存储已关闭")
        
        # 关闭数据库
        if self.database_manager:
            self.database_manager.close()
            logger.info("数据库已关闭")
        
        logger.info("msearch应用已停止")
    
    # 任务处理器
    
    def _handle_file_scan_task(self, task) -> dict:
        """
        处理文件扫描任务
        
        Args:
            task: 任务对象
        
        Returns:
            任务结果
        """
        try:
            file_path = task.task_data.get('file_path')
            if not file_path:
                raise ValueError("缺少file_path参数")
            
            # 处理文件
            result = self.media_processor.process_file(file_path)
            
            if not result.get('success'):
                raise Exception(result.get('error', '文件处理失败'))
            
            # 保存文件信息到数据库
            file_hash = result.get('file_hash')
            file_type = result.get('file_type')
            
            # 获取或创建文件记录
            file_uuid = self.database_manager.get_or_create_file_by_hash(
                file_hash=file_hash,
                file_path=file_path,
                metadata=result.get('metadata', {})
            )
            
            # 创建向量化任务
            self.task_manager.create_task(
                task_type='file_embed',
                task_data={
                    'file_uuid': file_uuid,
                    'file_path': file_path,
                    'file_type': file_type,
                    'file_hash': file_hash,
                    'processing_result': result
                },
                priority=3,
                depends_on=[task.id]
            )
            
            return {
                'success': True,
                'file_uuid': file_uuid,
                'file_hash': file_hash,
                'file_type': file_type
            }
        
        except Exception as e:
            logger.error(f"文件扫描任务失败: {e}")
            raise
    
    def _handle_file_embed_task(self, task) -> dict:
        """
        处理文件向量化任务
        
        Args:
            task: 任务对象
        
        Returns:
            任务结果
        """
        try:
            file_uuid = task.task_data.get('file_uuid')
            file_path = task.task_data.get('file_path')
            file_type = task.task_data.get('file_type')
            processing_result = task.task_data.get('processing_result', {})
            
            if not file_uuid or not file_path:
                raise ValueError("缺少必要参数")
            
            # 根据文件类型进行向量化
            if file_type == 'image':
                vector = self.embedding_engine.embed_image(file_path)
            elif file_type == 'video':
                # 视频处理
                if processing_result.get('is_short_video'):
                    # 短视频：提取帧并向量化
                    frames = processing_result.get('frames', [])
                    vectors = []
                    for frame in frames:
                        frame_vector = self.embedding_engine.embed_image(frame.get('path', ''))
                        vectors.append(frame_vector)
                    vector = vectors[0] if vectors else []
                else:
                    # 长视频：切片并向量化
                    segments = processing_result.get('segments', [])
                    vectors = []
                    for segment in segments:
                        segment_vector = self.embedding_engine.embed_video_segment(
                            file_path,
                            segment['start_time'],
                            segment['end_time']
                        )
                        vectors.append(segment_vector)
                    vector = vectors[0] if vectors else []
            elif file_type == 'audio':
                # 音频：转录文本并向量化
                transcript = self.embedding_engine.transcribe_audio(file_path)
                vector = self.embedding_engine.embed_text(transcript)
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
            
            if not vector:
                raise Exception("向量化失败")
            
            # 保存向量到向量数据库
            self.vector_store.insert_vectors([{
                'vector_id': f"{file_uuid}_0",
                'file_uuid': file_uuid,
                'segment_id': '0',
                'modality': file_type,
                'vector': vector,
                'metadata': processing_result.get('metadata', {})
            }])
            
            return {
                'success': True,
                'file_uuid': file_uuid,
                'vector_dimension': len(vector)
            }
        
        except Exception as e:
            logger.error(f"文件向量化任务失败: {e}")
            raise
    
    def _handle_video_slice_task(self, task) -> dict:
        """
        处理视频切片任务
        
        Args:
            task: 任务对象
        
        Returns:
            任务结果
        """
        # TODO: 实现视频切片任务
        return {'success': True}
    
    def _handle_audio_segment_task(self, task) -> dict:
        """
        处理音频分段任务
        
        Args:
            task: 任务对象
        
        Returns:
            任务结果
        """
        # TODO: 实现音频分段任务
        return {'success': True}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='msearch - 多模态检索系统')
    parser.add_argument('--config', '-c', type=str, help='配置文件路径')
    parser.add_argument('--version', '-v', action='version', version='msearch 1.0.0')
    
    args = parser.parse_args()
    
    # 创建应用实例
    app = MSearchApp(config_path=args.config)
    
    # 启动应用
    app.start()


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    main()