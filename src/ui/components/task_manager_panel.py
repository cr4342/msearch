"""
任务管理器面板组件
显示任务进度和历史记录
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QProgressBar, QGroupBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QColor


class TaskItemWidget(QWidget):
    """任务项组件"""
    
    def __init__(self, task_data: Dict[str, Any], parent=None):
        """初始化任务项"""
        super().__init__(parent)
        self.task_data = task_data
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 任务信息
        info_layout = QHBoxLayout()
        
        # 任务类型
        task_type = self.task_data.get("task_type", "未知")
        type_label = QLabel(task_type)
        type_label.setStyleSheet("""
            QLabel {
                background-color: #165DFF;
                color: white;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 11px;
                font-weight: 600;
            }
        """)
        info_layout.addWidget(type_label)
        
        # 任务状态
        status = self.task_data.get("status", "pending")
        status_text = {
            "pending": "⏳ 等待中",
            "running": "🔄 进行中",
            "completed": "✓ 已完成",
            "failed": "✗ 失败"
        }.get(status, status)
        
        status_label = QLabel(status_text)
        if status == "completed":
            status_label.setStyleSheet("color: #00B42A; font-weight: 600;")
        elif status == "failed":
            status_label.setStyleSheet("color: #F53F3F; font-weight: 600;")
        elif status == "running":
            status_label.setStyleSheet("color: #FF7D00; font-weight: 600;")
        else:
            status_label.setStyleSheet("color: #86909C;")
        
        info_layout.addWidget(status_label)
        info_layout.addStretch()
        
        # 任务ID
        task_id = self.task_data.get("id", "")[:8]
        id_label = QLabel(f"ID: {task_id}")
        id_label.setStyleSheet("color: #86909C; font-size: 11px;")
        info_layout.addWidget(id_label)
        
        layout.addLayout(info_layout)
        
        # 任务描述
        description = self.task_data.get("description", "无描述")
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #4E5969; font-size: 12px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 进度条
        if status == "running":
            progress = self.task_data.get("progress", 0.0)
            progress_bar = QProgressBar()
            progress_bar.setValue(int(progress * 100))
            progress_bar.setStyleSheet("""
                QProgressBar {
                    background-color: #E5E6EB;
                    border-radius: 3px;
                    border: none;
                    height: 6px;
                }
                QProgressBar::chunk {
                    background-color: #165DFF;
                    border-radius: 3px;
                }
            """)
            layout.addWidget(progress_bar)
        
        # 时间信息
        created_at = self.task_data.get("created_at")
        if created_at:
            time_label = QLabel(f"创建时间: {created_at}")
            time_label.setStyleSheet("color: #86909C; font-size: 10px;")
            layout.addWidget(time_label)


class TaskManagerPanel(QWidget):
    """任务管理器面板组件"""
    
    # 信号定义
    task_cancelled = Signal(str)
    task_restarted = Signal(str)
    
    def __init__(self, parent=None):
        """初始化任务管理器面板"""
        super().__init__(parent)
        
        self.tasks: List[Dict[str, Any]] = []
        self.task_history: List[Dict[str, Any]] = []
        
        self.init_ui()
        
        # 定时刷新任务状态
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_tasks)
        self.refresh_timer.start(2000)  # 每2秒刷新一次
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 容器
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 8px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("📋 任务管理")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #1D2129;
            }
        """)
        container_layout.addWidget(title_label)
        
        # 统计信息
        stats_layout = QHBoxLayout()
        
        self.total_tasks_label = QLabel("总任务: 0")
        self.total_tasks_label.setStyleSheet("""
            QLabel {
                background-color: #E8F3FF;
                color: #165DFF;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }
        """)
        stats_layout.addWidget(self.total_tasks_label)
        
        self.running_tasks_label = QLabel("进行中: 0")
        self.running_tasks_label.setStyleSheet("""
            QLabel {
                background-color: #FFF7E8;
                color: #FF7D00;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }
        """)
        stats_layout.addWidget(self.running_tasks_label)
        
        self.completed_tasks_label = QLabel("已完成: 0")
        self.completed_tasks_label.setStyleSheet("""
            QLabel {
                background-color: #E8FFEA;
                color: #00B42A;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }
        """)
        stats_layout.addWidget(self.completed_tasks_label)
        
        self.failed_tasks_label = QLabel("失败: 0")
        self.failed_tasks_label.setStyleSheet("""
            QLabel {
                background-color: #FFECE8;
                color: #F53F3F;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }
        """)
        stats_layout.addWidget(self.failed_tasks_label)
        
        stats_layout.addStretch()
        
        # 刷新按钮
        refresh_button = QPushButton("🔄 刷新")
        refresh_button.clicked.connect(self.refresh_tasks)
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #F2F3F5;
                color: #4E5969;
                border: 1px solid #E5E6EB;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #E5E6EB;
                border-color: #C9CDD4;
            }
            QPushButton:pressed {
                background-color: #C9CDD4;
            }
        """)
        stats_layout.addWidget(refresh_button)
        
        container_layout.addLayout(stats_layout)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E5E6EB;
                border-radius: 6px;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #F2F3F5;
                color: #4E5969;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #165DFF;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background-color: #E5E6EB;
            }
        """)
        
        # 当前任务选项卡
        current_tasks_tab = QWidget()
        current_tasks_layout = QVBoxLayout(current_tasks_tab)
        current_tasks_layout.setContentsMargins(10, 10, 10, 10)
        
        self.current_tasks_list = QListWidget()
        self.current_tasks_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
            }
            QListWidget::item {
                border-bottom: 1px solid #E5E6EB;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #E8F3FF;
            }
        """)
        current_tasks_layout.addWidget(self.current_tasks_list)
        
        self.tab_widget.addTab(current_tasks_tab, "📌 当前任务")
        
        # 任务历史选项卡
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        history_layout.setContentsMargins(10, 10, 10, 10)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["任务类型", "状态", "描述", "创建时间", "完成时间"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.history_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: transparent;
                gridline-color: #E5E6EB;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #F2F3F5;
                color: #4E5969;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #E5E6EB;
                font-weight: 600;
            }
        """)
        history_layout.addWidget(self.history_table)
        
        self.tab_widget.addTab(history_tab, "📜 任务历史")
        
        container_layout.addWidget(self.tab_widget)
        
        layout.addWidget(container)
    
    def add_task(self, task_data: Dict[str, Any]):
        """添加任务"""
        self.tasks.append(task_data)
        self.update_current_tasks()
        self.update_stats()
    
    def update_task(self, task_id: str, updates: Dict[str, Any]):
        """更新任务"""
        for task in self.tasks:
            if task.get("id") == task_id:
                task.update(updates)
                
                # 如果任务完成或失败，移到历史记录
                if task.get("status") in ["completed", "failed"]:
                    self.tasks.remove(task)
                    task["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.task_history.insert(0, task)
                    self.update_history()
                
                self.update_current_tasks()
                self.update_stats()
                break
    
    def update_current_tasks(self):
        """更新当前任务列表"""
        self.current_tasks_list.clear()
        
        for task in self.tasks:
            item_widget = TaskItemWidget(task)
            item = QListWidgetItem()
            item.setSizeHint(item_widget.sizeHint())
            self.current_tasks_list.addItem(item)
            self.current_tasks_list.setItemWidget(item, item_widget)
    
    def update_history(self):
        """更新任务历史表格"""
        self.history_table.setRowCount(0)
        
        for task in self.task_history[:100]:  # 只显示最近100条记录
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            # 任务类型
            type_item = QTableWidgetItem(task.get("task_type", "未知"))
            type_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(row, 0, type_item)
            
            # 状态
            status = task.get("status", "unknown")
            status_text = {
                "completed": "✓ 已完成",
                "failed": "✗ 失败"
            }.get(status, status)
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            if status == "completed":
                status_item.setForeground(QColor("#00B42A"))
            elif status == "failed":
                status_item.setForeground(QColor("#F53F3F"))
            self.history_table.setItem(row, 1, status_item)
            
            # 描述
            desc_item = QTableWidgetItem(task.get("description", ""))
            self.history_table.setItem(row, 2, desc_item)
            
            # 创建时间
            created_item = QTableWidgetItem(task.get("created_at", ""))
            self.history_table.setItem(row, 3, created_item)
            
            # 完成时间
            completed_item = QTableWidgetItem(task.get("completed_at", ""))
            self.history_table.setItem(row, 4, completed_item)
    
    def update_stats(self):
        """更新统计信息"""
        total = len(self.tasks) + len(self.task_history)
        running = len([t for t in self.tasks if t.get("status") == "running"])
        completed = len([t for t in self.task_history if t.get("status") == "completed"])
        failed = len([t for t in self.task_history if t.get("status") == "failed"])
        
        self.total_tasks_label.setText(f"总任务: {total}")
        self.running_tasks_label.setText(f"进行中: {running}")
        self.completed_tasks_label.setText(f"已完成: {completed}")
        self.failed_tasks_label.setText(f"失败: {failed}")
    
    def refresh_tasks(self):
        """刷新任务状态"""
        # 这里应该从任务管理器获取最新的任务状态
        # 暂时只是更新UI
        self.update_current_tasks()
        self.update_stats()
    
    def clear_history(self):
        """清空任务历史"""
        self.task_history.clear()
        self.update_history()
        self.update_stats()