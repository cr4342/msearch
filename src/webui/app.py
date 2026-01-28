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
from core.vector.vector_store import VectorStore
from core.embedding.embedding_engine import EmbeddingEngine
from core.database.database_manager import DatabaseManager
from core.task.central_task_manager import CentralTaskManager
from services.file.file_scanner import FileScanner
from services.file.file_indexer import FileIndexer

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
        
        # 初始化组件
        self._init_components()
        
        logger.info("MSearch WebUI 初始化完成")
    
    def _init_components(self):
        """初始化系统组件"""
        logger.info("初始化系统组件...")
        
        # 创建全局事件循环（在初始化时创建，避免后续冲突）
        global _global_event_loop
        if _global_event_loop is None or _global_event_loop.is_closed():
            _global_event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_global_event_loop)
            logger.info("✓ 全局事件循环创建完成")
        
        # 向量存储
        vector_store_config = {
            'data_dir': self.config_manager.get('database.lancedb.data_dir', 'data/database/lancedb'),
            'collection_name': self.config_manager.get('database.lancedb.collection_name', 'unified_vectors'),
            'index_type': self.config_manager.get('database.lancedb.index_type', 'ivf_pq'),
            'num_partitions': self.config_manager.get('database.lancedb.num_partitions', 128),
            'vector_dimension': self.config_manager.get('database.lancedb.vector_dimension', 512)
        }
        self.vector_store = VectorStore(vector_store_config)
        logger.info("✓ 向量存储初始化完成")
        
        # 向量化引擎
        self.embedding_engine = EmbeddingEngine(self.config)
        # 使用全局事件循环预加载模型
        _global_event_loop.run_until_complete(self.embedding_engine.preload_models())
        logger.info("✓ 向量化引擎初始化完成")
        
        # 数据库管理器
        db_path = self.config_manager.get('database.sqlite.path', 'data/database/sqlite/msearch.db')
        self.database_manager = DatabaseManager(db_path)
        logger.info("✓ 数据库管理器初始化完成")
        
        # 任务管理器
        device = self.config_manager.get('models.device', 'cpu')
        self.task_manager = CentralTaskManager(self.config, device)
        self.task_manager.initialize()
        logger.info("✓ 任务管理器初始化完成")
        
        # 文件扫描器
        self.file_scanner = FileScanner(self.config)
        logger.info("✓ 文件扫描器初始化完成")
        
        # 文件索引器
        self.file_indexer = FileIndexer(self.config, self.task_manager)
        logger.info("✓ 文件索引器初始化完成")
    
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
                
                # 向量化
                query_embedding = await self.embedding_engine.embed_text(query)
                logger.info(f"查询向量维度: {len(query_embedding)}")
                
                # 向量检索
                results = self.vector_store.search(
                    query_embedding, 
                    limit=top_k, 
                    similarity_threshold=similarity_threshold
                )
                logger.info(f"找到 {len(results)} 个结果")
                
                # 格式化结果为 Markdown
                output = f"# 🔍 文本搜索结果: '{query}'\n\n"
                output += f"**找到 {len(results)} 个结果**\n\n"
                
                if len(results) == 0:
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
                output += f"**搜索时间**: {len(results)} 个结果 | **查询**: `{query}`\n"
                
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
            
            # 向量化
            query_embedding = await self.embedding_engine.embed_image(image_path)
            logger.info(f"查询向量维度: {len(query_embedding)}")
            
            # 向量检索
            results = self.vector_store.search(
                query_embedding, 
                limit=top_k, 
                similarity_threshold=similarity_threshold
            )
            logger.info(f"找到 {len(results)} 个结果")
            
            # 格式化结果为 Markdown
            output = f"# 🖼️ 图像搜索结果\n\n"
            output += f"**查询图像**: `{image_path}`\n\n"
            output += f"**找到 {len(results)} 个结果**\n\n"
            
            if len(results) == 0:
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
                file_name = result.get('file_name', result.get('file_path', '未知'))
                file_path = result.get('file_path', '未知')
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
            output += f"**搜索时间**: {len(results)} 个结果 | **查询图像**: `{image_path}`\n"
            
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
        
        # 数据库信息
        try:
            # 获取向量存储统计
            vector_stats = self.vector_store.get_stats()
            status += "[向量数据库]\n"
            status += f"  数据目录: {vector_stats.get('data_dir', '未知')}\n"
            status += f"  集合名称: {vector_stats.get('collection_name', '未知')}\n"
            status += f"  向量数量: {vector_stats.get('vector_count', 0)}\n"
            status += f"  向量维度: {vector_stats.get('vector_dimension', '未知')}\n"
            status += "\n"
        except Exception as e:
            status += f"[向量数据库] 无法获取状态: {e}\n\n"
        
        # 系统信息
        status += "[系统信息]\n"
        status += f"  Python版本: {sys.version}\n"
        status += f"  项目路径: {project_root}\n"
        status += f"  配置文件: {self.config_manager.config_path}\n"
        status += "\n"
        
        # 任务管理器信息
        try:
            task_stats = self.task_manager.get_statistics()
            status += "[任务管理器]\n"
            status += f"  任务统计: {task_stats.get('task_stats', {})}\n"
            status += f"  并发数: {task_stats.get('concurrency', 0)}\n"
            status += f"  任务组统计: {task_stats.get('task_groups', {})}\n"
            status += "\n"
        except Exception as e:
            status += f"[任务管理器] 无法获取状态: {e}\n\n"
        
        status += "="*60 + "\n"
        
        return status
    
    def get_task_list(self) -> str:
        """
        获取任务列表
        
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
    
    def get_task_statistics(self) -> str:
        """
        获取任务统计信息
        
        Returns:
            任务统计字符串
        """
        try:
            stats = self.task_manager.get_statistics()
            
            output = "\n" + "="*60 + "\n"
            output += "任务统计信息\n"
            output += "="*60 + "\n\n"
            
            # 从CentralTaskManager获取统计信息
            output += "[任务队列]\n"
            output += f"  队列大小: {stats.get('queue_size', 0)}\n"
            output += f"  运行中任务: {stats.get('running_count', 0)}\n"
            output += "\n"
            
            # 资源状态
            resource_state = stats.get('resource_state', 'unknown')
            output += "[资源状态]\n"
            output += f"  状态: {resource_state}\n"
            output += "\n"
            
            # 统计信息
            task_stats = stats.get('task_stats', {})
            if task_stats:
                output += "[任务统计]\n"
                output += f"  总任务数: {task_stats.get('total', 0)}\n"
                output += f"  待处理: {task_stats.get('pending', 0)}\n"
                output += f"  运行中: {task_stats.get('running', 0)}\n"
                output += f"  已完成: {task_stats.get('completed', 0)}\n"
                output += f"  失败: {task_stats.get('failed', 0)}\n"
                output += f"  已取消: {task_stats.get('cancelled', 0)}\n"
                output += "\n"
            
            # 并发信息
            if 'concurrency' in stats:
                output += "[并发信息]\n"
                output += f"  当前并发数: {stats.get('concurrency', 0)}\n"
                output += "\n"
            
            # 任务组统计
            task_groups = stats.get('task_groups', {})
            if task_groups:
                output += "[任务组统计]\n"
                for group_name, group_stats in task_groups.items():
                    output += f"  {group_name}: {group_stats}\n"
                output += "\n"
            
            # 资源使用
            resource_usage = stats.get('resource_usage', {})
            if resource_usage:
                output += "[资源使用]\n"
                output += f"  CPU: {resource_usage.get('cpu_percent', 0):.1f}%\n"
                output += f"  内存: {resource_usage.get('memory_percent', 0):.1f}%\n"
                if 'gpu_memory_percent' in resource_usage:
                    output += f"  GPU内存: {resource_usage.get('gpu_memory_percent', 0):.1f}%\n"
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
                
                # 扫描文件
                file_paths = self.file_scanner.scan_directory(directory)
                output += f"  找到 {len(file_paths)} 个文件\n"
                
                # 索引文件
                indexed_count = 0
                for file_path in file_paths:
                    metadata = self.file_indexer.index_file(file_path, submit_task=False)
                    if metadata:
                        # 保存到数据库
                        try:
                            self.database_manager.insert_file_metadata({
                                'id': metadata.file_id,
                                'file_path': metadata.file_path,
                                'file_name': metadata.file_name,
                                'file_type': metadata.file_type.value,
                                'file_size': metadata.file_size,
                                'file_hash': metadata.file_hash,
                                'created_at': metadata.created_at,
                                'updated_at': metadata.updated_at,
                                'processing_status': 'pending'
                            })
                            indexed_count += 1
                        except Exception as e:
                            logger.error(f"保存文件元数据失败: {file_path}, 错误: {e}")
                
                output += f"  索引 {indexed_count} 个文件\n"
                total_files += len(file_paths)
                total_indexed += indexed_count
                output += "-"*60 + "\n"
            
            output += f"\n总计: 扫描 {total_files} 个文件，索引 {total_indexed} 个文件\n"
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
            # 获取所有待处理的文件
            pending_files = self.database_manager.get_files_by_status('pending', limit=1000)
            
            if not pending_files:
                return "没有待处理的文件"
            
            output = "\n" + "="*60 + "\n"
            output += "启动向量化处理\n"
            output += "="*60 + "\n\n"
            
            output += f"优先级: {priority}\n"
            output += f"最大并发数: {max_concurrent}\n"
            output += f"待处理文件数: {len(pending_files)}\n\n"
            
            # 更新并发配置
            self.task_manager.concurrency_manager.config.max_concurrent = max_concurrent
            
            # 为每个文件创建向量化任务
            task_count = 0
            for file_data in pending_files:
                file_id = file_data['id']
                file_path = file_data['file_path']
                file_type = file_data['file_type']
                
                # 根据文件类型选择任务类型
                task_type_map = {
                    'image': 'file_embed_image',
                    'video': 'file_embed_video',
                    'audio': 'file_embed_audio'
                }
                task_type = task_type_map.get(file_type, 'file_embed_unknown')
                
                # 创建任务
                task_data = {
                    'file_id': file_id,
                    'file_path': file_path,
                    'file_type': file_type,
                    'metadata': file_data
                }
                
                task_id = self.task_manager.create_task(
                    task_type=task_type,
                    task_data=task_data,
                    priority=priority,
                    file_id=file_id
                )
                
                task_count += 1
                output += f"创建任务: {task_id}, 文件: {file_path}\n"
            
            output += f"\n总计: 创建 {task_count} 个向量化任务\n"
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
            
            success = self.task_manager.cancel_task(task_id.strip())
            
            if success:
                return f"任务 {task_id} 已取消"
            else:
                return f"任务 {task_id} 取消失败"
                
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
            
            success = self.task_manager.update_task_priority(task_id.strip(), priority)
            
            if success:
                return f"任务 {task_id} 优先级已更新为 {priority}"
            else:
                return f"任务 {task_id} 优先级更新失败"
                
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
            tasks = self.task_manager.get_all_tasks()
            
            if not tasks:
                return "当前没有任务"
            
            output = "\n" + "="*60 + "\n"
            output += "处理进度\n"
            output += "="*60 + "\n\n"
            
            running_tasks = [t for t in tasks if t.get('status') == 'running']
            pending_tasks = [t for t in tasks if t.get('status') == 'pending']
            completed_tasks = [t for t in tasks if t.get('status') == 'completed']
            
            total_tasks = len(tasks)
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
        with gr.Blocks(title="msearch 多模态检索系统", theme=gr.themes.Soft()) as demo:
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
                gr.Markdown("""
                # 📋 任务管理器
                
                查看和管理系统中的任务，包括任务状态、进度和统计信息。
                """)
                
                with gr.Row():
                    task_list_btn = gr.Button("刷新任务列表", variant="secondary")
                    task_stats_btn = gr.Button("刷新任务统计", variant="secondary")
                    task_progress_btn = gr.Button("刷新处理进度", variant="secondary")
                
                task_output = gr.Textbox(
                    label="任务列表",
                    lines=15,
                    interactive=False
                )
                
                task_stats_output = gr.Textbox(
                    label="任务统计",
                    lines=10,
                    interactive=False
                )
                
                task_progress_output = gr.Textbox(
                    label="处理进度",
                    lines=8,
                    interactive=False
                )
                
                task_list_btn.click(
                    fn=self.get_task_list,
                    outputs=task_output
                )
                
                task_stats_btn.click(
                    fn=self.get_task_statistics,
                    outputs=task_stats_output
                )
                
                task_progress_btn.click(
                    fn=self.get_processing_progress,
                    outputs=task_progress_output
                )
                
                # 自动加载任务列表
                demo.load(
                    fn=self.get_task_list,
                    outputs=task_output
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
            share=False
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
