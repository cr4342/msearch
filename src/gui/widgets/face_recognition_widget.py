#!/usr/bin/env python3
"""
msearch PySide6人脸管理组件
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget, QFrame,
    QScrollArea, QProgressBar, QComboBox, QSpinBox, QCheckBox, QSlider,
    QGroupBox, QSplitter, QToolButton, QButtonGroup, QRadioButton,
    QSizePolicy, QSpacerItem, QFileDialog, QMessageBox, QTabWidget,
    QListWidget, QListWidgetItem, QTextBrowser, QStackedWidget
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QObject, QUrl, QSize, QPropertyAnimation
)
from PySide6.QtGui import (
    QIcon, QPixmap, QFont, QAction, QPalette, QColor, QDesktopServices, 
    QDragEnterEvent, QDropEvent, QImage, QPainter
)

from src.core.config import load_config
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class FaceRecognitionWidget(QWidget):
    """人脸管理组件"""
    
    # 信号定义
    status_message_changed = Signal(str)
    
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
        
        # 加载人脸数据
        self.load_face_data()
        
        logger.info("人脸管理组件初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建各个选项卡
        self.create_person_management_tab()
        self.create_face_search_tab()
        self.create_face_database_tab()
        
        # 状态信息
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self.status_label)
    
    def create_person_management_tab(self):
        """创建人员管理选项卡"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # 左侧：人员列表
        left_panel = QGroupBox("人员列表")
        left_layout = QVBoxLayout(left_panel)
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.person_search_input = QLineEdit()
        self.person_search_input.setPlaceholderText("搜索人员...")
        self.person_search_button = QPushButton("搜索")
        search_layout.addWidget(self.person_search_input)
        search_layout.addWidget(self.person_search_button)
        left_layout.addLayout(search_layout)
        
        # 人员列表
        self.person_list = QListWidget()
        self.person_list.setIconSize(QSize(64, 64))
        left_layout.addWidget(self.person_list)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.add_person_button = QPushButton("添加人员")
        self.edit_person_button = QPushButton("编辑人员")
        self.delete_person_button = QPushButton("删除人员")
        self.edit_person_button.setEnabled(False)
        self.delete_person_button.setEnabled(False)
        button_layout.addWidget(self.add_person_button)
        button_layout.addWidget(self.edit_person_button)
        button_layout.addWidget(self.delete_person_button)
        left_layout.addLayout(button_layout)
        
        layout.addWidget(left_panel)
        
        # 右侧：人员详情
        right_panel = QGroupBox("人员详情")
        right_layout = QVBoxLayout(right_panel)
        
        # 人员信息表单
        form_layout = QFormLayout()
        
        self.person_name_input = QLineEdit()
        form_layout.addRow("姓名:", self.person_name_input)
        
        self.person_aliases_input = QLineEdit()
        self.person_aliases_input.setPlaceholderText("用逗号分隔的别名")
        form_layout.addRow("别名:", self.person_aliases_input)
        
        self.person_description_input = QTextEdit()
        self.person_description_input.setMaximumHeight(100)
        form_layout.addRow("描述:", self.person_description_input)
        
        right_layout.addLayout(form_layout)
        
        # 人脸图片区域
        images_group = QGroupBox("人脸图片")
        images_layout = QVBoxLayout(images_group)
        
        # 图片列表
        self.face_images_list = QListWidget()
        self.face_images_list.setViewMode(QListWidget.IconMode)
        self.face_images_list.setIconSize(QSize(128, 128))
        self.face_images_list.setResizeMode(QListWidget.Adjust)
        self.face_images_list.setWrapping(True)
        images_layout.addWidget(self.face_images_list)
        
        # 图片操作按钮
        image_button_layout = QHBoxLayout()
        self.add_face_image_button = QPushButton("添加图片")
        self.remove_face_image_button = QPushButton("移除图片")
        self.remove_face_image_button.setEnabled(False)
        image_button_layout.addWidget(self.add_face_image_button)
        image_button_layout.addWidget(self.remove_face_image_button)
        image_button_layout.addStretch()
        images_layout.addLayout(image_button_layout)
        
        right_layout.addWidget(images_group)
        
        # 保存按钮
        save_button_layout = QHBoxLayout()
        save_button_layout.addStretch()
        self.save_person_button = QPushButton("保存")
        self.save_person_button.setEnabled(False)
        save_button_layout.addWidget(self.save_person_button)
        right_layout.addLayout(save_button_layout)
        
        layout.addWidget(right_panel)
        layout.setStretch(0, 1)
        layout.setStretch(1, 2)
        
        self.tab_widget.addTab(tab, "人员管理")
    
    def create_face_search_tab(self):
        """创建人脸搜索选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 搜索区域
        search_group = QGroupBox("人脸搜索")
        search_layout = QVBoxLayout(search_group)
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("选择人脸图片:"))
        
        self.face_search_path_input = QLineEdit()
        self.face_search_path_input.setPlaceholderText("选择要搜索的人脸图片...")
        self.face_search_path_input.setReadOnly(True)
        file_layout.addWidget(self.face_search_path_input)
        
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_face_search_file)
        file_layout.addWidget(browse_button)
        
        search_layout.addLayout(file_layout)
        
        # 拖放区域
        self.face_search_drop_area = QLabel("拖拽人脸图片到此处")
        self.face_search_drop_area.setAlignment(Qt.AlignCenter)
        self.face_search_drop_area.setMinimumHeight(100)
        self.face_search_drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
        """)
        self.face_search_drop_area.setAcceptDrops(True)
        self.face_search_drop_area.dragEnterEvent = self.face_search_drag_enter_event
        self.face_search_drop_area.dropEvent = self.face_search_drop_event
        
        search_layout.addWidget(self.face_search_drop_area)
        
        # 搜索选项
        options_layout = QHBoxLayout()
        
        # 结果数量限制
        options_layout.addWidget(QLabel("结果数量:"))
        self.face_search_result_limit = QSpinBox()
        self.face_search_result_limit.setMinimum(5)
        self.face_search_result_limit.setMaximum(50)
        self.face_search_result_limit.setValue(10)
        self.face_search_result_limit.setSuffix(" 个")
        options_layout.addWidget(self.face_search_result_limit)
        
        options_layout.addStretch()
        
        # 搜索按钮
        self.face_search_button = QPushButton("搜索相似人脸")
        self.face_search_button.clicked.connect(self.perform_face_search)
        options_layout.addWidget(self.face_search_button)
        
        search_layout.addLayout(options_layout)
        layout.addWidget(search_group)
        
        # 结果区域
        results_group = QGroupBox("搜索结果")
        results_layout = QVBoxLayout(results_group)
        
        # 进度条
        self.face_search_progress = QProgressBar()
        self.face_search_progress.setVisible(False)
        results_layout.addWidget(self.face_search_progress)
        
        # 结果表格
        self.face_search_results_table = QTableWidget()
        self.face_search_results_table.setColumnCount(4)
        self.face_search_results_table.setHorizontalHeaderLabels([
            "人员姓名", "相似度", "图片预览", "操作"
        ])
        self.face_search_results_table.setSelectionBehavior(QTableWidget.SelectRows)
        results_layout.addWidget(self.face_search_results_table)
        
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(tab, "人脸搜索")
    
    def create_face_database_tab(self):
        """创建人脸数据库选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 数据库信息
        info_group = QGroupBox("数据库信息")
        info_layout = QFormLayout(info_group)
        
        self.database_persons_count = QLabel("0")
        info_layout.addRow("人员总数:", self.database_persons_count)
        
        self.database_faces_count = QLabel("0")
        info_layout.addRow("人脸图片总数:", self.database_faces_count)
        
        self.database_last_update = QLabel("从未更新")
        info_layout.addRow("最后更新:", self.database_last_update)
        
        layout.addWidget(info_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        self.refresh_database_button = QPushButton("刷新数据库")
        self.export_database_button = QPushButton("导出数据库")
        self.import_database_button = QPushButton("导入数据库")
        self.clear_database_button = QPushButton("清空数据库")
        
        button_layout.addWidget(self.refresh_database_button)
        button_layout.addWidget(self.export_database_button)
        button_layout.addWidget(self.import_database_button)
        button_layout.addWidget(self.clear_database_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 日志区域
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_group)
        
        self.database_log = QTextBrowser()
        self.database_log.setMaximumHeight(200)
        log_layout.addWidget(self.database_log)
        
        layout.addWidget(log_group)
        
        self.tab_widget.addTab(tab, "数据库管理")
    
    def init_state(self):
        """初始化状态"""
        self.current_person = None
        self.persons_data = []
        self.face_images = []
    
    def connect_signals(self):
        """连接信号"""
        # 人员管理信号
        self.person_list.itemSelectionChanged.connect(self.on_person_selection_changed)
        self.person_search_input.textChanged.connect(self.filter_persons)
        self.add_person_button.clicked.connect(self.add_new_person)
        self.edit_person_button.clicked.connect(self.edit_selected_person)
        self.delete_person_button.clicked.connect(self.delete_selected_person)
        self.save_person_button.clicked.connect(self.save_person)
        self.add_face_image_button.clicked.connect(self.add_face_image)
        self.remove_face_image_button.clicked.connect(self.remove_face_image)
        self.face_images_list.itemSelectionChanged.connect(self.on_face_image_selection_changed)
        
        # 人脸搜索信号
        self.face_search_results_table.itemSelectionChanged.connect(self.on_search_result_selection_changed)
    
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
            
            QLineEdit, QTextEdit {
                padding: 8px;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
            }
            
            QLineEdit:focus, QTextEdit:focus {
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
            
            QListWidget {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
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
        """)
    
    def load_face_data(self):
        """加载人脸数据"""
        try:
            # TODO: 从API加载人脸数据
            # 模拟数据
            self.persons_data = [
                {
                    "id": "1",
                    "name": "张三",
                    "aliases": ["小张", "张总"],
                    "description": "公司员工",
                    "face_images": [
                        {"id": "101", "path": "/path/to/face1.jpg"},
                        {"id": "102", "path": "/path/to/face2.jpg"}
                    ]
                },
                {
                    "id": "2",
                    "name": "李四",
                    "aliases": ["李经理"],
                    "description": "部门主管",
                    "face_images": [
                        {"id": "201", "path": "/path/to/face3.jpg"}
                    ]
                }
            ]
            
            self.update_person_list()
            self.update_database_info()
            
        except Exception as e:
            logger.error(f"加载人脸数据失败: {e}")
            self.status_message_changed.emit(f"加载人脸数据失败: {e}")
    
    def update_person_list(self):
        """更新人员列表"""
        self.person_list.clear()
        
        search_text = self.person_search_input.text().lower()
        
        for person in self.persons_data:
            if search_text and search_text not in person["name"].lower():
                # 检查别名
                aliases_match = any(search_text in alias.lower() for alias in person["aliases"])
                if not aliases_match:
                    continue
            
            item = QListWidgetItem(person["name"])
            item.setData(Qt.UserRole, person)
            
            # TODO: 设置人员头像
            # item.setIcon(QIcon(":/icons/person.png"))
            
            self.person_list.addItem(item)
    
    def filter_persons(self, text):
        """过滤人员列表"""
        self.update_person_list()
    
    def on_person_selection_changed(self):
        """人员选择变化事件"""
        selected_items = self.person_list.selectedItems()
        has_selection = len(selected_items) > 0
        
        self.edit_person_button.setEnabled(has_selection)
        self.delete_person_button.setEnabled(has_selection)
        
        if has_selection:
            item = selected_items[0]
            person = item.data(Qt.UserRole)
            self.show_person_details(person)
        else:
            self.clear_person_details()
    
    def show_person_details(self, person):
        """显示人员详情"""
        self.current_person = person
        
        self.person_name_input.setText(person["name"])
        self.person_aliases_input.setText(", ".join(person["aliases"]))
        self.person_description_input.setText(person.get("description", ""))
        
        self.update_face_images_list(person["face_images"])
        
        self.save_person_button.setEnabled(False)
    
    def clear_person_details(self):
        """清空人员详情"""
        self.current_person = None
        
        self.person_name_input.clear()
        self.person_aliases_input.clear()
        self.person_description_input.clear()
        self.face_images_list.clear()
        
        self.save_person_button.setEnabled(False)
    
    def update_face_images_list(self, face_images):
        """更新人脸图片列表"""
        self.face_images_list.clear()
        self.face_images = face_images
        
        for face_image in face_images:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, face_image)
            
            # TODO: 加载并显示人脸图片缩略图
            # pixmap = self.load_face_thumbnail(face_image["path"])
            # if pixmap:
            #     item.setIcon(QIcon(pixmap))
            
            item.setText(Path(face_image["path"]).name)
            self.face_images_list.addItem(item)
    
    def on_face_image_selection_changed(self):
        """人脸图片选择变化事件"""
        selected_items = self.face_images_list.selectedItems()
        self.remove_face_image_button.setEnabled(len(selected_items) > 0)
    
    def add_new_person(self):
        """添加新人员"""
        self.person_list.clearSelection()
        self.clear_person_details()
        
        # 设置默认值
        self.person_name_input.setText("新人员")
        self.save_person_button.setEnabled(True)
        
        self.status_message_changed.emit("请填写新人员信息")
    
    def edit_selected_person(self):
        """编辑选中人员"""
        selected_items = self.person_list.selectedItems()
        if not selected_items:
            return
        
        self.save_person_button.setEnabled(True)
        self.status_message_changed.emit("正在编辑人员信息")
    
    def delete_selected_person(self):
        """删除选中人员"""
        selected_items = self.person_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        person = item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除人员 '{person['name']}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # TODO: 调用API删除人员
            # 从本地数据中移除
            self.persons_data = [p for p in self.persons_data if p["id"] != person["id"]]
            self.update_person_list()
            self.clear_person_details()
            self.update_database_info()
            self.status_message_changed.emit(f"已删除人员: {person['name']}")
    
    def save_person(self):
        """保存人员信息"""
        name = self.person_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入人员姓名")
            return
        
        aliases_text = self.person_aliases_input.text().strip()
        aliases = [alias.strip() for alias in aliases_text.split(",") if alias.strip()]
        
        description = self.person_description_input.toPlainText().strip()
        
        # 准备保存的数据
        if self.current_person:
            # 更新现有人员
            person_data = self.current_person
            person_data["name"] = name
            person_data["aliases"] = aliases
            person_data["description"] = description
            person_data["face_images"] = self.face_images
            
            # TODO: 调用API更新人员信息
            self.status_message_changed.emit(f"已更新人员信息: {name}")
        else:
            # 添加新人员
            person_data = {
                "id": str(len(self.persons_data) + 1),
                "name": name,
                "aliases": aliases,
                "description": description,
                "face_images": self.face_images
            }
            
            self.persons_data.append(person_data)
            self.update_person_list()
            self.status_message_changed.emit(f"已添加新人员: {name}")
        
        # 更新显示
        self.save_person_button.setEnabled(False)
        self.update_database_info()
    
    def add_face_image(self):
        """添加人脸图片"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择人脸图片", "", 
            "图像文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if not file_paths:
            return
        
        for file_path in file_paths:
            face_image = {
                "id": str(len(self.face_images) + 1),
                "path": file_path
            }
            self.face_images.append(face_image)
        
        self.update_face_images_list(self.face_images)
        self.save_person_button.setEnabled(True)
        self.status_message_changed.emit(f"已添加 {len(file_paths)} 张人脸图片")
    
    def remove_face_image(self):
        """移除人脸图片"""
        selected_items = self.face_images_list.selectedItems()
        if not selected_items:
            return
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除选中的 {len(selected_items)} 张图片吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 从列表中移除
            for item in selected_items:
                face_image = item.data(Qt.UserRole)
                self.face_images = [img for img in self.face_images if img["id"] != face_image["id"]]
            
            self.update_face_images_list(self.face_images)
            self.save_person_button.setEnabled(True)
            self.status_message_changed.emit(f"已删除 {len(selected_items)} 张图片")
    
    def browse_face_search_file(self):
        """浏览人脸搜索文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择人脸图片", "", 
            "图像文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.face_search_path_input.setText(file_path)
            self.face_search_drop_area.setText(f"已选择: {Path(file_path).name}")
    
    def face_search_drag_enter_event(self, event: QDragEnterEvent):
        """人脸搜索拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.face_search_drop_area.setStyleSheet("""
                QLabel {
                    border: 2px dashed #409EFF;
                    background-color: #ecf5ff;
                    border-radius: 5px;
                }
            """)
        else:
            event.ignore()
    
    def face_search_drop_event(self, event: QDropEvent):
        """人脸搜索拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path and self.is_image_file(file_path):
                self.face_search_path_input.setText(file_path)
                self.face_search_drop_area.setText(f"已选择: {Path(file_path).name}")
            else:
                QMessageBox.warning(self, "警告", "请选择有效的图像文件")
        
        # 恢复样式
        self.face_search_drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
        """)
    
    def is_image_file(self, file_path: str) -> bool:
        """检查是否为图像文件"""
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
        return Path(file_path).suffix.lower() in image_extensions
    
    def perform_face_search(self):
        """执行人脸搜索"""
        file_path = self.face_search_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择人脸图片")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "文件不存在")
            return
        
        # 显示进度条
        self.face_search_progress.setVisible(True)
        self.face_search_progress.setRange(0, 0)
        
        # 禁用搜索按钮
        self.face_search_button.setEnabled(False)
        
        # TODO: 调用API执行人脸搜索
        # 模拟搜索过程
        QTimer.singleShot(2000, self.on_face_search_completed)
        
        self.status_message_changed.emit(f"正在搜索人脸: {Path(file_path).name}")
    
    def on_face_search_completed(self):
        """人脸搜索完成"""
        # 隐藏进度条
        self.face_search_progress.setVisible(False)
        
        # 启用搜索按钮
        self.face_search_button.setEnabled(True)
        
        # 模拟搜索结果
        results = [
            {"person_name": "张三", "similarity": 0.95, "image_path": "/path/to/face1.jpg"},
            {"person_name": "李四", "similarity": 0.87, "image_path": "/path/to/face2.jpg"},
            {"person_name": "王五", "similarity": 0.78, "image_path": "/path/to/face3.jpg"}
        ]
        
        self.update_face_search_results(results)
        self.status_message_changed.emit(f"人脸搜索完成，找到 {len(results)} 个匹配结果")
    
    def update_face_search_results(self, results):
        """更新人脸搜索结果"""
        self.face_search_results_table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # 人员姓名
            self.face_search_results_table.setItem(row, 0, self.create_table_item(result["person_name"]))
            
            # 相似度
            similarity_text = f"{result['similarity']:.2%}"
            self.face_search_results_table.setItem(row, 1, self.create_table_item(similarity_text))
            
            # 图片预览
            preview_widget = QWidget()
            preview_layout = QHBoxLayout(preview_widget)
            preview_layout.setContentsMargins(5, 5, 5, 5)
            
            # TODO: 显示人脸图片缩略图
            preview_label = QLabel("预览")
            preview_label.setAlignment(Qt.AlignCenter)
            preview_label.setMinimumSize(64, 64)
            preview_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
            preview_layout.addWidget(preview_label)
            
            self.face_search_results_table.setCellWidget(row, 2, preview_widget)
            
            # 操作按钮
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            view_button = QPushButton("查看")
            view_button.clicked.connect(lambda checked, r=result: self.view_person(r))
            action_layout.addWidget(view_button)
            
            self.face_search_results_table.setCellWidget(row, 3, action_widget)
        
        # 调整列宽
        self.face_search_results_table.resizeColumnsToContents()
        self.face_search_results_table.setColumnWidth(2, 80)  # 图片预览列
    
    def create_table_item(self, text: str):
        """创建表格项"""
        from PySide6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item
    
    def on_search_result_selection_changed(self):
        """搜索结果选择变化事件"""
        # 可以在这里处理搜索结果的选择事件
        pass
    
    def view_person(self, result):
        """查看人员详情"""
        # 切换到人员管理选项卡
        self.tab_widget.setCurrentIndex(0)
        
        # 在人员列表中找到并选中该人员
        for i in range(self.person_list.count()):
            item = self.person_list.item(i)
            person = item.data(Qt.UserRole)
            if person["name"] == result["person_name"]:
                self.person_list.setCurrentItem(item)
                break
    
    def update_database_info(self):
        """更新数据库信息"""
        persons_count = len(self.persons_data)
        faces_count = sum(len(person["face_images"]) for person in self.persons_data)
        
        self.database_persons_count.setText(str(persons_count))
        self.database_faces_count.setText(str(faces_count))
        self.database_last_update.setText("刚刚")
    
    def refresh_database(self):
        """刷新数据库"""
        self.load_face_data()
        self.status_message_changed.emit("数据库已刷新")
    
    def export_database(self):
        """导出数据库"""
        # TODO: 实现数据库导出功能
        self.status_message_changed.emit("数据库导出功能待实现")
    
    def import_database(self):
        """导入数据库"""
        # TODO: 实现数据库导入功能
        self.status_message_changed.emit("数据库导入功能待实现")
    
    def clear_database(self):
        """清空数据库"""
        reply = QMessageBox.question(
            self, "确认清空", 
            "确定要清空整个人脸数据库吗？此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # TODO: 调用API清空数据库
            self.persons_data = []
            self.update_person_list()
            self.clear_person_details()
            self.update_database_info()
            self.status_message_changed.emit("人脸数据库已清空")