"""
msearch 主窗口
PySide6桌面应用主窗口
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QLabel, QPushButton,
    QStatusBar, QMenuBar, QMenu, QFileDialog, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QIcon, QPixmap, QImage, QAction

# 导入UI组件
from src.ui.components.search_panel import SearchPanel
from src.ui.components.result_panel_updated import ResultPanel
from src.ui.components.task_manager_panel import TaskManagerPanel

try:
    from src.core.config.config_manager import ConfigManager
    from src.core.database.database_manager import DatabaseManager
    from src.core.vector.vector_store import VectorStore
    from src.core.embedding.embedding_engine import EmbeddingEngine
    from src.services.search.search_engine import SearchEngine
except ImportError as e:
    print(f"导入核心模块失败: {e}")
    print("请确保已安装所有依赖: pip install -r requirements.txt")


class SearchThread(QThread):
    """后台搜索线程"""
    
    result_ready = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, search_engine, query: str, search_type: str, is_file_search: bool = False):
        """初始化搜索线程"""
        super().__init__()
        self.search_engine = search_engine
        self.query = query
        self.search_type = search_type
        self.is_file_search = is_file_search
    
    def run(self):
        """执行搜索任务"""
        try:
            import asyncio
            if self.is_file_search:
                # 文件搜索
                if self.search_type == "image":
                    search_result = asyncio.run(self.search_engine.image_search(self.query))
                elif self.search_type == "audio":
                    search_result = asyncio.run(self.search_engine.audio_search(self.query))
                else:
                    self.error_occurred.emit(f"不支持的文件搜索类型: {self.search_type}")
                    return
            else:
                # 常规搜索
                if self.search_type == "text":
                    search_result = asyncio.run(self.search_engine.search(self.query))
                elif self.search_type == "image":
                    search_result = asyncio.run(self.search_engine.image_search(self.query))
                elif self.search_type == "audio":
                    search_result = asyncio.run(self.search_engine.audio_search(self.query))
                else:
                    self.error_occurred.emit(f"不支持的搜索类型: {self.search_type}")
                    return
            
            # 检查搜索结果状态
            if search_result.get('status') != 'success':
                self.error_occurred.emit(search_result.get('error', '搜索失败'))
                return
            
            # 提取结果数据
            results = search_result.get('results', [])
            self.result_ready.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    """msearch主窗口"""
    
    # 信号定义
    search_completed = Signal(list)
    search_failed = Signal(str)
    indexing_completed = Signal(int)
    indexing_failed = Signal(str)
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 初始化核心组件
        self.config_manager: Optional[ConfigManager] = None
        self.search_engine: Optional[SearchEngine] = None
        self.database_manager: Optional[DatabaseManager] = None
        self.vector_store: Optional[VectorStore] = None
        self.embedding_engine: Optional[EmbeddingEngine] = None
        
        # 初始化UI
        self.init_ui()
        self.init_core_components()
        self.connect_signals()
        
        # 状态更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # 每5秒更新一次状态
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("msearch - 多模态搜索系统")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 添加顶部工具栏
        self.toolbar = self._create_toolbar()
        main_layout.addWidget(self.toolbar)
        
        # 创建中央内容区域（左右布局）
        central_layout = QHBoxLayout()
        central_layout.setContentsMargins(20, 20, 20, 20)
        central_layout.setSpacing(20)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧面板（搜索面板）
        self.search_panel = self.create_search_panel()
        splitter.addWidget(self.search_panel)
        
        # 创建右侧面板（结果面板）
        self.result_panel = self.create_result_panel()
        splitter.addWidget(self.result_panel)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        central_layout.addWidget(splitter)
        main_layout.addLayout(central_layout)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #F2F3F5;
                border-top: 1px solid #E5E6EB;
                color: #4E5969;
                font-size: 12px;
                padding: 2px;
            }
            QStatusBar::item {
                border: none;
            }
        """)
        self.setStatusBar(self.status_bar)
        
        # 添加状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #165DFF; font-weight: 600;")
        self.status_bar.addWidget(self.status_label)
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setMaximumHeight(20)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #E5E6EB;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #165DFF;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # 添加系统状态标签
        self.system_status_label = QLabel("系统正常")
        self.system_status_label.setStyleSheet("color: #00B42A;")
        self.status_bar.addPermanentWidget(self.system_status_label)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 初始化状态
        self.update_status("就绪")
    
    def _create_toolbar(self) -> QWidget:
        """创建顶部工具栏"""
        toolbar = QWidget()
        toolbar.setFixedHeight(60)
        toolbar.setStyleSheet("""
            QWidget {
                background-color: #165DFF;
                border-bottom: 1px solid #E5E6EB;
            }
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(20)
        
        # Logo 和标题
        logo_label = QLabel("msearch")
        logo_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        layout.addWidget(logo_label)
        
        layout.addStretch()
        
        # 功能按钮
        self.index_btn = QPushButton("📁 索引管理")
        self.index_btn.setFixedSize(110, 36)
        self.index_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.index_btn.clicked.connect(self.on_index_clicked)
        layout.addWidget(self.index_btn)
        
        self.task_btn = QPushButton("📋 任务管理")
        self.task_btn.setFixedSize(110, 36)
        self.task_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.task_btn.clicked.connect(self.on_task_manager_clicked)
        layout.addWidget(self.task_btn)
        
        self.settings_btn = QPushButton("⚙️ 设置")
        self.settings_btn.setFixedSize(90, 36)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.settings_btn.clicked.connect(self.on_settings_clicked)
        layout.addWidget(self.settings_btn)
        
        self.settings_btn = QPushButton("⚙️ 设置")
        self.settings_btn.setFixedSize(100, 36)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.settings_btn.clicked.connect(self.on_settings_clicked)
        layout.addWidget(self.settings_btn)
        
        self.tasks_btn = QPushButton("📋 任务")
        self.tasks_btn.setFixedSize(100, 36)
        self.tasks_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.tasks_btn.clicked.connect(self.on_tasks_clicked)
        layout.addWidget(self.tasks_btn)
        
        return toolbar
    
    def create_search_panel(self) -> QWidget:
        """创建左侧面板（搜索面板 + 过滤面板 + 统计面板）"""
        # 创建左侧面板容器
        left_panel = QWidget()
        left_panel.setFixedWidth(380)
        left_panel.setStyleSheet("""
            QWidget {
                background-color: #F2F3F5;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(left_panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 搜索面板
        from src.ui.components.search_panel import SearchPanel
        self.search_panel = SearchPanel()
        
        # 连接搜索信号
        self.search_panel.search_triggered.connect(self._on_search_requested)
        self.search_panel.file_search_requested.connect(self.on_file_search_requested)
        
        layout.addWidget(self.search_panel)
        
        # 过滤面板
        from src.ui.components.filter_panel import FilterPanel
        self.filter_panel = FilterPanel()
        self.filter_panel.filter_changed.connect(self._on_filter_changed)
        layout.addWidget(self.filter_panel)
        
        # 统计面板
        from src.ui.components.stats_panel import StatsPanel
        self.stats_panel = StatsPanel()
        layout.addWidget(self.stats_panel)
        
        layout.addStretch()
        
        return left_panel
    
    def create_result_panel(self) -> QWidget:
        """创建结果面板"""
        self.result_panel = ResultPanel()
        
        return self.result_panel
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        open_action = QAction("打开文件", self)
        open_action.triggered.connect(self.on_open_file)
        file_menu.addAction(open_action)
        
        open_dir_action = QAction("打开目录", self)
        open_dir_action.triggered.connect(self.on_open_directory)
        file_menu.addAction(open_dir_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.on_settings_clicked)
        edit_menu.addAction(settings_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        
        scan_action = QAction("扫描目录", self)
        scan_action.triggered.connect(self.on_scan_clicked)
        tools_menu.addAction(scan_action)
        
        index_action = QAction("索引文件", self)
        index_action.triggered.connect(self.on_index_clicked)
        tools_menu.addAction(index_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.on_about_clicked)
        help_menu.addAction(about_action)
    
    def init_core_components(self):
        """初始化核心组件"""
        try:
            # 加载配置
            self.config_manager = ConfigManager()
            
            # 初始化数据库管理器
            config_db = self.config_manager.get("database", {})
            db_path = config_db.get("sqlite_path", "data/database/msearch.db")
            self.database_manager = DatabaseManager(sqlite_path=db_path, config=self.config_manager)
            self.database_manager.initialize()
            
            # 初始化向量存储
            vector_dir = config_db.get("lancedb_path", "data/database/lancedb")
            self.vector_store = VectorStore(lancedb_path=vector_dir, config=self.config_manager)
            self.vector_store.initialize()
            
            # 初始化向量化引擎
            self.embedding_engine = EmbeddingEngine(config=self.config_manager)
            self.embedding_engine.initialize()
            
            # 初始化搜索引擎
            search_config = self.config_manager.get("search", {})
            self.search_engine = SearchEngine(
                config=search_config,
                embedding_engine=self.embedding_engine,
                vector_store=self.vector_store
            )
            self.search_engine.initialize()
            
            self.update_status("核心组件初始化完成")
            
        except Exception as e:
            self.update_status(f"核心组件初始化失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"初始化核心组件失败:\n{str(e)}")
    
    def connect_signals(self):
        """连接信号"""
        self.search_completed.connect(self.on_search_completed)
        self.search_failed.connect(self.on_search_failed)
        self.indexing_completed.connect(self.on_indexing_completed)
        self.indexing_failed.connect(self.on_indexing_failed)
    
    def update_status(self, message: str, show_progress: bool = False, progress_value: int = 0):
        """更新状态栏"""
        self.status_label.setText(message)
        
        if show_progress:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(progress_value)
        else:
            self.progress_bar.setVisible(False)
    
    def update_system_status(self, status: str, is_healthy: bool = True):
        """更新系统状态"""
        self.system_status_label.setText(status)
        if is_healthy:
            self.system_status_label.setStyleSheet("color: #00B42A; font-weight: 600;")
        else:
            self.system_status_label.setStyleSheet("color: #F53F3F; font-weight: 600;")
    
    # 事件处理函数
    
    def on_search_requested(self, query: str, search_type: str):
        """搜索请求处理函数"""
        self.update_status(f"正在{search_type}搜索...")
        
        # 根据搜索类型执行不同的搜索
        if not self.search_engine:
            QMessageBox.warning(self, "错误", "搜索引擎未初始化")
            self.update_status("搜索失败: 搜索引擎未初始化")
            return
        
        try:
            # 在后台线程中执行搜索
            search_thread = SearchThread(
                search_engine=self.search_engine,
                query=query,
                search_type=search_type
            )
            search_thread.result_ready.connect(self.on_search_completed)
            search_thread.error_occurred.connect(self.on_search_failed)
            search_thread.start()
        except Exception as e:
            self.on_search_failed(str(e))
    
    def on_file_search_requested(self, file_path: str):
        """文件搜索请求处理函数"""
        self.update_status(f"正在搜索相似文件...")
        
        if not self.search_engine:
            QMessageBox.warning(self, "错误", "搜索引擎未初始化")
            self.update_status("搜索失败: 搜索引擎未初始化")
            return
        
        try:
            # 确定文件类型
            file_ext = Path(file_path).suffix.lower()
            if file_ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif"]:
                search_type = "image"
            elif file_ext in [".mp3", ".wav", ".flac", ".ogg", ".wma"]:
                search_type = "audio"
            else:
                QMessageBox.warning(self, "错误", "不支持的文件类型")
                return
            
            # 在后台线程中执行搜索
            search_thread = SearchThread(
                search_engine=self.search_engine,
                query=file_path,
                search_type=search_type,
                is_file_search=True
            )
            search_thread.result_ready.connect(self.on_search_completed)
            search_thread.error_occurred.connect(self.on_search_failed)
            search_thread.start()
        except Exception as e:
            self.on_search_failed(str(e))
    
    def _on_filter_changed(self, filters: dict):
        """过滤条件变化处理函数"""
        self.update_status(f"应用过滤条件...")
        # 这里应该重新执行搜索并应用过滤条件
        # 暂时只显示消息
        print(f"过滤条件: {filters}")
    
    def on_search_clicked(self):
        """兼容旧的搜索按钮点击事件"""
        self.update_status("正在搜索...")
        # 这里应该实现实际的搜索逻辑
        # 为了演示，暂时使用模拟数据
        QTimer.singleShot(1000, lambda: self.search_completed.emit([]))
    
    def on_search_completed(self, results: List[Dict[str, Any]]):
        """搜索完成事件"""
        self.update_status(f"搜索完成，找到 {len(results)} 个结果")
        
        # 使用结果面板显示结果
        if hasattr(self.result_panel, 'display_results'):
            self.result_panel.display_results(results)
        else:
            self.update_status(f"搜索完成，找到 {len(results)} 个结果，但结果面板显示功能未实现")
    
    def on_search_failed(self, error: str):
        """搜索失败事件"""
        self.update_status(f"搜索失败: {error}")
        QMessageBox.warning(self, "搜索失败", error)
    
    def on_scan_clicked(self):
        """扫描目录按钮点击事件"""
        directory = QFileDialog.getExistingDirectory(self, "选择要扫描的目录")
        if directory:
            self.update_status(f"正在扫描目录: {directory}")
            # 这里应该实现实际的扫描逻辑
            QTimer.singleShot(2000, lambda: self.indexing_completed.emit(10))
    
    def on_index_clicked(self):
        """索引文件按钮点击事件"""
        self.update_status("正在索引文件...")
        # 这里应该实现实际的索引逻辑
        QTimer.singleShot(3000, lambda: self.indexing_completed.emit(5))
    
    def on_indexing_completed(self, count: int):
        """索引完成事件"""
        self.update_status(f"索引完成，处理了 {count} 个文件")
        QMessageBox.information(self, "索引完成", f"成功索引了 {count} 个文件")
    
    def on_indexing_failed(self, error: str):
        """索引失败事件"""
        self.update_status(f"索引失败: {error}")
        QMessageBox.warning(self, "索引失败", error)
    
    def on_open_file(self):
        """打开文件菜单事件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开文件",
            "",
            "所有文件 (*.*)"
        )
        if file_path:
            self.update_status(f"打开文件: {file_path}")
            # 这里应该实现打开文件的逻辑
    
    def on_open_directory(self):
        """打开目录菜单事件"""
        directory = QFileDialog.getExistingDirectory(self, "打开目录")
        if directory:
            self.update_status(f"打开目录: {directory}")
            # 这里应该实现打开目录的逻辑
    
    def on_settings_clicked(self):
        """设置菜单事件"""
        self.update_status("打开设置")
        # 创建设置对话框
        try:
            from src.ui.components.settings_panel import SettingsPanel
            from PySide6.QtWidgets import QDialog
            
            dialog = QDialog(self)
            dialog.setWindowTitle("系统设置")
            dialog.setMinimumSize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            settings_panel = SettingsPanel(self.config_manager)
            layout.addWidget(settings_panel)
            
            dialog.exec_()
        except ImportError as e:
            QMessageBox.warning(self, "设置", f"设置面板加载失败: {str(e)}")
    
    def on_task_manager_clicked(self):
        """任务管理器按钮点击事件"""
        self.update_status("打开任务管理器")
        # 创建任务管理器对话框
        try:
            from PySide6.QtWidgets import QDialog
            
            dialog = QDialog(self)
            dialog.setWindowTitle("任务管理")
            dialog.setMinimumSize(800, 600)
            
            layout = QVBoxLayout(dialog)
            
            task_manager_panel = TaskManagerPanel()
            layout.addWidget(task_manager_panel)
            
            dialog.exec_()
        except ImportError as e:
            QMessageBox.warning(self, "任务管理", f"任务管理器加载失败: {str(e)}")
    
    def on_index_management_clicked(self):
        """索引管理按钮点击事件"""
        self.update_status("打开索引管理")
        # 这里应该打开索引管理对话框
        QMessageBox.information(self, "索引管理", "索引管理功能开发中...")
    
    def on_tasks_clicked(self):
        """任务管理按钮点击事件"""
        self.update_status("打开任务管理")
        # 这里应该打开任务管理对话框
        QMessageBox.information(self, "任务管理", "任务管理功能开发中...")
    
    def on_about_clicked(self):
        """关于菜单事件"""
        about_text = """
        <h3>msearch - 多模态搜索系统</h3>
        <p>版本: 1.0.0</p>
        <p>一款单机可运行的跨平台多模态桌面检索软件</p>
        <p>支持文本、图像、视频、音频四种模态的精准检索</p>
        <hr>
        <p>© 2026 msearch Team</p>
        """
        QMessageBox.about(self, "关于 msearch", about_text)
    
    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出 msearch 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 清理资源
            if self.status_timer:
                self.status_timer.stop()
            event.accept()
        else:
            event.ignore()