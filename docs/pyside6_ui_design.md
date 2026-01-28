# PySide6 桌面 UI 设计方案

**文档版本**：v1.0  
**最后更新**：2026-01-24  
**适用范围**：msearch 多模态搜索系统桌面客户端
**对应设计文档**：[design.md](./design.md)

---

> **文档定位**：本文档是 [design.md](./design.md) 的补充文档，详细展开第 2.10 节"桌面 UI 系统"的内容。

**相关文档**：
- [design.md](./design.md) - 主设计文档
- [api.md](./api.md) - API接口文档

---

## 1. UI 设计原则

### 1.1 核心设计理念

**用户体验优先**：
- 简洁直观的界面，降低学习成本
- 高效的工作流程，减少操作步骤
- 响应式设计，适配不同屏幕尺寸
- 现代化的视觉风格，提升用户体验

**功能完整性**：
- 支持多模态检索（文本、图像、视频、音频）
- 提供数据管理和配置功能
- 实时状态监控和反馈
- 任务进度展示

**性能优化**：
- 异步加载，避免界面卡顿
- 虚拟滚动，支持大量数据展示
- 缓存机制，提升响应速度
- 资源监控，确保流畅运行

### 1.2 设计风格

**现代扁平化设计**：
- 简洁的线条和图标
- 清晰的视觉层次
- 适当的留白和间距
- 柔和的阴影效果

**配色方案**：
- 主色调：深蓝色系（#165DFF）- 专业、可信赖
- 辅助色：橙色系（#FF7D00）- 活力、创新
- 中性色：深灰（#1D2129）、中灰（#4E5969）、浅灰（#C9CDD4）
- 背景色：白色（#FFFFFF）、浅灰（#F2F3F5）
- 文本色：深灰（#1D2129）、中灰（#4E5969）、浅灰（#86909C）

**字体选择**：
- 主字体：Inter（跨平台无衬线字体）
- 备用字体：系统默认无衬线字体
- 字体大小：14px（正文）、16px（标题）、12px（辅助文本）

---

## 2. 整体架构设计

### 2.1 应用架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PySide6 桌面应用架构                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              MainWindow                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  菜单栏      │  │  工具栏      │  │  状态栏      │  │  主内容区    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ SearchModule │          │  DataModule  │          │ ConfigModule │
│  搜索模块     │          │  数据管理模块  │          │  配置模块     │
└──────────────┘          └──────────────┘          └──────────────┘
        │                          │                          │
        ▼                          ▼                          ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│  SearchBar   │          │  DataManager │          │  Settings    │
│  搜索栏       │          │  数据管理器   │          │  设置面板     │
└──────────────┘          └──────────────┘          └──────────────┘
        │                          │                          │
        ▼                          ▼                          ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ ResultPanel  │          │  TaskManager │          │  AboutDialog │
│ 结果展示面板   │          │  任务管理器   │          │  关于对话框   │
└──────────────┘          └──────────────┘          └──────────────┘

