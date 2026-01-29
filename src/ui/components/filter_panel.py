"""
过滤面板组件
提供搜索结果过滤功能（按照设计文档pyside6_ui_design.md实现）
"""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSlider, QDateEdit, QGroupBox, QPushButton
)
from PySide6.QtCore import Signal, Qt, QDate
from PySide6.QtGui import QFont


class FilterPanel(QWidget):
    """
    过滤面板 - 提供搜索结果过滤功能
    按照设计文档pyside6_ui_design.md实现
    """
    
    filter_changed = Signal(dict)  # filter_params
    
    def __init__(self, parent=None):
        """初始化过滤面板"""
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
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
    
    def get_filters(self) -> Dict[str, Any]:
        """获取当前过滤条件"""
        return {
            "file_type": self.file_type_combo.currentText(),
            "time_range": self.time_range_combo.currentText(),
            "start_date": self.start_date.date().toString("yyyy-MM-dd") if self.custom_time_widget.isVisible() else None,
            "end_date": self.end_date.date().toString("yyyy-MM-dd") if self.custom_time_widget.isVisible() else None,
            "similarity": self.score_slider.value() / 100
        }