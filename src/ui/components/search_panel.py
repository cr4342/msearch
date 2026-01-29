"""
搜索面板组件
提供搜索输入和搜索类型选择功能
按照设计文档pyside6_ui_design.md实现
"""

from typing import Optional, List, Callable
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QRadioButton,
    QButtonGroup, QFileDialog, QGroupBox, QCheckBox
)
from PySide6.QtCore import Signal, Qt


class SearchPanel(QWidget):
    """搜索面板组件 - 支持拖拽文件进行检索"""
    
    # 信号定义
    search_triggered = Signal(str, str)  # (query, search_type)
    file_search_requested = Signal(str)  # file_path
    
    def __init__(self, parent=None):
        """初始化搜索面板"""
        super().__init__(parent)
        
        self.current_search_type = "text"
        self.setAcceptDrops(True)  # 启用拖拽功能
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面 - 按照设计文档实现"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 搜索面板容器 - 使用设计文档的配色方案
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #F2F3F5;
                border-radius: 12px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(16)
        
        # 标题 - 使用设计文档的样式
        title_label = QLabel("多模态搜索")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #1D2129;
            }
        """)
        container_layout.addWidget(title_label)
        
        # 搜索输入框 - 使用设计文档的样式
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
        self.search_input.returnPressed.connect(self._on_search)
        container_layout.addWidget(self.search_input)
        
        # 搜索类型选择 - 使用按钮组而非单选框
        type_layout = QHBoxLayout()
        type_layout.setSpacing(12)
        
        self.type_group = QButtonGroup(self)
        
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
            btn.setObjectName(f"type_{type_id}")  # 设置对象名称
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
            self.type_group.addButton(btn, id=types.index((type_id, label, icon)))
            type_layout.addWidget(btn)
        
        # 默认选择文本搜索
        self.type_group.button(0).setChecked(True)
        
        container_layout.addLayout(type_layout)
        
        # 文件选择区域（仅图像/音频搜索显示）
        self.file_select_widget = QWidget()
        file_select_layout = QHBoxLayout(self.file_select_widget)
        file_select_layout.setSpacing(10)
        
        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setWordWrap(True)
        self.file_path_label.setStyleSheet("""
            QLabel {
                color: #86909C;
                font-size: 12px;
            }
        """)
        file_select_layout.addWidget(self.file_path_label)
        
        self.select_file_button = QPushButton("选择文件")
        self.select_file_button.clicked.connect(self._on_select_file_clicked)
        self.select_file_button.setVisible(False)
        self.select_file_button.setStyleSheet("""
            QPushButton {
                background-color: #F2F3F5;
                color: #4E5969;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #E5E6EB;
            }
        """)
        file_select_layout.addWidget(self.select_file_button)
        
        container_layout.addWidget(self.file_select_widget)
        self.file_select_widget.setVisible(False)
        
        # 搜索按钮 - 使用设计文档的样式
        self.search_button = QPushButton("🔍 搜索")
        self.search_button.setFixedHeight(48)
        self.search_button.setStyleSheet("""
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
        self.search_button.clicked.connect(self._on_search)
        container_layout.addWidget(self.search_button)
        
        # 添加弹性空间
        container_layout.addStretch()
        
        layout.addWidget(container)
        
        # 连接信号
        self.type_group.buttonClicked.connect(self._on_type_changed)
    
    def _on_type_changed(self, button):
        """搜索类型改变事件"""
        type_id = button.objectName()
        self.current_search_type = type_id.replace("type_", "")
        
        # 根据类型显示/隐藏文件选择区域
        if self.current_search_type in ["image", "audio"]:
            self.search_input.setVisible(False)
            self.search_input.setEnabled(False)
            self.file_select_widget.setVisible(True)
        else:
            self.search_input.setVisible(True)
            self.search_input.setEnabled(True)
            self.file_select_widget.setVisible(False)
    
    def _on_select_file_clicked(self):
        """选择文件按钮点击事件"""
        if self.current_search_type == "image":
            file_filter = "图像文件 (*.jpg *.jpeg *.png *.bmp *.gif *.webp)"
        elif self.current_search_type == "audio":
            file_filter = "音频文件 (*.mp3 *.wav *.flac *.aac *.ogg)"
        else:
            file_filter = "所有文件 (*.*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文件",
            "",
            file_filter
        )
        
        if file_path:
            self.file_path_label.setText(Path(file_path).name)
            self.file_path_label.setToolTip(file_path)
            self.file_search_requested.emit(file_path)
    
    def _on_search(self):
        """搜索按钮点击事件"""
        if self.current_search_type == "text":
            query = self.search_input.text().strip()
            if not query:
                return
            self.search_triggered.emit(query, "text")
        elif self.current_search_type == "image":
            file_path = self.file_path_label.toolTip()
            if not file_path or file_path == "未选择文件":
                return
            self.search_triggered.emit(file_path, "image")
        elif self.current_search_type == "audio":
            file_path = self.file_path_label.toolTip()
            if not file_path or file_path == "未选择文件":
                return
            self.search_triggered.emit(file_path, "audio")
        elif self.current_search_type == "video":
            file_path = self.file_path_label.toolTip()
            if not file_path or file_path == "未选择文件":
                return
            self.search_triggered.emit(file_path, "video")
        
        def get_search_query(self) -> Optional[str]:
        """获取搜索查询"""
        if self.current_search_type == "text":
            return self.search_input.text().strip()
        elif self.current_search_type in ["image", "audio", "video"]:
            return self.file_path_label.toolTip()
        return None
    
    def get_search_type(self) -> str:
        """获取搜索类型"""
        return self.current_search_type
    
    def clear_search(self):
        """清除搜索"""
        self.search_input.clear()
        self.file_path_label.setText("未选择文件")
        self.file_path_label.setToolTip("")
    
    def set_search_type(self, search_type: str):
        """设置搜索类型"""
        for btn in self.type_group.buttons():
            if btn.objectName() == f"type_{search_type}":
                btn.setChecked(True)
                break
    
    # ================================================================
    # 拖拽功能实现（根据设计文档要求）
    # ================================================================
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            # 检查文件类型
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                file_ext = Path(file_path).suffix.lower()
                
                # 支持的文件类型
                image_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
                video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.flv']
                audio_exts = ['.mp3', '.wav', '.flac', '.aac', '.ogg']
                
                if file_ext in image_exts or file_ext in video_exts or file_ext in audio_exts:
                    event.acceptProposedAction()
                    return
        
        event.ignore()
    
    def dropEvent(self, event):
        """拖拽放下事件"""
        urls = event.mimeData().urls()
        if not urls:
            return
        
        file_path = urls[0].toLocalFile()
        file_ext = Path(file_path).suffix.lower()
        
        # 根据文件类型自动识别并启动检索（设计文档要求）
        image_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
        video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.flv']
        audio_exts = ['.mp3', '.wav', '.flac', '.aac', '.ogg']
        
        if file_ext in image_exts:
            # 图像文件 - 切换到图像搜索
            for btn in self.type_group.buttons():
                if btn.objectName() == "type_image":
                    btn.setChecked(True)
                    break
            self.file_path_label.setText(Path(file_path).name)
            self.file_path_label.setToolTip(file_path)
            # 自动启动检索
            self.file_search_requested.emit(file_path)
        elif file_ext in video_exts:
            # 视频文件 - 切换到视频搜索
            for btn in self.type_group.buttons():
                if btn.objectName() == "type_video":
                    btn.setChecked(True)
                    break
            self.file_path_label.setText(Path(file_path).name)
            self.file_path_label.setToolTip(file_path)
            # 自动启动检索
            self.file_search_requested.emit(file_path)
        elif file_ext in audio_exts:
            # 音频文件 - 切换到音频搜索
            for btn in self.type_group.buttons():
                if btn.objectName() == "type_audio":
                    btn.setChecked(True)
                    break
            self.file_path_label.setText(Path(file_path).name)
            self.file_path_label.setToolTip(file_path)
            # 自动启动检索
            self.file_search_requested.emit(file_path)
        else:
            # 不支持的文件类型
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "不支持的文件类型",
                f"只支持图像({', '.join(image_exts)})、视频({', '.join(video_exts)})和音频({', '.join(audio_exts)})文件"
            )