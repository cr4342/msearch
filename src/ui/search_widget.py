"""
搜索组件
"""

import sys
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QComboBox, QProgressBar, QFrame, QScrollArea, QGridLayout, QMessageBox,
    QFileDialog, QStyle, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon, QFont, QAction


# 设置日志
logger = logging.getLogger(__name__)


class SearchWorker(QObject):
    """搜索工作线程"""
    
    finished = Signal(list)
    error = Signal(str)
    progress = Signal(int)
    
    def __init__(self, query, query_type):
        super().__init__()
        self.query = query
        self.query_type = query_type
    
    def run(self):
        """执行搜索"""
        try:
            # 模拟搜索过程
            from time import sleep
            for i in range(1, 101):
                sleep(0.02)
                self.progress.emit(i)
            
            # 模拟搜索结果
            results = []
            for i in range(1, 11):
                results.append({
                    "file_path": f"/tmp/test_file_{i}.jpg",
                    "file_name": f"test_file_{i}.jpg",
                    "file_size": i * 1024 * 1024,
                    "file_type": ".jpg",
                    "score": 0.8 - i * 0.05,
                    "type": "image"
                })
            
            self.finished.emit(results)
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            self.error.emit(str(e))


class ResultsWidget(QWidget):
    """搜索结果显示组件"""
    
    def __init__(self):
        super().__init__()
        self.results = []
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 结果标题
        results_label = QLabel("搜索结果")
        results_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(results_label)
        
        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")
        
        # 结果容器
        results_container = QWidget()
        self.results_layout = QGridLayout(results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(10)
        
        self.scroll_area.setWidget(results_container)
        layout.addWidget(self.scroll_area)
    
    def set_results(self, results: List[Dict[str, Any]]):
        """设置搜索结果"""
        self.results = results
        self._update_results_display()
    
    def _update_results_display(self):
        """更新结果显示"""
        # 清除现有结果
        for i in reversed(range(self.results_layout.count())):
            child = self.results_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not self.results:
            # 显示无结果提示
            no_results_label = QLabel("没有找到相关结果")
            no_results_label.setAlignment(Qt.AlignCenter)
            no_results_label.setStyleSheet("color: #666; font-size: 16px; padding: 20px;")
            self.results_layout.addWidget(no_results_label, 0, 0)
            return
        
        # 显示结果
        columns = 4
        for i, result in enumerate(self.results):
            row = i // columns
            col = i % columns
            
            result_item = self._create_result_item(result)
            self.results_layout.addWidget(result_item, row, col)
    
    def _create_result_item(self, result: Dict[str, Any]) -> QWidget:
        """创建结果项"""
        item = QFrame()
        item.setFrameStyle(QFrame.NoFrame)
        item.setStyleSheet("""
            QFrame {
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                background: white;
                padding: 12px;
                margin: 8px;
            }
            QFrame:hover {
                border-color: #0078d4;
                background: #f0f7ff;
            }
        """)
        
        layout = QVBoxLayout(item)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # 缩略图
        thumbnail = QLabel()
        thumbnail.setFixedSize(180, 180)
        thumbnail.setAlignment(Qt.AlignCenter)
        thumbnail.setStyleSheet("""
            QLabel {
                border: 1px solid #f0f0f0;
                border-radius: 8px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                font-size: 64px;
            }
        """)
        
        # 根据文件类型显示不同的占位符
        file_type = result.get('file_type', '')
        if file_type in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
            thumbnail.setText("🖼️")
        elif file_type in ['.mp4', '.avi', '.mov']:
            thumbnail.setText("🎬")
        elif file_type in ['.mp3', '.wav', '.flac']:
            thumbnail.setText("🎵")
        else:
            thumbnail.setText("📄")
        
        thumbnail.setFont(QFont("Segoe UI Emoji", 72))
        layout.addWidget(thumbnail)
        
        # 文件名
        name_label = QLabel(result.get('file_name', '未知文件'))
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setMaximumHeight(50)
        name_label.setStyleSheet("font-weight: 600; color: #333333; font-size: 14px;")
        layout.addWidget(name_label)
        
        # 相似度分数
        score = result.get('score', 0)
        score_label = QLabel(f"相似度: {score:.1%}")
        score_label.setAlignment(Qt.AlignCenter)
        score_label.setStyleSheet("color: #0078d4; font-weight: bold; font-size: 16px;")
        layout.addWidget(score_label)
        
        # 文件信息
        file_info = QWidget()
        info_layout = QVBoxLayout(file_info)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)
        
        # 文件大小
        file_size = result.get('file_size', 0)
        size_text = self._format_file_size(file_size)
        size_label = QLabel(size_text)
        size_label.setAlignment(Qt.AlignCenter)
        size_label.setStyleSheet("color: #666666; font-size: 12px;")
        info_layout.addWidget(size_label)
        
        # 文件类型
        type_label = QLabel(file_type.upper())
        type_label.setAlignment(Qt.AlignCenter)
        type_label.setStyleSheet("color: #999999; font-size: 11px; font-weight: 500;")
        info_layout.addWidget(type_label)
        
        layout.addWidget(file_info)
        
        # 操作按钮
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)
        action_layout.addStretch()
        
        # 查看按钮
        view_button = QPushButton("查看")
        view_button.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #5a6268;
            }
        """)
        action_layout.addWidget(view_button)
        
        # 打开文件夹按钮
        folder_button = QPushButton("打开")
        folder_button.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #5a6268;
            }
        """)
        action_layout.addWidget(folder_button)
        
        action_layout.addStretch()
        layout.addWidget(action_widget)
        
        return item
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"


