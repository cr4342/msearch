"""
统计面板组件
显示系统统计信息（按照设计文档pyside6_ui_design.md实现）
"""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QProgressBar,
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QFont


class StatCard(QWidget):
    """统计卡片组件"""

    def __init__(self, title: str, value: str, color: str = "#165DFF", parent=None):
        """初始化统计卡片"""
        super().__init__(parent)
        self.title = title
        self.value = value
        self.color = color
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setFixedHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # 标题
        title_label = QLabel(self.title)
        title_label.setStyleSheet(
            f"""
            QLabel {{
                font-size: 13px;
                color: #86909C;
            }}
        """
        )
        layout.addWidget(title_label)

        # 数值
        value_label = QLabel(self.value)
        value_label.setStyleSheet(
            f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {self.color};
            }}
        """
        )
        layout.addWidget(value_label)

        layout.addStretch()

    def update_value(self, value: str):
        """更新数值"""
        self.value = value
        # 更新第二个子控件（数值标签）
        if self.layout().itemAt(1):
            self.layout().itemAt(1).widget().setText(value)


class StatsPanel(QWidget):
    """
    统计面板 - 显示系统统计信息
    按照设计文档pyside6_ui_design.md实现
    """

    def __init__(self, parent=None):
        """初始化统计面板"""
        super().__init__(parent)
        self.init_ui()

        # 定时器用于更新统计信息
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(5000)  # 每5秒更新一次

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 标题
        title_label = QLabel("系统统计")
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

        # 统计卡片网格
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(12)

        # 索引数量
        self.index_count_card = StatCard("索引文件", "0", "#165DFF")
        stats_layout.addWidget(self.index_count_card)

        # 内存使用
        self.memory_card = StatCard("内存使用", "0 MB", "#FF7D00")
        stats_layout.addWidget(self.memory_card)

        # 任务数量
        self.task_count_card = StatCard("运行任务", "0", "#00B42A")
        stats_layout.addWidget(self.task_count_card)

        # 搜索次数
        self.search_count_card = StatCard("搜索次数", "0", "#F53F3F")
        stats_layout.addWidget(self.search_count_card)

        layout.addLayout(stats_layout)
        layout.addStretch()

    def update_stats(self):
        """更新统计信息"""
        # 这里应该从系统获取实际数据
        # 暂时使用示例数据
        import random

        self.index_count_card.update_value(str(random.randint(1000, 5000)))
        self.memory_card.update_value(f"{random.randint(200, 800)} MB")
        self.task_count_card.update_value(str(random.randint(0, 10)))
        self.search_count_card.update_value(str(random.randint(0, 100)))

    def set_index_count(self, count: int):
        """设置索引数量"""
        self.index_count_card.update_value(str(count))

    def set_memory_usage(self, memory_mb: int):
        """设置内存使用"""
        self.memory_card.update_value(f"{memory_mb} MB")

    def set_task_count(self, count: int):
        """设置任务数量"""
        self.task_count_card.update_value(str(count))

    def set_search_count(self, count: int):
        """设置搜索次数"""
        self.search_count_card.update_value(str(count))