```

### 2.2 模块划分

**核心模块**：
1. **搜索模块** - 提供多模态检索功能
2. **数据管理模块** - 管理索引和数据
3. **配置模块** - 系统设置和配置
4. **状态监控模块** - 实时状态展示
5. **任务管理模块** - 任务进度和历史

---

## 3. 主窗口设计

### 3.1 主窗口布局

```python
class MainWindow(QMainWindow):
    """
    主窗口 - 应用程序的主界面
    """
    
    def __init__(self, config_manager: ConfigManager, 
                 search_engine: SearchEngine,
                 task_manager: TaskManager):
        super().__init__()
        self.config_manager = config_manager
        self.search_engine = search_engine
        self.task_manager = task_manager
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """初始化 UI 组件"""
        # 设置窗口标题和大小
        self.setWindowTitle("msearch - 多模态搜索系统")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 添加顶部工具栏
        self.toolbar = self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)
        
        # 创建中央内容区域（左右布局）
        self.central_layout = QHBoxLayout()
        self.central_layout.setContentsMargins(20, 20, 20, 20)
        self.central_layout.setSpacing(20)
        
        # 左侧面板（搜索和过滤）
        self.left_panel = self._create_left_panel()
        self.central_layout.addWidget(self.left_panel, stretch=1)
        
        # 右侧面板（结果展示）
        self.right_panel = self._create_right_panel()
        self.central_layout.addWidget(self.right_panel, stretch=3)
        
        self.main_layout.addLayout(self.central_layout)
        
        # 添加底部状态栏
        self.statusbar = self._create_statusbar()
        self.setStatusBar(self.statusbar)
    
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
        self.index_btn.setFixedSize(100, 36)
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
                background-color: rgba(255, 255, 255, 0.4);
            }
        """)
        layout.addWidget(self.index_btn)
        
        self.settings_btn = QPushButton("⚙️ 设置")
        self.settings_btn.setFixedSize(80, 36)
        self.settings_btn.setStyleSheet(self.index_btn.styleSheet())
        layout.addWidget(self.settings_btn)
        
        return toolbar
    
    def _create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        panel.setFixedWidth(380)
        panel.setStyleSheet("""
            QWidget {
                background-color: #F2F3F5;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 搜索栏
        self.search_bar = SearchBar(self.search_engine)
        layout.addWidget(self.search_bar)
        
        # 过滤面板
        self.filter_panel = FilterPanel()
        layout.addWidget(self.filter_panel)
        
        # 统计信息
        self.stats_panel = StatsPanel()
        layout.addWidget(self.stats_panel)
        
        layout.addStretch()
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 结果标题栏
        self.result_header = ResultHeader()
        layout.addWidget(self.result_header)
        
        # 结果展示区
        self.result_view = ResultView()
        layout.addWidget(self.result_view)
        
        return panel
    
    def _create_statusbar(self) -> QStatusBar:
        """创建状态栏"""
        statusbar = QStatusBar()
        statusbar.setFixedHeight(36)
        statusbar.setStyleSheet("""
            QStatusBar {
                background-color: #F7F8FA;
                border-top: 1px solid #E5E6EB;
                font-size: 12px;
                color: #4E5969;
            }
        """)
        
        # 状态信息
        self.status_label = QLabel("就绪")
        statusbar.addWidget(self.status_label)
        
        statusbar.addPermanentWidget(QLabel("索引数量: "))
        self.index_count_label = QLabel("0")
        statusbar.addPermanentWidget(self.index_count_label)
        
        statusbar.addPermanentWidget(QLabel(" | "))
        statusbar.addPermanentWidget(QLabel("内存使用: "))
        self.memory_label = QLabel("0 MB")
        statusbar.addPermanentWidget(self.memory_label)
        
        return statusbar
    
    def setup_connections(self):
        """设置信号连接"""
        # 搜索栏信号
        self.search_bar.search_triggered.connect(self._on_search)
        
        # 过滤面板信号
        self.filter_panel.filter_changed.connect(self._on_filter_changed)
        
        # 工具栏按钮
        self.index_btn.clicked.connect(self._show_index_manager)
        self.settings_btn.clicked.connect(self._show_settings)
        
        # 任务管理器信号
        self.task_manager.task_updated.connect(self._on_task_updated)
    
    def _on_search(self, query: str, search_type: str):
        """处理搜索请求"""
        self.status_label.setText(f"正在搜索: {query}")
        # 异步执行搜索
        search_thread = SearchThread(self.search_engine, query, search_type)
        search_thread.finished.connect(self._on_search_finished)
        search_thread.start()
    
    def _on_search_finished(self, results):
        """搜索完成处理"""
        self.result_view.set_results(results)
        self.result_header.update_count(len(results))
        self.status_label.setText(f"找到 {len(results)} 个结果")
```

---

## 4. 搜索模块设计

### 4.1 搜索栏组件

```python
class SearchBar(QWidget):
    """
    搜索栏 - 提供多模态搜索功能
    """
    
    search_triggered = pyqtSignal(str, str)  # query, search_type
    
    def __init__(self, search_engine: SearchEngine):
        super().__init__()
        self.search_engine = search_engine
        self.setup_ui()
    
    def setup_ui(self):
        """初始化搜索栏"""
        self.setFixedHeight(180)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 标题
        title_label = QLabel("多模态搜索")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #1D2129;
            }
        """)
        layout.addWidget(title_label)
        
        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索...")
        self.search_input.setFixedHeight(48)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #C9CDD4;
                border-radius: 8px;
                padding: 0 16px;
                font-size: 14px;
                color: #1D2129;
            }
            QLineEdit:focus {
                border-color: #165DFF;
                outline: none;
            }
        """)
        layout.addWidget(self.search_input)
        
        # 搜索类型选择
        type_layout = QHBoxLayout()
        type_layout.setSpacing(12)
        
        self.type_group = QButtonGroup()
        
        types = [
            ("text", "文本", "📝"),
            ("image", "图像", "🖼️"),
            ("video", "视频", "🎥"),
            ("audio", "音频", "🎵")
        ]
        
        for type_id, label, icon in types:
            btn = QPushButton(f"{icon} {label}")
            btn.setCheckable(True)
            btn.setFixedSize(80, 36)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 2px solid #E5E6EB;
                    border-radius: 6px;
                    font-size: 13px;
                    color: #4E5969;
                }
                QPushButton:checked {
                    background-color: #165DFF;
                    border-color: #165DFF;
                    color: white;
                }
                QPushButton:hover {
                    border-color: #165DFF;
                }
            """)
            self.type_group.addButton(btn, id=type_id)
            type_layout.addWidget(btn)
        
        # 默认选择文本搜索
        self.type_group.button("text").setChecked(True)
        
        layout.addLayout(type_layout)
        
        # 搜索按钮
        self.search_btn = QPushButton("🔍 搜索")
        self.search_btn.setFixedHeight(48)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #165DFF;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #0F4CD3;
            }
            QPushButton:pressed {
                background-color: #0A389E;
            }
            QPushButton:disabled {
                background-color: #86909C;
            }
        """)
        layout.addWidget(self.search_btn)
        
        # 设置连接
        self.search_input.returnPressed.connect(self._on_search)
        self.search_btn.clicked.connect(self._on_search)
    
    def _on_search(self):
        """触发搜索"""
        query = self.search_input.text().strip()
        if not query:
            return
        
        selected_id = self.type_group.checkedId()
        search_type = self.type_group.button(selected_id).objectName() if selected_id else "text"
        
        self.search_triggered.emit(query, search_type)