class SearchWidget(QWidget):
    """搜索组件"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.current_worker = None
        self.current_thread = None
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 搜索类型选择
        search_type_layout = QHBoxLayout()
        search_type_layout.setSpacing(10)
        
        type_label = QLabel("搜索类型:")
        type_label.setStyleSheet("font-weight: bold;")
        search_type_layout.addWidget(type_label)
        
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["文本搜索", "图像搜索", "音频搜索"])
        self.search_type_combo.setMinimumWidth(150)
        search_type_layout.addWidget(self.search_type_combo)
        
        search_type_layout.addStretch()
        layout.addLayout(search_type_layout)
        
        # 搜索栏
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索关键词或文件路径")
        self.search_input.setMinimumHeight(40)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 20px;
                padding: 0 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
                outline: none;
            }
        """)
        search_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("搜索")
        self.search_button.setMinimumHeight(40)
        self.search_button.setMinimumWidth(80)
        self.search_button.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                color: white;
                border: none;
                border-radius: 20px;
                font-weight: bold;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: #106ebe;
            }
        """)
        self.search_button.clicked.connect(self._on_search)
        search_layout.addWidget(self.search_button)
        
        self.file_search_button = QPushButton("选择文件")
        self.file_search_button.setMinimumHeight(40)
        self.file_search_button.setMinimumWidth(100)
        self.file_search_button.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 20px;
                font-weight: bold;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: #5a6268;
            }
        """)
        self.file_search_button.clicked.connect(self._on_select_file)
        search_layout.addWidget(self.file_search_button)
        
        layout.addLayout(search_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background: #0078d4;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 搜索结果
        self.result_widget = ResultsWidget()
        layout.addWidget(self.result_widget, 1)
    
    def _on_search(self):
        """搜索处理"""
        query = self.search_input.text()
        if not query:
            QMessageBox.warning(self, "警告", "请输入搜索关键词")
            return
        
        self._start_search(query, "text")
    
    def _on_select_file(self):
        """选择文件"""
        search_type = self.search_type_combo.currentText()
        file_filter = "图像文件 (*.jpg *.jpeg *.png *.b