"""
PySide6主窗口
msearch多模态检索系统的主界面
"""

import sys
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List

# 尝试导入PySide6模块
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTabWidget, QStatusBar, QMenuBar, QMenu, QAction,
        QSystemTrayIcon, QStyle, QMessageBox, QLabel
    )
    from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject
    from PySide6.QtGui import QIcon, QPixmap, QFont
    PYSIDE6_AVAILABLE = True
    
    from src.core.config_manager import get_config_manager
    from src.core.logging_config import setup_logging
    
    class AsyncWorker(QObject):
        """异步工作线程"""
        
        # 信号定义
        finished = Signal(object)
        error = Signal(str)
        
        def __init__(self, coro):
            super().__init__()
            self.coro = coro
        
        def run(self):
            """运行异步任务"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.coro)
                self.finished.emit(result)
            except Exception as e:
                self.error.emit(str(e))
    
    class MainWindow(QMainWindow):
        """主窗口类"""
        
        def __init__(self):
            super().__init__()
            
            # 初始化配置管理器
            self.config_manager = get_config_manager()
            
            # 设置日志
            self.logger = logging.getLogger(__name__)
            
            # 初始化UI
            self._setup_ui()
            
            # 初始化组件
            self._init_components()
            
            # 应用全局样式
            self._apply_global_styles()
        
        def _setup_ui(self):
            """设置UI"""
            # 设置窗口标题和大小
            self.setWindowTitle("msearch - 多模态检索系统")
            self.resize(1200, 800)
            
            # 居中显示
            self.center()
            
            # 初始化中央部件
            self.central_widget = QWidget()
            self.setCentralWidget(self.central_widget)
            
            # 主布局
            self.main_layout = QVBoxLayout(self.central_widget)
            self.main_layout.setContentsMargins(0, 0, 0, 0)
            self.main_layout.setSpacing(0)
        
        def _init_components(self):
            """初始化组件"""
            # 初始化菜单
            self._init_menu_bar()
            
            # 初始化标签页
            self._init_tab_widget()
            
            # 初始化状态栏
            self._init_status_bar()
            
            # 初始化系统托盘
            self._init_system_tray()
        
        def _apply_global_styles(self):
            """应用全局样式"""
            # 全局样式表
            self.setStyleSheet("""                
                /* 主窗口背景 */
                QMainWindow {
                    background-color: #f0f0f0;
                }
                
                /* 标签页样式 */
                QTabWidget::pane {
                    background: #ffffff;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    margin: 0px;
                }
                
                QTabBar::tab {
                    background: #f5f5f5;
                    color: #333333;
                    padding: 8px 16px;
                    border: 1px solid #d0d0d0;
                    border-bottom-color: #ffffff;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    min-width: 80px;
                    font-weight: 500;
                }
                
                QTabBar::tab:selected {
                    background: #ffffff;
                    color: #1a73e8;
                    border-color: #d0d0d0;
                    border-bottom-color: #ffffff;
                }
                
                QTabBar::tab:hover {
                    background: #e8f0fe;
                }
                
                /* 按钮样式 */
                QPushButton {
                    background-color: #1a73e8;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: 500;
                }
                
                QPushButton:hover {
                    background-color: #1557b0;
                }
                
                QPushButton:pressed {
                    background-color: #0d47a1;
                }
                
                /* 输入框样式 */
                QLineEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 8px;
                }
                
                QLineEdit:focus {
                    border-color: #1a73e8;
                    outline: none;
                }
                
                /* 状态栏样式 */
                QStatusBar {
                    background-color: #f5f5f5;
                    color: #333333;
                    border-top: 1px solid #d0d0d0;
                }
            """)
        
        def center(self):
            """居中显示窗口"""
            screen = QApplication.primaryScreen()
            rect = screen.availableGeometry()
            window_rect = self.frameGeometry()
            window_rect.moveCenter(rect.center())
            self.move(window_rect.topLeft())
        
        def _init_menu_bar(self):
            """初始化菜单栏"""
            self.menu_bar = QMenuBar()
            self.setMenuBar(self.menu_bar)
            
            # 文件菜单
            file_menu = QMenu("文件")
            
            exit_action = QAction("退出")
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            self.menu_bar.addMenu(file_menu)
            
            # 设置菜单
            settings_menu = QMenu("设置")
            
            preferences_action = QAction("首选项")
            settings_menu.addAction(preferences_action)
            
            self.menu_bar.addMenu(settings_menu)
            
            # 帮助菜单
            help_menu = QMenu("帮助")
            
            about_action = QAction("关于")
            about_action.triggered.connect(self._show_about)
            help_menu.addAction(about_action)
            
            self.menu_bar.addMenu(help_menu)
        
        def _init_tab_widget(self):
            """初始化标签页"""
            self.tab_widget = QTabWidget()
            self.main_layout.addWidget(self.tab_widget)
            
            # 禁用标签页关闭按钮
            self.tab_widget.setTabsClosable(False)
            
            # 初始化标签页
            self._init_search_tab()
            self._init_config_tab()
            self._init_progress_tab()
        
        def _init_search_tab(self):
            """初始化搜索标签页"""
            try:
                from src.ui.search_widget import SearchWidget
                self.search_widget = SearchWidget()
                self.tab_widget.addTab(self.search_widget, "搜索")
            except ImportError:
                # 如果搜索组件不可用，创建占位符
                placeholder = QWidget()
                placeholder_layout = QVBoxLayout(placeholder)
                from PySide6.QtWidgets import QLabel
                placeholder_label = QLabel("搜索组件正在加载中...")
                placeholder_label.setAlignment(Qt.AlignCenter)
                placeholder_layout.addWidget(placeholder_label)
                self.tab_widget.addTab(placeholder, "搜索")
        
        def _init_config_tab(self):
            """初始化配置标签页"""
            try:
                from src.ui.config_widget import ConfigWidget
                self.config_widget = ConfigWidget(self.config_manager)
                self.tab_widget.addTab(self.config_widget, "配置")
            except ImportError as e:
                # 如果配置组件不可用，创建占位符
                from PySide6.QtWidgets import QLabel
                placeholder = QWidget()
                placeholder_layout = QVBoxLayout(placeholder)
                placeholder_label = QLabel(f"配置组件加载失败: {e}")
                placeholder_label.setAlignment(Qt.AlignCenter)
                placeholder_layout.addWidget(placeholder_label)
                self.tab_widget.addTab(placeholder, "配置")
        
        def _init_progress_tab(self):
            """初始化进度标签页"""
            try:
                from src.ui.progress_widget import ProgressWidget
                self.progress_widget = ProgressWidget()
                self.tab_widget.addTab(self.progress_widget, "进度")
            except ImportError as e:
                # 如果进度组件不可用，创建占位符
                from PySide6.QtWidgets import QLabel
                placeholder = QWidget()
                placeholder_layout = QVBoxLayout(placeholder)
                placeholder_label = QLabel(f"进度组件加载失败: {e}")
                placeholder_label.setAlignment(Qt.AlignCenter)
                placeholder_layout.addWidget(placeholder_label)
                self.tab_widget.addTab(placeholder, "进度")
        
        def _init_status_bar(self):
            """初始化状态栏"""
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            
            # 状态标签
            self.status_label = QLabel("就绪")
            self.status_bar.addWidget(self.status_label)
            
            # 永久消息
            self.status_bar.addPermanentWidget(QLabel("msearch v1.0.0"))
        
        def _init_system_tray(self):
            """初始化系统托盘"""
            if QSystemTrayIcon.isSystemTrayAvailable():
                # 创建托盘图标
                self.system_tray_icon = QSystemTrayIcon(self)
                
                # 使用系统默认图标
                icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
                self.system_tray_icon.setIcon(icon)
                
                # 创建托盘菜单
                tray_menu = QMenu()
                
                show_action = QAction("显示", self)
                show_action.triggered.connect(self.show)
                tray_menu.addAction(show_action)
                
                hide_action = QAction("隐藏", self)
                hide_action.triggered.connect(self.hide)
                tray_menu.addAction(hide_action)
                
                tray_menu.addSeparator()
                
                quit_action = QAction("退出", self)
                quit_action.triggered.connect(QApplication.quit)
                tray_menu.addAction(quit_action)
                
                self.system_tray_icon.setContextMenu(tray_menu)
                
                # 连接信号
                self.system_tray_icon.activated.connect(self._tray_icon_activated)
                
                # 显示托盘图标
                self.system_tray_icon.show()
        
        def _tray_icon_activated(self, reason):
            """托盘图标被激活时的处理"""
            if reason == QSystemTrayIcon.Trigger:
                # 左键点击 - 显示/隐藏窗口
                if self.isVisible():
                    self.hide()
                else:
                    self.show()
        
        def _show_about(self):
            """显示关于对话框"""
            QMessageBox.about(
                self,
                "关于 msearch",
                """<b>msearch 多模态检索系统</b>
                <p>版本 1.0.0</p>
                <p>支持文本、图像、视频、音频的智能检索系统</p>
                <p>© 2025 msearch 项目组</p>"""
            )

# 如果PySide6不可用，定义一个空的MainWindow类
except ImportError:
    class MainWindow:
        """PySide6不可用时的空主窗口类"""
        def __init__(self):
            print("警告: PySide6未安装，无法创建GUI窗口")

    # 确保PYSIDE6_AVAILABLE变量存在
    PYSIDE6_AVAILABLE = False


def main():
    """主函数"""
    if not PYSIDE6_AVAILABLE:
        print("错误: PySide6未安装，无法启动GUI界面")
        print("请执行: pip install PySide6")
        return 1

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("msearch")
    app.setOrganizationName("msearch")

    # 设置应用样式
    app.setStyle("Fusion")

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
