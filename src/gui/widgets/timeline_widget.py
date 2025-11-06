#!/usr/bin/env python3
"""
msearch PySide6时间线组件
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget, QFrame,
    QScrollArea, QProgressBar, QComboBox, QSpinBox, QCheckBox, QSlider,
    QGroupBox, QSplitter, QToolButton, QButtonGroup, QRadioButton,
    QSizePolicy, QSpacerItem, QFileDialog, QMessageBox, QTabWidget,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsLineItem, QScrollBar, QDateEdit, QDateTimeEdit
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QObject, QUrl, QSize, QPropertyAnimation,
    QRectF, QPointF, QDateTime
)
from PySide6.QtGui import (
    QIcon, QPixmap, QFont, QAction, QPalette, QColor, QDesktopServices,
    QPainter, QPen, QBrush, QFontMetrics
)

from src.core.config import load_config
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class TimelineView(QGraphicsView):
    """时间线视图"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 时间线参数
        self.start_time = QDateTime.currentDateTime().addDays(-7)
        self.end_time = QDateTime.currentDateTime()
        self.pixel_per_second = 100  # 每秒对应的像素数
        self.row_height = 60  # 每行高度
        self.row_spacing = 10  # 行间距
        
        # 项目数据
        self.timeline_items = []
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setBackgroundBrush(QBrush(QColor(245, 245, 245)))
        self.setCacheMode(QGraphicsView.CacheBackground)
    
    def set_time_range(self, start_time: QDateTime, end_time: QDateTime):
        """设置时间范围"""
        self.start_time = start_time
        self.end_time = end_time
        self.update_timeline()
    
    def set_pixel_per_second(self, pixel_per_second: float):
        """设置每秒像素数"""
        self.pixel_per_second = pixel_per_second
        self.update_timeline()
    
    def add_timeline_item(self, item_data: Dict[str, Any]):
        """添加时间线项目"""
        self.timeline_items.append(item_data)
        self.update_timeline()
    
    def clear_timeline(self):
        """清空时间线"""
        self.timeline_items = []
        self.scene().clear()
    
    def update_timeline(self):
        """更新时间线显示"""
        self.scene().clear()
        
        if not self.timeline_items:
            return
        
        # 计算时间范围
        total_duration = self.start_time.secsTo(self.end_time)
        scene_width = total_duration * self.pixel_per_second
        scene_height = len(self.timeline_items) * (self.row_height + self.row_spacing)
        
        # 设置场景大小
        self.scene().setSceneRect(0, 0, scene_width, scene_height)
        
        # 绘制时间轴
        self.draw_timeline_axis()
        
        # 绘制项目
        self.draw_timeline_items()
    
    def draw_timeline_axis(self):
        """绘制时间轴"""
        total_duration = self.start_time.secsTo(self.end_time)
        scene_width = total_duration * self.pixel_per_second
        
        # 绘制时间轴线
        line = QGraphicsLineItem(0, 20, scene_width, 20)
        line.setPen(QPen(QColor(100, 100, 100), 2))
        self.scene().addItem(line)
        
        # 绘制时间刻度
        font = QFont()
        font.setPointSize(8)
        font_metrics = QFontMetrics(font)
        
        # 计算刻度间隔
        if total_duration > 86400:  # 大于1天
            interval = 3600  # 1小时
        elif total_duration > 3600:  # 大于1小时
            interval = 300  # 5分钟
        else:
            interval = 60  # 1分钟
        
        current_time = self.start_time
        while current_time <= self.end_time:
            secs_from_start = self.start_time.secsTo(current_time)
            x_pos = secs_from_start * self.pixel_per_second
            
            # 绘制刻度线
            tick_line = QGraphicsLineItem(x_pos, 15, x_pos, 25)
            tick_line.setPen(QPen(QColor(150, 150, 150), 1))
            self.scene().addItem(tick_line)
            
            # 绘制时间标签
            time_str = current_time.toString("hh:mm")
            text_item = QGraphicsTextItem(time_str)
            text_item.setFont(font)
            text_width = font_metrics.horizontalAdvance(time_str)
            text_item.setPos(x_pos - text_width/2, 30)
            self.scene().addItem(text_item)
            
            current_time = current_time.addSecs(interval)
    
    def draw_timeline_items(self):
        """绘制时间线项目"""
        for row, item_data in enumerate(self.timeline_items):
            self.draw_timeline_item(row, item_data)
    
    def draw_timeline_item(self, row: int, item_data: Dict[str, Any]):
        """绘制单个时间线项目"""
        # 提取项目数据
        start_time = QDateTime.fromString(item_data.get("start_time", ""), "yyyy-MM-dd hh:mm:ss")
        end_time = QDateTime.fromString(item_data.get("end_time", ""), "yyyy-MM-dd hh:mm:ss")
        title = item_data.get("title", "未命名")
        file_path = item_data.get("file_path", "")
        file_type = item_data.get("file_type", "unknown")
        color = item_data.get("color", QColor(100, 150, 255))
        
        if not start_time.isValid() or not end_time.isValid():
            return
        
        # 计算位置和尺寸
        start_secs = self.start_time.secsTo(start_time)
        end_secs = self.start_time.secsTo(end_time)
        duration = end_secs - start_secs
        
        x_pos = start_secs * self.pixel_per_second
        y_pos = row * (self.row_height + self.row_spacing) + 40
        width = duration * self.pixel_per_second
        height = self.row_height
        
        # 确保最小宽度
        if width < 5:
            width = 5
        
        # 绘制项目矩形
        rect_item = QGraphicsRectItem(x_pos, y_pos, width, height)
        rect_item.setBrush(QBrush(color))
        rect_item.setPen(QPen(QColor(50, 50, 50), 1))
        rect_item.setFlag(QGraphicsItem.ItemIsSelectable)
        rect_item.setData(Qt.UserRole, item_data)
        self.scene().addItem(rect_item)
        
        # 绘制标题文本
        font = QFont()
        font.setPointSize(9)
        font_metrics = QFontMetrics(font)
        
        # 截断过长的标题
        max_width = width - 10
        if font_metrics.horizontalAdvance(title) > max_width:
            # 简单的截断处理
            title = title[:int(len(title) * max_width / font_metrics.horizontalAdvance(title)) - 3] + "..."
        
        text_item = QGraphicsTextItem(title)
        text_item.setFont(font)
        text_item.setDefaultTextColor(QColor(255, 255, 255))
        text_x = x_pos + 5
        text_y = y_pos + (height - font_metrics.height()) / 2
        text_item.setPos(text_x, text_y)
        self.scene().addItem(text_item)
    
    def wheelEvent(self, event):
        """鼠标滚轮事件 - 缩放时间线"""
        if event.modifiers() == Qt.ControlModifier:
            # 缩放时间线
            factor = 1.2 if event.angleDelta().y() > 0 else 1/1.2
            self.pixel_per_second *= factor
            self.update_timeline()
        else:
            # 水平滚动
            super().wheelEvent(event)