```

### 4.2 过滤面板

```python
class FilterPanel(QWidget):
    """
    过滤面板 - 提供搜索结果过滤功能
    """
    
    filter_changed = pyqtSignal(dict)  # filter_params
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """初始化过滤面板"""
        self.setFixedHeight(220)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 标题
        title_label = QLabel("搜索过滤")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1D2129;
            }
        """)
        layout.addWidget(title_label)
        
        # 文件类型过滤
        type_layout = QHBoxLayout()
        type_layout.setSpacing(8)
        
        type_label = QLabel("文件类型:")
        type_label.setFixedWidth(60)
        type_label.setStyleSheet("color: #4E5969; font-size: 14px;")
        type_layout.addWidget(type_label)
        
        self.file_type_combo = QComboBox()
        self.file_type_combo.addItems(["全部", "图片", "视频", "音频", "文档"])
        self.file_type_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #C9CDD4;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 14px;
                color: #1D2129;
                min-width: 150px;
            }
        """)
        type_layout.addWidget(self.file_type_combo)
        
        layout.addLayout(type_layout)
        
        # 时间范围过滤
        time_layout = QHBoxLayout()
        time_layout.setSpacing(8)
        
        time_label = QLabel("时间范围:")
        time_label.setFixedWidth(60)
        time_label.setStyleSheet("color: #4E5969; font-size: 14px;")
        time_layout.addWidget(time_label)
        
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems([
            "全部时间", "今天", "本周", "本月", "今年", "自定义"
        ])
        self.time_range_combo.setStyleSheet(self.file_type_combo.styleSheet())
        time_layout.addWidget(self.time_range_combo)
        
        layout.addLayout(time_layout)
        
        # 自定义时间范围（默认隐藏）
        self.custom_time_widget = QWidget()
        custom_layout = QHBoxLayout(self.custom_time_widget)
        custom_layout.setSpacing(8)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setStyleSheet("""
            QDateEdit {
                background-color: white;
                border: 1px solid #C9CDD4;
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
            }
        """)
        custom_layout.addWidget(self.start_date)
        
        custom_layout.addWidget(QLabel("至"))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setStyleSheet(self.start_date.styleSheet())
        custom_layout.addWidget(self.end_date)
        
        layout.addWidget(self.custom_time_widget)
        self.custom_time_widget.hide()
        
        # 相似度阈值
        score_layout = QHBoxLayout()
        score_layout.setSpacing(8)
        
        score_label = QLabel("相似度:")
        score_label.setFixedWidth(60)
        score_label.setStyleSheet("color: #4E5969; font-size: 14px;")
        score_layout.addWidget(score_label)
        
        self.score_slider = QSlider(Qt.Horizontal)
        self.score_slider.setRange(0, 100)
        self.score_slider.setValue(70)
        self.score_slider.setStyleSheet("""
            QSlider::handle:horizontal {
                background-color: #165DFF;
                border: 2px solid #165DFF;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #C9CDD4;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background-color: #165DFF;
                border-radius: 3px;
            }
        """)
        score_layout.addWidget(self.score_slider)
        
        self.score_label = QLabel("70%")
        self.score_label.setFixedWidth(40)
        self.score_label.setStyleSheet("color: #165DFF; font-weight: bold;")
        score_layout.addWidget(self.score_label)
        
        layout.addLayout(score_layout)
        
        # 应用按钮
        self.apply_btn = QPushButton("应用过滤")
        self.apply_btn.setFixedHeight(36)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF7D00;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                color: white;
            }
            QPushButton:hover {
                background-color: #E66F00;
            }
        """)
        layout.addWidget(self.apply_btn)
        
        # 设置连接
        self.time_range_combo.currentIndexChanged.connect(self._on_time_range_changed)
        self.score_slider.valueChanged.connect(self._on_score_changed)
        self.apply_btn.clicked.connect(self._on_apply)
    
    def _on_time_range_changed(self, index):
        """时间范围变化处理"""
        self.custom_time_widget.setVisible(index == 5)  # 自定义
    
    def _on_score_changed(self, value):
        """相似度变化处理"""
        self.score_label.setText(f"{value}%")
    
    def _on_apply(self):
        """应用过滤条件"""
        filters = {
            "file_type": self.file_type_combo.currentText(),
            "time_range": self.time_range_combo.currentText(),
            "start_date": self.start_date.date().toString("yyyy-MM-dd") if self.custom_time_widget.isVisible() else None,
            "end_date": self.end_date.date().toString("yyyy-MM-dd") if self.custom_time_widget.isVisible() else None,
            "similarity": self.score_slider.value() / 100
        }
        
        self.filter_changed.emit(filters)
```

---

## 5. 结果展示模块

### 5.1 结果视图

```python
class ResultView(QWidget):
    """
    结果视图 - 展示搜索结果
    """
    
    result_selected = pyqtSignal(dict)  # result_data
    
    def __init__(self):
        super().__init__()
        self.results = []
        self.setup_ui()
    
    def setup_ui(self):
        """初始化结果视图"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 使用 QListWidget 展示结果
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                selection-background-color: #E8F3FF;
                selection-color: #165DFF;
            }
            QListWidget::item {
                border-bottom: 1px solid #F2F3F5;
                padding: 12px;
                height: 100px;
            }
            QListWidget::item:hover {
                background-color: #F7F8FA;
            }
        """)
        self.list_widget.setUniformItemSizes(True)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        
        layout.addWidget(self.list_widget)
        
        # 设置连接
        self.list_widget.itemClicked.connect(self._on_item_clicked)
    
    def set_results(self, results):
        """设置搜索结果"""
        self.results = results
        self.list_widget.clear()
        
        for result in results:
            item = QListWidgetItem()
            item_widget = ResultItemWidget(result)
            item.setSizeHint(item_widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, item_widget)
    
    def _on_item_clicked(self, item):
        """处理结果点击"""
        index = self.list_widget.row(item)
        if 0 <= index < len(self.results):
            self.result_selected.emit(self.results[index])


class ResultItemWidget(QWidget):
    """
    结果项组件 - 展示单个搜索结果
    """
    
    def __init__(self, result: dict):
        super().__init__()
        self.result = result
        self.setup_ui()
    
    def setup_ui(self):
        """初始化结果项"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 缩略图
        thumbnail = self._create_thumbnail()
        layout.addWidget(thumbnail)
        
        # 信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        # 文件名
        name_label = QLabel(self.result.get("filename", "未知文件"))
        name_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: bold;
                color: #1D2129;
            }
        """)
        name_label.setWordWrap(True)
        info_layout.addWidget(name_label)
        
        # 文件信息
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(16)
        
        file_type = self._get_file_type_icon()
        type_label = QLabel(f"{file_type} {self.result.get('file_type', '未知')}")
        type_label.setStyleSheet("color: #86909C; font-size: 13px;")
        meta_layout.addWidget(type_label)
        
        size_label = QLabel(self._format_size(self.result.get('size', 0)))
        size_label.setStyleSheet("color: #86909C; font-size: 13px;")
        meta_layout.addWidget(size_label)
        
        date_label = QLabel(self.result.get('modified_time', '未知时间'))
        date_label.setStyleSheet("color: #86909C; font-size: 13px;")
        meta_layout.addWidget(date_label)
        
        meta_layout.addStretch()
        
        # 相似度
        score = self.result.get('similarity', 0)
        score_label = QLabel(f"相似度: {score:.1%}")
        score_label.setStyleSheet("""
            QLabel {
                color: #FF7D00;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        meta_layout.addWidget(score_label)
        
        info_layout.addLayout(meta_layout)
        
        # 文件路径
        path_label = QLabel(self.result.get('path', ''))
        path_label.setStyleSheet("color: #86909C; font-size: 12px;")
        path_label.setWordWrap(True)
        info_layout.addWidget(path_label)
        
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        layout.addStretch()
    
    def _create_thumbnail(self) -> QLabel:
        """创建缩略图"""
        thumbnail = QLabel()
        thumbnail.setFixedSize(80, 80)
        thumbnail.setStyleSheet("""
            QLabel {
                background-color: #F2F3F5;
                border-radius: 8px;
                border: 1px solid #E5E6EB;
            }
        """)
        thumbnail.setAlignment(Qt.AlignCenter)
        
        # 根据文件类型显示不同图标
        file_type = self.result.get('file_type', '')
        if file_type == 'image':
            thumbnail.setText("🖼️")
        elif file_type == 'video':
            thumbnail.setText("🎥")
        elif file_type == 'audio':
            thumbnail.setText("🎵")
        else:
            thumbnail.setText("📄")
        
        return thumbnail
    
    def _get_file_type_icon(self) -> str:
        """获取文件类型图标"""
        file_type = self.result.get('file_type', '')
        icons = {
            'image': '🖼️',
            'video': '🎥',
            'audio': '🎵',
            'document': '📄',
            'folder': '📁'
        }
        return icons.get(file_type, '📄')
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"
```

---

## 6. 数据管理模块

### 6.1 索引管理器

```python
class IndexManagerDialog(QDialog):
    """
    索引管理器 - 管理数据索引
    """
    
    def __init__(self, config_manager: ConfigManager, task_manager: TaskManager):
        super().__init__()
        self.config_manager = config_manager
        self.task_manager = task_manager
        self.setup_ui()
    
    def setup_ui(self):
        """初始化索引管理器"""
        self.setWindowTitle("索引管理")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 标题栏
        header = QWidget()
        header_layout = QHBoxLayout(header)
        
        title_label = QLabel("索引管理")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #1D2129;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setFixedSize(80, 36)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #165DFF;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 14px;
            }
        """)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(header)
        
        # 索引列表
        self.index_table = QTableWidget()
        self.index_table.setColumnCount(4)
        self.index_table.setHorizontalHeaderLabels([
            "路径", "文件数量", "状态", "操作"
        ])
        self.index_table.horizontalHeader().setStretchLastSection(True)
        self.index_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.index_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #E5E6EB;
                border-radius: 8px;
                gridline-color: #F2F3F5;
            }
            QHeaderView::section {
                background-color: #F7F8FA;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                color: #4E5969;
            }
            QTableWidget::item {
                padding: 12px;
                font-size: 14px;
                color: #1D2129;
            }
        """)
        layout.addWidget(self.index_table)
        
        # 底部操作栏
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        
        self.add_btn = QPushButton("➕ 添加索引")
        self.add_btn.setFixedSize(120, 40)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #165DFF;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0F4CD3;
            }
        """)
        footer_layout.addWidget(self.add_btn)
        
        footer_layout.addStretch()
        
        self.export_btn = QPushButton("📤 导出索引")
        self.export_btn.setFixedSize(100, 40)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF7D00;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 14px;
            }
        """)
        footer_layout.addWidget(self.export_btn)
        
        layout.addWidget(footer)
        
        # 设置连接
        self.add_btn.clicked.connect(self._on_add_index)
        self.refresh_btn.clicked.connect(self._refresh_indexes)
    
    def _refresh_indexes(self):
        """刷新索引列表"""
        # 从配置管理器获取索引列表
        indexes = self.config_manager.get_indexes()
        
        self.index_table.setRowCount(len(indexes))
        
        for row, index in enumerate(indexes):
            # 路径
            path_item = QTableWidgetItem(index.get('path', ''))
            self.index_table.setItem(row, 0, path_item)
            
            # 文件数量
            count_item = QTableWidgetItem(str(index.get('file_count', 0)))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.index_table.setItem(row, 1, count_item)
            
            # 状态
            status = index.get('status', 'unknown')
            status_item = QTableWidgetItem(self._get_status_text(status))
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(self._get_status_color(status))
            self.index_table.setItem(row, 2, status_item)
            
            # 操作按钮
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(8)
            
            scan_btn = QPushButton("扫描")
            scan_btn.setFixedSize(60, 28)
            scan_btn.setStyleSheet("""
                QPushButton {
                    background-color: #165DFF;
                    border: none;
                    border-radius: 4px;
                    color: white;
                    font-size: 12px;
                }
            """)
            scan_btn.clicked.connect(lambda checked, idx=index: self._on_scan(idx))
            action_layout.addWidget(scan_btn)
            
            remove_btn = QPushButton("删除")
            remove_btn.setFixedSize(60, 28)
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F53F3F;
                    border: none;
                    border-radius: 4px;
                    color: white;
                    font-size: 12px;
                }
            """)
            remove_btn.clicked.connect(lambda checked, idx=index: self._on_remove(idx))
            action_layout.addWidget(remove_btn)
            
            self.index_table.setCellWidget(row, 3, action_widget)
    
    def _get_status_text(self, status: str) -> str:
        """获取状态文本"""
        status_map = {
            'active': '活跃',
            'scanning': '扫描中',
            'paused': '已暂停',
            'error': '错误',
            'unknown': '未知'
        }
        return status_map.get(status, '未知')
    
    def _get_status_color(self, status: str) -> QColor:
        """获取状态颜色"""
        color_map = {
            'active': QColor('#00B42A'),
            'scanning': QColor('#165DFF'),
            'paused': QColor('#FF7D00'),
            'error': QColor('#F53F3F'),
            'unknown': QColor('#86909C')
        }
        return color_map.get(status, QColor('#86909C'))
    
    def _on_add_index(self):
        """添加索引"""
        path = QFileDialog.getExistingDirectory(
            self, "选择要索引的目录", QDir.homePath()
        )
        
        if path:
            # 创建索引任务
            task = self.task_manager.create_index_task(path)
            self.task_manager.submit_task(task)
            self._refresh_indexes()
    
    def _on_scan(self, index: dict):
        """扫描索引"""
        task = self.task_manager.create_scan_task(index['path'])
        self.task_manager.submit_task(task)
        self._refresh_indexes()
    
    def _on_remove(self, index: dict):
        """删除索引"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除索引 {index.get('path', '')} 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.config_manager.remove_index(index['path'])
            self._refresh_indexes()
