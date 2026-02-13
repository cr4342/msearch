"""
增强型任务管理器组件
满足 requirements.md 中需求5、6、17的所有要求

功能：
1. 目录监控可视化（需求5）
2. 实时进度显示和手动控制（需求6）
3. 任务队列可视化和优先级管理（需求17）
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class EnhancedTaskManager:
    """
    增强型任务管理器
    
    满足需求文档中关于任务管理的所有要求：
    - 需求5: 目录监控与可视化
    - 需求6: 手动操作控制与进度管理
    - 需求17: 任务优先级与调度
    """
    
    def __init__(self, api_client=None, config: Dict[str, Any] = None):
        """
        初始化增强型任务管理器
        
        Args:
            api_client: API客户端实例
            config: 配置字典
        """
        self.api_client = api_client
        self.config = config or {}
        
        # 监控目录列表
        self.monitored_directories: List[Dict[str, Any]] = []
        
        # 文件统计信息
        self.file_stats = {
            "total_files": 0,
            "image_files": 0,
            "video_files": 0,
            "audio_files": 0,
            "processing_files": 0,
            "new_files": 0,
        }
        
        # 任务队列信息
        self.task_queue = {
            "pending": [],
            "running": [],
            "completed": [],
            "failed": [],
            "cancelled": [],
        }
        
        # 线程池状态
        self.thread_pool_status = {
            "max_workers": 8,
            "active_threads": 0,
            "idle_threads": 8,
            "load_percentage": 0,
        }
        
        # 当前处理进度
        self.current_progress = {
            "current_file": "",
            "current_operation": "",
            "processed_count": 0,
            "total_count": 0,
            "progress_percentage": 0.0,
            "processing_speed": 0.0,  # 文件/分钟
            "estimated_remaining_time": 0,  # 秒
            "start_time": None,
            "status": "idle",  # idle, running, paused
        }
        
        # 文件类型优先级配置（需求17）
        self.file_type_priority = {
            "video": 1,  # 最高优先级
            "image": 5,  # 中等优先级
            "audio": 3,  # 较高优先级
        }
        
        # 任务类型优先级映射（需求17）
        self.task_type_priority = {
            # 向量化任务 - 最高优先级 (1-5)
            "file_embed_video": 1,
            "file_embed_image": 3,
            "file_embed_audio": 2,
            "file_embed_text": 4,
            
            # 预处理任务 - 中等优先级 (6-8)
            "video_preprocess": 6,
            "image_preprocess": 7,
            "audio_preprocess": 7,
            "video_slice": 6,
            
            # 辅助任务 - 较低优先级 (9-10)
            "thumbnail_generate": 9,
            "preview_generate": 10,
            "file_scan": 8,
        }
    
    # ==================== 需求5: 目录监控与可视化 ====================
    
    def get_monitored_directories(self) -> List[Dict[str, Any]]:
        """
        获取监控目录列表
        
        Returns:
            监控目录列表，包含路径、状态、统计信息
        """
        try:
            if self.api_client:
                # 从API获取监控目录
                response = self.api_client.get_monitored_directories()
                if response:
                    self.monitored_directories = response
            
            return self.monitored_directories
        except Exception as e:
            logger.error(f"获取监控目录失败: {e}")
            return []
    
    def add_monitored_directory(self, directory_path: str) -> bool:
        """
        添加监控目录
        
        Args:
            directory_path: 目录路径
            
        Returns:
            是否成功添加
        """
        try:
            if self.api_client:
                success = self.api_client.add_monitored_directory(directory_path)
                if success:
                    # 添加到本地列表
                    new_dir = {
                        "path": directory_path,
                        "status": "monitoring",  # 监控中
                        "file_count": 0,
                        "image_count": 0,
                        "video_count": 0,
                        "audio_count": 0,
                        "new_files": 0,
                        "processing_files": 0,
                        "added_time": datetime.now().isoformat(),
                    }
                    self.monitored_directories.append(new_dir)
                    logger.info(f"已添加监控目录: {directory_path}")
                    return True
            return False
        except Exception as e:
            logger.error(f"添加监控目录失败: {e}")
            return False
    
    def remove_monitored_directory(self, directory_path: str) -> bool:
        """
        移除监控目录
        
        Args:
            directory_path: 目录路径
            
        Returns:
            是否成功移除
        """
        try:
            if self.api_client:
                success = self.api_client.remove_monitored_directory(directory_path)
                if success:
                    # 从本地列表移除
                    self.monitored_directories = [
                        d for d in self.monitored_directories 
                        if d["path"] != directory_path
                    ]
                    logger.info(f"已移除监控目录: {directory_path}")
                    return True
            return False
        except Exception as e:
            logger.error(f"移除监控目录失败: {e}")
            return False
    
    def pause_directory_monitoring(self, directory_path: str) -> bool:
        """
        暂停目录监控
        
        Args:
            directory_path: 目录路径
            
        Returns:
            是否成功暂停
        """
        try:
            if self.api_client:
                success = self.api_client.pause_directory(directory_path)
                if success:
                    # 更新本地状态
                    for d in self.monitored_directories:
                        if d["path"] == directory_path:
                            d["status"] = "paused"
                            break
                    logger.info(f"已暂停监控目录: {directory_path}")
                    return True
            return False
        except Exception as e:
            logger.error(f"暂停监控目录失败: {e}")
            return False
    
    def resume_directory_monitoring(self, directory_path: str) -> bool:
        """
        恢复目录监控
        
        Args:
            directory_path: 目录路径
            
        Returns:
            是否成功恢复
        """
        try:
            if self.api_client:
                success = self.api_client.resume_directory(directory_path)
                if success:
                    # 更新本地状态
                    for d in self.monitored_directories:
                        if d["path"] == directory_path:
                            d["status"] = "monitoring"
                            break
                    logger.info(f"已恢复监控目录: {directory_path}")
                    return True
            return False
        except Exception as e:
            logger.error(f"恢复监控目录失败: {e}")
            return False
    
    def get_directory_status_display(self) -> str:
        """
        获取目录状态显示文本
        
        Returns:
            HTML格式的目录状态显示
        """
        html = "<div style='padding: 10px;'>"
        html += "<h3>📁 监控目录列表</h3>"
        
        if not self.monitored_directories:
            html += "<p style='color: #666;'>暂无监控目录</p>"
        else:
            html += "<table style='width: 100%; border-collapse: collapse;'>"
            html += "<tr style='background: #f0f0f0;'>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>状态</th>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>目录路径</th>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>总数</th>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>图像</th>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>视频</th>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>音频</th>"
            html += "</tr>"
            
            for dir_info in self.monitored_directories:
                status = dir_info.get("status", "unknown")
                status_icon = {
                    "monitoring": "🟢",  # 监控中
                    "paused": "🟡",      # 暂停
                    "error": "🔴",       # 错误
                    "initializing": "🔵", # 初始化中
                }.get(status, "⚪")
                
                html += "<tr>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{status_icon} {status}</td>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{dir_info.get('path', '')}</td>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{dir_info.get('file_count', 0)}</td>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{dir_info.get('image_count', 0)}</td>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{dir_info.get('video_count', 0)}</td>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{dir_info.get('audio_count', 0)}</td>"
                html += "</tr>"
            
            html += "</table>"
        
        html += "</div>"
        return html
    
    # ==================== 需求6: 手动操作控制与进度管理 ====================
    
    def trigger_full_scan(self) -> bool:
        """
        触发全量扫描
        
        Returns:
            是否成功触发
        """
        try:
            if self.api_client:
                success = self.api_client.trigger_full_scan()
                if success:
                    self.current_progress["status"] = "running"
                    self.current_progress["start_time"] = datetime.now()
                    self.current_progress["current_operation"] = "全量扫描"
                    logger.info("已触发全量扫描")
                    return True
            return False
        except Exception as e:
            logger.error(f"触发全量扫描失败: {e}")
            return False
    
    def trigger_directory_scan(self, directory: str) -> bool:
        """
        触发指定目录扫描
        
        Args:
            directory: 目录路径
            
        Returns:
            是否成功触发
        """
        try:
            if self.api_client:
                success = self.api_client.trigger_directory_scan(directory)
                if success:
                    self.current_progress["status"] = "running"
                    self.current_progress["start_time"] = datetime.now()
                    self.current_progress["current_operation"] = f"扫描目录: {directory}"
                    logger.info(f"已触发目录扫描: {directory}")
                    return True
            return False
        except Exception as e:
            logger.error(f"触发目录扫描失败: {e}")
            return False
    
    def trigger_vectorization(self, file_type: Optional[str] = None) -> bool:
        """
        触发向量化处理
        
        Args:
            file_type: 文件类型过滤（image/video/audio）
            
        Returns:
            是否成功触发
        """
        try:
            if self.api_client:
                success = self.api_client.trigger_vectorization(file_type)
                if success:
                    self.current_progress["status"] = "running"
                    self.current_progress["start_time"] = datetime.now()
                    type_str = file_type if file_type else "全部"
                    self.current_progress["current_operation"] = f"向量化处理 ({type_str})"
                    logger.info(f"已触发向量化处理: {type_str}")
                    return True
            return False
        except Exception as e:
            logger.error(f"触发向量化处理失败: {e}")
            return False
    
    def pause_processing(self) -> bool:
        """
        暂停当前处理
        
        Returns:
            是否成功暂停
        """
        try:
            if self.api_client:
                success = self.api_client.pause_tasks()
                if success:
                    self.current_progress["status"] = "paused"
                    logger.info("已暂停处理")
                    return True
            return False
        except Exception as e:
            logger.error(f"暂停处理失败: {e}")
            return False
    
    def resume_processing(self) -> bool:
        """
        恢复当前处理
        
        Returns:
            是否成功恢复
        """
        try:
            if self.api_client:
                success = self.api_client.resume_tasks()
                if success:
                    self.current_progress["status"] = "running"
                    logger.info("已恢复处理")
                    return True
            return False
        except Exception as e:
            logger.error(f"恢复处理失败: {e}")
            return False
    
    def cancel_processing(self) -> bool:
        """
        取消当前处理
        
        Returns:
            是否成功取消
        """
        try:
            if self.api_client:
                success = self.api_client.cancel_tasks()
                if success:
                    self.current_progress["status"] = "idle"
                    self.current_progress["current_operation"] = ""
                    self.current_progress["current_file"] = ""
                    logger.info("已取消处理")
                    return True
            return False
        except Exception as e:
            logger.error(f"取消处理失败: {e}")
            return False
    
    def get_progress_display(self) -> Tuple[str, str]:
        """
        获取进度显示HTML
        
        Returns:
            (progress_html, operation_html) 元组
        """
        # 从API获取最新进度
        try:
            if self.api_client:
                tasks = self.api_client.get_tasks(status="running")
                if tasks:
                    # 更新当前进度
                    self.current_progress["processed_count"] = len(tasks)
                    # 计算进度百分比
                    if self.current_progress["total_count"] > 0:
                        self.current_progress["progress_percentage"] = (
                            self.current_progress["processed_count"] / 
                            self.current_progress["total_count"] * 100
                        )
        except Exception as e:
            logger.error(f"获取进度失败: {e}")
        
        # 生成进度HTML
        progress = self.current_progress["progress_percentage"]
        processed = self.current_progress["processed_count"]
        total = self.current_progress["total_count"]
        status = self.current_progress["status"]
        
        if status == "idle" and processed == 0:
            progress_html = "<div style='padding: 20px; text-align: center; color: #666;'>暂无运行中的任务</div>"
            operation_html = "<div style='padding: 20px; text-align: center; color: #666;'>暂无操作</div>"
            return progress_html, operation_html
        
        # 进度条颜色
        if progress >= 100:
            bar_color = "#4caf50"
        elif progress >= 50:
            bar_color = "#2196f3"
        else:
            bar_color = "#ff9800"
        
        # 计算处理速度
        speed = self.current_progress["processing_speed"]
        speed_text = f"{speed:.1f} 文件/分钟" if speed > 0 else "计算中..."
        
        # 计算预计剩余时间
        remaining = self.current_progress["estimated_remaining_time"]
        if remaining > 0:
            remaining_min = int(remaining / 60)
            remaining_sec = int(remaining % 60)
            remaining_text = f"{remaining_min}分{remaining_sec}秒"
        else:
            remaining_text = "计算中..."
        
        # 进度HTML
        progress_html = f"""
        <div style='padding: 15px; background: #f5f5f5; border-radius: 8px;'>
            <div style='margin-bottom: 10px;'>
                <span style='font-weight: bold;'>处理进度:</span>
                <span style='float: right; color: {bar_color}; font-weight: bold;'>{progress:.1f}%</span>
            </div>
            <div style='background: #e0e0e0; height: 24px; border-radius: 12px; overflow: hidden;'>
                <div style='background: {bar_color}; height: 100%; width: {progress}%; 
                     transition: width 0.3s; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;'>
                    {processed}/{total}
                </div>
            </div>
            <div style='margin-top: 10px; display: flex; justify-content: space-between;'>
                <span>已处理: <strong>{processed}</strong></span>
                <span>总计: <strong>{total}</strong></span>
                <span>处理速度: <strong>{speed_text}</strong></span>
                <span>预计剩余: <strong>{remaining_text}</strong></span>
            </div>
        </div>
        """
        
        # 当前操作HTML
        current_file = self.current_progress["current_file"]
        current_op = self.current_progress["current_operation"]
        
        operation_html = f"""
        <div style='padding: 15px; background: #f5f5f5; border-radius: 8px;'>
            <div style='margin-bottom: 10px;'>
                <span style='font-weight: bold;'>当前操作:</span>
                <span style='color: #165DFF;'>{current_op}</span>
            </div>
            <div style='margin-bottom: 10px;'>
                <span style='font-weight: bold;'>正在处理:</span>
                <span style='color: #666; font-family: monospace;'>{current_file if current_file else "等待中..."}</span>
            </div>
            <div>
                <span style='font-weight: bold;'>状态:</span>
                <span style='color: {"#4caf50" if status == "running" else "#ff9800"};'>
                    {"运行中" if status == "running" else "已暂停" if status == "paused" else "空闲"}
                </span>
            </div>
        </div>
        """
        
        return progress_html, operation_html
    
    # ==================== 需求17: 任务优先级与调度 ====================
    
    def get_task_queue(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取任务队列
        
        Args:
            status: 状态过滤（pending/running/completed/failed/cancelled）
            
        Returns:
            任务列表
        """
        try:
            if self.api_client:
                tasks = self.api_client.get_tasks(status=status)
                return tasks if tasks else []
            return []
        except Exception as e:
            logger.error(f"获取任务队列失败: {e}")
            return []
    
    def update_task_priority(self, task_id: str, new_priority: int) -> bool:
        """
        更新任务优先级
        
        Args:
            task_id: 任务ID
            new_priority: 新优先级（0-11）
            
        Returns:
            是否成功更新
        """
        try:
            if self.api_client:
                success = self.api_client.update_task_priority(task_id, new_priority)
                if success:
                    logger.info(f"已更新任务 {task_id} 优先级为 {new_priority}")
                    return True
            return False
        except Exception as e:
            logger.error(f"更新任务优先级失败: {e}")
            return False
    
    def update_file_type_priority(self, file_type: str, priority: int) -> bool:
        """
        更新文件类型优先级
        
        Args:
            file_type: 文件类型（video/image/audio）
            priority: 优先级（0-11，数值越小优先级越高）
            
        Returns:
            是否成功更新
        """
        try:
            if file_type in self.file_type_priority:
                self.file_type_priority[file_type] = priority
                logger.info(f"已更新文件类型 {file_type} 优先级为 {priority}")
                return True
            return False
        except Exception as e:
            logger.error(f"更新文件类型优先级失败: {e}")
            return False
    
    def get_priority_level_color(self, priority: int) -> str:
        """
        根据优先级获取颜色
        
        Args:
            priority: 优先级（0-11）
            
        Returns:
            颜色代码
        """
        if priority <= 3:
            return "#F53F3F"  # 红色 - 高优先级
        elif priority <= 7:
            return "#FF7D00"  # 橙色 - 中优先级
        else:
            return "#86909C"  # 灰色 - 低优先级
    
    def get_task_queue_display(self) -> str:
        """
        获取任务队列显示HTML
        
        Returns:
            HTML格式的任务队列显示
        """
        # 获取任务列表
        pending_tasks = self.get_task_queue("pending")
        running_tasks = self.get_task_queue("running")
        
        html = "<div style='padding: 10px;'>"
        
        # 正在执行的任务
        html += "<h4>🔄 正在执行的任务</h4>"
        if running_tasks:
            html += "<table style='width: 100%; border-collapse: collapse; margin-bottom: 20px;'>"
            html += "<tr style='background: #e3f2fd;'>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>任务ID</th>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>类型</th>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>文件</th>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>进度</th>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>优先级</th>"
            html += "</tr>"
            
            for task in running_tasks:
                priority = task.get("priority", 5)
                color = self.get_priority_level_color(priority)
                
                html += "<tr>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{task.get('id', '')[:8]}</td>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{task.get('task_type', '')}</td>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{task.get('file_path', '')[20:]}</td>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{task.get('progress', 0):.1%}</td>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd; color: {color}; font-weight: bold;'>P{priority}</td>"
                html += "</tr>"
            
            html += "</table>"
        else:
            html += "<p style='color: #666;'>暂无运行中的任务</p>"
        
        # 等待中的任务
        html += "<h4>⏳ 等待中的任务</h4>"
        if pending_tasks:
            html += "<table style='width: 100%; border-collapse: collapse;'>"
            html += "<tr style='background: #fff3e0;'>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>任务ID</th>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>类型</th>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>文件</th>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>优先级</th>"
            html += "<th style='padding: 8px; border: 1px solid #ddd;'>创建时间</th>"
            html += "</tr>"
            
            # 按优先级排序
            sorted_tasks = sorted(pending_tasks, key=lambda x: x.get("priority", 5))
            
            for task in sorted_tasks[:20]:  # 只显示前20个
                priority = task.get("priority", 5)
                color = self.get_priority_level_color(priority)
                created_at = task.get("created_at", "")
                if created_at:
                    try:
                        created_at = created_at.split("T")[0] + " " + created_at.split("T")[1][:5]
                    except:
                        pass
                
                html += "<tr>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{task.get('id', '')[:8]}</td>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{task.get('task_type', '')}</td>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{task.get('file_path', '')[20:]}</td>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd; color: {color}; font-weight: bold;'>P{priority}</td>"
                html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{created_at}</td>"
                html += "</tr>"
            
            html += "</table>"
            if len(pending_tasks) > 20:
                html += f"<p style='color: #666; text-align: center;'>...还有 {len(pending_tasks) - 20} 个任务等待中</p>"
        else:
            html += "<p style='color: #666;'>暂无等待中的任务</p>"
        
        html += "</div>"
        return html
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """
        获取任务统计信息
        
        Returns:
            任务统计信息字典
        """
        try:
            if self.api_client:
                stats = self.api_client.get_task_stats()
                return stats if stats else {}
            return {}
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {}
    
    def get_file_type_priority_config(self) -> Dict[str, int]:
        """
        获取文件类型优先级配置
        
        Returns:
            文件类型优先级字典
        """
        return self.file_type_priority.copy()
    
    def refresh_all_data(self) -> Dict[str, Any]:
        """
        刷新所有数据
        
        Returns:
            包含所有数据的字典
        """
        return {
            "monitored_directories": self.get_monitored_directories(),
            "file_stats": self.file_stats,
            "task_queue": {
                "pending": len(self.get_task_queue("pending")),
                "running": len(self.get_task_queue("running")),
                "completed": len(self.get_task_queue("completed")),
                "failed": len(self.get_task_queue("failed")),
            },
            "thread_pool_status": self.thread_pool_status,
            "current_progress": self.current_progress,
            "file_type_priority": self.file_type_priority,
        }
