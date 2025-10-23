#!/usr/bin/env python3
"""
msearch PySide6搜索界面组件
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget, QFrame,
    QScrollArea, QProgressBar, QComboBox, QSpinBox, QCheckBox, QSlider,
    QGroupBox, QSplitter, QToolButton, QButtonGroup, QRadioButton,
    QSizePolicy, QSpacerItem, QFileDialog, QMessageBox, QTabWidget
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QObject, QUrl, QSize, QPropertyAnimation
)
from PySide6.QtGui import (
    QIcon, QPixmap, QFont, QAction, QPalette, QColor, QDesktopServices, QDragEnterEvent, QDropEvent
)

from src.core.config import load_config
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class SearchWorker(QObject):
    """搜索工作线程"""
    
    # 信号定义
    search_completed = Signal(list)  # 搜索完成，返回结果列表
    search_failed = Signal(str)      # 搜索失败，返回错误信息
    progress_updated = Signal(int)   # 进度更新
    
    def __init__(self):
        super().__init__()
        self.is_running = False
    
    def perform_text_search(self, query: str, limit: int = 20):
        """执行文本搜索"""
        try:
            self.is_running = True
            
            # 模拟搜索过程
            self.progress_updated.emit(10)
            
            # TODO: 实现实际的API调用
            import time
            time.sleep(1)
            
            if not self.is_running:
                return
            
            self.progress_updated.emit(50)
            time.sleep(1)
            
            if not self.is_running:
                return
            
            # 模拟搜索结果
            results = [
                {
                    "id": "1",
                    "file_path": "/path/to/file1.txt",
                    "file_type": "text",
                    "score": 0.95,
                    "start_time_ms": 0,
                    "end_time_ms": 0,
                    "metadata": {"content": "这是文件1的内容"}
                },
                {
                    "id": "2",
                    "file_path": "/path/to/file2.txt",
                    "file_type": "text",
                    "score": 0.85,
                    "start_time_ms": 0,
                    "end_time_ms": 0,
                    "metadata": {"content": "这是文件2的内容"}
                }
            ]
            
            self.progress_updated.emit(100)
            self.search_completed.emit(results)
            
        except Exception as e:
            logger.error(f"文本搜索失败: {e}")
            self.search_failed.emit(str(e))
        finally:
            self.is_running = False
    
    def perform_image_search(self, file_path: str, limit: int = 20):
        """执行图像搜索"""
        try:
            self.is_running = True
            
            # 模拟搜索过程
            self.progress_updated.emit(10)
            
            # TODO: 实现实际的API调用
            import time
            time.sleep(2)
            
            if not self.is_running:
                return
            
            self.progress_updated.emit(50)
            time.sleep(2)
            
            if not self.is_running:
                return
            
            # 模拟搜索结果
            results = [
                {
                    "id": "1",
                    "file_path": "/path/to/image1.jpg",
                    "file_type": "image",
                    "score": 0.90,
                    "start_time_ms": 0,
                    "end_time_ms": 0,
                    "metadata": {}
                },
                {
                    "id": "2",
                    "file_path": "/path/to/image2.jpg",
                    "file_type": "image",
                    "score": 0.80,
                    "start_time_ms": 0,
                    "end_time_ms": 0,
                    "metadata": {}
                }
            ]
            
            self.progress_updated.emit(100)
            self.search_completed.emit(results)
            
        except Exception as e:
            logger.error(f"图像搜索失败: {e}")
            self.search_failed.emit(str(e))
        finally:
            self.is_running = False
    
    def perform_audio_search(self, file_path: str, limit: int = 20):
        """执行音频搜索"""
        try:
            self.is_running = True
            
            # 模拟搜索过程
            self.progress_updated.emit(10)
            
            # TODO: 实现实际的API调用
            import time
            time.sleep(2)
            
            if not self.is_running:
                return
            
            self.progress_updated.emit(50)
            time.sleep(2)
            
            if not self.is_running:
                return
            
            # 模拟搜索结果
            results = [
                {
                    "id": "1",
                    "file_path": "/path/to/audio1.mp3",
                    "file_type": "audio",
                    "score": 0.88,
                    "start_time_ms": 1000,
                    "end_time_ms": 5000,
                    "metadata": {"transcribed_text": "这是音频1的转录文本"}
                },
                {
                    "id": "2",
                    "file_path": "/path/to/audio2.mp3",
                    "file_type": "audio",
                    "score": 0.78,
                    "start_time_ms": 2000,
                    "end_time_ms": 6000,
                    "metadata": {"transcribed_text": "这是音频2的转录文本"}
                }
            ]
            
            self.progress_updated.emit(100)
            self.search_completed.emit(results)
            
        except Exception as e:
            logger.error(f"音频搜索失败: {e}")
            self.search_failed.emit(str(e))
        finally:
            self.is_running = False
    
    def perform_video_search(self, file_path: str, limit: int = 20):
        """执行视频搜索"""
        try:
            self.is_running = True
            
            # 模拟搜索过程
            self.progress_updated.emit(10)
            
            # TODO: 实现实际的API调用
            import time
            time.sleep(3)
            
            if not self.is_running:
                return
            
            self.progress_updated.emit(50)
            time.sleep(3)
            
            if not self.is_running:
                return
            
            # 模拟搜索结果
            results = [
                {
                    "id": "1",
                    "file_path": "/path/to/video1.mp4",
                    "file_type": "video",
                    "score": 0.92,
                    "start_time_ms": 5000,
                    "end_time_ms": 10000,
                    "metadata": {}
                },
                {
                    "id": "2",
                    "file_path": "/path/to/video2.mp4",
                    "file_type": "video",
                    "score": 0.82,
                    "start_time_ms": 15000,
                    "end_time_ms": 20000,
                    "metadata": {}
                }
            ]
            
            self.progress_updated.emit(100)
            self.search_completed.emit(results)
            
        except Exception as e:
            logger.error(f"视频搜索失败: {e}")
            self.search_failed.emit(str(e))
        finally:
            self.is_running = False
    
    def perform_multimodal_search(self, query: str, image_path: str, audio_path: str, video_path: str, limit: int = 20):
        """执行多模态搜索"""
        try:
            self.is_running = True
            
            # 模拟搜索过程
            self.progress_updated.emit(10)
            
            # TODO: 实现实际的API调用
            import time
            time.sleep(3)
            
            if not self.is_running:
                return
            
            self.progress_updated.emit(50)
            time.sleep(3)
            
            if not self.is_running:
                return
            
            # 模拟搜索结果
            results = [
                {
                    "id": "1",
                    "file_path": "/path/to/multimodal1.mp4",
                    "file_type": "video",
                    "score": 0.94,
                    "start_time_ms": 8000,
                    "end_time_ms": 13000,
                    "metadata": {}
                },
                {
                    "id": "2",
                    "file_path": "/path/to/multimodal2.jpg",
                    "file_type": "image",
                    "score": 0.84,
                    "start_time_ms": 0,
                    "end_time_ms": 0,
                    "metadata": {}
                }
            ]
            
            self.progress_updated.emit(100)
            self.search_completed.emit(results)
            
        except Exception as e:
            logger.error(f"多模态搜索失败: {e}")
            self.search_failed.emit(str(e))
        finally:
            self.is_running = False
    
    def stop_search(self):
        """停止搜索"""
        self.is_running = False


class SearchWidget(QWidget):
    """搜索界面组件"""
    
    # 信号定义
    status_message_changed = Signal(str)
    result_selected = Signal(dict)  # 结果被选中
    
    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        
        # API客户端
        self.api_client = api_client
        
        # 搜索工作线程
        self.search_thread = None
        self.search_worker = None
        
        # 初始化UI
        self.init_ui()
        
        # 初始化状态
        self.init_state()
        
        # 连接信号
        self.connect_signals()
        
        # 应用样式
        self.apply_styles()
        
        logger.info("搜索界面组件初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建各个搜索选项卡
        self.create_text_search_tab()
        self.create_image_search_tab()
        self.create_audio_search_tab()
        self.create_video_search_tab()
        self.create_multimodal_search_tab()
        
        # 创建结果区域
        self.create_results_area(main_layout)
    
    def create_text_search_tab(self):
        """创建文本搜索选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 搜索输入区域
        search_group = QGroupBox("搜索查询")
        search_layout = QVBoxLayout(search_group)
        
        # 文本输入框
        self.text_search_input = QLineEdit()
        self.text_search_input.setPlaceholderText("输入搜索关键词...")
        self.text_search_input.returnPressed.connect(self.perform_text_search)
        search_layout.addWidget(self.text_search_input)
        
        # 搜索选项
        options_layout = QHBoxLayout()
        
        # 结果数量限制
        options_layout.addWidget(QLabel("结果数量:"))
        self.text_result_limit = QSpinBox()
        self.text_result_limit.setMinimum(10)
        self.text_result_limit.setMaximum(100)
        self.text_result_limit.setValue(20)
        self.text_result_limit.setSuffix(" 个")
        options_layout.addWidget(self.text_result_limit)
        
        options_layout.addStretch()
        
        # 搜索按钮
        self.text_search_button = QPushButton("搜索")
        self.text_search_button.clicked.connect(self.perform_text_search)
        options_layout.addWidget(self.text_search_button)
        
        search_layout.addLayout(options_layout)
        layout.addWidget(search_group)
        
        # 搜索历史
        history_group = QGroupBox("搜索历史")
        history_layout = QVBoxLayout(history_group)
        
        self.text_history_list = QTextEdit()
        self.text_history_list.setMaximumHeight(100)
        self.text_history_list.setReadOnly(True)
        history_layout.addWidget(self.text_history_list)
        
        layout.addWidget(history_group)
        
        self.tab_widget.addTab(tab, "文本搜索")
    
    def create_image_search_tab(self):
        """创建图像搜索选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文件选择区域
        file_group = QGroupBox("选择图像")
        file_layout = QVBoxLayout(file_group)
        
        # 文件路径输入
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("文件路径:"))
        
        self.image_path_input = QLineEdit()
        self.image_path_input.setPlaceholderText("选择图像文件...")
        self.image_path_input.setReadOnly(True)
        path_layout.addWidget(self.image_path_input)
        
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_image_file)
        path_layout.addWidget(browse_button)
        
        file_layout.addLayout(path_layout)
        
        # 拖放区域
        self.image_drop_area = QLabel("拖拽图像文件到此处")
        self.image_drop_area.setAlignment(Qt.AlignCenter)
        self.image_drop_area.setMinimumHeight(100)
        self.image_drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
        """)
        self.image_drop_area.setAcceptDrops(True)
        self.image_drop_area.dragEnterEvent = self.image_drag_enter_event
        self.image_drop_area.dropEvent = self.image_drop_event
        
        file_layout.addWidget(self.image_drop_area)
        
        # 搜索选项
        options_layout = QHBoxLayout()
        
        # 结果数量限制
        options_layout.addWidget(QLabel("结果数量:"))
        self.image_result_limit = QSpinBox()
        self.image_result_limit.setMinimum(10)
        self.image_result_limit.setMaximum(100)
        self.image_result_limit.setValue(20)
        self.image_result_limit.setSuffix(" 个")
        options_layout.addWidget(self.image_result_limit)
        
        options_layout.addStretch()
        
        # 搜索按钮
        self.image_search_button = QPushButton("搜索相似图像")
        self.image_search_button.clicked.connect(self.perform_image_search)
        options_layout.addWidget(self.image_search_button)
        
        file_layout.addLayout(options_layout)
        layout.addWidget(file_group)
        
        self.tab_widget.addTab(tab, "图像搜索")
    
    def create_audio_search_tab(self):
        """创建音频搜索选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文件选择区域
        file_group = QGroupBox("选择音频")
        file_layout = QVBoxLayout(file_group)
        
        # 文件路径输入
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("文件路径:"))
        
        self.audio_path_input = QLineEdit()
        self.audio_path_input.setPlaceholderText("选择音频文件...")
        self.audio_path_input.setReadOnly(True)
        path_layout.addWidget(self.audio_path_input)
        
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_audio_file)
        path_layout.addWidget(browse_button)
        
        file_layout.addLayout(path_layout)
        
        # 拖放区域
        self.audio_drop_area = QLabel("拖拽音频文件到此处")
        self.audio_drop_area.setAlignment(Qt.AlignCenter)
        self.audio_drop_area.setMinimumHeight(100)
        self.audio_drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
        """)
        self.audio_drop_area.setAcceptDrops(True)
        self.audio_drop_area.dragEnterEvent = self.audio_drag_enter_event
        self.audio_drop_area.dropEvent = self.audio_drop_event
        
        file_layout.addWidget(self.audio_drop_area)
        
        # 搜索选项
        options_layout = QHBoxLayout()
        
        # 结果数量限制
        options_layout.addWidget(QLabel("结果数量:"))
        self.audio_result_limit = QSpinBox()
        self.audio_result_limit.setMinimum(10)
        self.audio_result_limit.setMaximum(100)
        self.audio_result_limit.setValue(20)
        self.audio_result_limit.setSuffix(" 个")
        options_layout.addWidget(self.audio_result_limit)
        
        options_layout.addStretch()
        
        # 搜索按钮
        self.audio_search_button = QPushButton("搜索相似音频")
        self.audio_search_button.clicked.connect(self.perform_audio_search)
        options_layout.addWidget(self.audio_search_button)
        
        file_layout.addLayout(options_layout)
        layout.addWidget(file_group)
        
        self.tab_widget.addTab(tab, "音频搜索")
    
    def create_video_search_tab(self):
        """创建视频搜索选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文件选择区域
        file_group = QGroupBox("选择视频")
        file_layout = QVBoxLayout(file_group)
        
        # 文件路径输入
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("文件路径:"))
        
        self.video_path_input = QLineEdit()
        self.video_path_input.setPlaceholderText("选择视频文件...")
        self.video_path_input.setReadOnly(True)
        path_layout.addWidget(self.video_path_input)
        
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_video_file)
        path_layout.addWidget(browse_button)
        
        file_layout.addLayout(path_layout)
        
        # 拖放区域
        self.video_drop_area = QLabel("拖拽视频文件到此处")
        self.video_drop_area.setAlignment(Qt.AlignCenter)
        self.video_drop_area.setMinimumHeight(100)
        self.video_drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
        """)
        self.video_drop_area.setAcceptDrops(True)
        self.video_drop_area.dragEnterEvent = self.video_drag_enter_event
        self.video_drop_area.dropEvent = self.video_drop_event
        
        file_layout.addWidget(self.video_drop_area)
        
        # 搜索选项
        options_layout = QHBoxLayout()
        
        # 结果数量限制
        options_layout.addWidget(QLabel("结果数量:"))
        self.video_result_limit = QSpinBox()
        self.video_result_limit.setMinimum(10)
        self.video_result_limit.setMaximum(100)
        self.video_result_limit.setValue(20)
        self.video_result_limit.setSuffix(" 个")
        options_layout.addWidget(self.video_result_limit)
        
        options_layout.addStretch()
        
        # 搜索按钮
        self.video_search_button = QPushButton("搜索相似视频")
        self.video_search_button.clicked.connect(self.perform_video_search)
        options_layout.addWidget(self.video_search_button)
        
        file_layout.addLayout(options_layout)
        layout.addWidget(file_group)
        
        self.tab_widget.addTab(tab, "视频搜索")
    
    def create_multimodal_search_tab(self):
        """创建多模态搜索选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文本输入区域
        text_group = QGroupBox("文本查询（可选）")
        text_layout = QHBoxLayout(text_group)
        
        self.multimodal_text_input = QLineEdit()
        self.multimodal_text_input.setPlaceholderText("输入搜索关键词...")
        text_layout.addWidget(self.multimodal_text_input)
        
        layout.addWidget(text_group)
        
        # 文件选择区域
        file_group = QGroupBox("媒体文件（可选）")
        file_layout = QGridLayout(file_group)
        
        # 图像文件
        file_layout.addWidget(QLabel("图像:"), 0, 0)
        self.multimodal_image_input = QLineEdit()
        self.multimodal_image_input.setPlaceholderText("选择图像文件...")
        self.multimodal_image_input.setReadOnly(True)
        file_layout.addWidget(self.multimodal_image_input, 0, 1)
        image_browse_button = QPushButton("浏览...")
        image_browse_button.clicked.connect(self.browse_multimodal_image_file)
        file_layout.addWidget(image_browse_button, 0, 2)
        
        # 音频文件
        file_layout.addWidget(QLabel("音频:"), 1, 0)
        self.multimodal_audio_input = QLineEdit()
        self.multimodal_audio_input.setPlaceholderText("选择音频文件...")
        self.multimodal_audio_input.setReadOnly(True)
        file_layout.addWidget(self.multimodal_audio_input, 1, 1)
        audio_browse_button = QPushButton("浏览...")
        audio_browse_button.clicked.connect(self.browse_multimodal_audio_file)
        file_layout.addWidget(audio_browse_button, 1, 2)
        
        # 视频文件
        file_layout.addWidget(QLabel("视频:"), 2, 0)
        self.multimodal_video_input = QLineEdit()
        self.multimodal_video_input.setPlaceholderText("选择视频文件...")
        self.multimodal_video_input.setReadOnly(True)
        file_layout.addWidget(self.multimodal_video_input, 2, 1)
        video_browse_button = QPushButton("浏览...")
        video_browse_button.clicked.connect(self.browse_multimodal_video_file)
        file_layout.addWidget(video_browse_button, 2, 2)
        
        layout.addWidget(file_group)
        
        # 搜索选项
        options_layout = QHBoxLayout()
        
        # 结果数量限制
        options_layout.addWidget(QLabel("结果数量:"))
        self.multimodal_result_limit = QSpinBox()
        self.multimodal_result_limit.setMinimum(10)
        self.multimodal_result_limit.setMaximum(100)
        self.multimodal_result_limit.setValue(20)
        self.multimodal_result_limit.setSuffix(" 个")
        options_layout.addWidget(self.multimodal_result_limit)
        
        options_layout.addStretch()
        
        # 搜索按钮
        self.multimodal_search_button = QPushButton("多模态搜索")
        self.multimodal_search_button.clicked.connect(self.perform_multimodal_search)
        options_layout.addWidget(self.multimodal_search_button)
        
        layout.addLayout(options_layout)
        
        self.tab_widget.addTab(tab, "多模态搜索")
    
    def create_results_area(self, parent_layout):
        """创建结果区域"""
        results_group = QGroupBox("搜索结果")
        results_layout = QVBoxLayout(results_group)
        
        # 进度条
        self.search_progress = QProgressBar()
        self.search_progress.setVisible(False)
        results_layout.addWidget(self.search_progress)
        
        # 结果表格
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "文件路径", "文件类型", "相似度", "开始时间", "结束时间", "操作"
        ])
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.itemSelectionChanged.connect(self.on_result_selection_changed)
        results_layout.addWidget(self.results_table)
        
        # 结果操作按钮
        result_actions_layout = QHBoxLayout()
        
        self.open_file_button = QPushButton("打开文件")
        self.open_file_button.clicked.connect(self.open_selected_file)
        self.open_file_button.setEnabled(False)
        result_actions_layout.addWidget(self.open_file_button)
        
        self.open_folder_button = QPushButton("打开文件夹")
        self.open_folder_button.clicked.connect(self.open_selected_folder)
        self.open_folder_button.setEnabled(False)
        result_actions_layout.addWidget(self.open_folder_button)
        
        self.copy_path_button = QPushButton("复制路径")
        self.copy_path_button.clicked.connect(self.copy_selected_path)
        self.copy_path_button.setEnabled(False)
        result_actions_layout.addWidget(self.copy_path_button)
        
        result_actions_layout.addStretch()
        
        # 清空结果按钮
        self.clear_results_button = QPushButton("清空结果")
        self.clear_results_button.clicked.connect(self.clear_results)
        result_actions_layout.addWidget(self.clear_results_button)
        
        results_layout.addLayout(result_actions_layout)
        
        parent_layout.addWidget(results_group)
    
    def init_state(self):
        """初始化状态"""
        self.current_results = []
        self.search_history = []
    
    def connect_signals(self):
        """连接信号"""
        # 连接选项卡切换信号
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
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
            
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #409EFF;
            }
        """)
    
    def on_tab_changed(self, index):
        """选项卡切换事件"""
        tab_name = self.tab_widget.tabText(index)
        self.status_message_changed.emit(f"切换到{tab_name}")
    
    def on_result_selection_changed(self):
        """结果选择变化事件"""
        selected_rows = self.results_table.selectedItems()
        has_selection = len(selected_rows) > 0
        
        self.open_file_button.setEnabled(has_selection)
        self.open_folder_button.setEnabled(has_selection)
        self.copy_path_button.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            if row < len(self.current_results):
                result = self.current_results[row]
                self.result_selected.emit(result)
    
    def browse_image_file(self):
        """浏览图像文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图像文件", "", 
            "图像文件 (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            self.image_path_input.setText(file_path)
            self.image_drop_area.setText(f"已选择: {Path(file_path).name}")
    
    def browse_audio_file(self):
        """浏览音频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "", 
            "音频文件 (*.mp3 *.wav *.m4a *.flac *.ogg)"
        )
        if file_path:
            self.audio_path_input.setText(file_path)
            self.audio_drop_area.setText(f"已选择: {Path(file_path).name}")
    
    def browse_video_file(self):
        """浏览视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", 
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv)"
        )
        if file_path:
            self.video_path_input.setText(file_path)
            self.video_drop_area.setText(f"已选择: {Path(file_path).name}")
    
    def browse_multimodal_image_file(self):
        """浏览多模态图像文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图像文件", "", 
            "图像文件 (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            self.multimodal_image_input.setText(file_path)
    
    def browse_multimodal_audio_file(self):
        """浏览多模态音频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "", 
            "音频文件 (*.mp3 *.wav *.m4a *.flac *.ogg)"
        )
        if file_path:
            self.multimodal_audio_input.setText(file_path)
    
    def browse_multimodal_video_file(self):
        """浏览多模态视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", 
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv)"
        )
        if file_path:
            self.multimodal_video_input.setText(file_path)
    
    def image_drag_enter_event(self, event: QDragEnterEvent):
        """图像拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.image_drop_area.setStyleSheet("""
                QLabel {
                    border: 2px dashed #409EFF;
                    background-color: #ecf5ff;
                    border-radius: 5px;
                }
            """)
        else:
            event.ignore()
    
    def image_drop_event(self, event: QDropEvent):
        """图像拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path and self.is_image_file(file_path):
                self.image_path_input.setText(file_path)
                self.image_drop_area.setText(f"已选择: {Path(file_path).name}")
            else:
                QMessageBox.warning(self, "警告", "请选择有效的图像文件")
        
        # 恢复样式
        self.image_drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
        """)
    
    def audio_drag_enter_event(self, event: QDragEnterEvent):
        """音频拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.audio_drop_area.setStyleSheet("""
                QLabel {
                    border: 2px dashed #409EFF;
                    background-color: #ecf5ff;
                    border-radius: 5px;
                }
            """)
        else:
            event.ignore()
    
    def audio_drop_event(self, event: QDropEvent):
        """音频拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path and self.is_audio_file(file_path):
                self.audio_path_input.setText(file_path)
                self.audio_drop_area.setText(f"已选择: {Path(file_path).name}")
            else:
                QMessageBox.warning(self, "警告", "请选择有效的音频文件")
        
        # 恢复样式
        self.audio_drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
        """)
    
    def video_drag_enter_event(self, event: QDragEnterEvent):
        """视频拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.video_drop_area.setStyleSheet("""
                QLabel {
                    border: 2px dashed #409EFF;
                    background-color: #ecf5ff;
                    border-radius: 5px;
                }
            """)
        else:
            event.ignore()
    
    def video_drop_event(self, event: QDropEvent):
        """视频拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path and self.is_video_file(file_path):
                self.video_path_input.setText(file_path)
                self.video_drop_area.setText(f"已选择: {Path(file_path).name}")
            else:
                QMessageBox.warning(self, "警告", "请选择有效的视频文件")
        
        # 恢复样式
        self.video_drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
        """)
    
    def is_image_file(self, file_path: str) -> bool:
        """检查是否为图像文件"""
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
        return Path(file_path).suffix.lower() in image_extensions
    
    def is_audio_file(self, file_path: str) -> bool:
        """检查是否为音频文件"""
        audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma'}
        return Path(file_path).suffix.lower() in audio_extensions
    
    def is_video_file(self, file_path: str) -> bool:
        """检查是否为视频文件"""
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        return Path(file_path).suffix.lower() in video_extensions
    
    def start_search_worker(self):
        """启动搜索工作线程"""
        if self.search_thread and self.search_thread.isRunning():
            self.stop_search()
        
        # 创建工作线程
        self.search_thread = QThread()
        self.search_worker = SearchWorker()
        self.search_worker.moveToThread(self.search_thread)
        
        # 连接信号
        self.search_worker.search_completed.connect(self.on_search_completed)
        self.search_worker.search_failed.connect(self.on_search_failed)
        self.search_worker.progress_updated.connect(self.on_search_progress_updated)
        
        # 启动线程
        self.search_thread.start()
    
    def stop_search(self):
        """停止搜索"""
        if self.search_worker:
            self.search_worker.stop_search()
        
        if self.search_thread:
            self.search_thread.quit()
            self.search_thread.wait()
        
        self.search_progress.setVisible(False)
        self.enable_search_controls(True)
    
    def enable_search_controls(self, enabled: bool):
        """启用/禁用搜索控件"""
        self.text_search_button.setEnabled(enabled)
        self.image_search_button.setEnabled(enabled)
        self.audio_search_button.setEnabled(enabled)
        self.video_search_button.setEnabled(enabled)
        self.multimodal_search_button.setEnabled(enabled)
    
    def perform_text_search(self):
        """执行文本搜索"""
        query = self.text_search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "警告", "请输入搜索关键词")
            return
        
        # 添加到搜索历史
        self.add_to_search_history(f"文本: {query}")
        
        # 启动搜索
        self.start_search_worker()
        
        # 显示进度条
        self.search_progress.setVisible(True)
        self.search_progress.setRange(0, 0)
        self.enable_search_controls(False)
        
        # 执行搜索
        QTimer.singleShot(100, lambda: self.search_worker.perform_text_search(query, self.text_result_limit.value()))
        
        self.status_message_changed.emit(f"正在搜索: {query}")
    
    def perform_image_search(self):
        """执行图像搜索"""
        file_path = self.image_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择图像文件")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "文件不存在")
            return
        
        # 添加到搜索历史
        self.add_to_search_history(f"图像: {Path(file_path).name}")
        
        # 启动搜索
        self.start_search_worker()
        
        # 显示进度条
        self.search_progress.setVisible(True)
        self.search_progress.setRange(0, 0)
        self.enable_search_controls(False)
        
        # 执行搜索
        QTimer.singleShot(100, lambda: self.search_worker.perform_image_search(file_path, self.image_result_limit.value()))
        
        self.status_message_changed.emit(f"正在搜索图像: {Path(file_path).name}")
    
    def perform_audio_search(self):
        """执行音频搜索"""
        file_path = self.audio_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择音频文件")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "文件不存在")
            return
        
        # 添加到搜索历史
        self.add_to_search_history(f"音频: {Path(file_path).name}")
        
        # 启动搜索
        self.start_search_worker()
        
        # 显示进度条
        self.search_progress.setVisible(True)
        self.search_progress.setRange(0, 0)
        self.enable_search_controls(False)
        
        # 执行搜索
        QTimer.singleShot(100, lambda: self.search_worker.perform_audio_search(file_path, self.audio_result_limit.value()))
        
        self.status_message_changed.emit(f"正在搜索音频: {Path(file_path).name}")
    
    def perform_video_search(self):
        """执行视频搜索"""
        file_path = self.video_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择视频文件")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "文件不存在")
            return
        
        # 添加到搜索历史
        self.add_to_search_history(f"视频: {Path(file_path).name}")
        
        # 启动搜索
        self.start_search_worker()
        
        # 显示进度条
        self.search_progress.setVisible(True)
        self.search_progress.setRange(0, 0)
        self.enable_search_controls(False)
        
        # 执行搜索
        QTimer.singleShot(100, lambda: self.search_worker.perform_video_search(file_path, self.video_result_limit.value()))
        
        self.status_message_changed.emit(f"正在搜索视频: {Path(file_path).name}")
    
    def perform_multimodal_search(self):
        """执行多模态搜索"""
        text_query = self.multimodal_text_input.text().strip()
        image_path = self.multimodal_image_input.text().strip()
        audio_path = self.multimodal_audio_input.text().strip()
        video_path = self.multimodal_video_input.text().strip()
        
        if not any([text_query, image_path, audio_path, video_path]):
            QMessageBox.warning(self, "警告", "请至少提供一种查询条件")
            return
        
        # 检查文件是否存在
        for path in [image_path, audio_path, video_path]:
            if path and not os.path.exists(path):
                QMessageBox.warning(self, "警告", f"文件不存在: {path}")
                return
        
        # 构建搜索历史记录
        history_parts = []
        if text_query:
            history_parts.append(f"文本: {text_query}")
        if image_path:
            history_parts.append(f"图像: {Path(image_path).name}")
        if audio_path:
            history_parts.append(f"音频: {Path(audio_path).name}")
        if video_path:
            history_parts.append(f"视频: {Path(video_path).name}")
        
        self.add_to_search_history(f"多模态: {', '.join(history_parts)}")
        
        # 启动搜索
        self.start_search_worker()
        
        # 显示进度条
        self.search_progress.setVisible(True)
        self.search_progress.setRange(0, 0)
        self.enable_search_controls(False)
        
        # 执行搜索
        QTimer.singleShot(100, lambda: self.search_worker.perform_multimodal_search(
            text_query, image_path, audio_path, video_path, self.multimodal_result_limit.value()
        ))
        
        self.status_message_changed.emit("正在进行多模态搜索...")
    
    def on_search_completed(self, results: List[Dict[str, Any]]):
        """搜索完成事件"""
        self.current_results = results
        self.update_results_table(results)
        
        self.search_progress.setVisible(False)
        self.enable_search_controls(True)
        
        self.status_message_changed.emit(f"搜索完成，找到 {len(results)} 个结果")
    
    def on_search_failed(self, error_message: str):
        """搜索失败事件"""
        self.search_progress.setVisible(False)
        self.enable_search_controls(True)
        
        QMessageBox.critical(self, "搜索失败", f"搜索失败: {error_message}")
        self.status_message_changed.emit(f"搜索失败: {error_message}")
    
    def on_search_progress_updated(self, progress: int):
        """搜索进度更新事件"""
        self.search_progress.setRange(0, 100)
        self.search_progress.setValue(progress)
    
    def update_results_table(self, results: List[Dict[str, Any]]):
        """更新结果表格"""
        self.results_table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # 文件路径
            self.results_table.setItem(row, 0, self.create_table_item(result["file_path"]))
            
            # 文件类型
            self.results_table.setItem(row, 1, self.create_table_item(result["file_type"]))
            
            # 相似度
            score_text = f"{result['score']:.2%}"
            self.results_table.setItem(row, 2, self.create_table_item(score_text))
            
            # 开始时间
            start_time = result.get("start_time_ms", 0)
            start_time_text = self.format_timestamp(start_time)
            self.results_table.setItem(row, 3, self.create_table_item(start_time_text))
            
            # 结束时间
            end_time = result.get("end_time_ms", 0)
            end_time_text = self.format_timestamp(end_time)
            self.results_table.setItem(row, 4, self.create_table_item(end_time_text))
            
            # 操作按钮
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            play_button = QPushButton("播放")
            play_button.clicked.connect(lambda checked, r=result: self.play_result(r))
            action_layout.addWidget(play_button)
            
            self.results_table.setCellWidget(row, 5, action_widget)
        
        # 调整列宽
        self.results_table.resizeColumnsToContents()
    
    def create_table_item(self, text: str):
        """创建表格项"""
        from PySide6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item
    
    def format_timestamp(self, ms: int) -> str:
        """格式化时间戳"""
        if ms <= 0:
            return ""
        
        total_seconds = ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        return f"{minutes:02d}:{seconds:02d}"
    
    def add_to_search_history(self, query: str):
        """添加到搜索历史"""
        if query not in self.search_history:
            self.search_history.append(query)
            
            # 更新历史显示
            history_text = "\n".join(self.search_history[-10:])  # 只显示最近10条
            self.text_history_list.setText(history_text)
    
    def open_selected_file(self):
        """打开选中的文件"""
        selected_rows = self.results_table.selectedItems()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if row < len(self.current_results):
            result = self.current_results[row]
            file_path = result["file_path"]
            
            if os.path.exists(file_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            else:
                QMessageBox.warning(self, "警告", f"文件不存在: {file_path}")
    
    def open_selected_folder(self):
        """打开选中文件的文件夹"""
        selected_rows = self.results_table.selectedItems()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if row < len(self.current_results):
            result = self.current_results[row]
            file_path = result["file_path"]
            
            if os.path.exists(file_path):
                folder_path = os.path.dirname(file_path)
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
            else:
                QMessageBox.warning(self, "警告", f"文件不存在: {file_path}")
    
    def copy_selected_path(self):
        """复制选中文件的路径"""
        selected_rows = self.results_table.selectedItems()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if row < len(self.current_results):
            result = self.current_results[row]
            file_path = result["file_path"]
            
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(file_path)
            
            self.status_message_changed.emit("路径已复制到剪贴板")
    
    def play_result(self, result: Dict[str, Any]):
        """播放结果"""
        file_path = result["file_path"]
        
        if os.path.exists(file_path):
            # 如果有时间戳，可以添加时间戳参数
            start_time = result.get("start_time_ms", 0)
            if start_time > 0:
                # TODO: 实现带时间戳的播放
                pass
            
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            QMessageBox.warning(self, "警告", f"文件不存在: {file_path}")
    
    def clear_results(self):
        """清空结果"""
        self.current_results = []
        self.results_table.setRowCount(0)
        self.status_message_changed.emit("结果已清空")
    
    def refresh(self):
        """刷新界面"""
        # 清空搜索输入
        self.text_search_input.clear()
        self.image_path_input.clear()
        self.audio_path_input.clear()
        self.video_path_input.clear()
        self.multimodal_text_input.clear()
        self.multimodal_image_input.clear()
        self.multimodal_audio_input.clear()
        self.multimodal_video_input.clear()
        
        # 重置拖放区域文本
        self.image_drop_area.setText("拖拽图像文件到此处")
        self.audio_drop_area.setText("拖拽音频文件到此处")
        self.video_drop_area.setText("拖拽视频文件到此处")
        
        # 清空结果
        self.clear_results()
        
        self.status_message_changed.emit("界面已刷新")