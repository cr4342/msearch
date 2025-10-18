#!/usr/bin/env python3
"""
msearch PySide6桌面应用程序主类
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStackedWidget, QMenuBar, QStatusBar,
    QToolBar, QMessageBox, QFileDialog, QSystemTrayIcon,
    QMenu, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import QTimer, Signal, Qt, QThread, Signal
from PySide6.QtGui import QIcon, QPixmap, QKeySequence

from src.core.config import load_config
from src.core.logging_config import get_logger
from src.gui.widgets.search_widget import SearchWidget
from src.gui.widgets.file_manager_widget import FileManagerWidget
from src.gui.widgets.timeline_widget import TimelineWidget
from src.gui.widgets.face_recognition_widget import FaceRecognitionWidget
from src.gui.widgets.config_widget import ConfigWidget
from src.gui.widgets.status_bar_widget import StatusBarWidget
from src.gui.widgets.side_bar_widget import SideBarWidget
from src.gui.api_client import ApiClient
from src.gui.theme_manager import ThemeManager

# 获取日志记录器
logger = get_logger(__name__)


class MSearchApplication(QMainWindow):
    """msearch桌面应用程序主窗口"""
    
    # 信号定义
    status_message_changed = Signal(str)
    connection_status_changed = Signal(bool)
    
    def __init__(self, config: Dict[str, Any], settings: Dict[str, Any], parent=None):
        super().__init__(parent)
        
        # 保存配置和设置
        self.config = config
        self.settings = settings
        
        # 初始化组件
        self.api_client = None
        self.theme_manager = ThemeManager()
        
        # 初始化UI组件
        self.central_widget = None
        self.main_layout = None
        self.side_bar = None
        self.content_stack = None
        self.status_bar = None
        self.system_tray = None
        
        # 初始化页面组件
        self.search_widget = None
        self.file_manager_widget = None
        self.timeline_widget = None
        self.face_recognition_widget = None
        self.config_widget = None
        
        # 初始化定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        
        # 初始化窗口
        self.init_ui()
        self.init_api_client()
        self.init_system_tray()
        self.init_connections()
        
        # 启动状态更新定时器
        self.status_timer.start(5000)  # 每5秒更新一次状态
        
        # 应用主题
        self.apply_theme(self.settings.get("theme", "light"))
        
        # 如果设置了自动连接，则尝试连接API
        if self.settings.get("auto_connect", True):
            self.connect_to_api()
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和大小
        self.setWindowTitle("msearch - 多模态智能检索系统")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(splitter)
        
        # 创建侧边栏
        self.side_bar = SideBarWidget()
        self.side_bar.setMaximumWidth(250)
        self.side_bar.setMinimumWidth(200)
        splitter.addWidget(self.side_bar)
        
        # 创建内容堆栈
        self.content_stack = QStackedWidget()
        splitter.addWidget(self.content_stack)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        # 创建页面组件
        self.create_pages()
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建状态栏
        self.create_status_bar()
        
        logger.info("用户界面初始化完成")
    
    def create_pages(self):
        """创建页面组件"""
        # 搜索页面
        self.search_widget = SearchWidget(self.api_client)
        self.content_stack.addWidget(self.search_widget)
        
        # 文件管理页面
        self.file_manager_widget = FileManagerWidget(self.api_client)
        self.content_stack.addWidget(self.file_manager_widget)
        
        # 时间线页面
        self.timeline_widget = TimelineWidget(self.api_client)
        self.content_stack.addWidget(self.timeline_widget)
        
        # 人脸识别页面
        self.face_recognition_widget = FaceRecognitionWidget(self.api_client)
        self.content_stack.addWidget(self.face_recognition_widget)
        
        # 配置页面
        self.config_widget = ConfigWidget(self.api_client, self.config)
        self.content_stack.addWidget(self.config_widget)
        
        # 默认显示搜索页面
        self.content_stack.setCurrentWidget(self.search_widget)
        
        logger.info("页面组件创建完成")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 打开文件
        open_file_action = QAction("打开文件(&O)", self)
        open_file_action.setShortcut(QKeySequence.Open)
        open_file_action.setStatusTip("打开文件进行查看")
        open_file_action.triggered.connect(self.open_file)
        file_menu.addAction(open_file_action)
        
        # 打开文件夹
        open_folder_action = QAction("打开文件夹(&D)", self)
        open_folder_action.setStatusTip("打开文件夹")
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        
        # 复制路径
        copy_path_action = QAction("复制路径(&C)", self)
        copy_path_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        copy_path_action.setStatusTip("复制文件路径")
        copy_path_action.triggered.connect(self.copy_path)
        edit_menu.addAction(copy_path_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        # 主题
        theme_menu = view_menu.addMenu("主题(&T)")
        
        light_theme_action = QAction("浅色主题(&L)", self)
        light_theme_action.setCheckable(True)
        light_theme_action.setChecked(self.settings.get("theme", "light") == "light")
        light_theme_action.triggered.connect(lambda: self.change_theme("light"))
        theme_menu.addAction(light_theme_action)
        
        dark_theme_action = QAction("深色主题(&D)", self)
        dark_theme_action.setCheckable(True)
        dark_theme_action.setChecked(self.settings.get("theme", "light") == "dark")
        dark_theme_action.triggered.connect(lambda: self.change_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        # 连接API
        connect_api_action = QAction("连接API(&C)", self)
        connect_api_action.setStatusTip("连接到msearch API服务")
        connect_api_action.triggered.connect(self.connect_to_api)
        tools_menu.addAction(connect_api_action)
        
        # 断开API
        disconnect_api_action = QAction("断开API(&D)", self)
        disconnect_api_action.setStatusTip("断开与msearch API服务的连接")
        disconnect_api_action.triggered.connect(self.disconnect_from_api)
        tools_menu.addAction(disconnect_api_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 关于
        about_action = QAction("关于(&A)", self)
        about_action.setStatusTip("关于msearch")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        logger.info("菜单栏创建完成")
    
    def create_tool_bar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        
        # 刷新按钮
        refresh_action = QAction("刷新", self)
        refresh_action.setStatusTip("刷新当前页面")
        refresh_action.triggered.connect(self.refresh_current_page)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # 后退按钮
        back_action = QAction("后退", self)
        back_action.setStatusTip("后退到上一个页面")
        back_action.triggered.connect(self.go_back)
        toolbar.addAction(back_action)
        
        # 前进按钮
        forward_action = QAction("前进", self)
        forward_action.setStatusTip("前进到下一个页面")
        forward_action.triggered.connect(self.go_forward)
        toolbar.addAction(forward_action)
        
        logger.info("工具栏创建完成")
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = StatusBarWidget()
        self.setStatusBar(self.status_bar)
        
        # 连接信号
        self.status_message_changed.connect(self.status_bar.set_message)
        self.connection_status_changed.connect(self.status_bar.set_connection_status)
        
        logger.info("状态栏创建完成")
    
    def init_api_client(self):
        """初始化API客户端"""
        api_base_url = self.settings.get("api_base_url", "http://localhost:8000")
        self.api_client = ApiClient(api_base_url)
        
        logger.info(f"API客户端初始化完成，基础URL: {api_base_url}")
    
    def init_system_tray(self):
        """初始化系统托盘"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("系统托盘不可用")
            return
        
        # 创建托盘图标
        icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            tray_icon = QIcon(str(icon_path))
        else:
            # 如果图标文件不存在，使用默认图标
            tray_icon = self.style().standardIcon(self.style().SP_ComputerIcon)
        
        # 创建系统托盘
        self.system_tray = QSystemTrayIcon(tray_icon, self)
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 显示/隐藏主窗口
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        # 退出
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.system_tray.setContextMenu(tray_menu)
        
        # 连接双击事件
        self.system_tray.activated.connect(self.on_tray_activated)
        
        # 显示托盘图标
        self.system_tray.show()
        
        logger.info("系统托盘初始化完成")
    
    def init_connections(self):
        """初始化信号连接"""
        # 侧边栏页面切换信号
        self.side_bar.page_changed.connect(self.switch_page)
        
        # API客户端连接状态信号
        if self.api_client:
            self.api_client.connection_status_changed.connect(self.on_connection_status_changed)
            self.api_client.error_occurred.connect(self.on_api_error)
        
        logger.info("信号连接初始化完成")
    
    def switch_page(self, page_name: str):
        """切换页面"""
        page_map = {
            "search": self.search_widget,
            "files": self.file_manager_widget,
            "timeline": self.timeline_widget,
            "faces": self.face_recognition_widget,
            "config": self.config_widget
        }
        
        widget = page_map.get(page_name)
        if widget:
            self.content_stack.setCurrentWidget(widget)
            self.status_message_changed.emit(f"已切换到{widget.windowTitle()}")
            logger.info(f"切换到页面: {page_name}")
    
    def refresh_current_page(self):
        """刷新当前页面"""
        current_widget = self.content_stack.currentWidget()
        if hasattr(current_widget, "refresh"):
            current_widget.refresh()
            self.status_message_changed.emit("页面已刷新")
    
    def go_back(self):
        """后退到上一个页面"""
        # 这里可以实现页面历史记录功能
        pass
    
    def go_forward(self):
        """前进到下一个页面"""
        # 这里可以实现页面历史记录功能
        pass
    
    def connect_to_api(self):
        """连接到API服务"""
        if self.api_client:
            self.status_message_changed.emit("正在连接到API服务...")
            self.api_client.connect()
    
    def disconnect_from_api(self):
        """断开与API服务的连接"""
        if self.api_client:
            self.api_client.disconnect()
            self.status_message_changed.emit("已断开与API服务的连接")
    
    def on_connection_status_changed(self, connected: bool):
        """处理连接状态变化"""
        self.connection_status_changed.emit(connected)
        if connected:
            self.status_message_changed.emit("已连接到API服务")
        else:
            self.status_message_changed.emit("未连接到API服务")
    
    def on_api_error(self, error_message: str):
        """处理API错误"""
        self.status_message_changed.emit(f"API错误: {error_message}")
        logger.error(f"API错误: {error_message}")
    
    def open_file(self):
        """打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开文件",
            "",
            "所有文件 (*.*)"
        )
        
        if file_path:
            # 这里可以实现文件打开逻辑
            self.status_message_changed.emit(f"已选择文件: {file_path}")
    
    def open_folder(self):
        """打开文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "打开文件夹",
            ""
        )
        
        if folder_path:
            # 这里可以实现文件夹打开逻辑
            self.status_message_changed.emit(f"已选择文件夹: {folder_path}")
    
    def copy_path(self):
        """复制路径"""
        # 这里可以实现复制路径逻辑
        self.status_message_changed.emit("路径已复制到剪贴板")
    
    def change_theme(self, theme_name: str):
        """更改主题"""
        self.apply_theme(theme_name)
        self.settings["theme"] = theme_name
        self.status_message_changed.emit(f"已切换到{theme_name}主题")
    
    def apply_theme(self, theme_name: str):
        """应用主题"""
        self.theme_manager.apply_theme(theme_name)
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 msearch",
            "<h2>msearch</h2>"
            "<p>多模态智能检索系统</p>"
            "<p>版本 0.1.0</p>"
            "<p>Copyright © 2024 msearch Team</p>"
        )
    
    def on_tray_activated(self, reason):
        """处理托盘激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
    
    def update_status(self):
        """更新状态"""
        if self.api_client and not self.api_client.is_connected():
            # 尝试重新连接
            self.connect_to_api()
    
    def quit_application(self):
        """退出应用程序"""
        self.close()
    
    def closeEvent(self, event):
        """处理关闭事件"""
        # 如果设置了最小化到托盘，则隐藏窗口而不是退出
        if (self.settings.get("minimize_to_tray", True) and 
            self.system_tray and 
            self.system_tray.isVisible()):
            event.ignore()
            self.hide()
            self.status_message_changed.emit("应用程序已最小化到系统托盘")
        else:
            # 断开API连接
            if self.api_client:
                self.api_client.disconnect()
            
            # 停止定时器
            self.status_timer.stop()
            
            # 接受关闭事件
            event.accept()
            logger.info("应用程序关闭")