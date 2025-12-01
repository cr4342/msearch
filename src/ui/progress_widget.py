"""
进度组件
显示系统处理进度和状态
"""

import logging
import time
from typing import Dict, Any, List, Optional

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
        QLabel, QPushButton, QProgressBar, QTableWidget,
        QTableWidgetItem, QHeaderView, QGroupBox, QFrame,
        QScrollArea, QSplitter, QComboBox, QSpinBox
    )
    from PySide6.QtCore import Qt, QTimer, Signal, QThread, QObject
    from PySide6.QtGui import QFont, QColor, QPalette
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False


class StatusUpdateWorker(QObject):
    """状态更新工作线程"""
    
    # 信号定义
    status_updated = Signal(dict)
    error = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
    
    def run(self):
        """运行状态更新"""
        try:
            while self.running:
                # 模拟获取系统状态
                import random
                import psutil
                
                status = {
                    "timestamp": time.time(),
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent,
                    "total_files": random.randint(100, 1000),
                    "processed_files": random.randint(50, 800),
                    "pending_files": random.randint(0, 200),
                    "active_tasks": random.randint(0, 10),
                    "completed_tasks": random.randint(100, 500),
                    "failed_tasks": random.randint(0, 10)
                }
                
                self.status_updated.emit(status)
                
                # 每5秒更新一次
                for _ in range(50):
                    if not self.running:
                        break
                    time.sleep(0.1)
                
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        """停止工作线程"""
        self.running = False


