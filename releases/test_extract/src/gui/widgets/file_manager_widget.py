#!/usr/bin/env python3
"""
msearch PySide6文件管理器组件
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
    QTreeWidget, QTreeWidgetItem, QHeaderView
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


class FileManagerWidget(QWidget):
    """文件管理器组件"""
    
    # 信号定义
    status_message_changed = Signal(str)
    file_selected = Signal(str)  # 文件被选中
    
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
        
        logger.info("文件管理器组件初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建文件浏览选项卡
        self.create_file_browser_tab()
        
        # 创建文件处理选项卡
        self.create_file_processing_tab()
    
    def create_file_browser_tab(self):
        """创建文件浏览选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文件路径输入区域
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("路径:"))
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("输入文件路径...")
        self.path_input.returnPressed.connect(self.browse_path)
        path_layout.addWidget(self.path_input)
        
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_button)
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_file_list)
        path_layout.addWidget(refresh_button)
        
        layout.addLayout(path_layout)
        
        # 文件树
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["名称", "类型", "大小", "修改时间"])
        self.file_tree.setSortingEnabled(True)
        self.file_tree.sortByColumn(0, Qt.AscendingOrder)
        self.file_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.file_tree)
        
        self.tab_widget.addTab(tab, "文件浏览")
    
    def create_file_processing_tab(self):
        """创建文件处理选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文件处理区域
        process_group = QGroupBox("文件处理")
        process_layout = QVBoxLayout(process_group)
        
        # 文件路径输入
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("文件路径:"))
        
        self.process_path_input = QLineEdit()
        self.process_path_input.setPlaceholderText("选择要处理的文件...")
        self.process_path_input.setReadOnly(True)
        path_layout.addWidget(self.process_path_input)
        
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_process_file)
        path_layout.addWidget(browse_button)
        
        process_layout.addLayout(path_layout)
        
        # 处理选项
        options_layout = QHBoxLayout()
        
        # 处理按钮
        self.process_button = QPushButton("处理文件")
        self.process_button.clicked.connect(self.process_file)
        options_layout.addWidget(self.process_button)
        
        # 处理状态
        self.process_status = QLabel("状态: 就绪")
        options_layout.addWidget(self.process_status)
        
        options_layout.addStretch()
        
        process_layout.addLayout(options_layout)
        
        # 进度条
        self.process_progress = QProgressBar()
        self.process_progress.setVisible(False)
        process_layout.addWidget(self.process_progress)
        
        layout.addWidget(process_group)
        
        # 处理历史
        history_group = QGroupBox("处理历史")
        history_layout = QVBoxLayout(history_group)
        
        self.history_list = QTextEdit()
        self.history_list.setMaximumHeight(150)
        self.history_list.setReadOnly(True)
        history_layout.addWidget(self.history_list)
        
        layout.addWidget(history_group)
        
        self.tab_widget.addTab(tab, "文件处理")
    
    def init_state(self):
        """初始化状态"""
        self.current_path = ""
        self.process_history = []
    
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
            
            QTreeWidget {
                gridline-color: #e4e7ed;
                selection-background-color: #f5f7fa;
            }
            
            QHeaderView::section {
                background-color: #f5f7fa;
                padding: 8px;
                border: 1px solid #e4e7ed;
            }
        """)
    
    def browse_path(self):
        """浏览路径"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择文件夹", self.path_input.text() or ""
        )
        
        if folder_path:
            self.path_input.setText(folder_path)
            self.load_file_list(folder_path)
    
    def browse_process_file(self):
        """浏览要处理的文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", 
            "所有文件 (*.*)"
        )
        if file_path:
            self.process_path_input.setText(file_path)
    
    def load_file_list(self, path: str):
        """加载文件列表"""
        try:
            if not os.path.exists(path):
                QMessageBox.warning(self, "警告", f"路径不存在: {path}")
                return
            
            self.current_path = path
            self.file_tree.clear()
            
            # 添加父目录项
            if os.path.dirname(path):
                parent_item = QTreeWidgetItem(["..", "目录", "", ""])
                parent_item.setData(0, Qt.UserRole, os.path.dirname(path))
                self.file_tree.addTopLevelItem(parent_item)
            
            # 遍历目录内容
            try:
                for item_name in os.listdir(path):
                    item_path = os.path.join(path, item_name)
                    is_dir = os.path.isdir(item_path)
                    
                    # 获取文件信息
                    stat_info = os.stat(item_path)
                    size = stat_info.st_size
                    mtime = stat_info.st_mtime
                    
                    # 格式化大小
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    elif size < 1024 * 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.1f} MB"
                    else:
                        size_str = f"{size / (1024 * 1024 * 1024):.1f} GB"
                    
                    # 格式化时间
                    from datetime import datetime
                    mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 创建树项
                    item_type = "目录" if is_dir else "文件"
                    item = QTreeWidgetItem([item_name, item_type, size_str, mtime_str])
                    item.setData(0, Qt.UserRole, item_path)
                    
                    # 设置图标
                    if is_dir:
                        item.setIcon(0, self.style().standardIcon(self.style().SP_DirIcon))
                    else:
                        item.setIcon(0, self.style().standardIcon(self.style().SP_FileIcon))
                    
                    self.file_tree.addTopLevelItem(item)
                
                self.status_message_changed.emit(f"已加载 {self.file_tree.topLevelItemCount()} 个项目")
            except PermissionError:
                QMessageBox.warning(self, "警告", f"没有权限访问目录: {path}")
        except Exception as e:
            logger.error(f"加载文件列表失败: {e}")
            QMessageBox.critical(self, "错误", f"加载文件列表失败: {e}")
    
    def refresh_file_list(self):
        """刷新文件列表"""
        if self.current_path:
            self.load_file_list(self.current_path)
    
    def on_item_double_clicked(self, item, column):
        """项双击事件"""
        item_path = item.data(0, Qt.UserRole)
        if item_path:
            if os.path.isdir(item_path):
                self.load_file_list(item_path)
            else:
                # 文件被选中，发出信号
                self.file_selected.emit(item_path)
                QDesktopServices.openUrl(QUrl.fromLocalFile(item_path))
    
    def process_file(self):
        """处理文件"""
        file_path = self.process_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择要处理的文件")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "文件不存在")
            return
        
        # 如果有API客户端，调用API处理文件
        if self.api_client and self.api_client.is_connected():
            self.process_progress.setVisible(True)
            self.process_progress.setRange(0, 0)  # 无限进度条
            self.process_button.setEnabled(False)
            self.process_status.setText("状态: 处理中...")
            
            # 生成文件ID
            import uuid
            file_id = str(uuid.uuid4())
            
            # 调用API处理文件
            result = self.api_client.process_file(file_path, file_id)
            
            self.process_progress.setVisible(False)
            self.process_button.setEnabled(True)
            
            if result and result.get("status") == "success":
                self.process_status.setText("状态: 处理完成")
                self.add_to_process_history(f"处理完成: {Path(file_path).name}")
                QMessageBox.information(self, "成功", "文件处理完成")
            else:
                error_msg = result.get("message", "未知错误") if result else "API调用失败"
                self.process_status.setText("状态: 处理失败")
                self.add_to_process_history(f"处理失败: {Path(file_path).name} - {error_msg}")
                QMessageBox.critical(self, "错误", f"文件处理失败: {error_msg}")
        else:
            # 模拟处理过程
            self.process_progress.setVisible(True)
            self.process_progress.setRange(0, 0)
            self.process_button.setEnabled(False)
            self.process_status.setText("状态: 处理中...")
            
            # 模拟处理时间
            QTimer.singleShot(2000, self.on_process_completed)
    
    def on_process_completed(self):
        """处理完成回调"""
        self.process_progress.setVisible(False)
        self.process_button.setEnabled(True)
        self.process_status.setText("状态: 处理完成")
        
        file_path = self.process_path_input.text().strip()
        self.add_to_process_history(f"处理完成: {Path(file_path).name}")
        QMessageBox.information(self, "成功", "文件处理完成")
    
    def add_to_process_history(self, message: str):
        """添加到处理历史"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_entry = f"[{timestamp}] {message}"
        
        self.process_history.append(history_entry)
        
        # 更新历史显示
        history_text = "\n".join(self.process_history[-20:])  # 只显示最近20条
        self.history_list.setText(history_text)
    
    def refresh(self):
        """刷新界面"""
        # 清空输入
        self.path_input.clear()
        self.process_path_input.clear()
        self.file_tree.clear()
        
        # 重置状态
        self.process_status.setText("状态: 就绪")
        self.process_progress.setVisible(False)
        self.process_button.setEnabled(True)
        
        self.status_message_changed.emit("文件管理器界面已刷新")
