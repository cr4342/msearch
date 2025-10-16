#!/usr/bin/env python3
"""
msearch GUI API客户端
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union

import requests
from PySide6.QtCore import QObject, Signal, QThread

from src.core.logging_config import get_logger

# 获取日志记录器
logger = get_logger(__name__)


class ApiClient(QObject):
    """API客户端类，用于与msearch后端API通信"""
    
    # 信号定义
    connection_status_changed = Signal(bool)
    error_occurred = Signal(str)
    search_completed = Signal(dict)
    file_list_updated = Signal(list)
    system_status_updated = Signal(dict)
    config_updated = Signal(dict)
    
    def __init__(self, base_url: str = "http://localhost:8000", parent=None):
        super().__init__(parent)
        
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.connected = False
        
        # 设置请求头
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        logger.info(f"API客户端初始化完成，基础URL: {self.base_url}")
    
    def connect(self) -> bool:
        """连接到API服务"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.connected = True
                self.connection_status_changed.emit(True)
                logger.info("已连接到API服务")
                return True
            else:
                self.connected = False
                self.connection_status_changed.emit(False)
                logger.error(f"连接API服务失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            self.connected = False
            self.connection_status_changed.emit(False)
            error_msg = f"连接API服务失败: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def disconnect(self):
        """断开与API服务的连接"""
        self.connected = False
        self.connection_status_changed.emit(False)
        logger.info("已断开与API服务的连接")
    
    def is_connected(self) -> bool:
        """检查是否已连接到API服务"""
        return self.connected
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     files: Optional[Dict] = None, params: Optional[Dict] = None) -> Optional[Dict]:
        """发送HTTP请求"""
        if not self.connected:
            self.error_occurred.emit("未连接到API服务")
            return None
        
        url = f"{self.base_url}/api/v1{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=30)
            elif method.upper() == 'POST':
                if files:
                    # 文件上传请求
                    headers = {'Accept': 'application/json'}
                    response = self.session.post(url, data=data, files=files, headers=headers, timeout=60)
                else:
                    response = self.session.post(url, json=data, params=params, timeout=30)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, params=params, timeout=30)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params, timeout=30)
            else:
                self.error_occurred.emit(f"不支持的HTTP方法: {method}")
                return None
            
            # 检查响应状态
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"success": True, "data": response.text}
            else:
                error_msg = f"API请求失败，状态码: {response.status_code}"
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg += f", 错误信息: {error_data['message']}"
                except json.JSONDecodeError:
                    pass
                
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return None
                
        except requests.exceptions.Timeout:
            error_msg = "API请求超时"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None
        except requests.exceptions.ConnectionError:
            error_msg = "API连接错误"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.connected = False
            self.connection_status_changed.emit(False)
            return None
        except Exception as e:
            error_msg = f"API请求异常: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None
    
    # 搜索API
    def search_text(self, query: str, limit: int = 20) -> Optional[Dict]:
        """文本搜索"""
        data = {"query": query, "limit": limit}
        result = self._make_request("POST", "/search/text", data)
        if result:
            self.search_completed.emit(result)
        return result
    
    def search_image(self, image_path: str, limit: int = 20) -> Optional[Dict]:
        """图像搜索"""
        try:
            with open(image_path, 'rb') as f:
                files = {"file": f}
                data = {"limit": limit}
                result = self._make_request("POST", "/search/image", data=data, files=files)
                if result:
                    self.search_completed.emit(result)
                return result
        except Exception as e:
            error_msg = f"图像搜索失败: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None
    
    def search_audio(self, audio_path: str, limit: int = 20) -> Optional[Dict]:
        """音频搜索"""
        try:
            with open(audio_path, 'rb') as f:
                files = {"file": f}
                data = {"limit": limit}
                result = self._make_request("POST", "/search/audio", data=data, files=files)
                if result:
                    self.search_completed.emit(result)
                return result
        except Exception as e:
            error_msg = f"音频搜索失败: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None
    
    def search_video(self, video_path: str, limit: int = 20) -> Optional[Dict]:
        """视频搜索"""
        try:
            with open(video_path, 'rb') as f:
                files = {"file": f}
                data = {"limit": limit}
                result = self._make_request("POST", "/search/video", data=data, files=files)
                if result:
                    self.search_completed.emit(result)
                return result
        except Exception as e:
            error_msg = f"视频搜索失败: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None
    
    def search_multimodal(self, query_text: Optional[str] = None, 
                         image_path: Optional[str] = None,
                         audio_path: Optional[str] = None,
                         video_path: Optional[str] = None,
                         limit: int = 20) -> Optional[Dict]:
        """多模态搜索"""
        files = {}
        data = {"limit": limit}
        
        if query_text:
            data["query_text"] = query_text
        
        if image_path:
            try:
                with open(image_path, 'rb') as f:
                    files["image_file"] = f
            except Exception as e:
                error_msg = f"读取图像文件失败: {str(e)}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return None
        
        if audio_path:
            try:
                with open(audio_path, 'rb') as f:
                    files["audio_file"] = f
            except Exception as e:
                error_msg = f"读取音频文件失败: {str(e)}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return None
        
        if video_path:
            try:
                with open(video_path, 'rb') as f:
                    files["video_file"] = f
            except Exception as e:
                error_msg = f"读取视频文件失败: {str(e)}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return None
        
        result = self._make_request("POST", "/search/multimodal", data=data, files=files)
        if result:
            self.search_completed.emit(result)
        return result
    
    def search_timeline(self, query: Optional[str] = None,
                       time_range: Optional[Dict] = None,
                       file_types: Optional[List[str]] = None,
                       limit: int = 20) -> Optional[Dict]:
        """时间线搜索"""
        data = {"limit": limit}
        
        if query:
            data["query"] = query
        
        if time_range:
            data["time_range"] = time_range
        
        if file_types:
            data["file_types"] = file_types
        
        result = self._make_request("POST", "/search/timeline", data)
        if result:
            self.search_completed.emit(result)
        return result
    
    # 文件管理API
    def get_file_list(self, path: Optional[str] = None) -> Optional[Dict]:
        """获取文件列表"""
        params = {}
        if path:
            params["path"] = path
        
        result = self._make_request("GET", "/files/list", params=params)
        if result:
            self.file_list_updated.emit(result.get("data", []))
        return result
    
    def process_file(self, file_path: str, file_id: str) -> Optional[Dict]:
        """处理文件"""
        data = {"file_path": file_path, "file_id": file_id}
        return self._make_request("POST", "/files/process", data)
    
    def get_process_status(self, file_id: str) -> Optional[Dict]:
        """获取文件处理状态"""
        return self._make_request("GET", f"/files/process-status/{file_id}")
    
    # 系统API
    def get_system_status(self) -> Optional[Dict]:
        """获取系统状态"""
        result = self._make_request("GET", "/system/status")
        if result:
            self.system_status_updated.emit(result.get("data", {}))
        return result
    
    def get_system_config(self) -> Optional[Dict]:
        """获取系统配置"""
        result = self._make_request("GET", "/config")
        if result:
            self.config_updated.emit(result.get("data", {}))
        return result
    
    def update_system_config(self, config: Dict) -> Optional[Dict]:
        """更新系统配置"""
        result = self._make_request("PUT", "/config", config)
        if result:
            self.config_updated.emit(result.get("data", {}))
        return result
    
    def system_reset(self, reset_type: str = "all") -> Optional[Dict]:
        """系统重置"""
        data = {"reset_type": reset_type}
        return self._make_request("POST", "/system/reset", data)
    
    # 监控API
    def get_monitoring_status(self) -> Optional[Dict]:
        """获取文件监控状态"""
        return self._make_request("GET", "/monitoring/status")
    
    def start_monitoring(self) -> Optional[Dict]:
        """启动文件监控"""
        return self._make_request("POST", "/monitoring/start")
    
    def stop_monitoring(self) -> Optional[Dict]:
        """停止文件监控"""
        return self._make_request("POST", "/monitoring/stop")
    
    # 人脸识别API
    def get_face_persons(self) -> Optional[Dict]:
        """获取所有人名列表"""
        return self._make_request("GET", "/face/persons")
    
    def add_person_to_face_database(self, name: str, image_paths: List[str], 
                                   aliases: Optional[List[str]] = None,
                                   description: Optional[str] = None) -> Optional[Dict]:
        """添加人物到人脸库"""
        files = {}
        data = {"name": name}
        
        if aliases:
            data["aliases"] = json.dumps(aliases)
        
        if description:
            data["description"] = description
        
        # 添加图片文件
        for i, image_path in enumerate(image_paths):
            try:
                with open(image_path, 'rb') as f:
                    files[f"image_files"] = f
            except Exception as e:
                error_msg = f"读取图片文件失败: {str(e)}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return None
        
        return self._make_request("POST", "/face/persons", data=data, files=files)
    
    def search_faces(self, image_path: str, limit: int = 10) -> Optional[Dict]:
        """人脸搜索"""
        try:
            with open(image_path, 'rb') as f:
                files = {"image_file": f}
                data = {"limit": limit}
                return self._make_request("POST", "/face/search", data=data, files=files)
        except Exception as e:
            error_msg = f"人脸搜索失败: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None