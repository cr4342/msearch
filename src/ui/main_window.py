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
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTabWidget,
    QLabel,
    QPushButton,
    QStatusBar,
    QMenuBar,
    QMenu,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QFrame,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QIcon, QPixmap, QImage, QAction

# 导入UI组件
from src.ui.components.search_panel import SearchPanel
from src.ui.components.result_panel_updated import ResultPanel
from src.ui.components.task_manager_panel import TaskManagerPanel
from src.ui.components.monitored_directories_panel import MonitoredDirectoriesPanel
from src.ui.components.task_queue_panel import TaskQueuePanel
from src.ui.components.manual_control_panel import ManualControlPanel

try:
    from src.core.config.config_manager import ConfigManager
    from src.core.database.database_manager import DatabaseManager
    from src.core.vector.vector_store import VectorStore
    from src.core.embedding.embedding_engine import EmbeddingEngine
    from src.services.search.search_engine import SearchEngine
    from src.api.api_client import APIClient
except ImportError as e:
    print(f"导入核心模块失败: {e}")
    print("请确保已安装所有依赖: pip install -r requirements.txt")


class SearchThread(QThread):
    """后台搜索线程"""

    result_ready = Signal(list)
    error_occurred = Signal(str)

    def __init__(
        self, search_engine, query: str, search_type: str, is_file_search: bool = False
    ):
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
                    search_result = asyncio.run(
                        self.search_engine.image_search(self.query)
                    )
                elif self.search_type == "audio":
                    search_result = asyncio.run(
                        self.search_engine.audio_search(self.query)
                    )
                else:
                    self.error_occurred.emit(
                        f"不支持的文件搜索类型: {self.search_type}"
                    )
                    return
            else:
                # 常规搜索
                if self.search_type == "text":
                    search_result = asyncio.run(self.search_engine.search(self.query))
                elif self.search_type == "image":
                    search_result = asyncio.run(
                        self.search_engine.image_search(self.query)
                    )
                elif self.search_type == "audio":
                    search_result = asyncio.run(
                        self.search_engine.audio_search(self.query)
                    )
                else:
                    self.error_occurred.emit(f"不支持的搜索类型: {self.search_type}")
                    return

            # 检查搜索结果状态
            if search_result.get("status") != "success":
                self.error_occurred.emit(search_result.get("error", "搜索失败"))
                return

            # 提取结果数据
            results = search_result.get("results", [])
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

        # 初始化API客户端
        try:
            self.api_client = APIClient()
        except Exception as e:
            print(f"初始化API客户端失败: {e}")
            self.api_client = None

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

        # 创建左侧面板（搜索 + 监控目录 + 任务队列）
        self.left_panel = self._create_left_panel()
        splitter.addWidget(self.left_panel)

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
        self.status_bar.setStyleSheet(
            """
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
        """
        )
        self.setStatusBar(self.status_bar)

        # 添加状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #165DFF; font-weight: 600;")
        self.status_bar.addWidget(self.status_label)

        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setMaximumHeight(20)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                background-color: #E5E6EB;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #165DFF;
                border-radius: 3px;
            }
        """
        )
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
        toolbar.setStyleSheet(
            """
            QWidget {
                background-color: #165DFF;
                border-bottom: 1px solid #E5E6EB;
            }
        """
        )

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(20)

        # Logo 和标题
        logo_label = QLabel("msearch")
        logo_label.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
        """
        )
        layout.addWidget(logo_label)

        layout.addStretch()

        # 功能按钮
        self.index_btn = QPushButton("📁 索引管理")
        self.index_btn.setFixedSize(110, 36)
        self.index_btn.setStyleSheet(
            """
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
        """
        )
        self.index_btn.clicked.connect(self.on_index_clicked)
        layout.addWidget(self.index_btn)

        self.task_btn = QPushButton("📋 任务管理")
        self.task_btn.setFixedSize(110, 36)
        self.task_btn.setStyleSheet(
            """
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
        """
        )
        self.task_btn.clicked.connect(self.on_task_manager_clicked)
        layout.addWidget(self.task_btn)

        self.settings_btn = QPushButton("⚙️ 设置")
        self.settings_btn.setFixedSize(90, 36)
        self.settings_btn.setStyleSheet(
            """
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
        """
        )
        self.settings_btn.clicked.connect(self.on_settings_clicked)
        layout.addWidget(self.settings_btn)

        self.settings_btn = QPushButton("⚙️ 设置")
        self.settings_btn.setFixedSize(100, 36)
        self.settings_btn.setStyleSheet(
            """
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
        """
        )
        self.settings_btn.clicked.connect(self.on_settings_clicked)
        layout.addWidget(self.settings_btn)

        self.tasks_btn = QPushButton("📋 任务")
        self.tasks_btn.setFixedSize(100, 36)
        self.tasks_btn.setStyleSheet(
            """
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
        """
        )
        self.tasks_btn.clicked.connect(self.on_tasks_clicked)
        layout.addWidget(self.tasks_btn)

        return toolbar

    def _create_left_panel(self) -> QWidget:
        """创建左侧面板（搜索 + 监控目录 + 手动控制 + 任务队列）"""
        panel = QWidget()
        panel.setFixedWidth(420)
        panel.setStyleSheet(
            """
            QWidget {
                background-color: #F2F3F5;
                border-radius: 12px;
            }
        """
        )

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 搜索区域
        search_title = QLabel("🔍 搜索")
        search_title.setStyleSheet("color: #4E5969; font-size: 12px; font-weight: 600;")
        layout.addWidget(search_title)

        search_container = self.create_search_panel()
        layout.addWidget(search_container)

        # 分隔线
        layout.addWidget(self._create_separator())

        # 监控目录区域
        dir_title = QLabel("📁 监控目录")
        dir_title.setStyleSheet("color: #4E5969; font-size: 12px; font-weight: 600;")
        layout.addWidget(dir_title)

        self.monitored_directories_panel = MonitoredDirectoriesPanel()
        # 连接信号
        self.monitored_directories_panel.directory_added.connect(
            self._on_directory_added
        )
        self.monitored_directories_panel.directory_removed.connect(
            self._on_directory_removed
        )
        self.monitored_directories_panel.directory_paused.connect(
            self._on_directory_paused
        )
        self.monitored_directories_panel.directory_resumed.connect(
            self._on_directory_resumed
        )
        layout.addWidget(self.monitored_directories_panel)

        # 分隔线
        layout.addWidget(self._create_separator())

        # 手动操作控制区域
        control_title = QLabel("🎛️ 手动控制")
        control_title.setStyleSheet(
            "color: #4E5969; font-size: 12px; font-weight: 600;"
        )
        layout.addWidget(control_title)

        self.manual_control_panel = ManualControlPanel()
        # 连接信号
        self.manual_control_panel.scan_triggered.connect(self._on_scan_triggered)
        self.manual_control_panel.vectorization_triggered.connect(
            self._on_vectorization_triggered
        )
        self.manual_control_panel.control_changed.connect(self._on_control_changed)
        layout.addWidget(self.manual_control_panel)

        # 分隔线
        layout.addWidget(self._create_separator())

        # 任务队列区域
        task_title = QLabel("📋 任务队列")
        task_title.setStyleSheet("color: #4E5969; font-size: 12px; font-weight: 600;")
        layout.addWidget(task_title)

        self.task_queue_panel = TaskQueuePanel(api_client=self.api_client)
        # 连接信号
        self.task_queue_panel.tasks_paused.connect(self._on_tasks_paused)
        self.task_queue_panel.tasks_resumed.connect(self._on_tasks_resumed)
        self.task_queue_panel.tasks_cancelled.connect(self._on_tasks_cancelled)
        self.task_queue_panel.priority_changed.connect(self._on_priority_changed)
        layout.addWidget(self.task_queue_panel)

        layout.addStretch()

        return panel

    def create_search_panel(self) -> QWidget:
        """创建搜索面板（向后兼容）"""
        # 创建左侧面板容器
        search_panel = QWidget()
        search_panel.setStyleSheet(
            """
            QWidget {
                background-color: white;
                border-radius: 8px;
            }
        """
        )

        layout = QVBoxLayout(search_panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 搜索面板
        from src.ui.components.search_panel import SearchPanel

        self.search_panel_widget = SearchPanel()

        # 连接搜索信号
        self.search_panel_widget.search_triggered.connect(self._on_search_requested)
        self.search_panel_widget.file_search_requested.connect(
            self.on_file_search_requested
        )

        layout.addWidget(self.search_panel_widget)

        # 过滤面板
        from src.ui.components.filter_panel import FilterPanel

        self.filter_panel = FilterPanel()
        self.filter_panel.filter_changed.connect(self._on_filter_changed)
        layout.addWidget(self.filter_panel)

        # 统计面板
        from src.ui.components.stats_panel import StatsPanel

        self.stats_panel = StatsPanel()
        layout.addWidget(self.stats_panel)

        return search_panel

    def _create_separator(self) -> QFrame:
        """创建分隔线"""
        line = QFrame()
        line.setFixedHeight(1)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(
            """
            QFrame {
                background-color: #E5E6EB;
                border: none;
            }
        """
        )
        return line

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
            self.database_manager = DatabaseManager(
                sqlite_path=db_path, config=self.config_manager
            )
            self.database_manager.initialize()

            # 初始化向量存储
            vector_dir = config_db.get("lancedb_path", "data/database/lancedb")
            self.vector_store = VectorStore(
                lancedb_path=vector_dir, config=self.config_manager
            )
            self.vector_store.initialize()

            # 初始化向量化引擎
            self.embedding_engine = EmbeddingEngine(config=self.config_manager)
            self.embedding_engine.initialize()

            # 初始化搜索引擎
            search_config = self.config_manager.get("search", {})
            self.search_engine = SearchEngine(
                config=search_config,
                embedding_engine=self.embedding_engine,
                vector_store=self.vector_store,
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

    def update_status(
        self, message: str, show_progress: bool = False, progress_value: int = 0
    ):
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
                search_engine=self.search_engine, query=query, search_type=search_type
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
                is_file_search=True,
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
        if hasattr(self.result_panel, "display_results"):
            self.result_panel.display_results(results)
        else:
            self.update_status(
                f"搜索完成，找到 {len(results)} 个结果，但结果面板显示功能未实现"
            )

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
            self, "打开文件", "", "所有文件 (*.*)"
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

    # ==================== 监控目录事件处理 ====================

    def _on_directory_added(self, path: str):
        """目录添加事件"""
        self.update_status(f"已添加监控目录: {path}")
        # TODO: 调用API添加监控目录
        # self.api_client.add_monitored_directory(path)

    def _on_directory_removed(self, path: str):
        """目录移除事件"""
        self.update_status(f"已移除监控目录: {path}")
        # TODO: 调用API移除监控目录
        # self.api_client.remove_monitored_directory(path)

    def _on_directory_paused(self, path: str):
        """目录暂停事件"""
        self.update_status(f"已暂停监控: {path}")
        # TODO: 调用API暂停监控
        # self.api_client.pause_directory(path)

    def _on_directory_resumed(self, path: str):
        """目录恢复事件"""
        self.update_status(f"已恢复监控: {path}")
        # TODO: 调用API恢复监控
        # self.api_client.resume_directory(path)

    # ==================== 任务队列事件处理 ====================

    def _on_tasks_paused(self):
        """任务暂停事件"""
        self.update_status("已暂停所有任务")
        # TODO: 调用API暂停任务
        # self.api_client.pause_tasks()

    def _on_tasks_resumed(self):
        """任务恢复事件"""
        self.update_status("已恢复所有任务")
        # TODO: 调用API恢复任务
        # self.api_client.resume_tasks()

    def _on_tasks_cancelled(self):
        """任务取消事件"""
        self.update_status("已取消所有任务")
        # TODO: 调用API取消任务
        # self.api_client.cancel_tasks()

    def _on_priority_changed(self, settings: dict):
        """优先级变更事件"""
        self.update_status(f"优先级设置已更新: {settings}")
        # TODO: 调用API设置优先级
        # self.api_client.set_priority_settings(settings)

    # ==================== 手动操作控制事件处理 ====================

    def _on_scan_triggered(self, config: dict):
        """扫描触发事件"""
        scan_type = config.get("type", "full_scan")
        directory = config.get("directory", None)

        if scan_type == "full_scan":
            self.update_status("正在启动全量扫描...")
            # TODO: 调用API执行全量扫描
            # self.api_client.trigger_full_scan()
        elif scan_type == "directory_scan":
            self.update_status(f"正在扫描目录: {directory}")
            # TODO: 调用API执行目录扫描
            # self.api_client.trigger_directory_scan(directory)

    def _on_vectorization_triggered(self, config: dict):
        """向量化触发事件"""
        file_type = config.get("file_type", None)
        concurrent = config.get("concurrent", 4)
        use_gpu = config.get("use_gpu", False)
        revectorize_failed = config.get("revectorize_failed", False)

        if revectorize_failed:
            self.update_status("正在重新向量化失败文件...")
            # TODO: 调用API重新向量化失败文件
            # self.api_client.revectorize_failed()
        else:
            self.update_status(f"正在启动向量化: {file_type or '全部'}")
            # TODO: 调用API执行向量化
            # self.api_client.trigger_vectorization(file_type, concurrent, use_gpu)

    def _on_control_changed(self, config: dict):
        """控制参数变更事件"""
        action = config.get("action", None)

        if action == "pause_all":
            self.update_status("正在暂停所有任务...")
            # TODO: 调用API暂停所有任务
            # self.api_client.pause_all_tasks()
        elif action == "resume_all":
            self.update_status("正在恢复所有任务...")
            # TODO: 调用API恢复所有任务
            # self.api_client.resume_all_tasks()
        elif action == "cancel_all":
            self.update_status("正在取消所有任务...")
            # TODO: 调用API取消所有任务
            # self.api_client.cancel_all_tasks()
        else:
            concurrent = config.get("concurrent", 4)
            use_gpu = config.get("use_gpu", False)
            self.update_status(
                f"资源配置已更新: 并发={concurrent}, GPU={'启用' if use_gpu else '禁用'}"
            )
            # TODO: 调用API更新资源配置
            # self.api_client.update_resource_config(concurrent, use_gpu)

    # ==================== API客户端方法（占位符）====================
    # TODO: 在后续任务中实现真实的API客户端

    def get_monitored_directories(self) -> List[Dict[str, Any]]:
        """获取监控目录列表（占位符）"""
        # TODO: 调用API获取真实数据
        return self.monitored_directories_panel.get_directories()

    def get_file_stats(self) -> Dict[str, int]:
        """获取文件统计（占位符）"""
        # TODO: 调用API获取真实数据
        return self.monitored_directories_panel.get_stats()

    def set_priority_settings(self, settings: dict):
        """设置优先级（占位符）"""
        # TODO: 调用API设置优先级
        pass

    def pause_tasks(self):
        """暂停任务（占位符）"""
        # TODO: 调用API暂停任务
        pass

    def resume_tasks(self):
        """恢复任务（占位符）"""
        # TODO: 调用API恢复任务
        pass

    def cancel_tasks(self):
        """取消任务（占位符）"""
        # TODO: 调用API取消任务
        pass

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
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # 清理资源
            if self.status_timer:
                self.status_timer.stop()
            event.accept()
        else:
            event.ignore()