```

---

## 7. 配置模块

### 7.1 设置对话框

```python
class SettingsDialog(QDialog):
    """
    设置对话框 - 管理应用程序配置
    """
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.setup_ui()
    
    def setup_ui(self):
        """初始化设置对话框"""
        self.setWindowTitle("设置")
        self.setMinimumSize(700, 500)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 使用 QTabWidget 组织设置
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E5E6EB;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #F7F8FA;
                border: 1px solid #E5E6EB;
                border-bottom: none;
                padding: 12px 24px;
                margin-right: 4px;
                font-size: 14px;
                color: #4E5969;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #165DFF;
                font-weight: bold;
            }
        """)
        
        # 常规设置
        general_tab = self._create_general_tab()
        self.tab_widget.addTab(general_tab, "常规")
        
        # 模型设置
        model_tab = self._create_model_tab()
        self.tab_widget.addTab(model_tab, "模型")
        
        # 高级设置
        advanced_tab = self._create_advanced_tab()
        self.tab_widget.addTab(advanced_tab, "高级")
        
        layout.addWidget(self.tab_widget)
        
        # 底部按钮栏
        button_bar = QWidget()
        button_bar.setFixedHeight(60)
        button_bar.setStyleSheet("""
            QWidget {
                background-color: #F7F8FA;
                border-top: 1px solid #E5E6EB;
            }
        """)
        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(20, 12, 20, 12)
        button_layout.setSpacing(12)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedSize(80, 36)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #C9CDD4;
                border-radius: 6px;
                color: #4E5969;
                font-size: 14px;
            }
        """)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.setFixedSize(80, 36)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #165DFF;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0F4CD3;
            }
        """)
        button_layout.addWidget(self.save_btn)
        
        layout.addWidget(button_bar)
        
        # 设置连接
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._on_save)
    
    def _create_general_tab(self) -> QWidget:
        """创建常规设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)
        
        # 语言设置
        language_group = self._create_setting_group(
            "语言设置",
            [
                ("简体中文", "zh_CN"),
                ("English", "en_US"),
                ("日本語", "ja_JP")
            ],
            "language"
        )
        layout.addWidget(language_group)
        
        # 主题设置
        theme_group = self._create_setting_group(
            "主题设置",
            [
                ("浅色主题", "light"),
                ("深色主题", "dark"),
                ("跟随系统", "system")
            ],
            "theme"
        )
        layout.addWidget(theme_group)
        
        layout.addStretch()
        
        return tab
    
    def _create_model_tab(self) -> QWidget:
        """创建模型设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)
        
        # 模型存储路径
        path_group = QGroupBox("模型存储路径")
        path_layout = QVBoxLayout(path_group)
        path_layout.setSpacing(12)
        
        self.model_path_edit = QLineEdit()
        self.model_path_edit.setText(self.config_manager.get("model_path", "./models"))
        self.model_path_edit.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #C9CDD4;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }
        """)
        path_layout.addWidget(self.model_path_edit)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self._on_browse_model_path)
        path_layout.addWidget(browse_btn)
        
        layout.addWidget(path_group)
        
        # 模型选择
        model_group = QGroupBox("嵌入模型")
        model_layout = QVBoxLayout(model_group)
        model_layout.setSpacing(12)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "chinese-clip-vit-base-patch16",
            "chinese-clip-vit-large-patch14",
            "multilingual-clip-vit-base"
        ])
        self.model_combo.setCurrentText(
            self.config_manager.get("embedding_model", "chinese-clip-vit-base-patch16")
        )
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #C9CDD4;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 300px;
            }
        """)
        model_layout.addWidget(self.model_combo)
        
        layout.addWidget(model_group)
        
        layout.addStretch()
        
        return tab
    
    def _create_advanced_tab(self) -> QWidget:
        """创建高级设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)
        
        # 性能设置
        performance_group = QGroupBox("性能设置")
        perf_layout = QVBoxLayout(performance_group)
        perf_layout.setSpacing(16)
        
        # 并发数
        thread_layout = QHBoxLayout()
        thread_label = QLabel("最大并发数:")
        thread_label.setFixedWidth(100)
        thread_layout.addWidget(thread_label)
        
        self.thread_spin = QSpinBox()
        self.thread_spin.setRange(1, 32)
        self.thread_spin.setValue(self.config_manager.get("max_threads", 4))
        self.thread_spin.setStyleSheet("""
            QSpinBox {
                background-color: white;
                border: 1px solid #C9CDD4;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 14px;
                min-width: 100px;
            }
        """)
        thread_layout.addWidget(self.thread_spin)
        
        thread_layout.addStretch()
        perf_layout.addLayout(thread_layout)
        
        # 内存限制
        memory_layout = QHBoxLayout()
        memory_label = QLabel("内存限制 (GB):")
        memory_label.setFixedWidth(100)
        memory_layout.addWidget(memory_label)
        
        self.memory_spin = QDoubleSpinBox()
        self.memory_spin.setRange(1, 64)
        self.memory_spin.setValue(self.config_manager.get("max_memory_gb", 8))
        self.memory_spin.setStyleSheet(self.thread_spin.styleSheet())
        memory_layout.addWidget(self.memory_spin)
        
        memory_layout.addStretch()
        perf_layout.addLayout(memory_layout)
        
        layout.addWidget(performance_group)
        
        # 高级选项
        advanced_group = QGroupBox("高级选项")
        adv_layout = QVBoxLayout(advanced_group)
        adv_layout.setSpacing(12)
        
        self.auto_start_check = QCheckBox("开机自动启动")
        self.auto_start_check.setChecked(self.config_manager.get("auto_start", False))
        adv_layout.addWidget(self.auto_start_check)
        
        self.minimize_tray_check = QCheckBox("最小化到托盘")
        self.minimize_tray_check.setChecked(self.config_manager.get("minimize_to_tray", True))
        adv_layout.addWidget(self.minimize_tray_check)
        
        self.enable_logging_check = QCheckBox("启用详细日志")
        self.enable_logging_check.setChecked(self.config_manager.get("enable_logging", False))
        adv_layout.addWidget(self.enable_logging_check)
        
        layout.addWidget(advanced_group)
        
        layout.addStretch()
        
        return tab
    
    def _create_setting_group(self, title: str, options: list, config_key: str) -> QGroupBox:
        """创建设置选项组"""
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        
        current_value = self.config_manager.get(config_key, options[0][1])
        
        for label, value in options:
            radio = QRadioButton(label)
            radio.setChecked(value == current_value)
            radio.setProperty("value", value)
            radio.setProperty("config_key", config_key)
            layout.addWidget(radio)
        
        return group
    
    def _on_browse_model_path(self):
        """浏览模型路径"""
        path = QFileDialog.getExistingDirectory(
            self, "选择模型存储目录", self.model_path_edit.text()
        )
        if path:
            self.model_path_edit.setText(path)
    
    def _on_save(self):
        """保存设置"""
        # 保存常规设置
        for tab_index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(tab_index)
            for radio in tab.findChildren(QRadioButton):
                if radio.isChecked():
                    config_key = radio.property("config_key")
                    value = radio.property("value")
                    self.config_manager.set(config_key, value)
        
        # 保存模型设置
        self.config_manager.set("model_path", self.model_path_edit.text())
        self.config_manager.set("embedding_model", self.model_combo.currentText())
        
        # 保存高级设置
        self.config_manager.set("max_threads", self.thread_spin.value())
        self.config_manager.set("max_memory_gb", self.memory_spin.value())
        self.config_manager.set("auto_start", self.auto_start_check.isChecked())
        self.config_manager.set("minimize_to_tray", self.minimize_tray_check.isChecked())
        self.config_manager.set("enable_logging", self.enable_logging_check.isChecked())
        
        # 保存配置
        self.config_manager.save()
        
        QMessageBox.information(self, "保存成功", "设置已保存，部分设置需要重启应用生效")
        self.accept()