class ProgressWidget(QWidget):
    """进度组件"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.status_worker = None
        self.status_thread = None
        self._init_ui()
        self._start_status_monitoring()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：系统状态
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 系统资源组
        self._create_system_resources_group(left_layout)
        
        # 处理统计组
        self._create_processing_stats_group(left_layout)
        
        left_layout.addStretch()
        
        # 右侧：任务列表
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 任务管理组
        self._create_task_management_group(right_layout)
        
        # 添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("刷新状态")
        self.refresh_button.clicked.connect(self._refresh_status)
        control_layout.addWidget(self.refresh_button)
        
        control_layout.addStretch()
        
        self.clear_completed_button = QPushButton("清理已完成任务")
        self.clear_completed_button.clicked.connect(self._clear_completed_tasks)
        control_layout.addWidget(self.clear_completed_button)
        
        self.pause_button = QPushButton("暂停处理")
        self.pause_button.setCheckable(True)
        self.pause_button.clicked.connect(self._toggle_processing)
        control_layout.addWidget(self.pause_button)
        
        layout.addLayout(control_layout)
    
    def _create_system_resources_group(self, layout):
        """创建系统资源组"""
        group = QGroupBox("系统资源")
        group_layout = QGridLayout(group)
        
        # CPU使用率
        group_layout.addWidget(QLabel("CPU使用率:"), 0, 0)
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        group_layout.addWidget(self.cpu_progress, 0, 1)
        self.cpu_label = QLabel("0%")
        group_layout.addWidget(self.cpu_label, 0, 2)
        
        # 内存使用率
        group_layout.addWidget(QLabel("内存使用率:"), 1, 0)
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        group_layout.addWidget(self.memory_progress, 1, 1)
        self.memory_label = QLabel("0%")
        group_layout.addWidget(self.memory_label, 1, 2)
        
        # 磁盘使用率
        group_layout.addWidget(QLabel("磁盘使用率:"), 2, 0)
        self.disk_progress = QProgressBar()
        self.disk_progress.setRange(0, 100)
        group_layout.addWidget(self.disk_progress, 2, 1)
        self.disk_label = QLabel("0%")
        group_layout.addWidget(self.disk_label, 2, 2)
        
        # 设置进度条样式
        progress_style = """
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                text-align: center;
                background: white;
            }
            QProgressBar::chunk {
                background: #0078d4;
                border-radius: 2px;
            }
        """
        
        self.cpu_progress.setStyleSheet(progress_style)
        self.memory_progress.setStyleSheet(progress_style)
        self.disk_progress.setStyleSheet(progress_style)
        
        layout.addWidget(group)
    
    def _create_processing_stats_group(self, layout):
        """创建处理统计组"""
        group = QGroupBox("处理统计")
        group_layout = QGridLayout(group)
        
        # 总文件数
        group_layout.addWidget(QLabel("总文件数:"), 0, 0)
        self.total_files_label = QLabel("0")
        self.total_files_label.setStyleSheet("font-weight: bold; color: #333;")
        group_layout.addWidget(self.total_files_label, 0, 1)
        
        # 已处理文件数
        group_layout.addWidget(QLabel("已处理:"), 1, 0)
        self.processed_files_label = QLabel("0")
        self.processed_files_label.setStyleSheet("font-weight: bold; color: #28a745;")
        group_layout.addWidget(self.processed_files_label, 1, 1)
        
        # 待处理文件数
        group_layout.addWidget(QLabel("待处理:"), 2, 0)
        self.pending_files_label = QLabel("0")
        self.pending_files_label.setStyleSheet("font-weight: bold; color: #ffc107;")
        group_layout.addWidget(self.pending_files_label, 2, 1)
        
        # 处理进度
        group_layout.addWidget(QLabel("处理进度:"), 3, 0)
        self.processing_progress = QProgressBar()
        self.processing_progress.setRange(0, 100)
        group_layout.addWidget(self.processing_progress, 3, 1)
        self.processing_progress_label = QLabel("0%")
        group_layout.addWidget(self.processing_progress_label, 3, 2)
        
        self.processing_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                text-align: center;
                background: white;
            }
            QProgressBar::chunk {
                background: #28a745;
                border-radius: 2px;
            }
        """)
        
        layout.addWidget(group)
    
    def _create_task_management_group(self, layout):
        """创建任务管理组"""
        group = QGroupBox("任务管理")
        group_layout = QVBoxLayout(group)
        
        # 任务筛选
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("筛选:"))
        
        self.task_filter_combo = QComboBox()
        self.task_filter_combo.addItems(["全部", "进行中", "已完成", "失败", "重试"])
        self.task_filter_combo.currentTextChanged.connect(self._filter_tasks)
        filter_layout.addWidget(self.task_filter_combo)
        
        filter_layout.addStretch()
        
        self.refresh_tasks_button = QPushButton("刷新任务")
        self.refresh_tasks_button.clicked.connect(self._refresh_tasks)
        filter_layout.addWidget(self.refresh_tasks_button)
        
        group_layout.addLayout(filter_layout)
        
        # 任务表格
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(6)
        self.tasks_table.setHorizontalHeaderLabels([
            "任务ID", "文件名", "类型", "状态", "进度", "更新时间"
        ])
        
        # 设置表格属性
        header = self.tasks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.tasks_table.setAlternatingRowColors(True)
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        group_layout.addWidget(self.tasks_table)
        
        # 任务统计
        stats_layout = QHBoxLayout()
        
        self.active_tasks_label = QLabel("活动任务: 0")
        self.active_tasks_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        stats_layout.addWidget(self.active_tasks_label)
        
        self.completed_tasks_label = QLabel("已完成: 0")
        self.completed_tasks_label.setStyleSheet("color: #28a745; font-weight: bold;")
        stats_layout.addWidget(self.completed_tasks_label)
        
        self.failed_tasks_label = QLabel("失败: 0")
        self.failed_tasks_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        stats_layout.addWidget(self.failed_tasks_label)
        
        stats_layout.addStretch()
        
        group_layout.addLayout(stats_layout)
        
        layout.addWidget(group)
        
        # 初始化任务数据
        self._init_task_data()
    
    def _init_task_data(self):
        """初始化任务数据"""
        # 模拟任务数据
        self.tasks_data = []
        
        task_types = ["图像处理", "视频处理", "音频处理", "向量化"]
        task_statuses = ["进行中", "已完成", "失败", "重试"]
        
        import random
        
        for i in range(20):
            task = {
                "id": f"task_{i+1:03d}",
                "file_name": f"sample_file_{i+1}.jpg",
                "type": random.choice(task_types),
                "status": random.choice(task_statuses),
                "progress": random.randint(0, 100),
                "updated_at": time.time() - random.randint(0, 3600)
            }
            self.tasks_data.append(task)
        
        self._update_tasks_table()
    
    def _start_status_monitoring(self):
        """启动状态监控"""
        self.status_worker = StatusUpdateWorker()
        self.status_thread = QThread()
        self.status_worker.moveToThread(self.status_thread)
        
        self.status_thread.started.connect(self.status_worker.run)
        self.status_worker.status_updated.connect(self._update_status)
        self.status_worker.error.connect(self._on_status_error)
        self.status_thread.finished.connect(self.status_thread.deleteLater)
        
        self.status_thread.start()
    
    def _update_status(self, status):
        """更新状态显示"""
        try:
            # 更新系统资源
            cpu_percent = status.get("cpu_percent", 0)
            self.cpu_progress.setValue(int(cpu_percent))
            self.cpu_label.setText(f"{cpu_percent:.1f}%")
            
            memory_percent = status.get("memory_percent", 0)
            self.memory_progress.setValue(int(memory_percent))
            self.memory_label.setText(f"{memory_percent:.1f}%")
            
            disk_percent = status.get("disk_percent", 0)
            self.disk_progress.setValue(int(disk_percent))
            self.disk_label.setText(f"{disk_percent:.1f}%")
            
            # 更新处理统计
            total_files = status.get("total_files", 0)
            processed_files = status.get("processed_files", 0)
            pending_files = status.get("pending_files", 0)
            
            self.total_files_label.setText(str(total_files))
            self.processed_files_label.setText(str(processed_files))
            self.pending_files_label.setText(str(pending_files))
            
            # 计算处理进度
            if total_files > 0:
                progress_percent = int((processed_files / total_files) * 100)
                self.processing_progress.setValue(progress_percent)
                self.processing_progress_label.setText(f"{progress_percent}%")
            
            # 更新任务统计
            active_tasks = status.get("active_tasks", 0)
            completed_tasks = status.get("completed_tasks", 0)
            failed_tasks = status.get("failed_tasks", 0)
            
            self.active_tasks_label.setText(f"活动任务: {active_tasks}")
            self.completed_tasks_label.setText(f"已完成: {completed_tasks}")
            self.failed_tasks_label.setText(f"失败: {failed_tasks}")
            
        except Exception as e:
            self.logger.error(f"更新状态失败: {e}")
    
    def _on_status_error(self, error):
        """状态更新错误处理"""
        self.logger.error(f"状态更新错误: {error}")
    
    def _filter_tasks(self, filter_text):
        """筛选任务"""
        filtered_tasks = []
        
        if filter_text == "全部":
            filtered_tasks = self.tasks_data
        else:
            for task in self.tasks_data:
                if task["status"] == filter_text:
                    filtered_tasks.append(task)
        
        self._update_tasks_table_with_data(filtered_tasks)
    
    def _update_tasks_table(self):
        """更新任务表格"""
        self._update_tasks_table_with_data(self.tasks_data)
    
    def _update_tasks_table_with_data(self, tasks_data):
        """使用指定数据更新任务表格"""
        self.tasks_table.setRowCount(len(tasks_data))
        
        for row, task in enumerate(tasks_data):
            # 任务ID
            self.tasks_table.setItem(row, 0, QTableWidgetItem(task["id"]))
            
            # 文件名
            self.tasks_table.setItem(row, 1, QTableWidgetItem(task["file_name"]))
            
            # 类型
            self.tasks_table.setItem(row, 2, QTableWidgetItem(task["type"]))
            
            # 状态
            status_item = QTableWidgetItem(task["status"])
            # 根据状态设置颜色
            if task["status"] == "已完成":
                status_item.setForeground(QColor("#28a745"))
            elif task["status"] == "失败":
                status_item.setForeground(QColor("#dc3545"))
            elif task["status"] == "进行中":
                status_item.setForeground(QColor("#0078d4"))
            self.tasks_table.setItem(row, 3, status_item)
            
            # 进度
            progress_item = QTableWidgetItem(f"{task['progress']}%")
            if task["status"] == "已完成":
                progress_item.setForeground(QColor("#28a745"))
            elif task["status"] == "失败":
                progress_item.setForeground(QColor("#dc3545"))
            self.tasks_table.setItem(row, 4, progress_item)
            
            # 更新时间
            updated_time = time.strftime("%H:%M:%S", time.localtime(task["updated_at"]))
            self.tasks_table.setItem(row, 5, QTableWidgetItem(updated_time))
    
    def _refresh_status(self):
        """刷新状态"""
        # 手动触发状态更新
        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("刷新中...")
        
        # 2秒后恢复按钮
        QTimer.singleShot(2000, self._enable_refresh_button)
    
    def _enable_refresh_button(self):
        """启用刷新按钮"""
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("刷新状态")
    
    def _refresh_tasks(self):
        """刷新任务"""
        self.refresh_tasks_button.setEnabled(False)
        self.refresh_tasks_button.setText("刷新中...")
        
        # 模拟刷新任务
        import random
        for task in self.tasks_data:
            if task["status"] == "进行中":
                task["progress"] = min(100, task["progress"] + random.randint(5, 15))
                if task["progress"] == 100:
                    task["status"] = "已完成"
                task["updated_at"] = time.time()
        
        self._update_tasks_table()
        
        # 1秒后恢复按钮
        QTimer.singleShot(1000, self._enable_refresh_tasks_button)
    
    def _enable_refresh_tasks_button(self):
        """启用刷新任务按钮"""
        self.refresh_tasks_button.setEnabled(True)
        self.refresh_tasks_button.setText("刷新任务")
    
    def _clear_completed_tasks(self):
        """清理已完成任务"""
        reply = QMessageBox.question(
            self,
            "确认清理",
            "确定要清理所有已完成的任务吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 移除已完成的任务
            self.tasks_data = [task for task in self.tasks_data if task["status"] != "已完成"]
            self._update_tasks_table()
            
            QMessageBox.information(self, "成功", f"已清理 {len([t for t in self.tasks_data if t['status'] == '已完成'])} 个任务")
    
    def _toggle_processing(self, checked):
        """切换处理状态"""
        if checked:
            self.pause_button.setText("继续处理")
            self.pause_button.setStyleSheet("""
                QPushButton {
                    padding: 8px 16px;
                    font-size: 14px;
                    background: #28a745;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
        else:
            self.pause_button.setText("暂停处理")
            self.pause_button.setStyleSheet("""
                QPushButton {
                    padding: 8px 16px;
                    font-size: 14px;
                    background: #ffc107;
                    color: black;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
    
    def closeEvent(self, event):
        """关闭事件"""
        # 停止状态监控
        if self.status_worker:
            self.status_worker.stop()
        
        if self.status_thread and self.status_thread.isRunning():
            self.status_thread.quit()
            self.status_thread.wait()
        
        event.accept()