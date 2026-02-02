"""
结果面板组件
显示搜索结果，支持时间轴展示（根据设计文档要求）
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QFrame,
    QGridLayout,
    QSplitter,
    QGroupBox,
    QCheckBox,
    QComboBox,
    QTabWidget,
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QPixmap, QImage, QIcon, QFont

# 导入时间轴面板
from src.ui.components.timeline_panel import TimelinePanel, TimelineItem


class ResultItemWidget(QFrame):
    """结果项组件"""

    # 信号定义
    item_clicked = Signal(dict)
    item_double_clicked = Signal(dict)

    def __init__(self, result_data: Dict[str, Any], parent=None):
        """初始化结果项"""
        super().__init__(parent)

        self.result_data = result_data
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet(
            """
            ResultItemWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
                margin: 5px;
            }
            ResultItemWidget:hover {
                border: 1px solid #4CAF50;
                background-color: #f9f9f9;
            }
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 缩略图
        thumbnail_label = QLabel()
        thumbnail_label.setFixedSize(120, 90)
        thumbnail_label.setStyleSheet("border: 1px solid #ddd; border-radius: 3px;")

        # 尝试加载缩略图
        thumbnail_path = self.result_data.get("thumbnail_path")
        if thumbnail_path and Path(thumbnail_path).exists():
            pixmap = QPixmap(thumbnail_path)
            scaled_pixmap = pixmap.scaled(
                120, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            thumbnail_label.setPixmap(scaled_pixmap)
        else:
            # 使用占位符
            thumbnail_label.setText("无缩略图")
            thumbnail_label.setAlignment(Qt.AlignCenter)
            thumbnail_label.setStyleSheet(
                """
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: #f0f0f0;
                color: #999;
            """
            )

        layout.addWidget(thumbnail_label)

        # 信息区域
        info_layout = QVBoxLayout()

        # 文件名
        file_name = self.result_data.get("file_name", "未知文件")
        name_label = QLabel(file_name)
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        name_label.setWordWrap(True)
        info_layout.addWidget(name_label)

        # 文件路径
        file_path = self.result_data.get("file_path", "")
        if file_path:
            path_label = QLabel(Path(file_path).name)
            path_label.setStyleSheet("color: #666; font-size: 10px;")
            path_label.setWordWrap(True)
            info_layout.addWidget(path_label)

        # 相似度分数
        score = self.result_data.get("score", 0.0)
        if score > 0:
            score_label = QLabel(f"相似度: {score:.2%}")
            score_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            info_layout.addWidget(score_label)

        # 模态类型
        modality = self.result_data.get("modality", "")
        if modality:
            modality_label = QLabel(f"类型: {modality}")
            modality_label.setStyleSheet("color: #666; font-size: 10px;")
            info_layout.addWidget(modality_label)

        # 时间戳（如果是视频）
        if "start_time" in self.result_data:
            start_time = self.result_data.get("start_time", 0.0)
            end_time = self.result_data.get("end_time", 0.0)
            time_label = QLabel(f"时间: {start_time:.1f}s - {end_time:.1f}s")
            time_label.setStyleSheet("color: #666; font-size: 10px;")
            info_layout.addWidget(time_label)

        info_layout.addStretch()
        layout.addLayout(info_layout)

        # 操作按钮
        button_layout = QVBoxLayout()

        open_button = QPushButton("打开")
        open_button.clicked.connect(lambda: self.item_clicked.emit(self.result_data))
        button_layout.addWidget(open_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件"""
        self.item_double_clicked.emit(self.result_data)
        super().mouseDoubleClickEvent(event)


class ResultPanel(QWidget):
    """结果面板组件"""

    # 信号定义
    result_selected = Signal(dict)
    result_opened = Signal(dict)

    def __init__(self, parent=None):
        """初始化结果面板"""
        super().__init__(parent)

        self.results: List[Dict[str, Any]] = []
        self.current_view_mode = "grid"  # grid, list
        self.show_thumbnails = True

        # 时间轴数据（根据设计文档要求）
        self.timeline_items: List[TimelineItem] = []

        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 结果面板容器
        container = QWidget()
        container.setStyleSheet(
            """
            QWidget {
                background-color: #FFFFFF;
                border-radius: 8px;
            }
        """
        )
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)

        # 标题和统计
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        title_label = QLabel("📊 搜索结果")
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #1D2129;
            }
        """
        )
        header_layout.addWidget(title_label)

        self.stats_label = QLabel("共找到 0 个结果")
        self.stats_label.setStyleSheet(
            """
            QLabel {
                color: #86909C;
                font-size: 14px;
            }
        """
        )
        header_layout.addWidget(self.stats_label)

        header_layout.addStretch()

        # 视图模式切换
        view_mode_label = QLabel("视图:")
        view_mode_label.setStyleSheet(
            """
            QLabel {
                color: #4E5969;
                font-size: 14px;
            }
        """
        )
        header_layout.addWidget(view_mode_label)

        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["⊞ 网格视图", "☰ 列表视图"])
        self.view_mode_combo.setMinimumWidth(120)
        self.view_mode_combo.currentIndexChanged.connect(self.on_view_mode_changed)
        self.view_mode_combo.setStyleSheet(
            """
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #E5E6EB;
                border-radius: 6px;
                font-size: 13px;
                background-color: #FFFFFF;
            }
            QComboBox:hover {
                border: 1px solid #165DFF;
            }
            QComboBox::drop-down {
                border: none;
            }
        """
        )
        header_layout.addWidget(self.view_mode_combo)

        container_layout.addLayout(header_layout)

        # 工具栏
        toolbar = QWidget()
        toolbar.setStyleSheet(
            """
            QWidget {
                background-color: #F2F3F5;
                border-radius: 6px;
                padding: 8px;
            }
        """
        )
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        toolbar_layout.setSpacing(15)

        self.show_thumbnail_checkbox = QCheckBox("显示缩略图")
        self.show_thumbnail_checkbox.setChecked(True)
        self.show_thumbnail_checkbox.toggled.connect(self.on_thumbnail_toggled)
        self.show_thumbnail_checkbox.setStyleSheet(
            """
            QCheckBox {
                font-size: 14px;
                color: #4E5969;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 2px solid #C9CDD4;
            }
            QCheckBox::indicator:checked {
                background-color: #165DFF;
                border-color: #165DFF;
            }
        """
        )
        toolbar_layout.addWidget(self.show_thumbnail_checkbox)

        toolbar_layout.addStretch()

        # 排序选项
        sort_label = QLabel("排序:")
        sort_label.setStyleSheet(
            """
            QLabel {
                color: #4E5969;
                font-size: 14px;
            }
        """
        )
        toolbar_layout.addWidget(sort_label)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["相似度 ↓", "相似度 ↑", "文件名 ↓", "文件名 ↑"])
        self.sort_combo.setMinimumWidth(120)
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        self.sort_combo.setStyleSheet(
            """
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #E5E6EB;
                border-radius: 6px;
                font-size: 13px;
                background-color: #FFFFFF;
            }
            QComboBox:hover {
                border: 1px solid #165DFF;
            }
            QComboBox::drop-down {
                border: none;
            }
        """
        )
        toolbar_layout.addWidget(self.sort_combo)

        # 类型过滤
        filter_label = QLabel("类型:")
        filter_label.setStyleSheet(
            """
            QLabel {
                color: #4E5969;
                font-size: 14px;
            }
        """
        )
        toolbar_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "🖼️ 图像", "🎬 视频", "🎵 音频"])
        self.filter_combo.setMinimumWidth(120)
        self.filter_combo.currentIndexChanged.connect(self.on_filter_changed)
        self.filter_combo.setStyleSheet(
            """
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #E5E6EB;
                border-radius: 6px;
                font-size: 13px;
                background-color: #FFFFFF;
            }
            QComboBox:hover {
                border: 1px solid #165DFF;
            }
            QComboBox::drop-down {
                border: none;
            }
        """
        )
        toolbar_layout.addWidget(self.filter_combo)

        container_layout.addWidget(toolbar)

        # 创建选项卡（常规结果 + 时间轴）
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            """
            QTabWidget::pane {
                border: 1px solid #E5E6EB;
                border-radius: 6px;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #F2F3F5;
                color: #4E5969;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #165DFF;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background-color: #E5E6EB;
            }
        """
        )

        # 常规结果选项卡
        self.results_tab = QWidget()
        results_layout = QVBoxLayout(self.results_tab)
        results_layout.setContentsMargins(0, 0, 0, 0)

        # 结果显示区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #F2F3F5;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #C9CDD4;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #86909C;
            }
        """
        )

        # 结果容器
        self.results_container = QWidget()
        self.results_layout = QGridLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignTop)
        self.results_layout.setSpacing(15)
        self.scroll_area.setWidget(self.results_container)

        results_layout.addWidget(self.scroll_area)
        self.tab_widget.addTab(self.results_tab, "结果列表")

        # 时间轴选项卡
        self.timeline_tab = TimelinePanel()
        self.timeline_tab.segment_selected.connect(self.on_timeline_segment_selected)
        self.timeline_tab.segment_play.connect(self.on_timeline_segment_play)
        self.tab_widget.addTab(self.timeline_tab, "时间轴")

        container_layout.addWidget(self.tab_widget)

        layout.addWidget(container)

    def set_results(self, results: List[Dict[str, Any]]):
        """设置搜索结果"""
        self.results = results
        self.update_results_display()

        # 提取视频结果的时间轴信息（根据设计文档要求）
        self.extract_timeline_from_results()

    def extract_timeline_from_results(self):
        """从搜索结果中提取时间轴信息"""
        self.timeline_items = []

        for result in self.results:
            modality = result.get("modality", "")
            if modality == "video":
                # 检查是否有时间戳信息
                if "start_time" in result and "end_time" in result:
                    timeline_item = TimelineItem(
                        video_uuid=result.get("uuid", ""),
                        video_name=result.get("file_name", ""),
                        video_path=result.get("file_path", ""),
                        start_time=result.get("start_time", 0.0),
                        end_time=result.get("end_time", 0.0),
                        duration=result.get("end_time", 0.0)
                        - result.get("start_time", 0.0),
                        relevance_score=result.get("score", 0.0),
                        thumbnail_path=result.get("thumbnail_path"),
                    )
                    self.timeline_items.append(timeline_item)

        # 更新时间轴面板
        if self.timeline_items:
            self.timeline_tab.set_timeline_items(self.timeline_items)
            self.tab_widget.setTabEnabled(1, True)  # 启用时间轴选项卡
        else:
            self.timeline_tab.clear_timeline()
            self.tab_widget.setTabEnabled(1, False)  # 禁用时间轴选项卡

    def on_timeline_segment_selected(self, item: TimelineItem):
        """时间轴片段选中事件"""
        # 高亮显示对应的搜索结果
        pass

    def on_timeline_segment_play(self, item: TimelineItem):
        """时间轴片段播放事件"""
        # 在系统默认播放器中打开视频并跳转到指定位置
        import subprocess
        import platform

        video_path = item.video_path
        if Path(video_path).exists():
            if platform.system() == "Windows":
                os.startfile(video_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", video_path])
            else:  # Linux
                subprocess.call(["xdg-open", video_path])

    def update_results_display(self):
        """更新结果显示"""
        # 清除现有结果
        for i in reversed(range(self.results_layout.count())):
            widget = self.results_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # 应用类型过滤（根据设计文档要求）
        filter_type = self.filter_combo.currentText()
        filtered_results = self.results
        if filter_type != "全部":
            if filter_type == "图像":
                filtered_results = [
                    r for r in self.results if r.get("modality") == "image"
                ]
            elif filter_type == "视频":
                filtered_results = [
                    r for r in self.results if r.get("modality") == "video"
                ]
            elif filter_type == "音频":
                filtered_results = [
                    r for r in self.results if r.get("modality") == "audio"
                ]

        # 更新统计
        self.stats_label.setText(
            f"共找到 {len(filtered_results)} 个结果 (总计: {len(self.results)})"
        )

        # 显示结果
        if not filtered_results:
            no_result_label = QLabel("没有找到匹配的结果")
            no_result_label.setAlignment(Qt.AlignCenter)
            no_result_label.setStyleSheet("color: #999; font-size: 14px;")
            self.results_layout.addWidget(no_result_label, 0, 0)
            return

        # 根据视图模式显示结果
        if self.current_view_mode == "grid":
            self.display_grid_results(filtered_results)
        else:
            self.display_list_results(filtered_results)

    def display_grid_results(self, results: List[Dict[str, Any]]):
        """以网格模式显示结果"""
        columns = 3
        for idx, result in enumerate(results):
            row = idx // columns
            col = idx % columns

            result_widget = ResultItemWidget(result)
            result_widget.item_clicked.connect(self.result_opened.emit)
            result_widget.item_double_clicked.connect(self.result_opened.emit)

            self.results_layout.addWidget(result_widget, row, col)

    def display_list_results(self, results: List[Dict[str, Any]]):
        """以列表模式显示结果"""
        for idx, result in enumerate(results):
            result_widget = ResultItemWidget(result)
            result_widget.item_clicked.connect(self.result_opened.emit)
            result_widget.item_double_clicked.connect(self.result_opened.emit)

            self.results_layout.addWidget(result_widget, idx, 0)

    def display_list_results(self):
        """以列表模式显示结果"""
        for idx, result in enumerate(self.results):
            result_widget = ResultItemWidget(result)
            result_widget.item_clicked.connect(self.result_opened.emit)
            result_widget.item_double_clicked.connect(self.result_opened.emit)

            self.results_layout.addWidget(result_widget, idx, 0)

    def on_view_mode_changed(self, index):
        """视图模式改变事件"""
        if index == 0:
            self.current_view_mode = "grid"
        else:
            self.current_view_mode = "list"

        self.update_results_display()

    def on_thumbnail_toggled(self, checked):
        """缩略图显示切换事件"""
        self.show_thumbnails = checked
        self.update_results_display()

    def on_sort_changed(self, index):
        """排序改变事件"""
        sort_type = self.sort_combo.currentText()

        if sort_type == "相似度":
            self.results.sort(key=lambda x: x.get("score", 0), reverse=True)
        elif sort_type == "文件名":
            self.results.sort(key=lambda x: x.get("file_name", ""))
        elif sort_type == "文件大小":
            self.results.sort(key=lambda x: x.get("file_size", 0))
        elif sort_type == "修改时间":
            self.results.sort(key=lambda x: x.get("modified_time", 0), reverse=True)

        self.update_results_display()

    def on_filter_changed(self, index):
        """类型过滤改变事件（根据设计文档要求）"""
        self.update_results_display()

    def clear_results(self):
        """清除结果"""
        self.results = []
        self.update_results_display()

    def get_selected_result(self) -> Optional[Dict[str, Any]]:
        """获取选中的结果"""
        # 这里应该实现获取选中结果的逻辑
        # 暂时返回None
        return None

    def display_results(self, results: List[Dict[str, Any]]):
        """显示搜索结果"""
        self.set_results(results)
