"""
结果面板组件
显示搜索结果，支持时间轴展示（根据设计文档pyside6_ui_design.md实现）
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


class ResultItemWidget(QWidget):
    """结果项组件 - 按照设计文档实现"""

    # 信号定义
    item_clicked = Signal(dict)

    def __init__(self, result_data: Dict[str, Any], parent=None):
        """初始化结果项"""
        super().__init__(parent)

        self.result_data = result_data
        self.init_ui()

    def init_ui(self):
        """初始化用户界面 - 按照设计文档实现"""
        self.setFixedHeight(100)
        self.setStyleSheet(
            """
            QWidget {
                border-bottom: 1px solid #F2F3F5;
                background-color: transparent;
            }
            QWidget:hover {
                background-color: #F7F8FA;
            }
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # 缩略图 - 按照设计文档样式
        thumbnail_label = self._create_thumbnail()
        layout.addWidget(thumbnail_label)

        # 信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        # 文件名
        file_name = self.result_data.get("file_name", "未知文件")
        name_label = QLabel(file_name)
        name_label.setStyleSheet(
            """
            QLabel {
                font-size: 15px;
                font-weight: bold;
                color: #1D2129;
            }
        """
        )
        name_label.setWordWrap(True)
        info_layout.addWidget(name_label)

        # 文件信息
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(16)

        file_type = self._get_file_type_icon()
        type_label = QLabel(f"{file_type} {self.result_data.get('file_type', '未知')}")
        type_label.setStyleSheet("color: #86909C; font-size: 13px;")
        meta_layout.addWidget(type_label)

        size_label = QLabel(self._format_size(self.result_data.get("size", 0)))
        size_label.setStyleSheet("color: #86909C; font-size: 13px;")
        meta_layout.addWidget(size_label)

        date_label = QLabel(self.result_data.get("modified_time", "未知时间"))
        date_label.setStyleSheet("color: #86909C; font-size: 13px;")
        meta_layout.addWidget(date_label)

        meta_layout.addStretch()

        # 相似度 - 按照设计文档样式
        score = self.result_data.get("score", 0.0)
        if score > 0:
            score_label = QLabel(f"相似度: {score:.1%}")
            score_label.setStyleSheet(
                """
                QLabel {
                    color: #FF7D00;
                    font-weight: bold;
                    font-size: 13px;
                }
            """
            )
            meta_layout.addWidget(score_label)

        info_layout.addLayout(meta_layout)

        # 文件路径
        file_path = self.result_data.get("file_path", "")
        if file_path:
            path_label = QLabel(Path(file_path).name)
            path_label.setStyleSheet("color: #86909C; font-size: 12px;")
            path_label.setWordWrap(True)
            info_layout.addWidget(path_label)

        info_layout.addStretch()

        layout.addLayout(info_layout)
        layout.addStretch()

    def _create_thumbnail(self) -> QLabel:
        """创建缩略图 - 按照设计文档样式"""
        thumbnail = QLabel()
        thumbnail.setFixedSize(80, 80)
        thumbnail.setStyleSheet(
            """
            QLabel {
                background-color: #F2F3F5;
                border-radius: 8px;
                border: 1px solid #E5E6EB;
            }
        """
        )
        thumbnail.setAlignment(Qt.AlignCenter)

        # 尝试加载缩略图
        thumbnail_path = self.result_data.get("thumbnail_path")
        if thumbnail_path and Path(thumbnail_path).exists():
            pixmap = QPixmap(thumbnail_path)
            scaled_pixmap = pixmap.scaled(
                80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            thumbnail.setPixmap(scaled_pixmap)
        else:
            # 根据文件类型显示不同图标
            file_type = self.result_data.get("file_type", "")
            if file_type == "image":
                thumbnail.setText("🖼️")
            elif file_type == "video":
                thumbnail.setText("🎥")
            elif file_type == "audio":
                thumbnail.setText("🎵")
            else:
                thumbnail.setText("📄")

        return thumbnail

    def _get_file_type_icon(self) -> str:
        """获取文件类型图标"""
        file_type = self.result_data.get("file_type", "")
        icons = {
            "image": "🖼️",
            "video": "🎥",
            "audio": "🎵",
            "document": "📄",
            "folder": "📁",
        }
        return icons.get(file_type, "📄")

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

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        self.item_clicked.emit(self.result_data)
        super().mousePressEvent(event)


class ResultHeader(QWidget):
    """结果标题栏 - 按照设计文档实现"""

    def __init__(self, parent=None):
        """初始化结果标题栏"""
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 标题
        title_label = QLabel("搜索结果")
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1D2129;
            }
        """
        )
        layout.addWidget(title_label)

        # 结果数量
        self.count_label = QLabel("共 0 个结果")
        self.count_label.setStyleSheet(
            """
            QLabel {
                color: #86909C;
                font-size: 14px;
            }
        """
        )
        layout.addWidget(self.count_label)

        layout.addStretch()

        # 视图切换
        self.view_combo = QComboBox()
        self.view_combo.addItems(["📋 列表视图", "⊞ 网格视图"])
        self.view_combo.setMinimumWidth(120)
        self.view_combo.setStyleSheet(
            """
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #C9CDD4;
                border-radius: 6px;
                font-size: 13px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #165DFF;
            }
        """
        )
        layout.addWidget(self.view_combo)

    def update_count(self, count: int):
        """更新结果数量"""
        self.count_label.setText(f"共 {count} 个结果")


class ResultView(QListWidget):
    """结果视图 - 按照设计文档实现"""

    result_selected = Signal(dict)

    def __init__(self, parent=None):
        """初始化结果视图"""
        super().__init__(parent)
        self.results = []
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setStyleSheet(
            """
            QListWidget {
                background-color: transparent;
                border: none;
                selection-background-color: #E8F3FF;
                selection-color: #165DFF;
            }
            QListWidget::item {
                border-bottom: 1px solid #F2F3F5;
                padding: 0;
                height: 100px;
            }
            QListWidget::item:hover {
                background-color: #F7F8FA;
            }
        """
        )
        self.setUniformItemSizes(True)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        # 设置连接
        self.itemClicked.connect(self._on_item_clicked)

    def set_results(self, results: List[Dict[str, Any]]):
        """设置搜索结果"""
        self.results = results
        self.clear()

        for result in results:
            item = QListWidgetItem()
            item_widget = ResultItemWidget(result)
            item.setSizeHint(item_widget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, item_widget)

    def _on_item_clicked(self, item):
        """处理结果点击"""
        index = self.row(item)
        if 0 <= index < len(self.results):
            self.result_selected.emit(self.results[index])


class ResultPanel(QWidget):
    """结果面板组件 - 按照设计文档实现"""

    # 信号定义
    result_selected = Signal(dict)

    def __init__(self, parent=None):
        """初始化结果面板"""
        super().__init__(parent)

        self.results: List[Dict[str, Any]] = []
        self.init_ui()

    def init_ui(self):
        """初始化用户界面 - 按照设计文档实现"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # 结果标题栏
        self.result_header = ResultHeader()
        layout.addWidget(self.result_header)

        # 结果展示区
        self.result_view = ResultView()
        layout.addWidget(self.result_view)

        # 设置连接
        self.result_view.result_selected.connect(self.result_selected)

    def set_results(self, results: List[Dict[str, Any]]):
        """设置搜索结果"""
        self.results = results
        self.result_view.set_results(results)
        self.result_header.update_count(len(results))
