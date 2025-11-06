#!/usr/bin/env python3
"""
msearch PySide6主题管理器
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QSplitter, QMenuBar, QStatusBar, QToolBar, QDockWidget,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget, QFrame,
    QScrollArea, QProgressBar, QComboBox, QSpinBox, QCheckBox, QSlider,
    QGroupBox, QGridLayout, QFormLayout, QMessageBox, QFileDialog,
    QTreeView, QFileSystemModel, QListView, QStackedWidget, QToolButton,
    QButtonGroup, QRadioButton, QSizePolicy, QSpacerItem,
    QTableWidgetItem, QColorDialog, QFontDialog, QDialog, QListWidget, QListWidgetItem
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QObject, QSettings, QUrl, QSize, 
    QPropertyAnimation, QEasingCurve, QRect
)
from PySide6.QtGui import (
    QIcon, QPixmap, QFont, QAction, QKeySequence, QPalette, QColor,
    QDesktopServices, QTextCursor, QStandardItemModel, QStandardItem,
    QLinearGradient, QBrush, QPainter
)

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ThemeManager:
    """主题管理器"""
    
    # 预定义主题
    THEMES = {
        "light": {
            "name": "浅色主题",
            "primary_color": "#409EFF",
            "secondary_color": "#67C23A",
            "background_color": "#FFFFFF",
            "text_color": "#303133",
            "light_text_color": "#909399",
            "border_color": "#DCDFE6",
            "hover_color": "#ECF5FF"
        },
        "dark": {
            "name": "深色主题",
            "primary_color": "#409EFF",
            "secondary_color": "#67C23A",
            "background_color": "#1D1E1F",
            "text_color": "#E4E7ED",
            "light_text_color": "#909399",
            "border_color": "#4C4D4F",
            "hover_color": "#2D2E2F"
        },
        "blue": {
            "name": "蓝色主题",
            "primary_color": "#1976D2",
            "secondary_color": "#42A5F5",
            "background_color": "#F5F9FF",
            "text_color": "#1A237E",
            "light_text_color": "#5C6BC0",
            "border_color": "#90CAF9",
            "hover_color": "#E3F2FD"
        },
        "green": {
            "name": "绿色主题",
            "primary_color": "#388E3C",
            "secondary_color": "#66BB6A",
            "background_color": "#F1F8E9",
            "text_color": "#1B5E20",
            "light_text_color": "#689F38",
            "border_color": "#AED581",
            "hover_color": "#DCEDC8"
        },
        "purple": {
            "name": "紫色主题",
            "primary_color": "#7B1FA2",
            "secondary_color": "#AB47BC",
            "background_color": "#F3E5F5",
            "text_color": "#4A148C",
            "light_text_color": "#8E24AA",
            "border_color": "#CE93D8",
            "hover_color": "#E1BEE7"
        }
    }
    
    def __init__(self):
        self.current_theme = "light"
        self.custom_themes = {}
        self.app = QApplication.instance()
        
        # 加载保存的主题设置
        self.load_settings()
    
    def set_theme(self, theme_name: str):
        """设置主题"""
        if theme_name in self.THEMES:
            self.current_theme = theme_name
            theme_config = self.THEMES[theme_name]
        elif theme_name in self.custom_themes:
            self.current_theme = theme_name
            theme_config = self.custom_themes[theme_name]
        else:
            logger.warning(f"主题 {theme_name} 不存在，使用默认主题")
            theme_config = self.THEMES["light"]
        
        # 应用主题到应用程序
        self.apply_theme(theme_config)
        
        # 保存设置
        self.save_settings()
        
        logger.info(f"已切换到主题: {theme_name}")
    
    def apply_theme(self, theme_config: Dict[str, str]):
        """应用主题配置"""
        if not self.app:
            return
        
        # 设置应用程序调色板
        palette = QPalette()
        
        # 设置背景色
        bg_color = QColor(theme_config["background_color"])
        palette.setColor(QPalette.Window, bg_color)
        palette.setColor(QPalette.Base, bg_color)
        palette.setColor(QPalette.AlternateBase, bg_color.lighter(110))
        
        # 设置文本颜色
        text_color = QColor(theme_config["text_color"])
        palette.setColor(QPalette.WindowText, text_color)
        palette.setColor(QPalette.Text, text_color)
        palette.setColor(QPalette.ToolTipText, text_color)
        
        # 设置高亮颜色
        primary_color = QColor(theme_config["primary_color"])
        palette.setColor(QPalette.Highlight, primary_color)
        palette.setColor(QPalette.Button, primary_color)
        
        # 设置按钮文本颜色
        button_text_color = QColor(255, 255, 255) if self.is_dark_color(primary_color) else QColor(0, 0, 0)
        palette.setColor(QPalette.ButtonText, button_text_color)
        
        self.app.setPalette(palette)
        
        # 设置样式表
        self.app.setStyleSheet(self.generate_stylesheet(theme_config))
    
    def generate_stylesheet(self, theme_config: Dict[str, str]) -> str:
        """生成样式表"""
        return f"""
            /* 全局样式 */
            QMainWindow {{
                background-color: {theme_config["background_color"]};
            }}
            
            QWidget {{
                color: {theme_config["text_color"]};
                background-color: {theme_config["background_color"]};
            }}
            
            /* 按钮样式 */
            QPushButton {{
                background-color: {theme_config["primary_color"]};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background-color: {self.lighten_color(theme_config["primary_color"], 20)};
            }}
            
            QPushButton:pressed {{
                background-color: {self.darken_color(theme_config["primary_color"], 20)};
            }}
            
            QPushButton:disabled {{
                background-color: {self.lighten_color(theme_config["primary_color"], 50)};
                color: {theme_config["light_text_color"]};
            }}
            
            /* 输入框样式 */
            QLineEdit, QTextEdit, QComboBox, QSpinBox {{
                background-color: {self.lighten_color(theme_config["background_color"], 5)};
                border: 1px solid {theme_config["border_color"]};
                border-radius: 4px;
                padding: 5px;
                color: {theme_config["text_color"]};
            }}
            
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
                border-color: {theme_config["primary_color"]};
                selection-background-color: {theme_config["primary_color"]};
            }}
            
            /* 分组框样式 */
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {theme_config["border_color"]};
                border-radius: 5px;
                margin-top: 1ex;
                color: {theme_config["text_color"]};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
            
            /* 表格样式 */
            QTableWidget {{
                gridline-color: {theme_config["border_color"]};
                background-color: {theme_config["background_color"]};
                alternate-background-color: {self.lighten_color(theme_config["background_color"], 3)};
            }}
            
            QTableWidget::item {{
                border-right: 1px solid {theme_config["border_color"]};
                border-bottom: 1px solid {theme_config["border_color"]};
            }}
            
            QTableWidget::item:selected {{
                background-color: {theme_config["hover_color"]};
                color: {theme_config["text_color"]};
            }}
            
            QHeaderView::section {{
                background-color: {self.lighten_color(theme_config["background_color"], 10)};
                padding: 8px;
                border: 1px solid {theme_config["border_color"]};
                color: {theme_config["text_color"]};
            }}
            
            /* 进度条样式 */
            QProgressBar {{
                border: 1px solid {theme_config["border_color"]};
                border-radius: 4px;
                text-align: center;
                color: {theme_config["text_color"]};
                background-color: {self.lighten_color(theme_config["background_color"], 5)};
            }}
            
            QProgressBar::chunk {{
                background-color: {theme_config["primary_color"]};
                border-radius: 3px;
            }}
            
            /* 滚动条样式 */
            QScrollBar:vertical {{
                background: {self.lighten_color(theme_config["background_color"], 5)};
                width: 15px;
                border-radius: 4px;
            }}
            
            QScrollBar::handle:vertical {{
                background: {theme_config["border_color"]};
                border-radius: 4px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {theme_config["primary_color"]};
            }}
            
            /* 选项卡样式 */
            QTabWidget::pane {{
                border: 1px solid {theme_config["border_color"]};
                background-color: {theme_config["background_color"]};
            }}
            
            QTabBar::tab {{
                background-color: {self.lighten_color(theme_config["background_color"], 8)};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                color: {theme_config["light_text_color"]};
            }}
            
            QTabBar::tab:selected {{
                background-color: {theme_config["background_color"]};
                color: {theme_config["text_color"]};
                border-bottom: 2px solid {theme_config["primary_color"]};
            }}
            
            QTabBar::tab:hover {{
                background-color: {theme_config["hover_color"]};
            }}
            
            /* 菜单样式 */
            QMenuBar {{
                background-color: {theme_config["background_color"]};
                spacing: 3px;
            }}
            
            QMenuBar::item {{
                padding: 5px 10px;
                background: transparent;
            }}
            
            QMenuBar::item:selected {{
                background: {theme_config["hover_color"]};
            }}
            
            QMenuBar::item:pressed {{
                background: {theme_config["primary_color"]};
                color: white;
            }}
            
            QMenu {{
                background-color: {theme_config["background_color"]};
                border: 1px solid {theme_config["border_color"]};
            }}
            
            QMenu::item {{
                padding: 5px 20px;
                color: {theme_config["text_color"]};
            }}
            
            QMenu::item:selected {{
                background-color: {theme_config["hover_color"]};
            }}
            
            QMenu::separator {{
                height: 1px;
                background: {theme_config["border_color"]};
            }}
            
            /* 工具栏样式 */
            QToolBar {{
                background-color: {theme_config["background_color"]};
                border: none;
                spacing: 2px;
            }}
            
            /* 停靠窗口样式 */
            QDockWidget {{
                border: 1px solid {theme_config["border_color"]};
                titlebar-close-icon: url(:/icons/close.png);
                titlebar-normal-icon: url(:/icons/float.png);
            }}
            
            QDockWidget::title {{
                text-align: left;
                background: {theme_config["background_color"]};
                padding: 5px;
            }}
            
            /* 状态栏样式 */
            QStatusBar {{
                background-color: {theme_config["background_color"]};
                border-top: 1px solid {theme_config["border_color"]};
            }}
        """
    
    def is_dark_color(self, color: QColor) -> bool:
        """判断颜色是否为深色"""
        # 使用相对亮度公式
        luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
        return luminance < 0.5
    
    def lighten_color(self, color_str: str, percent: int) -> str:
        """使颜色变亮"""
        color = QColor(color_str)
        h, s, v, a = color.getHsv()
        v = min(255, v + int(255 * percent / 100))
        new_color = QColor.fromHsv(h, s, v, a)
        return new_color.name()
    
    def darken_color(self, color_str: str, percent: int) -> str:
        """使颜色变暗"""
        color = QColor(color_str)
        h, s, v, a = color.getHsv()
        v = max(0, v - int(255 * percent / 100))
        new_color = QColor.fromHsv(h, s, v, a)
        return new_color.name()
    
    def add_custom_theme(self, name: str, config: Dict[str, str]):
        """添加自定义主题"""
        self.custom_themes[name] = config
    
    def remove_custom_theme(self, name: str):
        """移除自定义主题"""
        if name in self.custom_themes:
            del self.custom_themes[name]
    
    def get_available_themes(self) -> Dict[str, str]:
        """获取可用主题列表"""
        all_themes = {}
        all_themes.update(self.THEMES)
        all_themes.update(self.custom_themes)
        return {name: config["name"] for name, config in all_themes.items()}
    
    def save_settings(self):
        """保存主题设置"""
        settings = QSettings("mSearch", "ThemeSettings")
        settings.setValue("current_theme", self.current_theme)
        settings.sync()
    
    def load_settings(self):
        """加载主题设置"""
        settings = QSettings("mSearch", "ThemeSettings")
        saved_theme = settings.value("current_theme", "light")
        
        if saved_theme in self.THEMES or saved_theme in self.custom_themes:
            self.current_theme = saved_theme
        else:
            self.current_theme = "light"
    
    def get_current_theme_name(self) -> str:
        """获取当前主题名称"""
        themes = self.get_available_themes()
        return themes.get(self.current_theme, self.current_theme)


class ThemeSelectorDialog(QDialog):
    """主题选择对话框"""
    
    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        
        self.setWindowTitle("主题选择")
        self.setModal(True)
        self.resize(400, 300)
        
        self.init_ui()
        self.load_themes()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 主题列表
        self.theme_list = QListWidget()
        self.theme_list.itemClicked.connect(self.on_theme_selected)
        layout.addWidget(self.theme_list)
        
        # 预览区域
        preview_group = QGroupBox("主题预览")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_widget)
        
        # 预览控件
        preview_label = QLabel("这是主题预览区域")
        preview_label.setAlignment(Qt.AlignCenter)
        
        preview_button = QPushButton("预览按钮")
        preview_line_edit = QLineEdit("预览输入框")
        preview_combo = QComboBox()
        preview_combo.addItems(["选项1", "选项2", "选项3"])
        
        self.preview_layout.addWidget(preview_label)
        self.preview_layout.addWidget(preview_button)
        self.preview_layout.addWidget(preview_line_edit)
        self.preview_layout.addWidget(preview_combo)
        
        preview_layout.addWidget(self.preview_widget)
        layout.addWidget(preview_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.custom_theme_button = QPushButton("自定义主题")
        self.custom_theme_button.clicked.connect(self.on_custom_theme)
        button_layout.addWidget(self.custom_theme_button)
        
        button_layout.addStretch()
        
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def load_themes(self):
        """加载主题列表"""
        self.theme_list.clear()
        themes = self.theme_manager.get_available_themes()
        
        for name, display_name in themes.items():
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, name)
            self.theme_list.addItem(item)
        
        # 选中当前主题
        current_theme_name = self.theme_manager.get_current_theme_name()
        for i in range(self.theme_list.count()):
            item = self.theme_list.item(i)
            if item.text() == current_theme_name:
                self.theme_list.setCurrentItem(item)
                break
    
    def on_theme_selected(self, item):
        """主题选择事件"""
        theme_name = item.data(Qt.UserRole)
        theme_config = self.get_theme_config(theme_name)
        
        # 临时应用主题以预览
        self.apply_preview_theme(theme_config)
    
    def get_theme_config(self, theme_name: str) -> Dict[str, str]:
        """获取主题配置"""
        if theme_name in self.theme_manager.THEMES:
            return self.theme_manager.THEMES[theme_name]
        elif theme_name in self.theme_manager.custom_themes:
            return self.theme_manager.custom_themes[theme_name]
        else:
            return self.theme_manager.THEMES["light"]
    
    def apply_preview_theme(self, theme_config: Dict[str, str]):
        """应用预览主题"""
        # 创建临时样式表应用到预览区域
        style = f"""
            QWidget {{
                color: {theme_config["text_color"]};
                background-color: {theme_config["background_color"]};
            }}
            QPushButton {{
                background-color: {theme_config["primary_color"]};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QLineEdit {{
                background-color: {self.theme_manager.lighten_color(theme_config["background_color"], 5)};
                border: 1px solid {theme_config["border_color"]};
                border-radius: 4px;
                padding: 5px;
                color: {theme_config["text_color"]};
            }}
        """
        self.preview_widget.setStyleSheet(style)
    
    def on_custom_theme(self):
        """自定义主题"""
        # 简单的自定义主题对话框
        color = QColorDialog.getColor()
        if color.isValid():
            theme_config = {
                "name": "自定义主题",
                "primary_color": color.name(),
                "secondary_color": "#67C23A",
                "background_color": "#FFFFFF",
                "text_color": "#303133",
                "light_text_color": "#909399",
                "border_color": "#DCDFE6",
                "hover_color": "#ECF5FF"
            }
            self.theme_manager.add_custom_theme("custom", theme_config)
            self.load_themes()


class ThemePreviewWidget(QWidget):
    """主题预览组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QHBoxLayout(self)
        
        # 创建一些控件来预览主题
        label = QLabel("主题预览")
        button = QPushButton("按钮")
        line_edit = QLineEdit("输入框")
        combo = QComboBox()
        combo.addItems(["选项1", "选项2", "选项3"])
        progress = QProgressBar()
        progress.setValue(50)
        
        layout.addWidget(label)
        layout.addWidget(button)
        layout.addWidget(line_edit)
        layout.addWidget(combo)
        layout.addWidget(progress)
        
        layout.addStretch()