```

---

## 8. 任务管理模块

### 8.1 任务管理器

```python
class TaskManagerWidget(QWidget):
    """
    任务管理器 - 管理和展示后台任务
    """
    
    def __init__(self, task_manager: TaskManager):
        super().__init__()
        self.task_manager = task_manager
        self.setup_ui()
    
    def setup_ui(self):
        """初始化任务管理器"""
        self.setFixedWidth(350)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题栏
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet("""
            QWidget {
                background-color: #165DFF;
                border-radius: 8px 8px 0 0;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        
        title_label = QLabel("任务管理器")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.task_count_label = QLabel("0 个任务")
        self.task_count_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
            }
        """)
        header_layout.addWidget(self.task_count_label)
        
        layout.addWidget(header)
        
        # 任务列表
        self.task_list = QListWidget()
        self.task_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #F2F3F5;
                padding: 12px;
                height: 80px;
            }
        """)
        layout.addWidget(self.task_list)
        
        # 设置连接
        self.task_manager.task_updated.connect(self._on_task_updated)
        self._refresh_tasks()
    
    def _refresh_tasks(self):
        """刷新任务列表"""
        tasks = self.task_manager.get_active_tasks()
        self.task_list.clear()
        self.task_count_label.setText(f"{len(tasks)} 个任务")
        
        for task in tasks:
            item = QListWidgetItem()
            item_widget = TaskItemWidget(task)
            item.setSizeHint(item_widget.sizeHint())
            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, item_widget)
    
    def _on_task_updated(self, task):
        """任务更新处理"""
        self._refresh_tasks()


class TaskItemWidget(QWidget):
    """
    任务项组件 - 展示单个任务
    """
    
    def __init__(self, task: dict):
        super().__init__()
        self.task = task
        self.setup_ui()
    
    def setup_ui(self):
        """初始化任务项"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 任务信息
        info_layout = QHBoxLayout()
        
        # 任务类型图标
        icon_label = QLabel(self._get_task_icon())
        icon_label.setFixedSize(32, 32)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #E8F3FF;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(icon_label)
        
        # 任务信息
        task_info = QVBoxLayout()
        
        name_label = QLabel(self.task.get("name", "未知任务"))
        name_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #1D2129;
            }
        """)
        task_info.addWidget(name_label)
        
        status_label = QLabel(self._get_status_text())
        status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #4E5969;
            }
        """)
        task_info.addWidget(status_label)
        
        info_layout.addLayout(task_info)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
        # 进度条
        progress = self.task.get("progress", 0)
        progress_bar = QProgressBar()
        progress_bar.setValue(progress)
        progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #F2F3F5;
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #165DFF;
                border-radius: 4px;
            }
        """)
        layout.addWidget(progress_bar)
        
        # 进度文本
        progress_text = QLabel(f"{progress}% - {self._get_progress_detail()}")
        progress_text.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #86909C;
            }
        """)
        layout.addWidget(progress_text)
    
    def _get_task_icon(self) -> str:
        """获取任务图标"""
        task_type = self.task.get("type", "unknown")
        icons = {
            "index": "📁",
            "scan": "🔍",
            "process": "⚙️",
            "export": "📤",
            "import": "📥",
            "unknown": "❓"
        }
        return icons.get(task_type, "❓")
    
    def _get_status_text(self) -> str:
        """获取状态文本"""
        status = self.task.get("status", "pending")
        status_map = {
            "pending": "等待中",
            "running": "运行中",
            "paused": "已暂停",
            "completed": "已完成",
            "failed": "失败"
        }
        return status_map.get(status, "未知")
    
    def _get_progress_detail(self) -> str:
        """获取进度详情"""
        total = self.task.get("total", 0)
        completed = self.task.get("completed", 0)
        
        if total > 0:
            return f"已完成 {completed}/{total}"
        return "处理中..."
