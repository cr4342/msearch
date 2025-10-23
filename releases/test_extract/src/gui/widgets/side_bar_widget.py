#!/usr/bin/env python3
"""
msearch PySide6侧边栏组件
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QButtonGroup,
    QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QFont

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class SideBarWidget(QWidget):
    """侧边栏组件"""
    
    # 页面切换信号
    page_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化UI
        self.init_ui()
        
        # 初始化状态
        self.init_state()
        
        # 应用样式
        self.apply_styles()
        
        logger.info("侧边栏组件初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 标题
        title_label = QLabel("msearch")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("sidebar_title")
        main_layout.addWidget(title_label)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # 按钮组
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)
        self.button_group.buttonClicked.connect(self.on_button_clicked)
        
        # 创建导航按钮
        self.create_nav_buttons(main_layout)
        
        # 添加弹性空间
        main_layout.addStretch()
        
        # 状态信息
        status_label = QLabel("状态: 就绪")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setObjectName("sidebar_status")
        main_layout.addWidget(status_label)
    
    def create_nav_buttons(self, parent_layout):
        """创建导航按钮"""
        # 页面定义
        pages = [
            ("search", "搜索", "🔍"),
            ("files", "文件", "📁"),
            ("timeline", "时间线", "⏱️"),
            ("faces", "人脸", "👤"),
            ("config", "设置", "⚙️")
        ]
        
        self.buttons = {}
        
        for page_id, page_name, icon in pages:
            button = QPushButton(f"{icon} {page_name}")
            button.setCheckable(True)
            button.setObjectName(f"nav_button_{page_id}")
            button.setProperty("page_id", page_id)
            
            # 设置按钮大小策略
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setMinimumHeight(40)
            
            # 添加到按钮组
            self.button_group.addButton(button)
            self.buttons[page_id] = button
            
            parent_layout.addWidget(button)
        
        # 默认选中第一个按钮
        if self.buttons:
            first_button = list(self.buttons.values())[0]
            first_button.setChecked(True)
    
    def init_state(self):
        """初始化状态"""
        self.current_page = "search"
    
    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            #sidebar_title {
                font-size: 18px;
                font-weight: bold;
                color: #303133;
                padding: 15px 0;
                background-color: #f5f7fa;
            }
            
            #sidebar_status {
                font-size: 12px;
                color: #909399;
                padding: 10px 0;
                background-color: #f5f7fa;
            }
            
            QPushButton {
                text-align: left;
                padding: 10px 20px;
                border: none;
                background-color: transparent;
                font-size: 14px;
                color: #606266;
            }
            
            QPushButton:hover {
                background-color: #ecf5ff;
                color: #409EFF;
            }
            
            QPushButton:checked {
                background-color: #409EFF;
                color: white;
                font-weight: bold;
            }
            
            QPushButton::icon {
                padding-right: 10px;
            }
        """)
    
    def on_button_clicked(self, button):
        """按钮点击事件"""
        page_id = button.property("page_id")
        if page_id and page_id != self.current_page:
            self.current_page = page_id
            self.page_changed.emit(page_id)
            logger.info(f"切换到页面: {page_id}")
    
    def set_page(self, page_id: str):
        """设置当前页面"""
        if page_id in self.buttons:
            button = self.buttons[page_id]
            button.setChecked(True)
            self.current_page = page_id
            self.page_changed.emit(page_id)
    
    def set_status(self, status_text: str):
        """设置状态文本"""
        # 查找状态标签并更新文本
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QLabel) and widget.objectName() == "sidebar_status":
                    widget.setText(status_text)
                    break