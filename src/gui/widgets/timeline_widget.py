#!/usr/bin/env python3
"""
msearch PySide6时间线组件
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget, QFrame,
    QScrollArea, QProgressBar, QComboBox, QSpinBox, QCheckBox, QSlider,
    QGroupBox, QSplitter, QToolButton, QButtonGroup, QRadioButton,
    QSizePolicy, QSpacerItem, QFileDialog, QMessageBox, QTabWidget,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QObject, QUrl, QSize, QPropertyAnimation, QRectF, QPointF
)
from PySide6.QtGui import (
    QIcon, QPixmap, QFont, QAction, QPalette, QColor, QDesktopServices, QDragEnterEvent, QDropEvent,
    QPainter, QPen, QBrush
)

from src.core.config import load_config
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class TimelineWidget(QWidget):
    """时间线组件"""
    
    # 信号定义
    status_message_changed = Signal(str)
    timeline_item_selected = Signal(dict)  # 时间线项被选中
    
    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        
        # API客户端
        self.api_client = api_client
        
        # 初始化UI
        self.init_ui()
        
        # 初始化状态
        self.init_state()
        
        # 连接信号
        self.connect_signals()
        
        # 应用样式
        self.apply_styles()
        
        logger.info("时间线组件初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建时间线浏览选项卡
        self.create_timeline_browser_tab()
        
        # 创建时间线搜索选项卡
        self.create_timeline_search_tab()
    
    def create_timeline_browser_tab(self):
        """创建时间线浏览选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 时间线视图
        self.timeline_view = QGraphicsView()
        self.timeline_scene = QGraphicsScene()
        self.timeline_view.setScene(self.timeline_scene)
        self.timeline_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.timeline_view)
        
        # 控制按钮
        controls_layout = QHBoxLayout()
        
        self.zoom_in_button = QPushButton("放大")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        controls_layout.addWidget(self.zoom_in_button)
        
        self.zoom_out_button = QPushButton("缩小")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        controls_layout.addWidget(self.zoom_out_button)
        
        self.reset_view_button = QPushButton("重置视图")
        self.reset_view_button.clicked.connect(self.reset_view)
        controls_layout.addWidget(self.reset_view_button)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        self.tab_widget.addTab(tab, "时间线浏览")
    
    def create_timeline_search_tab(self):
        """创建时间线搜索选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 搜索输入区域
        search_group = QGroupBox("时间线搜索")
        search_layout = QVBoxLayout(search_group)
        
        # 查询输入
        query_layout = QHBoxLayout()
        query_layout.addWidget(QLabel("查询:"))
        
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("输入搜索关键词...")
        self.query_input.returnPressed.connect(self.perform_timeline_search)
        query_layout.addWidget(self.query_input)
        
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.perform_timeline_search)
        query_layout.addWidget(search_button)
        
        search_layout.addLayout(query_layout)
        
        # 时间范围选择
        time_range_layout = QHBoxLayout()
        
        time_range_layout.addWidget(QLabel("时间范围:"))
        
        self.start_time_input = QLineEdit()
        self.start_time_input.setPlaceholderText("开始时间 (YYYY-MM-DD)")
        time_range_layout.addWidget(self.start_time_input)
        
        time_range_layout.addWidget(QLabel("至"))
        
        self.end_time_input = QLineEdit()
        self.end_time_input.setPlaceholderText("结束时间 (YYYY-MM-DD)")
        time_range_layout.addWidget(self.end_time_input)
        
        search_layout.addLayout(time_range_layout)
        
        # 文件类型选择
        file_type_layout = QHBoxLayout()
        
        file_type_layout.addWidget(QLabel("文件类型:"))
        
        self.file_type_combo = QComboBox()
        self.file_type_combo.addItems(["全部", "视频", "音频", "图片"])
        file_type_layout.addWidget(self.file_type_combo)
        
        file_type_layout.addStretch()
        
        search_layout.addLayout(file_type_layout)
        
        layout.addWidget(search_group)
        
        # 搜索结果表格
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "文件路径", "文件类型", "开始时间", "结束时间", "操作"
        ])
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.itemSelectionChanged.connect(self.on_result_selection_changed)
        layout.addWidget(self.results_table)
        
        self.tab_widget.addTab(tab, "时间线搜索")
    
    def init_state(self):
        """初始化状态"""
        self.timeline_items = []
        self.current_results = []
    
    def connect_signals(self):
        """连接信号"""
        pass
    
    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QPushButton {
                background-color: #409EFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: #66b1ff;
            }
            
            QPushButton:pressed {
                background-color: #3a8ee6;
            }
            
            QPushButton:disabled {
                background-color: #c0c4cc;
                color: #ffffff;
            }
            
            QLineEdit {
                padding: 8px;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
            }
            
            QLineEdit:focus {
                border-color: #409EFF;
            }
            
            QTableWidget {
                gridline-color: #e4e7ed;
                selection-background-color: #f5f7fa;
            }
            
            QHeaderView::section {
                background-color: #f5f7fa;
                padding: 8px;
                border: 1px solid #e4e7ed;
            }
        """)
    
    def zoom_in(self):
        """放大"""
        self.timeline_view.scale(1.2, 1.2)
        self.status_message_changed.emit("时间线视图已放大")
    
    def zoom_out(self):
        """缩小"""
        self.timeline_view.scale(0.8, 0.8)
        self.status_message_changed.emit("时间线视图已缩小")
    
    def reset_view(self):
        """重置视图"""
        self.timeline_view.resetTransform()
        self.timeline_view.centerOn(0, 0)
        self.status_message_changed.emit("时间线视图已重置")
    
    def perform_timeline_search(self):
        """执行时间线搜索"""
        query = self.query_input.text().strip()
        start_time = self.start_time_input.text().strip()
        end_time = self.end_time_input.text().strip()
        file_type = self.file_type_combo.currentText()
        
        # 如果有API客户端，调用API搜索
        if self.api_client and self.api_client.is_connected():
            # 构造搜索参数
            search_params = {}
            if query:
                search_params["query"] = query
            if start_time or end_time:
                search_params["time_range"] = {
                    "start": start_time if start_time else None,
                    "end": end_time if end_time else None
                }
            if file_type != "全部":
                search_params["file_types"] = [file_type.lower()]
            
            # 调用API搜索
            result = self.api_client.search_timeline(**search_params)
            
            if result and result.get("status") == "success":
                self.display_search_results(result.get("results", []))
                self.status_message_changed.emit(f"时间线搜索完成，找到 {len(result.get('results', []))} 个结果")
            else:
                error_msg = result.get("message", "未知错误") if result else "API调用失败"
                QMessageBox.critical(self, "错误", f"时间线搜索失败: {error_msg}")
                self.status_message_changed.emit(f"时间线搜索失败: {error_msg}")
        else:
            # 模拟搜索结果
            self.display_search_results(self.generate_mock_results())
            self.status_message_changed.emit("时间线搜索完成（模拟数据）")
    
    def generate_mock_results(self):
        """生成模拟搜索结果"""
        return [
            {
                "file_path": "/path/to/video1.mp4",
                "file_type": "视频",
                "start_time": "00:01:30",
                "end_time": "00:02:15",
                "timestamp": 90
            },
            {
                "file_path": "/path/to/audio1.mp3",
                "file_type": "音频",
                "start_time": "00:05:20",
                "end_time": "00:06:45",
                "timestamp": 320
            },
            {
                "file_path": "/path/to/image1.jpg",
                "file_type": "图片",
                "start_time": "00:10:15",
                "end_time": "00:10:15",
                "timestamp": 615
            }
        ]
    
    def display_search_results(self, results: List[Dict]):
        """显示搜索结果"""
        self.current_results = results
        self.results_table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # 文件路径
            self.results_table.setItem(row, 0, self.create_table_item(result.get("file_path", "")))
            
            # 文件类型
            self.results_table.setItem(row, 1, self.create_table_item(result.get("file_type", "")))
            
            # 开始时间
            self.results_table.setItem(row, 2, self.create_table_item(result.get("start_time", "")))
            
            # 结束时间
            self.results_table.setItem(row, 3, self.create_table_item(result.get("end_time", "")))
            
            # 操作按钮
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            play_button = QPushButton("播放")
            play_button.clicked.connect(lambda checked, r=result: self.play_result(r))
            action_layout.addWidget(play_button)
            
            self.results_table.setCellWidget(row, 4, action_widget)
        
        # 调整列宽
        self.results_table.resizeColumnsToContents()
    
    def create_table_item(self, text: str):
        """创建表格项"""
        from PySide6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item
    
    def on_result_selection_changed(self):
        """结果选择变化事件"""
        selected_rows = self.results_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            if row < len(self.current_results):
                result = self.current_results[row]
                self.timeline_item_selected.emit(result)
    
    def play_result(self, result: Dict):
        """播放结果"""
        file_path = result.get("file_path", "")
        if file_path and os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            QMessageBox.warning(self, "警告", f"文件不存在: {file_path}")
    
    def refresh(self):
        """刷新界面"""
        # 清空输入
        self.query_input.clear()
        self.start_time_input.clear()
        self.end_time_input.clear()
        self.results_table.setRowCount(0)
        self.timeline_scene.clear()
        
        # 重置状态
        self.file_type_combo.setCurrentIndex(0)
        
        self.status_message_changed.emit("时间线界面已刷新")