```

---

## 9. 辅助组件

### 9.1 通知提示框

```python
class NotificationWidget(QWidget):
    """
    通知提示框 - 显示应用通知
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """初始化通知组件"""
        self.setFixedSize(350, 80)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E5E6EB;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)
        
        # 内容
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #1D2129;
            }
        """)
        content_layout.addWidget(self.title_label)
        
        self.message_label = QLabel()
        self.message_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #4E5969;
            }
        """)
        content_layout.addWidget(self.message_label)
        
        layout.addLayout(content_layout)
        layout.addStretch()
        
        # 关闭按钮
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 18px;
                color: #86909C;
            }
            QPushButton:hover {
                color: #1D2129;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        layout.addWidget(self.close_btn)
    
    def show_notification(self, title: str, message: str, level: str = "info"):
        """显示通知"""
        self.title_label.setText(title)
        self.message_label.setText(message)
        
        # 设置图标和样式
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        
        colors = {
            "info": "#165DFF",
            "success": "#00B42A",
            "warning": "#FF7D00",
            "error": "#F53F3F"
        }
        
        self.icon_label.setText(icons.get(level, "ℹ️"))
        self.icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: {colors.get(level, '#165DFF')}20;
                border-radius: 6px;
                padding: 4px;
            }}
        """)
        
        # 显示通知
        self.show()
        
        # 自动关闭
        QTimer.singleShot(3000, self.close)


