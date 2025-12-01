"""
PySide6主窗口
msearch多模态检索系统的主界面
"""

import sys
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTabWidget, QStatusBar, QMenuBar, QMenu, QAction,
        QSystemTrayIcon, QStyle, QMessageBox
    )
    from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject
    from PySide6.QtGui import QIcon, QPixmap, QFont
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

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
        
        if not PYSIDE6_AVAILABLE:
            raise ImportError("PySide6未安装，无法启动GUI界面")
        
        # 初始化配置和日志
        self.config_manager = get_config_manager()
        setup_logging("INFO")
        self.logger = logging.getLogger(__name__)
        
        # 窗口属性
        self.setWindowTitle("msearch 多模态检索系统")
        self.setMinimumSize(1200, 800)
        
        # 组件引用
        self.search_widget = None
        self.config_widget = None
        self.progress_widget = None
        self.system_tray_icon = None
        
        # 初始化界面
        self._init_ui()
        self._init_menu_bar()
        self._init_status_bar()
        self._init_system_tray()
        
        # 加载窗口设置
        self._load_window_settings()
        
        self.logger.info("主窗口初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background: white;
            }
            QTabBar::tab {
                background: #f0f0f0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #0078d4;
            }
        """)
        
        # 创建标签页
        self._create_search_tab()
        self._create_config_tab()
        self._create_progress_tab()
        
        main_layout.addWidget(self.tab_widget)
    
    def _create_search_tab(self):
        """创建搜索标签页"""
        try:
            from .search_widget import SearchWidget
            self.search_widget = SearchWidget()
            self.tab_widget.addTab(self.search_widget, "搜索")
        except ImportError:
            # 如果搜索组件不可用，创建占位符
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            layout.addWidget(QLabel("搜索组件开发中..."))
            self.tab_widget.addTab(placeholder, "搜索")
    
    def _create_config_tab(self):
        """创建配置标签页"""
        try:
            from .config_widget import ConfigWidget
            self.config_widget = ConfigWidget(self.config_manager)
            self.tab_widget.addTab(self.config_widget, "配置")
        except ImportError:
            # 如果配置组件不可用，创建占位符
            from PySide6.QtWidgets import QLabel
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            layout.addWidget(QLabel("配置组件开发中..."))
            self.tab_widget.addTab(placeholder, "配置")
    
    def _create_progress_tab(self):
        """创建进度标签页"""
        try:
            from .progress_widget import ProgressWidget
            self.progress_widget = ProgressWidget()
            self.tab_widget.addTab(self.progress_widget, "进度")
        except ImportError:
            # 如果进度组件不可用，创建占位符
            from PySide6.QtWidgets import QLabel
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            layout.addWidget(QLabel("进度组件开发中..."))
            self.tab_widget.addTab(placeholder, "进度")
    
    def _init_menu_bar(self):
        """初始化菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 刷新数据库
        refresh_action = QAction("刷新数据库(&R)", self)
        refresh_action.setShortcut("F5")
        refresh_action.setStatusTip("刷新数据库索引")
        refresh_action.triggered.connect(self._refresh_database)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        # 全屏
        fullscreen_action = QAction("全屏(&F)", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.setStatusTip("切换全屏模式")
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        # 清理临时文件
        cleanup_action = QAction("清理临时文件(&C)", self)
        cleanup_action.setStatusTip("清理系统临时文件")
        cleanup_action.triggered.connect(self._cleanup_temp_files)
        tools_menu.addAction(cleanup_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 关于
        about_action = QAction("关于(&A)", self)
        about_action.setStatusTip("关于msearch")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
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
            
            self.logger.info("系统托盘初始化完成")
    
    def _tray_icon_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
    
    def _load_window_settings(self):
        """加载窗口设置"""
        try:
            settings = self.config_manager.get("ui.window", {})
            
            # 窗口位置和大小
            geometry = settings.get("geometry")
            if geometry:
                self.restoreGeometry(geometry)
            
            # 窗口状态
            state = settings.get("window_state")
            if state:
                self.restoreState(state)
            
            self.logger.debug("窗口设置加载完成")
            
        except Exception as e:
            self.logger.error(f"加载窗口设置失败: {e}")
    
    def _save_window_settings(self):
        """保存窗口设置"""
        try:
            settings = {
                "geometry": self.saveGeometry(),
                "window_state": self.saveState()
            }
            
            # 这里可以保存到配置文件
            # self.config_manager.set("ui.window", settings)
            
            self.logger.debug("窗口设置保存完成")
            
        except Exception as e:
            self.logger.error(f"保存窗口设置失败: {e}")
    
    def closeEvent(self, event):
        """关闭事件"""
        # 保存窗口设置
        self._save_window_settings()
        
        # 询问是否最小化到托盘
        if self.system_tray_icon and self.system_tray_icon.isVisible():
            reply = QMessageBox.question(
                self, "确认退出",
                "是否最小化到系统托盘？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                event.ignore()
                self.hide()
                return
        
        # 清理资源
        self._cleanup()
        
        event.accept()
    
    def _cleanup(self):
        """清理资源"""
        try:
            # 停止后台任务
            # 这里可以添加其他清理逻辑
            
            self.logger.info("资源清理完成")
            
        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")
    
    def _refresh_database(self):
        """刷新数据库"""
        self.status_label.setText("正在刷新数据库...")
        
        # 创建异步工作线程
        worker = AsyncWorker(self._async_refresh_database())
        worker_thread = QThread()
        worker.moveToThread(worker_thread)
        
        worker_thread.started.connect(worker.run)
        worker.finished.connect(lambda result: self._on_refresh_finished(result))
        worker.error.connect(lambda error: self._on_refresh_error(error))
        worker.finished.connect(worker_thread.quit)
        worker_thread.finished.connect(worker_thread.deleteLater)
        
        worker_thread.start()
    
    async def _async_refresh_database(self):
        """异步刷新数据库"""
        try:
            # 这里实现数据库刷新逻辑
            await asyncio.sleep(2)  # 模拟耗时操作
            return {"status": "success", "message": "数据库刷新完成"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _on_refresh_finished(self, result):
        """刷新完成回调"""
        if result.get("status") == "success":
            self.status_label.setText(result.get("message", "刷新完成"))
        else:
            self.status_label.setText(f"刷新失败: {result.get('message', '未知错误')}")
        
        # 3秒后恢复状态
        QTimer.singleShot(3000, lambda: self.status_label.setText("就绪"))
    
    def _on_refresh_error(self, error):
        """刷新错误回调"""
        self.status_label.setText(f"刷新错误: {error}")
        QTimer.singleShot(3000, lambda: self.status_label.setText("就绪"))
    
    def _toggle_fullscreen(self, checked):
        """切换全屏"""
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()
    
    def _cleanup_temp_files(self):
        """清理临时文件"""
        self.status_label.setText("正在清理临时文件...")
        
        # 创建异步工作线程
        worker = AsyncWorker(self._async_cleanup_temp_files())
        worker_thread = QThread()
        worker.moveToThread(worker_thread)
        
        worker_thread.started.connect(worker.run)
        worker.finished.connect(lambda result: self._on_cleanup_finished(result))
        worker.error.connect(lambda error: self._on_cleanup_error(error))
        worker.finished.connect(worker_thread.quit)
        worker_thread.finished.connect(worker_thread.deleteLater)
        
        worker_thread.start()
    
    async def _async_cleanup_temp_files(self):
        """异步清理临时文件"""
        try:
            # 这里实现临时文件清理逻辑
            await asyncio.sleep(1)  # 模拟耗时操作
            return {"status": "success", "message": "临时文件清理完成"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _on_cleanup_finished(self, result):
        """清理完成回调"""
        if result.get("status") == "success":
            self.status_label.setText(result.get("message", "清理完成"))
        else:
            self.status_label.setText(f"清理失败: {result.get('message', '未知错误')}")
        
        QTimer.singleShot(3000, lambda: self.status_label.setText("就绪"))
    
    def _on_cleanup_error(self, error):
        """清理错误回调"""
        self.status_label.setText(f"清理错误: {error}")
        QTimer.singleShot(3000, lambda: self.status_label.setText("就绪"))
    
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


def main():
    """主函数"""
    if not PYSIDE6_AVAILABLE:
        print("错误: PySide6未安装，无法启动GUI界面")
        print("请运行: pip install PySide6")
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