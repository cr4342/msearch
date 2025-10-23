#!/usr/bin/env python3
"""
msearch PySide6主题管理器
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
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


class ThemeManager:
    """主题管理器"""
    
    def __init__(self):
        """初始化主题管理器"""
        self.current_theme = "light"
        logger.info("主题管理器初始化完成")
    
    def apply_theme(self, theme_name: str):
        """应用主题"""
        self.current_theme = theme_name
        
        if theme_name == "dark":
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
        
        logger.info(f"主题已应用: {theme_name}")
    
    def _apply_light_theme(self):
        """应用浅色主题"""
        # 浅色主题样式
        light_stylesheet = """
            QMainWindow {
                background-color: #ffffff;
            }
            
            QWidget {
                background-color: #ffffff;
                color: #303133;
            }
            
            QMenuBar {
                background-color: #f5f7fa;
                color: #303133;
                border-bottom: 1px solid #dcdfe6;
            }
            
            QMenuBar::item {
                background: transparent;
                padding: 4px 8px;
            }
            
            QMenuBar::item:selected {
                background: #ecf5ff;
            }
            
            QMenuBar::item:pressed {
                background: #409EFF;
                color: white;
            }
            
            QMenu {
                background-color: #ffffff;
                border: 1px solid #dcdfe6;
            }
            
            QMenu::item {
                padding: 4px 20px;
            }
            
            QMenu::item:selected {
                background-color: #ecf5ff;
            }
            
            QToolBar {
                background-color: #f5f7fa;
                border-bottom: 1px solid #dcdfe6;
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
                background-color: #ffffff;
            }
            
            QLineEdit:focus {
                border-color: #409EFF;
            }
            
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
                color: #303133;
            }
            
            QTableWidget {
                gridline-color: #e4e7ed;
                selection-background-color: #f5f7fa;
                alternate-background-color: #fafafa;
            }
            
            QHeaderView::section {
                background-color: #f5f7fa;
                padding: 8px;
                border: 1px solid #e4e7ed;
                font-weight: bold;
            }
            
            QTabWidget::pane {
                border: 1px solid #dcdfe6;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #f5f7fa;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #dcdfe6;
                border-bottom: none;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #409EFF;
            }
            
            QScrollBar:vertical {
                background: #f5f7fa;
                width: 15px;
                border: 1px solid #dcdfe6;
            }
            
            QScrollBar::handle:vertical {
                background: #c0c4cc;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #a8abb2;
            }
        """
        
        # 应用样式表
        QApplication.instance().setStyleSheet(light_stylesheet)
    
    def _apply_dark_theme(self):
        """应用深色主题"""
        # 深色主题样式
        dark_stylesheet = """
            QMainWindow {
                background-color: #1d1e1f;
            }
            
            QWidget {
                background-color: #1d1e1f;
                color: #e5eaf3;
            }
            
            QMenuBar {
                background-color: #2d2e2f;
                color: #e5eaf3;
                border-bottom: 1px solid #3d3e3f;
            }
            
            QMenuBar::item {
                background: transparent;
                padding: 4px 8px;
            }
            
            QMenuBar::item:selected {
                background: #3d3e3f;
            }
            
            QMenuBar::item:pressed {
                background: #409EFF;
                color: white;
            }
            
            QMenu {
                background-color: #2d2e2f;
                border: 1px solid #3d3e3f;
            }
            
            QMenu::item {
                padding: 4px 20px;
                color: #e5eaf3;
            }
            
            QMenu::item:selected {
                background-color: #3d3e3f;
            }
            
            QToolBar {
                background-color: #2d2e2f;
                border-bottom: 1px solid #3d3e3f;
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
                background-color: #4d4d4d;
                color: #8c8c8c;
            }
            
            QLineEdit {
                padding: 8px;
                border: 1px solid #3d3e3f;
                border-radius: 4px;
                background-color: #2d2e2f;
                color: #e5eaf3;
            }
            
            QLineEdit:focus {
                border-color: #409EFF;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3d3e3f;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #e5eaf3;
            }
            
            QTableWidget {
                gridline-color: #3d3e3f;
                selection-background-color: #3d3e3f;
                alternate-background-color: #252627;
                background-color: #1d1e1f;
                color: #e5eaf3;
            }
            
            QHeaderView::section {
                background-color: #2d2e2f;
                padding: 8px;
                border: 1px solid #3d3e3f;
                font-weight: bold;
                color: #e5eaf3;
            }
            
            QTabWidget::pane {
                border: 1px solid #3d3e3f;
                background-color: #1d1e1f;
            }
            
            QTabBar::tab {
                background-color: #2d2e2f;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #3d3e3f;
                border-bottom: none;
                color: #e5eaf3;
            }
            
            QTabBar::tab:selected {
                background-color: #1d1e1f;
                border-bottom: 2px solid #409EFF;
            }
            
            QScrollBar:vertical {
                background: #2d2e2f;
                width: 15px;
                border: 1px solid #3d3e3f;
            }
            
            QScrollBar::handle:vertical {
                background: #4d4d4d;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #6d6d6d;
            }
        """
        
        # 应用样式表
        QApplication.instance().setStyleSheet(dark_stylesheet)
    
    def get_current_theme(self) -> str:
        """获取当前主题"""
        return self.current_theme
    
    def is_dark_theme(self) -> bool:
        """检查是否为深色主题"""
        return self.current_theme == "dark"