class NotificationManager:
    """
    通知管理器 - 管理应用通知
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        """初始化"""
        self.notifications = []
    
    def show(self, title: str, message: str, level: str = "info"):
        """显示通知"""
        notification = NotificationWidget()
        notification.show_notification(title, message, level)
        self.notifications.append(notification)


# 全局通知管理器
notification_manager = NotificationManager()

---

## 10. 样式管理

### 10.1 主题管理器

```python
class ThemeManager:
    """
    主题管理器 - 管理应用主题
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.current_theme = self.config_manager.get("theme", "light")
        self.setup_theme()
    
    def setup_theme(self):
        """设置主题"""
        if self.current_theme == "dark":
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
    
    def _apply_light_theme(self):
        """应用浅色主题"""
        app = QApplication.instance()
        if app:
            app.setStyleSheet("""
                QWidget {
                    background-color: #F7F8FA;
                    color: #1D2129;
                }
                QMainWindow {
                    background-color: #F7F8FA;
                }
                QHeaderView::section {
                    background-color: #F2F3F5;
                    color: #4E5969;
                }
                QTableView {
                    background-color: white;
                    alternate-background-color: #F7F8FA;
                }
                QListWidget {
                    background-color: white;
                }
                QPushButton {
                    background-color: #165DFF;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #0F4CD3;
                }
                QPushButton:pressed {
                    background-color: #0A389E;
                }
                QLineEdit {
                    background-color: white;
                    border: 1px solid #C9CDD4;
                    border-radius: 6px;
                    padding: 8px 12px;
                }
                QLineEdit:focus {
                    border-color: #165DFF;
                }
                QComboBox {
                    background-color: white;
                    border: 1px solid #C9CDD4;
                    border-radius: 6px;
                    padding: 8px 12px;
                }
                QScrollBar:vertical {
                    background-color: #F2F3F5;
                    width: 8px;
                    border-radius: 4px;
                }
                QScrollBar::handle:vertical {
                    background-color: #C9CDD4;
                    border-radius: 4px;
                    min-height: 40px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #86909C;
                }
            """)
    
    def _apply_dark_theme(self):
        """应用深色主题"""
        app = QApplication.instance()
        if app:
            app.setStyleSheet("""
                QWidget {
                    background-color: #1D2129;
                    color: #E5E6EB;
                }
                QMainWindow {
                    background-color: #1D2129;
                }
                QHeaderView::section {
                    background-color: #272E3B;
                    color: #C9CDD4;
                }
                QTableView {
                    background-color: #272E3B;
                    alternate-background-color: #1D2129;
                }
                QListWidget {
                    background-color: #272E3B;
                }
                QPushButton {
                    background-color: #165DFF;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #0F4CD3;
                }
                QPushButton:pressed {
                    background-color: #0A389E;
                }
                QLineEdit {
                    background-color: #272E3B;
                    border: 1px solid #4E5969;
                    border-radius: 6px;
                    padding: 8px 12px;
                    color: #E5E6EB;
                }
                QLineEdit:focus {
                    border-color: #165DFF;
                }
                QComboBox {
                    background-color: #272E3B;
                    border: 1px solid #4E5969;
                    border-radius: 6px;
                    padding: 8px 12px;
                    color: #E5E6EB;
                }
                QScrollBar:vertical {
                    background-color: #272E3B;
                    width: 8px;
                    border-radius: 4px;
                }
                QScrollBar::handle:vertical {
                    background-color: #4E5969;
                    border-radius: 4px;
                    min-height: 40px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #86909C;
                }
            """)
    
    def set_theme(self, theme: str):
        """设置主题"""
        self.current_theme = theme
        self.config_manager.set("theme", theme)
        self.config_manager.save()
        self.setup_theme()
```

---

## 11. 应用启动流程

### 11.1 主程序入口

```python
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.core.config.config_manager import ConfigManager
from src.core.search.search_engine import SearchEngine
from src.core.task.task_manager import TaskManager
from src.ui.main_window import MainWindow
from src.ui.theme_manager import ThemeManager


def main():
    """应用程序主入口"""
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("msearch")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("msearch")
    
    # 启用高DPI支持
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 初始化主题管理器
    theme_manager = ThemeManager(config_manager)
    
    # 初始化搜索引擎
    search_engine = SearchEngine(config_manager)
    
    # 初始化任务管理器
    task_manager = TaskManager(config_manager)
    
    # 创建主窗口
    main_window = MainWindow(
        config_manager=config_manager,
        search_engine=search_engine,
        task_manager=task_manager
    )
    
    # 显示主窗口
    main_window.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

