"""
搜索面板组件
提供搜索输入和搜索类型选择功能
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
    search_requested = Signal(str, str)  # (query, search_type)
    file_search_requested = Signal(str)  # file_path
    
    def __init__(self, parent=None):
        """初始化搜索面板"""
        super().__init__(parent)
        
        self.current_search_type = "text"
        self.setAcceptDrops(True)  # 启用拖拽功能
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 搜索面板容器
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 8px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(20)
        
        # 标题
        title_label = QLabel("🔍 搜索")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #1D2129;
                margin-bottom: 5px;
            }
        """)
        container_layout.addWidget(title_label)
        
        # 搜索类型选择
        search_type_group = QGroupBox("搜索类型")
        search_type_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1D2129;
                border: 1px solid #E5E6EB;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        search_type_layout = QVBoxLayout(search_type_group)
        search_type_layout.setSpacing(8)
        
        self.search_type_button_group = QButtonGroup(self)
        
        # 文本搜索
        self.text_radio = QRadioButton("📝 文本搜索")
        self.text_radio.setChecked(True)
        self.text_radio.toggled.connect(self.on_search_type_changed)
        self.text_radio.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                color: #4E5969;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid #C9CDD4;
            }
            QRadioButton::indicator:checked {
                background-color: #165DFF;
                border-color: #165DFF;
            }
        """)
        self.search_type_button_group.addButton(self.text_radio, 0)
        search_type_layout.addWidget(self.text_radio)
        
        # 图像搜索
        self.image_radio = QRadioButton("🖼️ 图像搜索")
        self.image_radio.toggled.connect(self.on_search_type_changed)
        self.image_radio.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                color: #4E5969;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid #C9CDD4;
            }
            QRadioButton::indicator:checked {
                background-color: #165DFF;
                border-color: #165DFF;
            }
        """)
        self.search_type_button_group.addButton(self.image_radio, 1)
        search_type_layout.addWidget(self.image_radio)
        
        # 音频搜索
        self.audio_radio = QRadioButton("🎵 音频搜索")
        self.audio_radio.toggled.connect(self.on_search_type_changed)
        self.audio_radio.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                color: #4E5969;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid #C9CDD4;
            }
            QRadioButton::indicator:checked {
                background-color: #165DFF;
                border-color: #165DFF;
            }
        """)
        self.search_type_button_group.addButton(self.audio_radio, 2)
        search_type_layout.addWidget(self.audio_radio)
        
        container_layout.addWidget(search_type_group)
        
        # 搜索输入区域
        search_input_group = QGroupBox("搜索查询")
        search_input_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1D2129;
                border: 1px solid #E5E6EB;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        search_input_layout = QVBoxLayout(search_input_group)
        search_input_layout.setSpacing(12)
        
        # 文本输入框
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("输入搜索文本...")
        self.text_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #E5E6EB;
                border-radius: 6px;
                font-size: 14px;
                background-color: #FFFFFF;
            }
            QLineEdit:focus {
                border: 1px solid #165DFF;
            }
        """)
        self.text_input.returnPressed.connect(self.on_search_clicked)
        search_input_layout.addWidget(self.text_input)
        
        # 文件选择按钮（用于图像和音频搜索）
        file_select_layout = QHBoxLayout()
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
        self.select_file_button.clicked.connect(self.on_select_file_clicked)
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
            QPushButton:pressed {
                background-color: #C9CDD4;
            }
        """)
        file_select_layout.addWidget(self.select_file_button)
        
        search_input_layout.addLayout(file_select_layout)
        
        container_layout.addWidget(search_input_group)
        
        # 搜索选项
        options_group = QGroupBox("搜索选项")
        options_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1D2129;
                border: 1px solid #E5E6EB;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(12)
        
        # 结果数量
        result_count_layout = QHBoxLayout()
        result_count_layout.setSpacing(10)
        result_count_layout.addWidget(QLabel("结果数量:"))
        self.result_count_combo = QComboBox()
        self.result_count_combo.addItems(["10", "20", "50", "100"])
        self.result_count_combo.setCurrentText("20")
        self.result_count_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
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
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)
        result_count_layout.addWidget(self.result_count_combo)
        result_count_layout.addStretch()
        options_layout.addLayout(result_count_layout)
        
        # 显示缩略图
        self.show_thumbnail_checkbox = QCheckBox("显示缩略图")
        self.show_thumbnail_checkbox.setChecked(True)
        self.show_thumbnail_checkbox.setStyleSheet("""
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
        """)
        options_layout.addWidget(self.show_thumbnail_checkbox)
        
        container_layout.addWidget(options_group)
        
        # 搜索按钮
        self.search_button = QPushButton("🔎 搜索")
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #165DFF;
                color: white;
                border: none;
                padding: 12px;
                font-size: 15px;
                font-weight: 600;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0E42D2;
            }
            QPushButton:pressed {
                background-color: #0927B9;
            }
        """)
        self.search_button.clicked.connect(self.on_search_clicked)
        container_layout.addWidget(self.search_button)
        
        # 添加弹性空间
        container_layout.addStretch()
        
        layout.addWidget(container)
    
    def on_search_type_changed(self):
        """搜索类型改变事件"""
        if self.text_radio.isChecked():
            self.current_search_type = "text"
            self.text_input.setVisible(True)
            self.text_input.setEnabled(True)
            self.select_file_button.setVisible(False)
            self.file_path_label.setVisible(False)
        elif self.image_radio.isChecked():
            self.current_search_type = "image"
            self.text_input.setVisible(False)
            self.text_input.setEnabled(False)
            self.select_file_button.setVisible(True)
            self.file_path_label.setVisible(True)
        elif self.audio_radio.isChecked():
            self.current_search_type = "audio"
            self.text_input.setVisible(False)
            self.text_input.setEnabled(False)
            self.select_file_button.setVisible(True)
            self.file_path_label.setVisible(True)
    
    def on_select_file_clicked(self):
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
    
    def on_search_clicked(self):
        """搜索按钮点击事件"""
        if self.current_search_type == "text":
            query = self.text_input.text().strip()
            if not query:
                return
            self.search_requested.emit(query, "text")
        elif self.current_search_type == "image":
            file_path = self.file_path_label.toolTip()
            if not file_path or file_path == "未选择文件":
                return
            self.search_requested.emit(file_path, "image")
        elif self.current_search_type == "audio":
            file_path = self.file_path_label.toolTip()
            if not file_path or file_path == "未选择文件":
                return
            self.search_requested.emit(file_path, "audio")
    
    def get_search_query(self) -> Optional[str]:
        """获取搜索查询"""
        if self.current_search_type == "text":
            return self.text_input.text().strip()
        elif self.current_search_type in ["image", "audio"]:
            return self.file_path_label.toolTip()
        return None
    
    def get_search_type(self) -> str:
        """获取搜索类型"""
        return self.current_search_type
    
    def get_result_count(self) -> int:
        """获取结果数量"""
        return int(self.result_count_combo.currentText())
    
    def should_show_thumbnail(self) -> bool:
        """是否显示缩略图"""
        return self.show_thumbnail_checkbox.isChecked()
    
    def clear_search(self):
        """清除搜索"""
        self.text_input.clear()
        self.file_path_label.setText("未选择文件")
        self.file_path_label.setToolTip("")
    
    def set_search_type(self, search_type: str):
        """设置搜索类型"""
        if search_type == "text":
            self.text_radio.setChecked(True)
        elif search_type == "image":
            self.image_radio.setChecked(True)
        elif search_type == "audio":
            self.audio_radio.setChecked(True)
    
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
                audio_exts = ['.mp3', '.wav', '.flac', '.aac', '.ogg']
                
                if file_ext in image_exts or file_ext in audio_exts:
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
        audio_exts = ['.mp3', '.wav', '.flac', '.aac', '.ogg']
        
        if file_ext in image_exts:
            # 图像文件 - 切换到图像搜索
            self.image_radio.setChecked(True)
            self.file_path_label.setText(Path(file_path).name)
            self.file_path_label.setToolTip(file_path)
            # 自动启动检索
            self.file_search_requested.emit(file_path)
        elif file_ext in audio_exts:
            # 音频文件 - 切换到音频搜索
            self.audio_radio.setChecked(True)
            self.file_path_label.setText(Path(file_path).name)
            self.file_path_label.setToolTip(file_path)
            # 自动启动检索
            self.file_search_requested.emit(file_path)
        else:
            # 不支持的文件类型
            QMessageBox.warning(
                self,
                "不支持的文件类型",
                f"只支持图像({', '.join(image_exts)})和音频({', '.join(audio_exts)})文件"
            )