#!/usr/bin/env python3
"""
msearch GUI搜索工作线程
"""

from typing import Dict, Any, Optional, List, Union
import os

from PySide6.QtCore import QObject, QThread, Signal

from src.gui.api_client import ApiClient
from src.core.logging_config import get_logger

# 获取日志记录器
logger = get_logger(__name__)


class SearchWorker(QThread):
    """搜索工作线程，用于执行耗时的搜索操作"""
    
    # 信号定义
    search_started = Signal(str)  # 搜索开始
    search_progress = Signal(int, str)  # 搜索进度
    search_completed = Signal(dict)  # 搜索完成
    search_failed = Signal(str)  # 搜索失败
    
    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        
        self.api_client = api_client
        self.search_type = None
        self.search_params = {}
        self.is_running = False
    
    def start_text_search(self, query: str, limit: int = 20):
        """开始文本搜索"""
        self.search_type = "text"
        self.search_params = {
            "query": query,
            "limit": limit
        }
        self.start()
    
    def start_image_search(self, image_path: str, limit: int = 20):
        """开始图像搜索"""
        if not os.path.exists(image_path):
            self.search_failed.emit(f"图像文件不存在: {image_path}")
            return
        
        self.search_type = "image"
        self.search_params = {
            "image_path": image_path,
            "limit": limit
        }
        self.start()
    
    def start_audio_search(self, audio_path: str, limit: int = 20):
        """开始音频搜索"""
        if not os.path.exists(audio_path):
            self.search_failed.emit(f"音频文件不存在: {audio_path}")
            return
        
        self.search_type = "audio"
        self.search_params = {
            "audio_path": audio_path,
            "limit": limit
        }
        self.start()
    
    def start_video_search(self, video_path: str, limit: int = 20):
        """开始视频搜索"""
        if not os.path.exists(video_path):
            self.search_failed.emit(f"视频文件不存在: {video_path}")
            return
        
        self.search_type = "video"
        self.search_params = {
            "video_path": video_path,
            "limit": limit
        }
        self.start()
    
    def start_multimodal_search(self, query_text: Optional[str] = None,
                               image_path: Optional[str] = None,
                               audio_path: Optional[str] = None,
                               video_path: Optional[str] = None,
                               limit: int = 20):
        """开始多模态搜索"""
        # 检查至少有一个查询条件
        if not any([query_text, image_path, audio_path, video_path]):
            self.search_failed.emit("请至少提供一种查询条件")
            return
        
        # 检查文件是否存在
        if image_path and not os.path.exists(image_path):
            self.search_failed.emit(f"图像文件不存在: {image_path}")
            return
        
        if audio_path and not os.path.exists(audio_path):
            self.search_failed.emit(f"音频文件不存在: {audio_path}")
            return
        
        if video_path and not os.path.exists(video_path):
            self.search_failed.emit(f"视频文件不存在: {video_path}")
            return
        
        self.search_type = "multimodal"
        self.search_params = {
            "query_text": query_text,
            "image_path": image_path,
            "audio_path": audio_path,
            "video_path": video_path,
            "limit": limit
        }
        self.start()
    
    def start_timeline_search(self, query: Optional[str] = None,
                             time_range: Optional[Dict] = None,
                             file_types: Optional[List[str]] = None,
                             limit: int = 20):
        """开始时间线搜索"""
        self.search_type = "timeline"
        self.search_params = {
            "query": query,
            "time_range": time_range,
            "file_types": file_types,
            "limit": limit
        }
        self.start()
    
    def stop_search(self):
        """停止搜索"""
        self.is_running = False
        if self.isRunning():
            self.terminate()
            self.wait()
    
    def run(self):
        """执行搜索操作"""
        self.is_running = True
        
        try:
            # 发出搜索开始信号
            search_name = self.get_search_name()
            self.search_started.emit(search_name)
            logger.info(f"开始{search_name}")
            
            # 根据搜索类型执行相应的搜索
            if self.search_type == "text":
                result = self._execute_text_search()
            elif self.search_type == "image":
                result = self._execute_image_search()
            elif self.search_type == "audio":
                result = self._execute_audio_search()
            elif self.search_type == "video":
                result = self._execute_video_search()
            elif self.search_type == "multimodal":
                result = self._execute_multimodal_search()
            elif self.search_type == "timeline":
                result = self._execute_timeline_search()
            else:
                self.search_failed.emit(f"未知的搜索类型: {self.search_type}")
                return
            
            # 检查是否被停止
            if not self.is_running:
                return
            
            # 发出搜索完成信号
            if result:
                self.search_completed.emit(result)
                logger.info(f"{search_name}完成，找到 {len(result.get('data', {}).get('results', []))} 个结果")
            else:
                self.search_failed.emit("搜索失败，未返回结果")
                
        except Exception as e:
            error_msg = f"搜索过程中发生错误: {str(e)}"
            logger.error(error_msg)
            self.search_failed.emit(error_msg)
    
    def get_search_name(self) -> str:
        """获取搜索名称"""
        names = {
            "text": "文本搜索",
            "image": "图像搜索",
            "audio": "音频搜索",
            "video": "视频搜索",
            "multimodal": "多模态搜索",
            "timeline": "时间线搜索"
        }
        return names.get(self.search_type, "未知搜索")
    
    def _execute_text_search(self) -> Optional[Dict]:
        """执行文本搜索"""
        query = self.search_params.get("query", "")
        limit = self.search_params.get("limit", 20)
        
        self.search_progress.emit(10, "正在发送搜索请求...")
        result = self.api_client.search_text(query, limit)
        
        if not self.is_running:
            return None
        
        self.search_progress.emit(100, "搜索完成")
        return result
    
    def _execute_image_search(self) -> Optional[Dict]:
        """执行图像搜索"""
        image_path = self.search_params.get("image_path", "")
        limit = self.search_params.get("limit", 20)
        
        self.search_progress.emit(10, "正在读取图像文件...")
        
        self.search_progress.emit(30, "正在发送搜索请求...")
        result = self.api_client.search_image(image_path, limit)
        
        if not self.is_running:
            return None
        
        self.search_progress.emit(100, "搜索完成")
        return result
    
    def _execute_audio_search(self) -> Optional[Dict]:
        """执行音频搜索"""
        audio_path = self.search_params.get("audio_path", "")
        limit = self.search_params.get("limit", 20)
        
        self.search_progress.emit(10, "正在读取音频文件...")
        
        self.search_progress.emit(30, "正在发送搜索请求...")
        result = self.api_client.search_audio(audio_path, limit)
        
        if not self.is_running:
            return None
        
        self.search_progress.emit(100, "搜索完成")
        return result
    
    def _execute_video_search(self) -> Optional[Dict]:
        """执行视频搜索"""
        video_path = self.search_params.get("video_path", "")
        limit = self.search_params.get("limit", 20)
        
        self.search_progress.emit(10, "正在读取视频文件...")
        
        self.search_progress.emit(30, "正在发送搜索请求...")
        result = self.api_client.search_video(video_path, limit)
        
        if not self.is_running:
            return None
        
        self.search_progress.emit(100, "搜索完成")
        return result
    
    def _execute_multimodal_search(self) -> Optional[Dict]:
        """执行多模态搜索"""
        query_text = self.search_params.get("query_text")
        image_path = self.search_params.get("image_path")
        audio_path = self.search_params.get("audio_path")
        video_path = self.search_params.get("video_path")
        limit = self.search_params.get("limit", 20)
        
        progress = 10
        
        if query_text:
            self.search_progress.emit(progress, "正在处理文本查询...")
            progress += 10
        
        if image_path:
            self.search_progress.emit(progress, "正在读取图像文件...")
            progress += 10
        
        if audio_path:
            self.search_progress.emit(progress, "正在读取音频文件...")
            progress += 10
        
        if video_path:
            self.search_progress.emit(progress, "正在读取视频文件...")
            progress += 10
        
        self.search_progress.emit(50, "正在发送搜索请求...")
        result = self.api_client.search_multimodal(
            query_text=query_text,
            image_path=image_path,
            audio_path=audio_path,
            video_path=video_path,
            limit=limit
        )
        
        if not self.is_running:
            return None
        
        self.search_progress.emit(100, "搜索完成")
        return result
    
    def _execute_timeline_search(self) -> Optional[Dict]:
        """执行时间线搜索"""
        query = self.search_params.get("query")
        time_range = self.search_params.get("time_range")
        file_types = self.search_params.get("file_types")
        limit = self.search_params.get("limit", 20)
        
        self.search_progress.emit(10, "正在发送时间线搜索请求...")
        result = self.api_client.search_timeline(query, time_range, file_types, limit)
        
        if not self.is_running:
            return None
        
        self.search_progress.emit(100, "搜索完成")
        return result