---

## 12. 性能优化策略

### 12.1 异步处理

**搜索异步化**：
- 使用 QThread 执行搜索操作
- 避免阻塞主线程
- 实时更新搜索进度
- 支持搜索取消

```python
class SearchThread(QThread):
    """
    搜索线程 - 异步执行搜索
    """
    
    result_ready = pyqtSignal(list)  # 搜索结果
    progress_updated = pyqtSignal(int)  # 进度
    error_occurred = pyqtSignal(str)  # 错误信息
    
    def __init__(self, search_engine: SearchEngine, query: str, search_type: str):
        super().__init__()
        self.search_engine = search_engine
        self.query = query
        self.search_type = search_type
        self._is_cancelled = False
    
    def run(self):
        """执行搜索"""
        try:
            results = self.search_engine.search(
                query=self.query,
                search_type=self.search_type,
                progress_callback=self._on_progress
            )
            
            if not self._is_cancelled:
                self.result_ready.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _on_progress(self, progress: int):
        """进度回调"""
        if not self._is_cancelled:
            self.progress_updated.emit(progress)
    
    def cancel(self):
        """取消搜索"""
        self._is_cancelled = True
```

### 12.2 虚拟滚动

**大量数据优化**：
- 使用 QTableView 或 QListView
- 实现自定义 QAbstractItemModel
- 仅渲染可见区域
- 支持百万级数据展示

```python
class ResultModel(QAbstractListModel):
    """
    结果模型 - 支持虚拟滚动
    """
    
    def __init__(self, results: list = None):
        super().__init__()
        self.results = results or []
    
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.results)
    
    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.results):
            return None
        
        result = self.results[index.row()]
        
        if role == Qt.DisplayRole:
            return result.get("filename", "")
        elif role == Qt.UserRole:
            return result
        elif role == Qt.ToolTipRole:
            return result.get("path", "")
        
        return None
    
    def set_results(self, results: list):
        """设置结果"""
        self.beginResetModel()
        self.results = results
        self.endResetModel()
```

### 12.3 缓存机制

**结果缓存**：
- 缓存最近搜索结果
- 基于 LRU 算法
- 减少重复搜索
- 提升用户体验

```python
from functools import lru_cache

class SearchCache:
    """
    搜索缓存 - 缓存搜索结果
    """
    
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
        self.order = []
    
    def get(self, key: str):
        """获取缓存"""
        if key in self.cache:
            # 移到最近使用位置
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value):
        """设置缓存"""
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.max_size:
            # 删除最旧的
            oldest = self.order.pop(0)
            del self.cache[oldest]
        
        self.cache[key] = value
        self.order.append(key)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.order.clear()
```

---

## 13. 测试与调试

### 13.1 UI 测试

```python
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from src.ui.main_window import MainWindow
from src.ui.search_bar import SearchBar


@pytest.fixture
def app(qtbot):
    """创建应用程序"""
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


def test_search_bar_initialization(qtbot):
    """测试搜索栏初始化"""
    search_bar = SearchBar(None)
    qtbot.addWidget(search_bar)
    
    assert search_bar.search_input is not None
    assert search_bar.search_btn is not None
    assert search_bar.type_group is not None


def test_search_bar_search(qtbot):
    """测试搜索功能"""
    search_bar = SearchBar(None)
    qtbot.addWidget(search_bar)
    
    # 输入搜索词
    qtbot.keyClicks(search_bar.search_input, "test query")
    
    # 点击搜索按钮
    with qtbot.waitSignal(search_bar.search_triggered, timeout=1000):
        qtbot.mouseClick(search_bar.search_btn, Qt.LeftButton)


def test_main_window_initialization(qtbot):
    """测试主窗口初始化"""
    main_window = MainWindow(None, None, None)
    qtbot.addWidget(main_window)
    
    assert main_window.search_bar is not None
    assert main_window.result_view is not None
    assert main_window.filter_panel is not None
```

---

## 14. 部署与打包

### 14.1 PyInstaller 配置

```spec
# msearch.spec

import sys
from pathlib import Path

block_cipher = None

# 项目根目录
ROOT = Path(__file__).parent

# 数据文件
datas = [
    (ROOT / "assets", "assets"),
    (ROOT / "configs", "configs"),
]

# 隐藏导入
hiddenimports = [
    "torch",
    "torchvision",
    "transformers",
    "numpy",
    "pandas",
    "lancedb",
    "sqlite3",
]

# 排除模块
excludes = [
    "tkinter",
    "matplotlib",
    "scipy",
]

# a 分析

a = Analysis(
    ["src/__main__.py"],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 可执行文件
if sys.platform == "win32":
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="msearch",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon="assets/icons/app.ico",
    )
elif sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="msearch",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    
    app = BUNDLE(
        exe,
        name="msearch.app",
        icon="assets/icons/app.icns",
        bundle_identifier="com.msearch.app",
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="msearch",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
```

### 14.2 打包命令

```bash
# Windows
pyinstaller msearch.spec

# macOS
pyinstaller msearch.spec

# Linux
pyinstaller msearch.spec
```

---

## 15. 总结

### 15.1 设计亮点

**用户体验**：
- 简洁直观的界面设计
- 高效的工作流程
- 实时状态反馈
- 多模态搜索支持

**技术实现**：
- 模块化的架构设计
- 异步处理机制
- 虚拟滚动优化
- 主题管理系统

**可扩展性**：
- 易于添加新功能
- 支持主题定制
- 灵活的配置系统
- 完善的测试覆盖

### 15.2 后续优化

**短期目标**：
- 完善深色主题
- 添加更多快捷键
- 优化搜索性能
- 增加文件预览功能

**长期目标**：
- 支持多语言
- 添加插件系统
- 实现云端同步
- 支持协作功能

---

**文档版本**：v1.0  
**最后更新**：2026-01-24  
**作者**：msearch 开发团队