#!/usr/bin/env python3
"""
msearch PySide6状态栏组件
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
    QStatusBar, QStyle
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


class StatusBarWidget(QStatusBar):
    """状态栏组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化UI
        self.init_ui()
        
        # 初始化状态
        self.init_state()
        
        # 应用样式
        self.apply_styles()
        
        logger.info("状态栏组件初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("status_label")
        self.addWidget(self.status_label, 1)
        
        # 创建连接状态标签
        self.connection_label = QLabel("未连接")
        self.connection_label.setObjectName("connection_label")
        self.connection_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.addWidget(self.connection_label)
        
        # 创建连接状态图标
        self.connection_icon = QLabel()
        self.connection_icon.setObjectName("connection_icon")
        self.connection_icon.setFixedSize(16, 16)
        self.connection_icon.setAlignment(Qt.AlignCenter)
        self.addWidget(self.connection_icon)
        
        # 设置初始状态
        self.set_connection_status(False)
    
    def init_state(self):
        """初始化状态"""
        pass
    
    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QStatusBar {
                background-color: #f5f7fa;
                border-top: 1px solid #dcdfe6;
                padding: 2px;
            }
            
            QLabel#status_label {
                color: #606266;
                font-size: 12px;
            }
            
            QLabel#connection_label {
                color: #606266;
                font-size: 12px;
                margin-right: 5px;
            }
            
            QLabel#connection_icon {
                background-color: #f56c6c;
                border-radius: 8px;
                margin-right: 5px;
            }
        """)
    
    def set_message(self, message: str):
        """设置状态消息"""
        self.status_label.setText(message)
        logger.debug(f"状态栏消息更新: {message}")
    
    def set_connection_status(self, connected: bool):
        """设置连接状态"""
        if connected:
            self.connection_label.setText("已连接")
            self.connection_label.setStyleSheet("color: #67c23a;")
            self.connection_icon.setStyleSheet("background-color: #67c23a; border-radius: 8px;")
        else:
            self.connection_label.setText("未连接")
            self.connection_label.setStyleSheet("color: #f56c6c;")
            self.connection_icon.setStyleSheet("background-color: #f56c6c; border-radius: 8px;")
        
        logger.debug(f"连接状态更新: {'已连接' if connected else '未连接'}")