class TimelineWidget(QWidget):
    """时间线组件"""
    
    # 信号定义
    status_message_changed = Signal(str)
    item_selected = Signal(dict)  # 项目被选中
    
    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        
        # API客户端
        self.api_client = api_client
        
        # 初始化UI
        self.init_ui()
        
        # 初始化状态
        self.init_state()
        
        # 连接信号
        self.connect_signals()
        
        # 应用样式
        self.apply_styles()
        
        # 加载示例数据
        self.load_sample_data()
        
        logger.info("时间线组件初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 控制面板
        self.create_control_panel(main_layout)
        
        # 时间线视图
        self.timeline_view = TimelineView()
        main_layout.addWidget(self.timeline_view)
        
        # 状态信息
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self.status_label)
    
    def create_control_panel(self, parent_layout):
        """创建控制面板"""
        control_group = QGroupBox("时间线控制")
        control_layout = QHBoxLayout(control_group)
        
        # 时间范围选择
        control_layout.addWidget(QLabel("开始时间:"))
        self.start_date_edit = QDateTimeEdit()
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd hh:mm")
        self.start_date_edit.setDateTime(QDateTime.currentDateTime().addDays(-7))
        control_layout.addWidget(self.start_date_edit)
        
        control_layout.addWidget(QLabel("结束时间:"))
        self.end_date_edit = QDateTimeEdit()
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd hh:mm")
        self.end_date_edit.setDateTime(QDateTime.currentDateTime())
        control_layout.addWidget(self.end_date_edit)
        
        # 更新按钮
        self.update_timeline_button = QPushButton("更新时间线")
        self.update_timeline_button.clicked.connect(self.update_timeline_view)
        control_layout.addWidget(self.update_timeline_button)
        
        # 缩放控制
        control_layout.addWidget(QLabel("缩放:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 500)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setToolTip("调整时间线缩放比例")
        control_layout.addWidget(self.zoom_slider)
        
        self.zoom_label = QLabel("100%")
        control_layout.addWidget(self.zoom_label)
        
        # 操作按钮
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.refresh_timeline)
        control_layout.addWidget(self.refresh_button)
        
        parent_layout.addWidget(control_group)
    
    def init_state(self):
        """初始化状态"""
        self.timeline_data = []
    
    def connect_signals(self):
        """连接信号"""
        # 时间范围变化
        self.start_date_edit.dateTimeChanged.connect(self.on_time_range_changed)
        self.end_date_edit.dateTimeChanged.connect(self.on_time_range_changed)
        
        # 缩放控制
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        
        # 时间线视图选择
        # 注意：QGraphicsView的选择信号需要特殊处理
    
    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
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
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: #66b1ff;
            }
            
            QPushButton:pressed {
                background-color: #3a8ee6;
            }
            
            QPushButton:disabled {
                background-color: #c0c4cc;
                color: #ffffff;
            }
            
            QDateTimeEdit {
                padding: 8px;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
            }
            
            QDateTimeEdit:focus {
                border-color: #409EFF;
            }
            
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
            }
            
            QSlider::handle:horizontal {
                background: #409EFF;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
    
    def on_time_range_changed(self):
        """时间范围变化事件"""
        self.update_timeline_view()
    
    def on_zoom_changed(self, value):
        """缩放变化事件"""
        zoom_percentage = value
        self.zoom_label.setText(f"{zoom_percentage}%")
        
        # 更新时间线视图的像素比例
        base_pixel_per_second = 100  # 基准值
        pixel_per_second = base_pixel_per_second * (zoom_percentage / 100.0)
        self.timeline_view.set_pixel_per_second(pixel_per_second)
    
    def update_timeline_view(self):
        """更新时间线视图"""
        start_time = self.start_date_edit.dateTime()
        end_time = self.end_date_edit.dateTime()
        
        if start_time >= end_time:
            QMessageBox.warning(self, "警告", "开始时间必须早于结束时间")
            return
        
        self.timeline_view.set_time_range(start_time, end_time)
        self.status_message_changed.emit("时间线已更新")
    
    def load_sample_data(self):
        """加载示例数据"""
        # 生成示例时间线数据
        base_time = QDateTime.currentDateTime().addDays(-3)
        
        sample_data = [
            {
                "title": "会议记录视频",
                "start_time": base_time.addSecs(3600).toString("yyyy-MM-dd hh:mm:ss"),
                "end_time": base_time.addSecs(7200).toString("yyyy-MM-dd hh:mm:ss"),
                "file_path": "/path/to/meeting.mp4",
                "file_type": "video",
                "color": QColor(255, 100, 100)
            },
            {
                "title": "产品演示文稿",
                "start_time": base_time.addSecs(10800).toString("yyyy-MM-dd hh:mm:ss"),
                "end_time": base_time.addSecs(14400).toString("yyyy-MM-dd hh:mm:ss"),
                "file_path": "/path/to/presentation.pptx",
                "file_type": "document",
                "color": QColor(100, 255, 100)
            },
            {
                "title": "客户访谈音频",
                "start_time": base_time.addSecs(18000).toString("yyyy-MM-dd hh:mm:ss"),
                "end_time": base_time.addSecs(21600).toString("yyyy-MM-dd hh:mm:ss"),
                "file_path": "/path/to/interview.mp3",
                "file_type": "audio",
                "color": QColor(100, 100, 255)
            },
            {
                "title": "项目讨论图片",
                "start_time": base_time.addSecs(25200).toString("yyyy-MM-dd hh:mm:ss"),
                "end_time": base_time.addSecs(28800).toString("yyyy-MM-dd hh:mm:ss"),
                "file_path": "/path/to/discussion.jpg",
                "file_type": "image",
                "color": QColor(255, 255, 100)
            }
        ]
        
        # 添加到时间线视图
        for item in sample_data:
            self.timeline_view.add_timeline_item(item)
        
        self.status_message_changed.emit(f"加载了 {len(sample_data)} 个示例项目")
    
    def refresh_timeline(self):
        """刷新时间线"""
        self.timeline_view.clear_timeline()
        self.load_sample_data()
        self.update_timeline_view()
        self.status_message_changed.emit("时间线已刷新")
    
    def add_timeline_item(self, item_data: Dict[str, Any]):
        """添加时间线项目"""
        self.timeline_view.add_timeline_item(item_data)
        self.status_message_changed.emit("已添加时间线项目")
    
    def clear_timeline(self):
        """清空时间线"""
        self.timeline_view.clear_timeline()
        self.status_message_changed.emit("时间线已清空")
    
    def set_api_client(self, api_client):
        """设置API客户端"""
        self.api_client = api_client
    
    def load_timeline_data_from_api(self):
        """从API加载时间线数据"""
        if not self.api_client:
            self.status_message_changed.emit("API客户端未设置")
            return
        
        try:
            # TODO: 调用API获取时间线数据
            # 这里暂时使用示例数据
            self.refresh_timeline()
            self.status_message_changed.emit("从API加载时间线数据完成")
        except Exception as e:
            logger.error(f"从API加载时间线数据失败: {e}")
            self.status_message_changed.emit(f"加载时间线数据失败: {e}")