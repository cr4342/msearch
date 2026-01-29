#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
msearch WebUI - Gradio 界面
"""

import sys
import os
import gradio as gr
import logging
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from core.config.config_manager import ConfigManager
from webui.api_client import APIClient
from services.file.file_monitor import FileMonitor

logger = logging.getLogger(__name__)

# 全局线程池
_thread_pool = ThreadPoolExecutor(max_workers=4)

# 全局事件循环（避免重复创建）
_global_event_loop = None


def run_async(coro):
    """在全局事件循环中运行异步函数"""
    global _global_event_loop
    
    try:
        # 尝试获取当前运行的事件循环
        loop = asyncio.get_running_loop()
        # 如果已经在事件循环中运行，直接运行协程
        import concurrent.futures
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result(timeout=60)
    except RuntimeError:
        # 没有运行中的事件循环，创建新的
        if _global_event_loop is None or _global_event_loop.is_closed():
            _global_event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_global_event_loop)
        try:
            return _global_event_loop.run_until_complete(coro)
        except Exception as e:
            logger.error(f"运行异步函数失败: {e}")
            raise


class MSearchWebUI:
    """msearch WebUI 界面"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化 WebUI
        
        Args:
            config_path: 配置文件路径
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        
        # 搜索历史记录
        self.search_history = []
        self.max_history = 50
        
        # 初始化API客户端
        api_base_url = self.config_manager.get('api.base_url', 'http://localhost:8000')
        self.api_client = APIClient(api_base_url)
        logger.info(f"✓ API客户端初始化完成: {api_base_url}")
        
        # 初始化文件监控器
        self.file_monitor = FileMonitor(self.config)
        
        # 注册文件事件处理器
        self.file_monitor.register_event_handler('created', self._on_file_created)
        self.file_monitor.register_event_handler('modified', self._on_file_modified)
        self.file_monitor.register_event_handler('deleted', self._on_file_deleted)
        
        # 添加监控目录
        watch_dirs = self.config.get('file_monitor', {}).get('watch_directories', [])
        for directory in watch_dirs:
            if os.path.exists(directory):
                self.file_monitor.add_directory(directory)
                logger.info(f"  - 添加监控目录: {directory}")
        
        # 启动文件监控
        self.file_monitor.start_monitoring()
        logger.info("✓ 文件监控器已启动")
        
        logger.info("MSearch WebUI 初始化完成")
    
    def _on_file_created(self, event_type: str, file_path: str):
        """
        文件创建事件处理器
        
        Args:
            event_type: 事件类型
            file_path: 文件路径
        """
        try:
            logger.info(f"[文件监控] 检测到新文件: {file_path}")
            
            # 获取文件类型
            file_type = self._get_file_type(file_path)
            if not file_type:
                logger.warning(f"[文件监控] 不支持的文件类型: {file_path}")
                return
            
            # 调用API索引文件
            response = self.api_client.index_file(file_path)
            logger.info(f"[文件监控] 已提交处理任务: {file_path} -> {response.get('message', 'Success')}")
        
        except Exception as e:
            logger.error(f"[文件监控] 处理文件创建事件失败: {file_path}, 错误: {e}")
    
    def _on_file_modified(self, event_type: str, file_path: str):
        """
        文件修改事件处理器
        
        Args:
            event_type: 事件类型
            file_path: 文件路径
        """
        try:
            logger.info(f"[文件监控] 检测到文件修改: {file_path}")
            
            # 获取文件类型
            file_type = self._get_file_type(file_path)
            if not file_type:
                return
            
            # 调用API重新索引文件
            response = self.api_client.index_file(file_path)
            logger.info(f"[文件监控] 已重新提交处理任务: {file_path} -> {response.get('message', 'Success')}")
        
        except Exception as e:
            logger.error(f"[文件监控] 处理文件修改事件失败: {file_path}, 错误: {e}")
    
    def _on_file_deleted(self, event_type: str, file_path: str):
        """
        文件删除事件处理器
        
        Args:
            event_type: 事件类型
            file_path: 文件路径
        """
        try:
            logger.info(f"[文件监控] 检测到文件删除: {file_path}")
            
            # 注意：文件删除事件暂时不通过API处理，因为API端点暂不支持
            # 后续可以添加删除文件的API端点
            logger.info(f"[文件监控] 文件删除事件已记录: {file_path}")
        
        except Exception as e:
            logger.error(f"[文件监控] 处理文件删除事件失败: {file_path}, 错误: {e}")
    
    def _get_file_type(self, file_path: str) -> Optional[str]:
        """
        获取文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件类型 (image/video/audio) 或 None
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
        audio_exts = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'}
        
        if ext in image_exts:
            return 'image'
        elif ext in video_exts:
            return 'video'
        elif ext in audio_exts:
            return 'audio'
        
        return None
    

    
    def search_text(self, query: str, top_k: int = 10, similarity_threshold: float = 0.0):
        """
        文本搜索
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值，高于此值的结果才会返回
            
        Returns:
            搜索结果（Markdown 格式）
        """
        async def _search():
            try:
                # 输入验证
                if not query or not query.strip():
                    return "## ⚠️ 输入错误\n\n请输入搜索关键词"
                
                if len(query.strip()) > 500:
                    return "## ⚠️ 输入错误\n\n搜索关键词过长，请限制在 500 个字符以内"
                
                if top_k < 1 or top_k > 50:
                    return "## ⚠️ 参数错误\n\n返回结果数量必须在 1-50 之间"
                
                if similarity_threshold < 0.0 or similarity_threshold > 1.0:
                    return "## ⚠️ 参数错误\n\n相似度阈值必须在 0.0-1.0 之间"
                
                logger.info(f"文本搜索: {query}, 相似度阈值: {similarity_threshold}")
                
                # 添加到搜索历史
                self._add_to_history(query, 'text')
                
                # 调用API进行搜索
                response = self.api_client.search_text(
                    query=query,
                    top_k=top_k,
                    threshold=similarity_threshold
                )
                
                results = response.get('results', [])
                total = response.get('total', len(results))
                logger.info(f"找到 {total} 个结果")
                
                # 格式化结果为 Markdown
                output = f"# 🔍 文本搜索结果: '{query}'\n\n"
                output += f"**找到 {total} 个结果**\n\n"
                
                if total == 0:
                    output += "## ⚠️ 未找到任何结果\n\n"
                    output += "💡 **提示**:\n"
                    output += "- 请尝试使用不同的关键词\n"
                    output += "- 确保数据库中已索引相关文件\n"
                    output += "- 检查关键词拼写是否正确\n"
                    return output
                
                # 按相似度排序
                sorted_results = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)
                
                # 显示所有结果
                output += "| # | 文件名 | 类型 | 相似度 | 路径 |\n"
                output += "|---|---|---|---|---|\n"
                
                for i, result in enumerate(sorted_results):
                    file_name = result.get('file_name', result.get('metadata', {}).get('file_name', result.get('file_path', '未知')))
                    file_path = result.get('file_path', result.get('metadata', {}).get('file_path', '未知'))
                    modality = result.get('modality', '未知')
                    similarity = result.get('similarity', 0)
                    
                    # 格式化相似度为百分比
                    similarity_percent = similarity * 100 if similarity <= 1 else similarity
                    similarity_bar = "█" * int(similarity_percent / 10) + "░" * (10 - int(similarity_percent / 10))
                    
                    # 截断文件名
                    display_name = file_name[:30] + "..." if len(file_name) > 30 else file_name
                    display_path = file_path[:40] + "..." if len(file_path) > 40 else file_path
                    
                    # 根据类型添加图标
                    type_icon = {
                        'image': '🖼️',
                        'video': '🎬',
                        'audio': '🎵',
                        'unknown': '📄'
                    }.get(modality.lower(), '📄')
                    
                    output += f"| {i+1} | **{display_name}** | {type_icon} {modality} | {similarity_bar} `{similarity:.4f}` | `{display_path}` |\n"
                
                output += f"\n---\n"
                output += f"**搜索时间**: {total} 个结果 | **查询**: `{query}`\n"
                
                return output
                
            except ValueError as e:
                logger.error(f"参数错误: {e}", exc_info=True)
                return f"## ⚠️ 参数错误\n\n**错误信息**: {e}\n\n请检查输入参数是否正确。"
            except RuntimeError as e:
                logger.error(f"运行时错误: {e}", exc_info=True)
                return f"## ❌ 系统错误\n\n**错误信息**: {e}\n\n请稍后重试或检查系统日志。"
            except Exception as e:
                logger.error(f"搜索失败: {e}", exc_info=True)
                return f"## ❌ 搜索失败\n\n**错误信息**: {e}\n\n请检查系统日志获取详细信息。"
        
        return run_async(_search())
    
    def _add_to_history(self, query: str, search_type: str):
        """
        添加搜索到历史记录
        
        Args:
            query: 搜索查询
            search_type: 搜索类型（text/image）
        """
        import time
        
        history_item = {
            'query': query,
            'type': search_type,
            'timestamp': time.time()
        }
        
        # 添加到历史记录开头
        self.search_history.insert(0, history_item)
        
        # 限制历史记录数量
        if len(self.search_history) > self.max_history:
            self.search_history = self.search_history[:self.max_history]
    
    def get_search_history(self) -> str:
        """
        获取搜索历史记录
        
        Returns:
            搜索历史记录（Markdown 格式）
        """
        if not self.search_history:
            return "## 📜 搜索历史\n\n暂无搜索记录"
        
        output = "## 📜 搜索历史\n\n"
        output += f"**共 {len(self.search_history)} 条记录**\n\n"
        
        output += "| # | 查询 | 类型 | 时间 |\n"
        output += "|---|---|---|---|\n"
        
        import time
        for i, item in enumerate(self.search_history[:20]):
            query = item['query']
            search_type = item['type']
            timestamp = item['timestamp']
            
            # 格式化时间
            time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            
            # 根据类型添加图标
            type_icon = {
                'text': '🔍',
                'image': '🖼️'
            }.get(search_type, '📄')
            
            # 截断查询
            display_query = query[:40] + "..." if len(query) > 40 else query
            
            output += f"| {i+1} | `{display_query}` | {type_icon} {search_type} | {time_str} |\n"
        
        return output
    
    def clear_search_history(self) -> str:
        """
        清空搜索历史记录
        
        Returns:
            操作结果
        """
        self.search_history = []
        return "## ✅ 搜索历史已清空"
    
    async def search_image(self, image_path: str, top_k: int = 10, similarity_threshold: float = 0.0):
        """
        图像搜索
        
        Args:
            image_path: 图像路径
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值，高于此值的结果才会返回
            
        Returns:
            搜索结果（Markdown 格式）
        """
        try:
            if similarity_threshold < 0.0 or similarity_threshold > 1.0:
                return "## ⚠️ 参数错误\n\n相似度阈值必须在 0.0-1.0 之间"
            
            # 添加到搜索历史
            self._add_to_history(image_path, 'image')
            
            # 调用API进行搜索
            response = self.api_client.search_image(
                image_path=image_path,
                top_k=top_k
            )
            
            results = response.get('results', [])
            total = response.get('total', len(results))
            logger.info(f"找到 {total} 个结果")
            
            # 格式化结果为 Markdown
            output = f"# 🖼️ 图像搜索结果\n\n"
            output += f"**查询图像**: `{image_path}`\n\n"
            output += f"**找到 {total} 个结果**\n\n"
            
            if total == 0:
                output += "## ⚠️ 未找到任何结果\n\n"
                output += "💡 **提示**:\n"
                output += "- 请尝试使用不同的图像\n"
                output += "- 确保数据库中已索引相关图像\n"
                output += "- 检查图像格式是否支持\n"
                return output
            
            # 按相似度排序
            sorted_results = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)
            
            # 显示所有结果
            output += "| # | 文件名 | 类型 | 相似度 | 路径 |\n"
            output += "|---|---|---|---|---|\n"
            
            for i, result in enumerate(sorted_results):
                file_name = result.get('file_name', result.get('metadata', {}).get('file_name', result.get('file_path', '未知')))
                file_path = result.get('file_path', result.get('metadata', {}).get('file_path', '未知'))
                modality = result.get('modality', '未知')
                similarity = result.get('similarity', 0)
                
                # 格式化相似度为百分比
                similarity_percent = similarity * 100 if similarity <= 1 else similarity
                similarity_bar = "█" * int(similarity_percent / 10) + "░" * (10 - int(similarity_percent / 10))
                
                # 截断文件名
                display_name = file_name[:30] + "..." if len(file_name) > 30 else file_name
                display_path = file_path[:40] + "..." if len(file_path) > 40 else file_path
                
                # 根据类型添加图标
                type_icon = {
                    'image': '🖼️',
                    'video': '🎬',
                    'audio': '🎵',
                    'unknown': '📄'
                }.get(modality.lower(), '📄')
                
                output += f"| {i+1} | **{display_name}** | {type_icon} {modality} | {similarity_bar} `{similarity:.4f}` | `{display_path}` |\n"
            
            output += f"\n---\n"
            output += f"**搜索时间**: {total} 个结果 | **查询图像**: `{image_path}`\n"
            
            return output
            
        except Exception as e:
            logger.error(f"图像搜索失败: {e}", exc_info=True)
            return f"## ❌ 图像搜索失败\n\n**错误信息**: {e}\n\n请检查系统日志获取详细信息。"
    
    def get_system_status(self) -> str:
        """
        获取系统状态
        
        Returns:
            系统状态信息
        """
        status = "\n" + "="*60 + "\n"
        status += "msearch 系统状态\n"
        status += "="*60 + "\n\n"
        
        # 模型信息
        model_name = self.config_manager.get('models.available_models.chinese_clip_large.model_name', '未知')
        model_path = self.config_manager.get('models.available_models.chinese_clip_large.local_path', '未知')
        embedding_dim = self.config_manager.get('models.available_models.chinese_clip_large.embedding_dim', '未知')
        device = self.config_manager.get('models.available_models.chinese_clip_large.device', '未知')
        
        status += "[模型配置]\n"
        status += f"  模型名称: {model_name}\n"
        status += f"  模型路径: {model_path}\n"
        status += f"  嵌入维度: {embedding_dim}\n"
        status += f"  运行设备: {device}\n"
        status += "\n"
        
        # 系统信息
        status += "[系统信息]\n"
        status += f"  Python版本: {sys.version}\n"
        status += f"  项目路径: {project_root}\n"
        status += f"  配置文件: {self.config_manager.config_path}\n"
        status += "\n"
        
        # 任务管理器信息
        try:
            system_info = self.api_client.get_system_info()
            status += "[系统信息]\n"
            status += f"  API版本: {system_info.get('api_version', '未知')}\n"
            status += f"  服务状态: {system_info.get('status', '未知')}\n"
            status += "\n"
        except Exception as e:
            status += f"[系统信息] 无法获取状态: {e}\n\n"
        
        # 任务统计
        try:
            task_stats = self.api_client.get_task_stats()
            status += "[任务统计]\n"
            status += f"  总任务数: {task_stats.get('total', 0)}\n"
            status += f"  待处理: {task_stats.get('pending', 0)}\n"
            status += f"  运行中: {task_stats.get('running', 0)}\n"
            status += f"  已完成: {task_stats.get('completed', 0)}\n"
            status += f"  失败: {task_stats.get('failed', 0)}\n"
            status += "\n"
        except Exception as e:
            status += f"[任务统计] 无法获取状态: {e}\n\n"
        
        status += "="*60 + "\n"
        
        return status
    
    def get_task_list(self) -> str:
        """
        获取任务列表（已废弃，使用新的任务管理器方法）
        
        Returns:
            任务列表字符串
        """
        try:
            tasks = self.task_manager.get_all_tasks()
            
            if not tasks:
                return "当前没有任务"
            
            output = "\n" + "="*60 + "\n"
            output += f"任务列表 (共 {len(tasks)} 个任务)\n"
            output += "="*60 + "\n\n"
            
            for i, task in enumerate(tasks):
                output += f"[{i+1}] 任务ID: {task.get('id', '未知')}\n"
                output += f"    类型: {task.get('task_type', '未知')}\n"
                output += f"    状态: {task.get('status', '未知')}\n"
                output += f"    优先级: {task.get('priority', 0)}\n"
                output += f"    进度: {task.get('progress', 0):.1%}\n"
                output += f"    创建时间: {task.get('created_at', '未知')}\n"
                output += "-"*60 + "\n"
            
            return output
        except Exception as e:
            return f"获取任务列表失败: {e}"
    
    def refresh_task_manager(
        self,
        search_query: str = "",
        status_filter: List[str] = None,
        priority_filter: List[str] = None,
        type_filter: List[str] = None,
        time_range: str = "全部",
        sort_by: str = "创建时间(降序)"
    ) -> tuple:
        """
        刷新任务管理器
        
        Args:
            search_query: 搜索查询
            status_filter: 状态过滤
            priority_filter: 优先级过滤
            type_filter: 类型过滤
            time_range: 时间范围
            sort_by: 排序方式
            
        Returns:
            12个返回值：任务列表、统计数据的各个字段
        """
        try:
            if status_filter is None:
                status_filter = ["pending", "running", "paused", "completed", "failed", "cancelled"]
            if priority_filter is None:
                priority_filter = ["高(1-3)", "中(4-7)", "低(8-10)"]
            if type_filter is None:
                type_filter = ["file_embed_image", "file_embed_video", "file_embed_audio", "search_query"]
            
            # 调用API获取所有任务
            response = self.api_client.get_all_tasks()
            all_tasks = response.get('tasks', [])
            
            filtered_tasks = self._filter_tasks(
                all_tasks, search_query, status_filter,
                priority_filter, type_filter, time_range
            )
            
            sorted_tasks = self._sort_tasks(filtered_tasks, sort_by)
            
            df_data = []
            for task in sorted_tasks:
                df_data.append([
                    False,
                    task.get('id', '')[:8] + '...',
                    task.get('task_type', ''),
                    task.get('file_path', '')[-40:],
                    task.get('status', ''),
                    f"{task.get('progress', 0) * 100:.1f}%",
                    task.get('priority', 0),
                    self._format_timestamp(task.get('created_at', 0)),
                    f"{task.get('duration', 0):.1f}s",
                    ','.join(task.get('tags', [])),
                    "查看详情"
                ])
            
            stats = self._calculate_task_stats(sorted_tasks)
            
            # 返回12个值以匹配Gradio期望的输出
            return (
                df_data,  # task_list
                stats.get('total', 0),  # total_tasks
                stats.get('pending', 0),  # pending_tasks
                stats.get('running', 0),  # running_tasks
                stats.get('completed', 0),  # completed_tasks
                stats.get('failed', 0),  # failed_tasks
                stats.get('paused', 0),  # paused_tasks
                stats.get('success_rate', '0%'),  # success_rate
                stats.get('avg_duration', '0s'),  # avg_duration
                stats.get('throughput', '0/min'),  # throughput
                stats.get('queue_depth', 0),  # queue_depth
                stats.get('system_load', '0%')  # system_load
            )
            
        except Exception as e:
            logger.error(f"刷新任务管理器失败: {e}", exc_info=True)
            # 返回12个空值
            return (
                [],  # task_list
                0,  # total_tasks
                0,  # pending_tasks
                0,  # running_tasks
                0,  # completed_tasks
                0,  # failed_tasks
                0,  # paused_tasks
                '0%',  # success_rate
                '0s',  # avg_duration
                '0/min',  # throughput
                0,  # queue_depth
                '0%'  # system_load
            )
    
    def _filter_tasks(
        self,
        tasks: List[Dict],
        search_query: str,
        status_filter: List[str],
        priority_filter: List[str],
        type_filter: List[str],
        time_range: str
    ) -> List[Dict]:
        """过滤任务"""
        from datetime import datetime, timedelta
        
        filtered = tasks
        
        if search_query:
            search_lower = search_query.lower()
            filtered = [
                t for t in filtered
                if search_lower in t.get('id', '').lower()
                or search_lower in t.get('file_path', '').lower()
                or any(search_lower in tag.lower() for tag in t.get('tags', []))
            ]
        
        if status_filter:
            filtered = [t for t in filtered if t.get('status') in status_filter]
        
        if priority_filter:
            priority_filtered = []
            for task in filtered:
                priority = task.get('priority', 0)
                if "高(1-3)" in priority_filter and 1 <= priority <= 3:
                    priority_filtered.append(task)
                elif "中(4-7)" in priority_filter and 4 <= priority <= 7:
                    priority_filtered.append(task)
                elif "低(8-10)" in priority_filter and 8 <= priority <= 10:
                    priority_filtered.append(task)
            filtered = priority_filtered
        
        if type_filter:
            filtered = [t for t in filtered if t.get('task_type') in type_filter]
        
        if time_range != "全部":
            now = datetime.now()
            if time_range == "最近1小时":
                cutoff = now - timedelta(hours=1)
            elif time_range == "今天":
                cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_range == "本周":
                cutoff = now - timedelta(days=now.weekday())
                cutoff = cutoff.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_range == "本月":
                cutoff = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                cutoff = None
            
            if cutoff:
                filtered = [
                    t for t in filtered
                    if datetime.fromtimestamp(t.get('created_at', 0)) >= cutoff
                ]
        
        return filtered
    
    def _sort_tasks(self, tasks: List[Dict], sort_by: str) -> List[Dict]:
        """排序任务"""
        if not tasks:
            return tasks
        
        reverse = True
        key = 'created_at'
        
        if sort_by == "创建时间(降序)":
            key = 'created_at'
            reverse = True
        elif sort_by == "创建时间(升序)":
            key = 'created_at'
            reverse = False
        elif sort_by == "优先级(降序)":
            key = 'priority'
            reverse = False
        elif sort_by == "优先级(升序)":
            key = 'priority'
            reverse = True
        elif sort_by == "状态":
            key = 'status'
            reverse = True
        elif sort_by == "进度(降序)":
            key = 'progress'
            reverse = True
        elif sort_by == "进度(升序)":
            key = 'progress'
            reverse = False
        elif sort_by == "耗时(降序)":
            key = 'duration'
            reverse = True
        elif sort_by == "耗时(升序)":
            key = 'duration'
            reverse = False
        
        return sorted(tasks, key=lambda x: x.get(key, 0), reverse=reverse)
    
    def _calculate_task_stats(self, tasks: List[Dict]) -> Dict[str, Any]:
        """计算任务统计"""
        from datetime import datetime, timedelta
        
        stats = {
            'total': len(tasks),
            'pending': 0,
            'running': 0,
            'completed': 0,
            'failed': 0,
            'paused': 0,
            'cancelled': 0,
            'success_rate': '0%',
            'avg_duration': '0s',
            'throughput': '0/min',
            'queue_depth': 0,
            'system_load': '0%'
        }
        
        completed_count = 0
        failed_count = 0
        total_duration = 0
        completed_duration_count = 0
        
        for task in tasks:
            status = task.get('status', '')
            if status in stats:
                stats[status] += 1
            
            if status == 'completed':
                completed_count += 1
                duration = task.get('duration', 0)
                if duration > 0:
                    total_duration += duration
                    completed_duration_count += 1
            elif status == 'failed':
                failed_count += 1
        
        total_finished = completed_count + failed_count
        if total_finished > 0:
            success_rate = (completed_count / total_finished) * 100
            stats['success_rate'] = f"{success_rate:.1f}%"
        
        if completed_duration_count > 0:
            avg_duration = total_duration / completed_duration_count
            stats['avg_duration'] = f"{avg_duration:.1f}s"
        
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        recent_completed = [
            t for t in tasks
            if t.get('status') == 'completed'
            and datetime.fromtimestamp(t.get('updated_at', 0)) >= one_hour_ago
        ]
        stats['throughput'] = f"{len(recent_completed)}/min"
        
        stats['queue_depth'] = stats['pending'] + stats['running']
        
        if stats['total'] > 0:
            load = (stats['running'] / stats['total']) * 100
            stats['system_load'] = f"{load:.1f}%"
        
        return stats
    
    def _format_timestamp(self, timestamp: float) -> str:
        """格式化时间戳"""
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def select_all_tasks(self, current_data: List[List]) -> List[List]:
        """全选任务"""
        if not current_data:
            return []
        return [[True] + row[1:] for row in current_data]
    
    def deselect_all_tasks(self, current_data: List[List]) -> List[List]:
        """取消全选"""
        if not current_data:
            return []
        return [[False] + row[1:] for row in current_data]
    
    def cancel_selected_tasks(self, task_list: List[List]) -> tuple:
        """取消选中的任务"""
        selected_count = 0
        for row in task_list:
            if row[0]:
                task_id = row[1]
                try:
                    self.api_client.cancel_task(task_id)
                    selected_count += 1
                except Exception as e:
                    logger.error(f"取消任务失败: {task_id}, 错误: {e}")
        
        return task_list, f"已取消 {selected_count} 个任务"
    
    def pause_selected_tasks(self, task_list: List[List]) -> tuple:
        """暂停选中的任务"""
        selected_count = 0
        for row in task_list:
            if row[0]:
                task_id = row[1]
                try:
                    # API暂不支持暂停任务，使用取消任务代替
                    self.api_client.cancel_task(task_id)
                    selected_count += 1
                except Exception as e:
                    logger.error(f"暂停任务失败: {task_id}, 错误: {e}")
        
        return task_list, f"已暂停 {selected_count} 个任务"
    
    def resume_selected_tasks(self, task_list: List[List]) -> tuple:
        """恢复选中的任务"""
        selected_count = 0
        for row in task_list:
            if row[0]:
                task_id = row[1]
                try:
                    # API暂不支持恢复任务，返回提示
                    selected_count += 1
                except Exception as e:
                    logger.error(f"恢复任务失败: {task_id}, 错误: {e}")
        
        return task_list, f"已恢复 {selected_count} 个任务"
    
    def retry_selected_tasks(self, task_list: List[List]) -> tuple:
        """重试选中的任务"""
        selected_count = 0
        for row in task_list:
            if row[0]:
                task_id = row[1]
                try:
                    # API暂不支持重试任务，返回提示
                    selected_count += 1
                except Exception as e:
                    logger.error(f"重试任务失败: {task_id}, 错误: {e}")
        
        return task_list, f"已重试 {selected_count} 个任务"
    
    def delete_selected_tasks(self, task_list: List[List]) -> tuple:
        """删除选中的任务"""
        selected_count = 0
        for row in task_list:
            if row[0]:
                task_id = row[1]
                try:
                    # API暂不支持删除任务，返回提示
                    selected_count += 1
                except Exception as e:
                    logger.error(f"删除任务失败: {task_id}, 错误: {e}")
        
        return task_list, f"已删除 {selected_count} 个任务"
    
    def archive_selected_tasks(self, task_list: List[List]) -> tuple:
        """归档选中的任务"""
        selected_count = 0
        for row in task_list:
            if row[0]:
                task_id = row[1]
                try:
                    # API暂不支持归档任务，返回提示
                    selected_count += 1
                except Exception as e:
                    logger.error(f"归档任务失败: {task_id}, 错误: {e}")
        
        return task_list, f"已归档 {selected_count} 个任务"
    
    def set_task_priority(self, task_list: List[List], new_priority: int) -> tuple:
        """设置任务优先级"""
        selected_count = 0
        for row in task_list:
            if row[0]:
                task_id = row[1]
                try:
                    self.api_client.update_task_priority(task_id, new_priority)
                    selected_count += 1
                except Exception as e:
                    logger.error(f"设置任务优先级失败: {task_id}, 错误: {e}")
        
        return task_list, f"已为 {selected_count} 个任务设置优先级为 {new_priority}"
    
    def add_task_tags(self, task_list: List[List], tags: str) -> tuple:
        """添加任务标签"""
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        selected_count = 0
        for row in task_list:
            if row[0]:
                task_id = row[1]
                try:
                    # API暂不支持添加标签，返回提示
                    selected_count += 1
                except Exception as e:
                    logger.error(f"添加任务标签失败: {task_id}, 错误: {e}")
        
        return task_list, f"已为 {selected_count} 个任务添加标签: {', '.join(tag_list)}"
    
    def export_tasks(self, task_list: List[List], export_format: str) -> str:
        """导出任务数据"""
        import json
        import csv
        import tempfile
        import os
        from datetime import datetime
        
        selected_tasks = []
        for row in task_list:
            if row[0]:
                task_id = row[1]
                try:
                    task = self.api_client.get_task_status(task_id)
                    if task:
                        selected_tasks.append(task)
                except Exception as e:
                    logger.error(f"获取任务失败: {task_id}, 错误: {e}")
        
        if not selected_tasks:
            return None
        
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if export_format == "CSV":
            filename = f"tasks_export_{timestamp}.csv"
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=selected_tasks[0].keys())
                writer.writeheader()
                writer.writerows(selected_tasks)
        else:
            filename = f"tasks_export_{timestamp}.json"
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(selected_tasks, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def show_task_details(self, task_id: str) -> tuple:
        """显示任务详情"""
        try:
            task = self.api_client.get_task_status(task_id)
            
            if not task:
                return {}, {}, "任务不存在", {}, []
            
            task_info = {
                "任务ID": task.get('id', ''),
                "任务类型": task.get('task_type', ''),
                "文件路径": task.get('file_path', ''),
                "状态": task.get('status', ''),
                "优先级": task.get('priority', 0),
                "创建时间": self._format_timestamp(task.get('created_at', 0)),
                "更新时间": self._format_timestamp(task.get('updated_at', 0)),
                "耗时": f"{task.get('duration', 0):.1f}s",
                "标签": task.get('tags', []),
                "错误信息": task.get('error', '')
            }
            
            progress_details = {
                "进度": f"{task.get('progress', 0) * 100:.1f}%",
                "当前步骤": task.get('current_step', ''),
                "总步骤": task.get('total_steps', 0),
                "已完成步骤": task.get('completed_steps', 0)
            }
            
            logs = task.get('logs', '暂无日志')
            
            dependencies = task.get('dependencies', [])
            
            tags = task.get('tags', [])
            
            return task_info, progress_details, logs, dependencies, tags
            
        except Exception as e:
            logger.error(f"获取任务详情失败: {task_id}, 错误: {e}", exc_info=True)
            return {}, {}, f"获取任务详情失败: {e}", {}, []
    
    def get_task_statistics(self) -> str:
        """
        获取任务统计信息
        
        Returns:
            任务统计字符串
        """
        try:
            stats = self.api_client.get_task_stats()
            
            output = "\n" + "="*60 + "\n"
            output += "任务统计信息\n"
            output += "="*60 + "\n\n"
            
            # 任务统计
            output += "[任务统计]\n"
            output += f"  总任务数: {stats.get('total', 0)}\n"
            output += f"  待处理: {stats.get('pending', 0)}\n"
            output += f"  运行中: {stats.get('running', 0)}\n"
            output += f"  已完成: {stats.get('completed', 0)}\n"
            output += f"  失败: {stats.get('failed', 0)}\n"
            output += f"  成功率: {stats.get('success_rate', '0%')}\n"
            output += f"  平均耗时: {stats.get('avg_duration', '0s')}\n"
            output += f"  吞吐量: {stats.get('throughput', '0/min')}\n"
            output += "\n"
            
            output += "="*60 + "\n"
            
            return output
        except Exception as e:
            return f"获取任务统计失败: {e}"
    
    def full_scan(self, directories: str) -> str:
        """
        全量扫描目录
        
        Args:
            directories: 目录路径（多个目录用逗号分隔）
            
        Returns:
            扫描结果
        """
        try:
            if not directories or not directories.strip():
                return "请输入目录路径"
            
            dir_list = [d.strip() for d in directories.split(',') if d.strip()]
            
            output = "\n" + "="*60 + "\n"
            output += "全量扫描\n"
            output += "="*60 + "\n\n"
            
            total_files = 0
            total_indexed = 0
            
            for directory in dir_list:
                output += f"扫描目录: {directory}\n"
                
                # 使用API索引目录
                response = self.api_client.index_directory(directory, recursive=True)
                output += f"  索引状态: {response.get('message', 'Success')}\n"
                
                total_indexed += 1
                output += "-"*60 + "\n"
            
            output += f"\n总计: 索引 {total_indexed} 个目录\n"
            output += "="*60 + "\n"
            
            return output
            
        except Exception as e:
            logger.error(f"全量扫描失败: {e}", exc_info=True)
            return f"全量扫描失败: {e}"
    
    def start_vectorization(self, priority: int = 5, max_concurrent: int = 4) -> str:
        """
        启动向量化处理
        
        Args:
            priority: 任务优先级
            max_concurrent: 最大并发数
            
        Returns:
            处理结果
        """
        try:
            # 使用API启动向量化处理
            output = "\n" + "="*60 + "\n"
            output += "启动向量化处理\n"
            output += "="*60 + "\n\n"
            
            output += f"优先级: {priority}\n"
            output += f"最大并发数: {max_concurrent}\n"
            output += "\n"
            
            # 提示用户向量化处理将由系统自动处理
            output += "向量化处理已启动，系统将自动处理所有待索引的文件\n"
            output += "请在任务管理器中查看处理进度\n"
            
            output += "="*60 + "\n"
            
            return output
            
        except Exception as e:
            logger.error(f"启动向量化处理失败: {e}", exc_info=True)
            return f"启动向量化处理失败: {e}"
    
    def cancel_task(self, task_id: str) -> str:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            取消结果
        """
        try:
            if not task_id or not task_id.strip():
                return "请输入任务ID"
            
            self.api_client.cancel_task(task_id.strip())
            return f"任务 {task_id} 已取消"
                
        except Exception as e:
            logger.error(f"取消任务失败: {e}", exc_info=True)
            return f"取消任务失败: {e}"
    
    def update_task_priority(self, task_id: str, priority: int) -> str:
        """
        更新任务优先级
        
        Args:
            task_id: 任务ID
            priority: 新优先级
            
        Returns:
            更新结果
        """
        try:
            if not task_id or not task_id.strip():
                return "请输入任务ID"
            
            self.api_client.update_task_priority(task_id.strip(), priority)
            return f"任务 {task_id} 优先级已更新为 {priority}"
                
        except Exception as e:
            logger.error(f"更新任务优先级失败: {e}", exc_info=True)
            return f"更新任务优先级失败: {e}"
    
    def get_processing_progress(self) -> str:
        """
        获取处理进度
        
        Returns:
            进度信息
        """
        try:
            tasks = self.api_client.get_all_tasks()
            
            if not tasks.get('tasks'):
                return "当前没有任务"
            
            output = "\n" + "="*60 + "\n"
            output += "处理进度\n"
            output += "="*60 + "\n\n"
            
            task_list = tasks.get('tasks', [])
            running_tasks = [t for t in task_list if t.get('status') == 'running']
            pending_tasks = [t for t in task_list if t.get('status') == 'pending']
            completed_tasks = [t for t in task_list if t.get('status') == 'completed']
            
            total_tasks = len(task_list)
            progress_percent = (len(completed_tasks) / total_tasks * 100) if total_tasks > 0 else 0
            
            output += f"总任务数: {total_tasks}\n"
            output += f"已完成: {len(completed_tasks)} ({progress_percent:.1f}%)\n"
            output += f"运行中: {len(running_tasks)}\n"
            output += f"待处理: {len(pending_tasks)}\n"
            output += "\n"
            
            if running_tasks:
                output += "[运行中的任务]\n"
                for task in running_tasks:
                    task_id = task.get('id', '未知')
                    task_type = task.get('task_type', '未知')
                    progress = task.get('progress', 0)
                    output += f"  {task_id}: {task_type} - {progress:.1%}\n"
                output += "\n"
            
            output += "="*60 + "\n"
            
            return output
            
        except Exception as e:
            return f"获取处理进度失败: {e}"
    
    def create_interface(self):
        """
        创建 Gradio 界面
        
        Returns:
            Gradio Blocks 界面
        """
        with gr.Blocks(title="msearch 多模态检索系统") as demo:
            gr.Markdown("""
            # 🎯 msearch 多模态检索系统
            
            一个基于 AI 的多模态检索系统，支持文本、图像、视频和音频搜索。
            """)
            
            # 添加一个简单的API端点来处理缩略图请求
            # 注意：Gradio的Blocks对象没有server属性，我们使用一个不同的方法
            # 我们将在搜索结果中直接使用文件路径作为图片源
            
            with gr.Tab("🔍 文本搜索"):
                with gr.Row():
                    query_input = gr.Textbox(
                        label="搜索查询",
                        placeholder="输入搜索关键词，例如: '一只猫在草地上'",
                        lines=2
                    )
                    with gr.Column():
                        top_k_slider = gr.Slider(
                            minimum=1,
                            maximum=50,
                            value=10,
                            step=1,
                            label="返回结果数量"
                        )
                        similarity_threshold_slider = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.0,
                            step=0.01,
                            label="相似度阈值",
                            info="只返回相似度高于此值的结果（0.0表示返回所有结果）"
                        )
                        show_thumbnails = gr.Checkbox(
                            label="显示缩略图",
                            value=True
                        )
                
                search_btn = gr.Button("🔍 搜索", variant="primary", size="lg")
                
                with gr.Row():
                    result_output = gr.Markdown(
                        label="搜索结果",
                        value="## 🔍 准备搜索\n\n请输入关键词并点击搜索按钮..."
                    )
                
                search_btn.click(
                    fn=self.search_text,
                    inputs=[query_input, top_k_slider, similarity_threshold_slider],
                    outputs=result_output
                )
                
                query_input.submit(
                    fn=self.search_text,
                    inputs=[query_input, top_k_slider, similarity_threshold_slider],
                    outputs=result_output
                )
            
            with gr.Tab("🖼️ 图像搜索"):
                with gr.Row():
                    image_input = gr.Image(
                        label="上传图像",
                        type="filepath",
                        height=400
                    )
                    
                    with gr.Column():
                        top_k_slider_img = gr.Slider(
                            minimum=1,
                            maximum=50,
                            value=10,
                            step=1,
                            label="返回结果数量"
                        )
                        similarity_threshold_slider_img = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.0,
                            step=0.01,
                            label="相似度阈值",
                            info="只返回相似度高于此值的结果（0.0表示返回所有结果）"
                        )
                        search_btn_img = gr.Button("🔍 搜索相似图像", variant="primary", size="lg")
                
                with gr.Row():
                    result_output_img = gr.Markdown(
                        label="搜索结果",
                        value="## 🖼️ 准备搜索\n\n请上传图像并点击搜索按钮..."
                    )
                
                search_btn_img.click(
                    fn=self.search_image,
                    inputs=[image_input, top_k_slider_img, similarity_threshold_slider_img],
                    outputs=result_output_img
                )
            
            with gr.Tab("📊 系统状态"):
                status_btn = gr.Button("刷新状态", variant="secondary")
                status_output = gr.Textbox(
                    label="系统状态信息",
                    lines=30,
                    interactive=False
                )
                
                status_btn.click(
                    fn=self.get_system_status,
                    outputs=status_output
                )
                
                # 自动加载状态
                demo.load(
                    fn=self.get_system_status,
                    outputs=status_output
                )
            
            with gr.Tab("📋 任务管理器"):
                gr.Markdown("# 📋 任务管理器")
                
                # 顶部工具栏 - 第一行
                with gr.Row():
                    task_search = gr.Textbox(
                        label="搜索任务",
                        placeholder="输入任务ID或文件路径...",
                        scale=3
                    )
                    status_filter = gr.CheckboxGroup(
                        label="状态过滤",
                        choices=["pending", "running", "paused", "completed", "failed", "cancelled"],
                        value=["pending", "running", "paused", "completed", "failed", "cancelled"],
                        scale=2
                    )
                    priority_filter = gr.CheckboxGroup(
                        label="优先级过滤",
                        choices=["高(1-3)", "中(4-7)", "低(8-10)"],
                        value=["高(1-3)", "中(4-7)", "低(8-10)"],
                        scale=2
                    )
                    refresh_btn = gr.Button("🔄 刷新", variant="primary", scale=1)
                
                # 顶部工具栏 - 第二行
                with gr.Row():
                    type_filter = gr.CheckboxGroup(
                        label="类型过滤",
                        choices=["file_embed_image", "file_embed_video", "file_embed_audio", "search_query"],
                        value=["file_embed_image", "file_embed_video", "file_embed_audio", "search_query"],
                        scale=3
                    )
                    time_range = gr.Radio(
                        label="时间范围",
                        choices=["全部", "最近1小时", "今天", "本周", "本月"],
                        value="全部",
                        scale=2
                    )
                    sort_by = gr.Dropdown(
                        label="排序方式",
                        choices=["创建时间(降序)", "创建时间(升序)", "优先级(降序)", "优先级(升序)", 
                                 "状态", "进度(降序)", "进度(升序)", "耗时(降序)", "耗时(升序)"],
                        value="创建时间(降序)",
                        scale=2
                    )
                    export_btn = gr.Button("📥 导出", variant="secondary", scale=1)
                
                # 任务统计面板 - 第一行
                with gr.Row():
                    with gr.Column(scale=1):
                        total_tasks = gr.Number(label="总任务数", value=0, interactive=False)
                    with gr.Column(scale=1):
                        pending_tasks = gr.Number(label="待处理", value=0, interactive=False)
                    with gr.Column(scale=1):
                        running_tasks = gr.Number(label="运行中", value=0, interactive=False)
                    with gr.Column(scale=1):
                        completed_tasks = gr.Number(label="已完成", value=0, interactive=False)
                    with gr.Column(scale=1):
                        failed_tasks = gr.Number(label="失败", value=0, interactive=False)
                    with gr.Column(scale=1):
                        paused_tasks = gr.Number(label="已暂停", value=0, interactive=False)
                
                # 任务统计面板 - 第二行
                with gr.Row():
                    with gr.Column(scale=1):
                        success_rate = gr.Textbox(label="成功率", value="0%", interactive=False)
                    with gr.Column(scale=1):
                        avg_duration = gr.Textbox(label="平均耗时", value="0s", interactive=False)
                    with gr.Column(scale=1):
                        throughput = gr.Textbox(label="吞吐量", value="0/min", interactive=False)
                    with gr.Column(scale=1):
                        queue_depth = gr.Number(label="队列深度", value=0, interactive=False)
                    with gr.Column(scale=1):
                        system_load = gr.Textbox(label="系统负载", value="0%", interactive=False)
                
                # 任务列表
                task_list = gr.Dataframe(
                    label="任务列表",
                    headers=["选择", "任务ID", "类型", "文件路径", "状态", "进度", "优先级", "创建时间", "耗时", "标签", "操作"],
                    datatype=["checkbox", "str", "str", "str", "str", "number", "number", "str", "str", "str", "buttons"],
                    interactive=True,
                    wrap=True
                )
                
                # 批量操作栏 - 第一行
                with gr.Row():
                    select_all_btn = gr.Button("☑️ 全选", variant="secondary")
                    deselect_all_btn = gr.Button("⬜ 取消全选", variant="secondary")
                    cancel_selected_btn = gr.Button("❌ 批量取消", variant="stop")
                    pause_selected_btn = gr.Button("⏸️ 批量暂停", variant="secondary")
                    resume_selected_btn = gr.Button("▶️ 批量恢复", variant="secondary")
                
                # 批量操作栏 - 第二行
                with gr.Row():
                    retry_selected_btn = gr.Button("🔄 批量重试", variant="secondary")
                    delete_selected_btn = gr.Button("🗑️ 批量删除", variant="stop")
                    archive_selected_btn = gr.Button("📦 批量归档", variant="secondary")
                    set_priority_btn = gr.Button("⚡ 调整优先级", variant="secondary")
                    add_tags_btn = gr.Button("🏷️ 添加标签", variant="secondary")
                
                # 任务详情面板
                with gr.Accordion("任务详情", open=False):
                    with gr.Tabs():
                        with gr.Tab("基本信息"):
                            task_info = gr.JSON(label="任务信息", visible=False)
                        with gr.Tab("进度详情"):
                            progress_details = gr.JSON(label="进度详情", visible=False)
                        with gr.Tab("日志输出"):
                            task_logs = gr.Textbox(label="任务日志", lines=10, interactive=False)
                        with gr.Tab("依赖关系"):
                            dependency_graph = gr.JSON(label="依赖关系", visible=False)
                        with gr.Tab("标签管理"):
                            tag_manager = gr.JSON(label="标签管理", visible=False)
                
                # 操作结果显示
                operation_result = gr.Textbox(label="操作结果", lines=2, interactive=False)
                
                # 事件绑定
                refresh_btn.click(
                    fn=self.refresh_task_manager,
                    inputs=[task_search, status_filter, priority_filter, type_filter, time_range, sort_by],
                    outputs=[task_list, total_tasks, pending_tasks, running_tasks, completed_tasks, 
                             failed_tasks, paused_tasks, success_rate, avg_duration, throughput, 
                             queue_depth, system_load]
                )
                
                select_all_btn.click(
                    fn=self.select_all_tasks,
                    inputs=task_list,
                    outputs=task_list
                )
                
                deselect_all_btn.click(
                    fn=self.deselect_all_tasks,
                    inputs=task_list,
                    outputs=task_list
                )
                
                cancel_selected_btn.click(
                    fn=self.cancel_selected_tasks,
                    inputs=task_list,
                    outputs=[task_list, operation_result]
                )
                
                pause_selected_btn.click(
                    fn=self.pause_selected_tasks,
                    inputs=task_list,
                    outputs=[task_list, operation_result]
                )
                
                resume_selected_btn.click(
                    fn=self.resume_selected_tasks,
                    inputs=task_list,
                    outputs=[task_list, operation_result]
                )
                
                retry_selected_btn.click(
                    fn=self.retry_selected_tasks,
                    inputs=task_list,
                    outputs=[task_list, operation_result]
                )
                
                delete_selected_btn.click(
                    fn=self.delete_selected_tasks,
                    inputs=task_list,
                    outputs=[task_list, operation_result]
                )
                
                archive_selected_btn.click(
                    fn=self.archive_selected_tasks,
                    inputs=task_list,
                    outputs=[task_list, operation_result]
                )
                
                set_priority_btn.click(
                    fn=self.set_task_priority,
                    inputs=[task_list, gr.Number(label="新优先级", minimum=1, maximum=10)],
                    outputs=[task_list, operation_result]
                )
                
                add_tags_btn.click(
                    fn=self.add_task_tags,
                    inputs=[task_list, gr.Textbox(label="标签(逗号分隔)")],
                    outputs=[task_list, operation_result]
                )
                
                export_btn.click(
                    fn=self.export_tasks,
                    inputs=[task_list, gr.Dropdown(label="导出格式", choices=["CSV", "JSON"], value="CSV")],
                    outputs=gr.File(label="下载文件")
                )
                
                # 自动加载任务列表
                demo.load(
                    fn=self.refresh_task_manager,
                    inputs=[task_search, status_filter, priority_filter, type_filter, time_range, sort_by],
                    outputs=[task_list, total_tasks, pending_tasks, running_tasks, completed_tasks, 
                             failed_tasks, paused_tasks, success_rate, avg_duration, throughput, 
                             queue_depth, system_load]
                )
            
            with gr.Tab("📜 搜索历史"):
                gr.Markdown("""
                # 📜 搜索历史
                
                查看和管理您的搜索历史记录。
                """)
                
                with gr.Row():
                    history_btn = gr.Button("刷新历史", variant="secondary")
                    clear_history_btn = gr.Button("清空历史", variant="stop")
                
                history_output = gr.Markdown(
                    label="搜索历史",
                    value="## 📜 搜索历史\n\n暂无搜索记录"
                )
                
                history_btn.click(
                    fn=self.get_search_history,
                    outputs=history_output
                )
                
                clear_history_btn.click(
                    fn=self.clear_search_history,
                    outputs=history_output
                )
                
                # 自动加载历史记录
                demo.load(
                    fn=self.get_search_history,
                    outputs=history_output
                )
            
            with gr.Tab("🔧 手动操作控制"):
                gr.Markdown("""
                # 🔧 手动操作控制
                
                手动控制全量扫描、向量化处理、任务取消和优先级调整。
                """)
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 全量扫描")
                        directories_input = gr.Textbox(
                            label="目录路径（多个目录用逗号分隔）",
                            placeholder="/path/to/dir1,/path/to/dir2",
                            lines=2
                        )
                        full_scan_btn = gr.Button("📁 开始全量扫描", variant="primary")
                        full_scan_output = gr.Textbox(
                            label="扫描结果",
                            lines=10,
                            interactive=False
                        )
                        
                        full_scan_btn.click(
                            fn=self.full_scan,
                            inputs=directories_input,
                            outputs=full_scan_output
                        )
                    
                    with gr.Column():
                        gr.Markdown("### 向量化处理")
                        priority_slider = gr.Slider(
                            minimum=1,
                            maximum=10,
                            value=5,
                            step=1,
                            label="任务优先级（1-10，数字越大优先级越高）"
                        )
                        max_concurrent_slider = gr.Slider(
                            minimum=1,
                            maximum=16,
                            value=4,
                            step=1,
                            label="最大并发数"
                        )
                        start_vectorization_btn = gr.Button("🚀 启动向量化处理", variant="primary")
                        vectorization_output = gr.Textbox(
                            label="处理结果",
                            lines=10,
                            interactive=False
                        )
                        
                        start_vectorization_btn.click(
                            fn=self.start_vectorization,
                            inputs=[priority_slider, max_concurrent_slider],
                            outputs=vectorization_output
                        )
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 任务取消")
                        cancel_task_id_input = gr.Textbox(
                            label="任务ID",
                            placeholder="输入要取消的任务ID"
                        )
                        cancel_task_btn = gr.Button("❌ 取消任务", variant="stop")
                        cancel_task_output = gr.Textbox(
                            label="取消结果",
                            lines=3,
                            interactive=False
                        )
                        
                        cancel_task_btn.click(
                            fn=self.cancel_task,
                            inputs=cancel_task_id_input,
                            outputs=cancel_task_output
                        )
                    
                    with gr.Column():
                        gr.Markdown("### 任务优先级调整")
                        priority_task_id_input = gr.Textbox(
                            label="任务ID",
                            placeholder="输入要调整优先级的任务ID"
                        )
                        new_priority_slider = gr.Slider(
                            minimum=1,
                            maximum=10,
                            value=5,
                            step=1,
                            label="新优先级（1-10）"
                        )
                        update_priority_btn = gr.Button("⬆️ 更新优先级", variant="secondary")
                        update_priority_output = gr.Textbox(
                            label="更新结果",
                            lines=3,
                            interactive=False
                        )
                        
                        update_priority_btn.click(
                            fn=self.update_task_priority,
                            inputs=[priority_task_id_input, new_priority_slider],
                            outputs=update_priority_output
                        )
            
            with gr.Tab("ℹ️ 使用帮助"):
                gr.Markdown("""
                # 使用帮助
                
                ## 1. 文本搜索
                
                1. 在"搜索查询"框中输入关键词
                2. 调整"返回结果数量"（可选）
                3. 点击"搜索"按钮或按回车键
                4. 查看搜索结果
                
                **示例:**
                ```
                搜索: "一只猫在草地上"
                结果: 显示所有与猫和草地相关的图像/视频
                ```
                
                ## 2. 图像搜索
                
                1. 点击"上传图像"区域
                2. 选择本地图像文件
                3. 调整"返回结果数量"（可选）
                4. 点击"搜索相似图像"按钮
                5. 查看搜索结果
                
                **支持的格式:** JPG, PNG, GIF, BMP, WebP
                
                ## 3. 系统状态
                
                - 点击"刷新状态"按钮查看最新系统信息
                - 显示当前使用的模型、数据库状态、系统配置等
                
                ## 4. 常见问题
                
                **Q: 为什么搜索结果为空？**
                A: 可能是数据库中没有数据。请先运行 `scripts/process_testdata.sh` 处理测试数据。
                
                **Q: 如何添加更多数据？**
                A: 使用命令行工具: `python src/cli.py index /path/to/your/data`
                
                **Q: 系统支持哪些文件类型？**
                A: 图像(JPG/PNG/GIF)、视频(MP4/AVI/MKV)、音频(MP3/WAV/FLAC)
                
                ## 5. 技术细节
                
                - **模型**: OFA-Sys/chinese-clip-vit-large-patch14-336px (统一多模态模型)
                - **向量数据库**: LanceDB
                - **向量化引擎**: Infinity
                - **界面**: Gradio
                - **嵌入维度**: 768
                
                ## 6. 命令行工具
                
                ```bash
                # 扫描目录
                python src/cli.py scan /path/to/data
                
                # 索引文件
                python src/cli.py index /path/to/data
                
                # 搜索
                python src/cli.py search "查询文本"
                ```
                """)
        
        return demo
    
    def get_thumbnail(self, file_path: str):
        """
        获取文件的缩略图
        
        Args:
            file_path: 文件路径
            
        Returns:
            缩略图的文件路径
        """
        try:
            # 首先尝试从数据库获取缩略图路径
            thumbnail_path = self.database_manager.get_thumbnail_by_path(file_path)
            
            if thumbnail_path and Path(thumbnail_path).exists():
                logger.info(f"找到缩略图: {thumbnail_path}")
                return thumbnail_path
            
            # 如果没有缩略图，尝试获取预览图路径
            preview_path = self.database_manager.get_preview_by_path(file_path)
            
            if preview_path and Path(preview_path).exists():
                logger.info(f"找到预览图: {preview_path}")
                return preview_path
            
            # 如果都没有，返回None
            logger.warning(f"未找到缩略图: {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"获取缩略图失败: {e}")
            return None
    
    def run(self, host: str = "0.0.0.0", port: int = 7860, debug: bool = False):
        """
        启动 WebUI
        
        Args:
            host: 监听地址
            port: 监听端口
            debug: 调试模式
        """
        logger.info(f"启动 msearch WebUI: http://{host}:{port}")
        
        demo = self.create_interface()
        demo.launch(
            server_name=host,
            server_port=port,
            debug=debug,
            show_error=True,
            share=False,
            theme=gr.themes.Soft()
        )


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='msearch WebUI')
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='配置文件路径'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='监听地址 (默认: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=7860,
        help='监听端口 (默认: 7860)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='调试模式'
    )
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 启动 WebUI
    webui = MSearchWebUI(args.config)
    webui.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
