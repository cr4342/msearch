"""
时间轴面板组件
用于视频检索结果的时间轴可视化展示（根据设计文档要求）
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton, QSlider,
    QGroupBox, QCheckBox, QComboBox, QGridLayout
)
from PySide6.QtCore import Signal, Qt, QSize, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap


class TimelineItem:
    """时间轴条目"""
    
    def __init__(self, video_uuid: str, video_name: str, video_path: str,
                 start_time: float, end_time: float, duration: float,
                 relevance_score: float, thumbnail_path: Optional[str] = None):
        self.video_uuid = video_uuid
        self.video_name = video_name
        self.video_path = video_path
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.relevance_score = relevance_score
        self.thumbnail_path = thumbnail_path
    
    def get_formatted_duration(self) -> str:
        """格式化时长"""
        return f"{self.duration:.1f}s"
    
    def get_formatted_start_time(self) -> str:
        """格式化开始时间"""
        return f"{self.start_time:.1f}s"
    
    def get_formatted_end_time(self) -> str:
        """格式化结束时间"""
        return f"{self.end_time:.1f}s"


class TimelineWidget(QWidget):
    """时间轴可视化组件"""
    
    # 信号定义
    segment_clicked = Signal(TimelineItem)
    segment_double_clicked = Signal(TimelineItem)
    
    def __init__(self, parent=None):
        """初始化时间轴组件"""
        super().__init__(parent)
        
        self.timeline_items: List[TimelineItem] = []
        self.video_duration = 0.0
        self.current_time = 0.0
        self.segment_height = 30
        self.segment_spacing = 5
        self.padding = 10
        
        self.setMinimumHeight(100)
        self.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 5px;")
    
    def set_video_duration(self, duration: float):
        """设置视频总时长"""
        self.video_duration = duration
        self.update()
    
    def add_timeline_item(self, item: TimelineItem):
        """添加时间轴条目"""
        self.timeline_items.append(item)
        self.update()
    
    def set_timeline_items(self, items: List[TimelineItem]):
        """设置时间轴条目列表"""
        self.timeline_items = items
        self.update()
    
    def clear_timeline(self):
        """清除时间轴"""
        self.timeline_items = []
        self.video_duration = 0.0
        self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        painter.fillRect(self.rect(), QColor("#f5f5f5"))
        
        if self.video_duration == 0:
            painter.drawText(self.rect(), Qt.AlignCenter, "无时间轴数据")
            return
        
        # 绘制时间轴背景
        timeline_rect = QRectF(
            self.padding,
            self.padding,
            self.width() - 2 * self.padding,
            self.height() - 2 * self.padding
        )
        
        # 绘制时间刻度
        self._draw_time_scale(painter, timeline_rect)
        
        # 绘制视频片段
        self._draw_video_segments(painter, timeline_rect)
        
        # 绘制当前时间指示器
        if self.current_time > 0:
            self._draw_current_time_indicator(painter, timeline_rect)
    
    def _draw_time_scale(self, painter: QPainter, rect: QRectF):
        """绘制时间刻度"""
        painter.setPen(QPen(QColor("#999"), 1))
        painter.setFont(QFont("Arial", 8))
        
        # 计算刻度间隔
        if self.video_duration <= 60:
            interval = 10  # 10秒
        elif self.video_duration <= 300:
            interval = 30  # 30秒
        else:
            interval = 60  # 1分钟
        
        # 绘制刻度线和标签
        for t in range(0, int(self.video_duration) + 1, interval):
            x = rect.left() + (t / self.video_duration) * rect.width()
            
            # 刻度线
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.top() + 10))
            
            # 时间标签
            label = f"{t}s"
            painter.drawText(int(x) - 20, int(rect.top() - 5), 40, 15, Qt.AlignCenter, label)
    
    def _draw_video_segments(self, painter: QPainter, rect: QRectF):
        """绘制视频片段"""
        for i, item in enumerate(self.timeline_items):
            # 计算片段位置
            start_x = rect.left() + (item.start_time / self.video_duration) * rect.width()
            end_x = rect.left() + (item.end_time / self.video_duration) * rect.width()
            segment_width = end_x - start_x
            
            y = rect.top() + 20 + i * (self.segment_height + self.segment_spacing)
            
            # 根据相关性设置颜色（设计文档要求：可视化相关性）
            relevance = min(1.0, max(0.0, item.relevance_score))
            # 高相关性：绿色，低相关性：红色
            red = int(255 * (1 - relevance))
            green = int(255 * relevance)
            color = QColor(red, green, 0, 180)
            
            # 绘制片段矩形
            segment_rect = QRectF(start_x, y, segment_width, self.segment_height)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#333"), 1))
            painter.drawRoundedRect(segment_rect, 3, 3)
            
            # 绘制片段信息
            painter.setPen(QPen(QColor("#fff"), 1))
            painter.setFont(QFont("Arial", 7))
            info_text = f"{item.start_time:.1f}s-{item.end_time:.1f}s"
            painter.drawText(segment_rect, Qt.AlignCenter, info_text)
    
    def _draw_current_time_indicator(self, painter: QPainter, rect: QRectF):
        """绘制当前时间指示器"""
        x = rect.left() + (self.current_time / self.video_duration) * rect.width()
        
        # 绘制垂直线
        painter.setPen(QPen(QColor("#f44336"), 2))
        painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
        
        # 绘制三角形标记
        painter.setBrush(QBrush(QColor("#f44336")))
        painter.setPen(Qt.NoPen)
        triangle = [
            int(x), int(rect.top()),
            int(x) - 6, int(rect.top() - 8),
            int(x) + 6, int(rect.top() - 8)
        ]
        painter.drawPolygon(*triangle)
    
    def set_current_time(self, time: float):
        """设置当前时间"""
        self.current_time = time
        self.update()
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if self.video_duration == 0:
            return
        
        # 转换点击位置到时间
        rect = QRectF(
            self.padding,
            self.padding,
            self.width() - 2 * self.padding,
            self.height() - 2 * self.padding
        )
        
        if rect.contains(event.position().toPointF()):
            click_time = ((event.position().x() - rect.left()) / rect.width()) * self.video_duration
            
            # 查找点击的片段
            for item in self.timeline_items:
                if item.start_time <= click_time <= item.end_time:
                    self.segment_clicked.emit(item)
                    self.set_current_time(click_time)
                    return
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件"""
        if self.video_duration == 0:
            return
        
        rect = QRectF(
            self.padding,
            self.padding,
            self.width() - 2 * self.padding,
            self.height() - 2 * self.padding
        )
        
        if rect.contains(event.position().toPointF()):
            click_time = ((event.position().x() - rect.left()) / rect.width()) * self.video_duration
            
            for item in self.timeline_items:
                if item.start_time <= click_time <= item.end_time:
                    self.segment_double_clicked.emit(item)
                    return


