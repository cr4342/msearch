#!/usr/bin/env python3
"""
msearch PySide6桌面应用主窗口
提供完整的桌面应用界面和功能
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QSplitter, QMenuBar, QStatusBar, QToolBar, QDockWidget,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget, QFrame,
    QScrollArea, QProgressBar, QComboBox, QSpinBox, QCheckBox, QSlider,
    QGroupBox, QGridLayout, QFormLayout, QMessageBox, QFileDialog,
    QTreeView, QFileSystemModel, QListView, QStackedWidget, QToolButton,
    QButtonGroup, QRadioButton, QGroupBox, QSizePolicy, QSpacerItem,
    QTableWidgetItem, QDir
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QObject, QSettings, QUrl, QSize, 
    QPropertyAnimation, QEasingCurve, QRect
)
from PySide6.QtGui import (
    QIcon, QPixmap, QFont, QAction, QKeySequence, QPalette, QColor,
    QDesktopServices, QTextCursor, QStandardItemModel, QStandardItem
)

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import load_config
from src.core.logging_config import get_logger
from src.gui.api_client import ApiClient
from src.gui.search_worker import SearchWorker

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """msearch桌面应用主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 加载配置
        self.config = load_config()
        
        # 初始化API客户端
        self.api_client = ApiClient()
        
        # 初始化搜索工作线程
        self.search_worker = SearchWorker(self.api_client)
        
        # 初始化UI
        self.init_ui()

        # 初始化状态
        self.init_state()
        
        # 连接信号
        self.connect_signals()
        
        # 启动定时器
        self.start_timers()
        
        logger.info("主窗口初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口属性
        self.setWindowTitle("mSearch - 多模态智能检索系统")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)
        
        # 设置应用图标
        self.set_window_icon()
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建中央部件
        self.create_central_widget()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 创建停靠窗口
        self.create_dock_widgets()
        
        # 应用样式
        self.apply_styles()
    
    def set_window_icon(self):
        """设置窗口图标"""
        try:
            # 尝试加载应用图标
            icon_path = project_root / "webui" / "src" / "assets" / "icon.png"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception as e:
            logger.warning(f"加载图标失败: {e}")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 打开文件
        open_file_action = QAction("打开文件(&O)", self)
        open_file_action.setShortcut(QKeySequence.Open)
        open_file_action.setStatusTip("打开文件进行搜索")
        open_file_action.triggered.connect(self.open_file)
        file_menu.addAction(open_file_action)
        
        # 打开文件夹
        open_folder_action = QAction("打开文件夹(&D)", self)
        open_folder_action.setShortcut(QKeySequence("Ctrl+D"))
        open_folder_action.setStatusTip("打开文件夹进行搜索")
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        # 导入文件
        import_files_action = QAction("导入文件(&I)", self)
        import_files_action.setStatusTip("导入文件到索引库")
        import_files_action.triggered.connect(self.import_files)
        file_menu.addAction(import_files_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 搜索菜单
        search_menu = menubar.addMenu("搜索(&S)")
        
        # 文本搜索
        text_search_action = QAction("文本搜索(&T)", self)
        text_search_action.setShortcut(QKeySequence("Ctrl+T"))
        text_search_action.setStatusTip("进行文本搜索")
        text_search_action.triggered.connect(lambda: self.switch_tab("text_search"))
        search_menu.addAction(text_search_action)
        
        # 图像搜索
        image_search_action = QAction("图像搜索(&I)", self)
        image_search_action.setShortcut(QKeySequence("Ctrl+I"))
        image_search_action.setStatusTip("进行图像搜索")
        image_search_action.triggered.connect(lambda: self.switch_tab("image_search"))
        search_menu.addAction(image_search_action)
        
        # 音频搜索
        audio_search_action = QAction("音频搜索(&A)", self)
        audio_search_action.setShortcut(QKeySequence("Ctrl+A"))
        audio_search_action.setStatusTip("进行音频搜索")
        audio_search_action.triggered.connect(lambda: self.switch_tab("audio_search"))
        search_menu.addAction(audio_search_action)
        
        # 视频搜索
        video_search_action = QAction("视频搜索(&V)", self)
        video_search_action.setShortcut(QKeySequence("Ctrl+V"))
        video_search_action.setStatusTip("进行视频搜索")
        video_search_action.triggered.connect(lambda: self.switch_tab("video_search"))
        search_menu.addAction(video_search_action)
        
        # 多模态搜索
        multimodal_search_action = QAction("多模态搜索(&M)", self)
        multimodal_search_action.setShortcut(QKeySequence("Ctrl+M"))
        multimodal_search_action.setStatusTip("进行多模态搜索")
        multimodal_search_action.triggered.connect(lambda: self.switch_tab("multimodal_search"))
        search_menu.addAction(multimodal_search_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        # 配置
        config_action = QAction("配置(&C)", self)
        config_action.setStatusTip("打开配置对话框")
        config_action.triggered.connect(self.show_config_dialog)
        tools_menu.addAction(config_action)
        
        # 系统状态
        status_action = QAction("系统状态(&S)", self)
        status_action.setStatusTip("查看系统状态")
        status_action.triggered.connect(self.show_system_status)
        tools_menu.addAction(status_action)
        
        # 人脸管理
        face_management_action = QAction("人脸管理(&F)", self)
        face_management_action.setStatusTip("管理人脸库")
        face_management_action.triggered.connect(self.show_face_management)
        tools_menu.addAction(face_management_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 关于
        about_action = QAction("关于(&A)", self)
        about_action.setStatusTip("关于mSearch")
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def create_tool_bar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        
        # 文本搜索按钮
        text_search_btn = QAction("文本搜索", self)
        text_search_btn.triggered.connect(lambda: self.switch_tab("text_search"))
        toolbar.addAction(text_search_btn)
        
        # 图像搜索按钮
        image_search_btn = QAction("图像搜索", self)
        image_search_btn.triggered.connect(lambda: self.switch_tab("image_search"))
        toolbar.addAction(image_search_btn)
        
        # 音频搜索按钮
        audio_search_btn = QAction("音频搜索", self)
        audio_search_btn.triggered.connect(lambda: self.switch_tab("audio_search"))
        toolbar.addAction(audio_search_btn)
        
        # 视频搜索按钮
        video_search_btn = QAction("视频搜索", self)
        video_search_btn.triggered.connect(lambda: self.switch_tab("video_search"))
        toolbar.addAction(video_search_btn)
        
        # 多模态搜索按钮
        multimodal_search_btn = QAction("多模态搜索", self)
        multimodal_search_btn.triggered.connect(lambda: self.switch_tab("multimodal_search"))
        toolbar.addAction(multimodal_search_btn)
        
        toolbar.addSeparator()
        
        # 配置按钮
        config_btn = QAction("配置", self)
        config_btn.triggered.connect(self.show_config_dialog)
        toolbar.addAction(config_btn)
        
        # 系统状态按钮
        status_btn = QAction("系统状态", self)
        status_btn.triggered.connect(self.show_system_status)
        toolbar.addAction(status_btn)
    
    def create_central_widget(self):
        """创建中央部件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建选项卡部件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        
        # 创建各个选项卡
        self.create_search_tabs()
        self.create_file_manager_tab()
        self.create_timeline_tab()
        self.create_face_management_tab()
        
        main_layout.addWidget(self.tab_widget)
    
    def create_search_tabs(self):
        """创建搜索选项卡"""
        # 文本搜索选项卡
        self.text_search_tab = self.create_text_search_tab()
        self.tab_widget.addTab(self.text_search_tab, "文本搜索")
        
        # 图像搜索选项卡
        self.image_search_tab = self.create_image_search_tab()
        self.tab_widget.addTab(self.image_search_tab, "图像搜索")
        
        # 音频搜索选项卡
        self.audio_search_tab = self.create_audio_search_tab()
        self.tab_widget.addTab(self.audio_search_tab, "音频搜索")
        
        # 视频搜索选项卡
        self.video_search_tab = self.create_video_search_tab()
        self.tab_widget.addTab(self.video_search_tab, "视频搜索")
        
        # 多模态搜索选项卡
        self.multimodal_search_tab = self.create_multimodal_search_tab()
        self.tab_widget.addTab(self.multimodal_search_tab, "多模态搜索")
    
    def create_text_search_tab(self):
        """创建文本搜索选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 搜索输入区域
        search_group = QGroupBox("搜索查询")
        search_layout = QHBoxLayout(search_group)
        
        self.text_search_input = QLineEdit()
        self.text_search_input.setPlaceholderText("输入搜索关键词...")
        self.text_search_input.returnPressed.connect(self.perform_text_search)
        search_layout.addWidget(self.text_search_input)
        
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.perform_text_search)
        search_layout.addWidget(search_button)
        
        layout.addWidget(search_group)
        
        # 结果区域
        self.create_results_area(layout, "text")
        
        return tab
    
    def create_image_search_tab(self):
        """创建图像搜索选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文件选择区域
        file_group = QGroupBox("选择图像")
        file_layout = QHBoxLayout(file_group)
        
        self.image_path_input = QLineEdit()
        self.image_path_input.setPlaceholderText("选择图像文件...")
        file_layout.addWidget(self.image_path_input)
        
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_image_file)
        file_layout.addWidget(browse_button)
        
        layout.addWidget(file_group)
        
        # 搜索按钮
        search_button = QPushButton("搜索相似图像")
        search_button.clicked.connect(self.perform_image_search)
        layout.addWidget(search_button)
        
        # 结果区域
        self.create_results_area(layout, "image")
        
        return tab
    
    def create_audio_search_tab(self):
        """创建音频搜索选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文件选择区域
        file_group = QGroupBox("选择音频")
        file_layout = QHBoxLayout(file_group)
        
        self.audio_path_input = QLineEdit()
        self.audio_path_input.setPlaceholderText("选择音频文件...")
        file_layout.addWidget(self.audio_path_input)
        
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_audio_file)
        file_layout.addWidget(browse_button)
        
        layout.addWidget(file_group)
        
        # 搜索按钮
        search_button = QPushButton("搜索相似音频")
        search_button.clicked.connect(self.perform_audio_search)
        layout.addWidget(search_button)
        
        # 结果区域
        self.create_results_area(layout, "audio")
        
        return tab
    
    def create_video_search_tab(self):
        """创建视频搜索选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文件选择区域
        file_group = QGroupBox("选择视频")
        file_layout = QHBoxLayout(file_group)
        
        self.video_path_input = QLineEdit()
        self.video_path_input.setPlaceholderText("选择视频文件...")
        file_layout.addWidget(self.video_path_input)
        
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_video_file)
        file_layout.addWidget(browse_button)
        
        layout.addWidget(file_group)
        
        # 搜索按钮
        search_button = QPushButton("搜索相似视频")
        search_button.clicked.connect(self.perform_video_search)
        layout.addWidget(search_button)
        
        # 结果区域
        self.create_results_area(layout, "video")
        
        return tab
    
    def create_multimodal_search_tab(self):
        """创建多模态搜索选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文本输入区域
        text_group = QGroupBox("文本查询（可选）")
        text_layout = QHBoxLayout(text_group)
        
        self.multimodal_text_input = QLineEdit()
        self.multimodal_text_input.setPlaceholderText("输入搜索关键词...")
        text_layout.addWidget(self.multimodal_text_input)
        
        layout.addWidget(text_group)
        
        # 文件选择区域
        file_group = QGroupBox("媒体文件（可选）")
        file_layout = QGridLayout(file_group)
        
        # 图像文件
        file_layout.addWidget(QLabel("图像:"), 0, 0)
        self.multimodal_image_input = QLineEdit()
        self.multimodal_image_input.setPlaceholderText("选择图像文件...")
        file_layout.addWidget(self.multimodal_image_input, 0, 1)
        image_browse_button = QPushButton("浏览...")
        image_browse_button.clicked.connect(self.browse_multimodal_image_file)
        file_layout.addWidget(image_browse_button, 0, 2)
        
        # 音频文件
        file_layout.addWidget(QLabel("音频:"), 1, 0)
        self.multimodal_audio_input = QLineEdit()
        self.multimodal_audio_input.setPlaceholderText("选择音频文件...")
        file_layout.addWidget(self.multimodal_audio_input, 1, 1)
        audio_browse_button = QPushButton("浏览...")
        audio_browse_button.clicked.connect(self.browse_multimodal_audio_file)
        file_layout.addWidget(audio_browse_button, 1, 2)
        
        # 视频文件
        file_layout.addWidget(QLabel("视频:"), 2, 0)
        self.multimodal_video_input = QLineEdit()
        self.multimodal_video_input.setPlaceholderText("选择视频文件...")
        file_layout.addWidget(self.multimodal_video_input, 2, 1)
        video_browse_button = QPushButton("浏览...")
        video_browse_button.clicked.connect(self.browse_multimodal_video_file)
        file_layout.addWidget(video_browse_button, 2, 2)
        
        layout.addWidget(file_group)
        
        # 搜索按钮
        search_button = QPushButton("多模态搜索")
        search_button.clicked.connect(self.perform_multimodal_search)
        layout.addWidget(search_button)
        
        # 结果区域
        self.create_results_area(layout, "multimodal")
        
        return tab
    
    def create_results_area(self, parent_layout, search_type):
        """创建结果区域"""
        results_group = QGroupBox("搜索结果")
        results_layout = QVBoxLayout(results_group)
        
        # 结果表格
        if search_type == "text":
            self.text_results_table = QTableWidget()
            self.text_results_table.setColumnCount(4)
            self.text_results_table.setHorizontalHeaderLabels(["文件路径", "文件类型", "相似度", "时间戳"])
            results_layout.addWidget(self.text_results_table)
        elif search_type == "image":
            self.image_results_table = QTableWidget()
            self.image_results_table.setColumnCount(4)
            self.image_results_table.setHorizontalHeaderLabels(["文件路径", "文件类型", "相似度", "时间戳"])
            results_layout.addWidget(self.image_results_table)
        elif search_type == "audio":
            self.audio_results_table = QTableWidget()
            self.audio_results_table.setColumnCount(4)
            self.audio_results_table.setHorizontalHeaderLabels(["文件路径", "文件类型", "相似度", "时间戳"])
            results_layout.addWidget(self.audio_results_table)
        elif search_type == "video":
            self.video_results_table = QTableWidget()
            self.video_results_table.setColumnCount(4)
            self.video_results_table.setHorizontalHeaderLabels(["文件路径", "文件类型", "相似度", "时间戳"])
            results_layout.addWidget(self.video_results_table)
        elif search_type == "multimodal":
            self.multimodal_results_table = QTableWidget()
            self.multimodal_results_table.setColumnCount(4)
            self.multimodal_results_table.setHorizontalHeaderLabels(["文件路径", "文件类型", "相似度", "时间戳"])
            results_layout.addWidget(self.multimodal_results_table)
        
        parent_layout.addWidget(results_group)
    
    def create_file_manager_tab(self):
        """创建文件管理选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文件树
        self.file_tree = QTreeView()
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(QDir.rootPath())
        self.file_tree.setModel(self.file_model)
        self.file_tree.setRootIndex(self.file_model.index(QDir.homePath()))
        self.file_tree.setAnimated(False)
        self.file_tree.setIndentation(20)
        self.file_tree.setSortingEnabled(True)
        
        layout.addWidget(self.file_tree)
        
        return tab
    
    def create_timeline_tab(self):
        """创建时间线选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 时间线控件占位
        timeline_label = QLabel("时间线视图（待实现）")
        timeline_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(timeline_label)
        
        return tab
    
    def create_face_management_tab(self):
        """创建人脸管理选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 人脸管理控件占位
        face_label = QLabel("人脸管理视图（待实现）")
        face_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(face_label)
        
        return tab
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # 连接状态
        self.connection_label = QLabel("未连接")
        self.status_bar.addPermanentWidget(self.connection_label)
    
    def create_dock_widgets(self):
        """创建停靠窗口"""
        # 系统监控停靠窗口
        self.monitor_dock = QDockWidget("系统监控", self)
        self.monitor_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        monitor_widget = QWidget()
        monitor_layout = QVBoxLayout(monitor_widget)
        
        # CPU使用率
        cpu_label = QLabel("CPU使用率:")
        monitor_layout.addWidget(cpu_label)
        self.cpu_progress = QProgressBar()
        monitor_layout.addWidget(self.cpu_progress)
        
        # 内存使用率
        memory_label = QLabel("内存使用率:")
        monitor_layout.addWidget(memory_label)
        self.memory_progress = QProgressBar()
        monitor_layout.addWidget(self.memory_progress)
        
        # 磁盘使用率
        disk_label = QLabel("磁盘使用率:")
        monitor_layout.addWidget(disk_label)
        self.disk_progress = QProgressBar()
        monitor_layout.addWidget(self.disk_progress)
        
        self.monitor_dock.setWidget(monitor_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.monitor_dock)
    
    def apply_styles(self):
        """应用样式"""
        # 设置现代风格
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #409EFF;
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
            }
            
            QPushButton {
                background-color: #409EFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            
            QPushButton:hover {
                background-color: #66b1ff;
            }
            
            QPushButton:pressed {
                background-color: #3a8ee6;
            }
            
            QLineEdit {
                padding: 8px;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
            }
            
            QLineEdit:focus {
                border-color: #409EFF;
            }
            
            QTableWidget {
                gridline-color: #e4e7ed;
                selection-background-color: #f5f7fa;
            }
            
            QHeaderView::section {
                background-color: #f5f7fa;
                padding: 8px;
                border: 1px solid #e4e7ed;
            }
        """)
    
    def init_state(self):
        """初始化状态"""
        self.is_searching = False
        self.current_search_type = None
    
    def connect_signals(self):
        """连接信号"""
        # 连接搜索工作线程信号
        self.search_worker.search_started.connect(self.on_search_started)
        self.search_worker.search_progress.connect(self.on_search_progress)
        self.search_worker.search_completed.connect(self.on_search_completed)
        self.search_worker.search_failed.connect(self.on_search_failed)
    
    def start_timers(self):
        """启动定时器"""
        # 系统监控定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_system_monitor)
        self.monitor_timer.start(5000)  # 每5秒更新一次
    
    def on_tab_changed(self, index):
        """选项卡切换事件"""
        tab_name = self.tab_widget.tabText(index)
        self.status_label.setText(f"当前选项卡: {tab_name}")
    
    def on_file_tree_double_clicked(self, index):
        """文件树双击事件"""
        path = self.file_model.filePath(index)
        self.status_label.setText(f"选中文件: {path}")
    
    def switch_tab(self, tab_name):
        """切换到指定选项卡"""
        tab_map = {
            "text_search": 0,
            "image_search": 1,
            "audio_search": 2,
            "video_search": 3,
            "multimodal_search": 4,
            "file_manager": 5,
            "timeline": 6,
            "face_management": 7
        }
        
        if tab_name in tab_map:
            self.tab_widget.setCurrentIndex(tab_map[tab_name])
    
    def open_file(self):
        """打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", "所有文件 (*.*)"
        )
        if file_path:
            self.status_label.setText(f"打开文件: {file_path}")
    
    def open_folder(self):
        """打开文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "打开文件夹"
        )
        if folder_path:
            self.status_label.setText(f"打开文件夹: {folder_path}")
    
    def import_files(self):
        """导入文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "导入文件", "", "所有文件 (*.*)"
        )
        if file_paths:
            self.status_label.setText(f"导入 {len(file_paths)} 个文件")
    
    def browse_image_file(self):
        """浏览图像文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图像文件", "", 
            "图像文件 (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            self.image_path_input.setText(file_path)
    
    def browse_audio_file(self):
        """浏览音频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "", 
            "音频文件 (*.mp3 *.wav *.m4a *.flac *.ogg)"
        )
        if file_path:
            self.audio_path_input.setText(file_path)
    
    def browse_video_file(self):
        """浏览视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", 
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv)"
        )
        if file_path:
            self.video_path_input.setText(file_path)
    
    def browse_multimodal_image_file(self):
        """浏览多模态图像文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图像文件", "", 
            "图像文件 (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            self.multimodal_image_input.setText(file_path)
    
    def browse_multimodal_audio_file(self):
        """浏览多模态音频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "", 
            "音频文件 (*.mp3 *.wav *.m4a *.flac *.ogg)"
        )
        if file_path:
            self.multimodal_audio_input.setText(file_path)
    
    def browse_multimodal_video_file(self):
        """浏览多模态视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", 
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv)"
        )
        if file_path:
            self.multimodal_video_input.setText(file_path)
    
    def perform_text_search(self):
        """执行文本搜索"""
        query = self.text_search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "警告", "请输入搜索关键词")
            return
        
        # 启动搜索工作线程
        self.search_worker.start_text_search(query)
    
    def perform_image_search(self):
        """执行图像搜索"""
        file_path = self.image_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择图像文件")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "文件不存在")
            return
        
        # 启动搜索工作线程
        self.search_worker.start_image_search(file_path)
    
    def perform_audio_search(self):
        """执行音频搜索"""
        file_path = self.audio_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择音频文件")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "文件不存在")
            return
        
        # 启动搜索工作线程
        self.search_worker.start_audio_search(file_path)
    
    def perform_video_search(self):
        """执行视频搜索"""
        file_path = self.video_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择视频文件")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "文件不存在")
            return
        
        # 启动搜索工作线程
        self.search_worker.start_video_search(file_path)
    
    def perform_multimodal_search(self):
        """执行多模态搜索"""
        text_query = self.multimodal_text_input.text().strip()
        image_path = self.multimodal_image_input.text().strip()
        audio_path = self.multimodal_audio_input.text().strip()
        video_path = self.multimodal_video_input.text().strip()
        
        if not any([text_query, image_path, audio_path, video_path]):
            QMessageBox.warning(self, "警告", "请至少提供一种查询条件")
            return
        
        # 启动搜索工作线程
        self.search_worker.start_multimodal_search(
            query_text=text_query if text_query else None,
            image_path=image_path if image_path else None,
            audio_path=audio_path if audio_path else None,
            video_path=video_path if video_path else None
        )
    
    def on_text_search_completed(self):
        """文本搜索完成"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("文本搜索完成")
        
        # TODO: 更新结果表格
        self.text_results_table.setRowCount(0)
    
    def on_image_search_completed(self):
        """图像搜索完成"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("图像搜索完成")
        
        # TODO: 更新结果表格
        self.image_results_table.setRowCount(0)
    
    def on_audio_search_completed(self):
        """音频搜索完成"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("音频搜索完成")
        
        # TODO: 更新结果表格
        self.audio_results_table.setRowCount(0)
    
    def on_video_search_completed(self):
        """视频搜索完成"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("视频搜索完成")
        
        # TODO: 更新结果表格
        self.video_results_table.setRowCount(0)
    
    def on_search_started(self, search_name):
        """搜索开始"""
        self.status_label.setText(f"正在{search_name}...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
    
    def on_search_progress(self, progress, message):
        """搜索进度更新"""
        self.status_label.setText(message)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(progress)
    
    def on_search_completed(self, result):
        """搜索完成"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("搜索完成")
        
        # 根据当前活动的选项卡更新相应的结果表格
        current_tab = self.tab_widget.currentText()
        results = result.get('data', {}).get('results', [])
        
        if "文本搜索" in current_tab:
            self.update_results_table(self.text_results_table, results)
        elif "图像搜索" in current_tab:
            self.update_results_table(self.image_results_table, results)
        elif "音频搜索" in current_tab:
            self.update_results_table(self.audio_results_table, results)
        elif "视频搜索" in current_tab:
            self.update_results_table(self.video_results_table, results)
        elif "多模态" in current_tab:
            self.update_results_table(self.multimodal_results_table, results)
    
    def on_search_failed(self, error_message):
        """搜索失败"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("搜索失败")
        QMessageBox.critical(self, "搜索错误", error_message)
    
    def update_results_table(self, table, results):
        """更新结果表格"""
        table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # 文件路径
            file_path = result.get('file_path', '')
            table.setItem(row, 0, QTableWidgetItem(file_path))
            
            # 文件类型
            file_type = result.get('file_type', '')
            table.setItem(row, 1, QTableWidgetItem(file_type))
            
            # 相似度
            similarity = result.get('score', 0)
            table.setItem(row, 2, QTableWidgetItem(f"{similarity:.3f}"))
            
            # 时间戳
            timestamp = ''
            if 'start_time_ms' in result:
                # 格式化时间戳为 HH:MM:SS
                ms = result['start_time_ms']
                hours = ms // 3600000
                minutes = (ms % 3600000) // 60000
                seconds = (ms % 60000) // 1000
                timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            elif 'created_at' in result:
                timestamp = result['created_at']
            
            table.setItem(row, 3, QTableWidgetItem(timestamp))
        
        # 调整列宽
        table.resizeColumnsToContents()
    
    def on_multimodal_search_completed(self):
        """多模态搜索完成"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("多模态搜索完成")
        
        # TODO: 更新结果表格
        self.multimodal_results_table.setRowCount(0)
    
    def update_system_monitor(self):
        """更新系统监控"""
        try:
            import psutil
            
            # 更新CPU使用率
            cpu_percent = psutil.cpu_percent()
            self.cpu_progress.setValue(int(cpu_percent))
            
            # 更新内存使用率
            memory = psutil.virtual_memory()
            self.memory_progress.setValue(memory.percent)
            
            # 更新磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.disk_progress.setValue(int(disk_percent))
            
        except Exception as e:
            logger.error(f"更新系统监控失败: {e}")
    
    def show_config_dialog(self):
        """显示配置对话框"""
        # TODO: 实现配置对话框
        QMessageBox.information(self, "提示", "配置对话框功能待实现")
    
    def show_system_status(self):
        """显示系统状态"""
        # TODO: 实现系统状态对话框
        QMessageBox.information(self, "提示", "系统状态功能待实现")
    
    def show_face_management(self):
        """显示人脸管理"""
        self.switch_tab("face_management")
    
    def show_about_dialog(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, 
            "关于 mSearch", 
            "<h3>mSearch - 多模态智能检索系统</h3>"
            "<p>版本: 0.1.0</p>"
            "<p>一个强大的多模态智能检索系统，支持文本、图像、音频和视频的智能搜索。</p>"
            "<p>© 2024 mSearch Team</p>"
        )
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止搜索工作线程
        if hasattr(self, 'search_worker') and self.search_worker.isRunning():
            self.search_worker.stop_search()
            self.search_worker.wait()
        
        # 保存窗口状态
        settings = QSettings()
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        
        # 接受关闭事件
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("mSearch")
    app.setOrganizationName("mSearch Team")
    
    # 加载窗口状态
    settings = QSettings("mSearch", "MainWindow")
    
    # 创建主窗口
    window = MainWindow()
    
    # 恢复窗口状态
    if settings.contains("geometry"):
        window.restoreGeometry(settings.value("geometry"))
    if settings.contains("windowState"):
        window.restoreState(settings.value("windowState"))
    
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()