class TimelinePanel(QWidget):
    """时间轴面板组件（根据设计文档要求）"""
    
    # 信号定义
    segment_selected = Signal(TimelineItem)
    segment_play = Signal(TimelineItem)
    
    def __init__(self, parent=None):
        """初始化时间轴面板"""
        super().__init__(parent)
        
        self.timeline_items: List[TimelineItem] = []
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("视频时间轴")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(title_label)
        
        # 时间轴可视化
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.timeline_widget = TimelineWidget()
        scroll_area.setWidget(self.timeline_widget)
        layout.addWidget(scroll_area)
        
        # 控制区域
        control_layout = QHBoxLayout()
        
        # 时间滑块
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setRange(0, 100)
        self.time_slider.setValue(0)
        self.time_slider.sliderMoved.connect(self.on_slider_moved)
        control_layout.addWidget(QLabel("时间:"))
        control_layout.addWidget(self.time_slider)
        
        # 时间显示
        self.time_label = QLabel("0.0s")
        self.time_label.setStyleSheet("min-width: 60px;")
        control_layout.addWidget(self.time_label)
        
        control_layout.addStretch()
        
        # 播放按钮
        self.play_button = QPushButton("播放")
        self.play_button.clicked.connect(self.on_play_clicked)
        control_layout.addWidget(self.play_button)
        
        # 打开按钮
        self.open_button = QPushButton("在播放器中打开")
        self.open_button.clicked.connect(self.on_open_clicked)
        control_layout.addWidget(self.open_button)
        
        layout.addLayout(control_layout)
        
        # 连接信号
        self.timeline_widget.segment_clicked.connect(self.on_segment_clicked)
        self.timeline_widget.segment_double_clicked.connect(self.on_segment_double_clicked)
    
    def set_timeline_items(self, items: List[TimelineItem]):
        """设置时间轴条目"""
        self.timeline_items = items
        if items:
            # 获取视频总时长（假设所有片段来自同一个视频）
            max_duration = max(item.end_time for item in items)
            self.timeline_widget.set_video_duration(max_duration)
        
        self.timeline_widget.set_timeline_items(items)
    
    def clear_timeline(self):
        """清除时间轴"""
        self.timeline_items = []
        self.timeline_widget.clear_timeline()
        self.time_slider.setValue(0)
        self.time_label.setText("0.0s")
    
    def on_segment_clicked(self, item: TimelineItem):
        """片段点击事件"""
        self.segment_selected.emit(item)
        self.time_slider.setValue(int(item.start_time))
        self.time_label.setText(f"{item.start_time:.1f}s")
        self.timeline_widget.set_current_time(item.start_time)
    
    def on_segment_double_clicked(self, item: TimelineItem):
        """片段双击事件"""
        self.segment_play.emit(item)
    
    def on_slider_moved(self, value: float):
        """滑块移动事件"""
        if self.timeline_widget.video_duration > 0:
            time = (value / 100) * self.timeline_widget.video_duration
            self.time_label.setText(f"{time:.1f}s")
            self.timeline_widget.set_current_time(time)
    
    def on_play_clicked(self):
        """播放按钮点击事件"""
        if self.timeline_items:
            # 播放当前选中的片段或第一个片段
            current_time = self.time_slider.value() / 100 * self.timeline_widget.video_duration
            for item in self.timeline_items:
                if item.start_time <= current_time <= item.end_time:
                    self.segment_play.emit(item)
                    return
            # 如果没有选中片段，播放第一个
            if self.timeline_items:
                self.segment_play.emit(self.timeline_items[0])
    
    def on_open_clicked(self):
        """打开按钮点击事件"""
        if self.timeline_items:
            # 在系统默认播放器中打开视频
            import subprocess
            import platform
            video_path = self.timeline_items[0].video_path
            if Path(video_path).exists():
                if platform.system() == 'Windows':
                    os.startfile(video_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.call(['open', video_path])
                else:  # Linux
                    subprocess.call(['xdg-open', video_path])