#!/usr/bin/env python3
"""
msearch PySide6人脸识别组件
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget, QFrame,
    QScrollArea, QProgressBar, QComboBox, QSpinBox, QCheckBox, QSlider,
    QGroupBox, QSplitter, QToolButton, QButtonGroup, QRadioButton,
    QSizePolicy, QSpacerItem, QFileDialog, QMessageBox, QTabWidget,
    QListWidget, QListWidgetItem, QGridLayout
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QObject, QUrl, QSize, QPropertyAnimation
)
from PySide6.QtGui import (
    QIcon, QPixmap, QFont, QAction, QPalette, QColor, QDesktopServices, QDragEnterEvent, QDropEvent
)

from src.core.config import load_config
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class FaceRecognitionWidget(QWidget):
    """人脸识别组件"""
    
    # 信号定义
    status_message_changed = Signal(str)
    face_selected = Signal(dict)  # 人脸被选中
    
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
        
        logger.info("人脸识别组件初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建人脸搜索选项卡
        self.create_face_search_tab()
        
        # 创建人脸管理选项卡
        self.create_face_management_tab()
    
    def create_face_search_tab(self):
        """创建人脸搜索选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 搜索输入区域
        search_group = QGroupBox("人脸搜索")
        search_layout = QVBoxLayout(search_group)
        
        # 图像文件选择
        image_layout = QHBoxLayout()
        image_layout.addWidget(QLabel("图像文件:"))
        
        self.image_path_input = QLineEdit()
        self.image_path_input.setPlaceholderText("选择包含人脸的图像文件...")
        self.image_path_input.setReadOnly(True)
        image_layout.addWidget(self.image_path_input)
        
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_image_file)
        image_layout.addWidget(browse_button)
        
        search_layout.addLayout(image_layout)
        
        # 拖放区域
        self.image_drop_area = QLabel("拖拽包含人脸的图像文件到此处")
        self.image_drop_area.setAlignment(Qt.AlignCenter)
        self.image_drop_area.setMinimumHeight(100)
        self.image_drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
        """)
        self.image_drop_area.setAcceptDrops(True)
        self.image_drop_area.dragEnterEvent = self.image_drag_enter_event
        self.image_drop_area.dropEvent = self.image_drop_event
        
        search_layout.addWidget(self.image_drop_area)
        
        # 搜索按钮
        search_button = QPushButton("搜索相似人脸")
        search_button.clicked.connect(self.perform_face_search)
        search_layout.addWidget(search_button)
        
        layout.addWidget(search_group)
        
        # 搜索结果区域
        results_group = QGroupBox("搜索结果")
        results_layout = QVBoxLayout(results_group)
        
        # 结果列表
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.on_result_item_clicked)
        results_layout.addWidget(self.results_list)
        
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(tab, "人脸搜索")
    
    def create_face_management_tab(self):
        """创建人脸管理选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 人名管理区域
        person_group = QGroupBox("人名管理")
        person_layout = QVBoxLayout(person_group)
        
        # 人名列表
        self.person_list = QListWidget()
        self.person_list.itemClicked.connect(self.on_person_item_clicked)
        person_layout.addWidget(self.person_list)
        
        # 人名操作按钮
        person_actions_layout = QHBoxLayout()
        
        self.add_person_button = QPushButton("添加人名")
        self.add_person_button.clicked.connect(self.add_person)
        person_actions_layout.addWidget(self.add_person_button)
        
        self.edit_person_button = QPushButton("编辑人名")
        self.edit_person_button.clicked.connect(self.edit_person)
        self.edit_person_button.setEnabled(False)
        person_actions_layout.addWidget(self.edit_person_button)
        
        self.delete_person_button = QPushButton("删除人名")
        self.delete_person_button.clicked.connect(self.delete_person)
        self.delete_person_button.setEnabled(False)
        person_actions_layout.addWidget(self.delete_person_button)
        
        person_layout.addLayout(person_actions_layout)
        
        layout.addWidget(person_group)
        
        # 人脸图像管理区域
        face_group = QGroupBox("人脸图像管理")
        face_layout = QVBoxLayout(face_group)
        
        # 人脸图像网格
        self.face_grid = QGridLayout()
        self.face_grid_widgets = []
        face_layout.addLayout(self.face_grid)
        
        # 人脸操作按钮
        face_actions_layout = QHBoxLayout()
        
        self.add_face_button = QPushButton("添加人脸图像")
        self.add_face_button.clicked.connect(self.add_face_image)
        face_actions_layout.addWidget(self.add_face_button)
        
        self.remove_face_button = QPushButton("移除选中人脸")
        self.remove_face_button.clicked.connect(self.remove_selected_face)
        self.remove_face_button.setEnabled(False)
        face_actions_layout.addWidget(self.remove_face_button)
        
        face_actions_layout.addStretch()
        
        face_layout.addLayout(face_actions_layout)
        
        layout.addWidget(face_group)
        
        self.tab_widget.addTab(tab, "人脸管理")
    
    def init_state(self):
        """初始化状态"""
        self.current_results = []
        self.current_persons = []
        self.selected_person = None
        self.selected_faces = []
    
    def connect_signals(self):
        """连接信号"""
        pass
    
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
            
            QLineEdit {
                padding: 8px;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
            }
            
            QLineEdit:focus {
                border-color: #409EFF;
            }
            
            QListWidget {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
            }
        """)
    
    def browse_image_file(self):
        """浏览图像文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图像文件", "", 
            "图像文件 (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            self.image_path_input.setText(file_path)
            self.image_drop_area.setText(f"已选择: {Path(file_path).name}")
    
    def image_drag_enter_event(self, event: QDragEnterEvent):
        """图像拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.image_drop_area.setStyleSheet("""
                QLabel {
                    border: 2px dashed #409EFF;
                    background-color: #ecf5ff;
                    border-radius: 5px;
                }
            """)
        else:
            event.ignore()
    
    def image_drop_event(self, event: QDropEvent):
        """图像拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path and self.is_image_file(file_path):
                self.image_path_input.setText(file_path)
                self.image_drop_area.setText(f"已选择: {Path(file_path).name}")
            else:
                QMessageBox.warning(self, "警告", "请选择有效的图像文件")
        
        # 恢复样式
        self.image_drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
        """)
    
    def is_image_file(self, file_path: str) -> bool:
        """检查是否为图像文件"""
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
        return Path(file_path).suffix.lower() in image_extensions
    
    def perform_face_search(self):
        """执行人脸搜索"""
        file_path = self.image_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择图像文件")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "文件不存在")
            return
        
        # 如果有API客户端，调用API搜索
        if self.api_client and self.api_client.is_connected():
            # 调用API搜索人脸
            result = self.api_client.search_faces(file_path)
            
            if result and result.get("status") == "success":
                self.display_search_results(result.get("results", []))
                self.status_message_changed.emit(f"人脸搜索完成，找到 {len(result.get('results', []))} 个结果")
            else:
                error_msg = result.get("message", "未知错误") if result else "API调用失败"
                QMessageBox.critical(self, "错误", f"人脸搜索失败: {error_msg}")
                self.status_message_changed.emit(f"人脸搜索失败: {error_msg}")
        else:
            # 模拟搜索结果
            self.display_search_results(self.generate_mock_results())
            self.status_message_changed.emit("人脸搜索完成（模拟数据）")
    
    def generate_mock_results(self):
        """生成模拟搜索结果"""
        return [
            {
                "person_name": "张三",
                "similarity": 0.95,
                "file_path": "/path/to/image1.jpg",
                "timestamp": "00:01:30"
            },
            {
                "person_name": "李四",
                "similarity": 0.85,
                "file_path": "/path/to/image2.jpg",
                "timestamp": "00:05:20"
            }
        ]
    
    def display_search_results(self, results: List[Dict]):
        """显示搜索结果"""
        self.current_results = results
        self.results_list.clear()
        
        for result in results:
            item_text = f"{result.get('person_name', '未知')} (相似度: {result.get('similarity', 0):.2%})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, result)
            self.results_list.addItem(item)
    
    def on_result_item_clicked(self, item):
        """结果项点击事件"""
        result_data = item.data(Qt.UserRole)
        if result_data:
            self.face_selected.emit(result_data)
    
    def on_person_item_clicked(self, item):
        """人名项点击事件"""
        self.selected_person = item.text()
        self.edit_person_button.setEnabled(True)
        self.delete_person_button.setEnabled(True)
        self.load_person_faces(self.selected_person)
    
    def add_person(self):
        """添加人名"""
        person_name, ok = QMessageBox.getText(self, "添加人名", "请输入人名:")
        if ok and person_name:
            # 如果有API客户端，调用API添加人名
            if self.api_client and self.api_client.is_connected():
                # 这里应该调用API添加人名
                pass
            
            # 更新UI
            self.person_list.addItem(person_name)
            self.status_message_changed.emit(f"已添加人名: {person_name}")
    
    def edit_person(self):
        """编辑人名"""
        if not self.selected_person:
            return
        
        new_name, ok = QMessageBox.getText(self, "编辑人名", "请输入新的人名:", text=self.selected_person)
        if ok and new_name and new_name != self.selected_person:
            # 如果有API客户端，调用API编辑人名
            if self.api_client and self.api_client.is_connected():
                # 这里应该调用API编辑人名
                pass
            
            # 更新UI
            current_item = self.person_list.currentItem()
            if current_item:
                current_item.setText(new_name)
            self.selected_person = new_name
            self.status_message_changed.emit(f"已更新人名: {new_name}")
    
    def delete_person(self):
        """删除人名"""
        if not self.selected_person:
            return
        
        reply = QMessageBox.question(self, "确认删除", f"确定要删除人名 '{self.selected_person}' 吗？")
        if reply == QMessageBox.Yes:
            # 如果有API客户端，调用API删除人名
            if self.api_client and self.api_client.is_connected():
                # 这里应该调用API删除人名
                pass
            
            # 更新UI
            current_item = self.person_list.currentItem()
            if current_item:
                self.person_list.takeItem(self.person_list.row(current_item))
            self.selected_person = None
            self.edit_person_button.setEnabled(False)
            self.delete_person_button.setEnabled(False)
            self.clear_face_grid()
            self.status_message_changed.emit(f"已删除人名: {self.selected_person}")
    
    def load_person_faces(self, person_name: str):
        """加载人名对应的人脸图像"""
        # 如果有API客户端，调用API获取人脸图像
        if self.api_client and self.api_client.is_connected():
            # 这里应该调用API获取人脸图像
            face_images = []
        else:
            # 模拟人脸图像数据
            face_images = [
                "/path/to/face1.jpg",
                "/path/to/face2.jpg",
                "/path/to/face3.jpg"
            ]
        
        self.display_face_images(face_images)
    
    def display_face_images(self, face_images: List[str]):
        """显示人脸图像"""
        # 清除现有的图像
        self.clear_face_grid()
        
        # 添加新的人脸图像
        for i, image_path in enumerate(face_images):
            row = i // 3
            col = i % 3
            
            # 创建图像标签
            label = QLabel()
            label.setAlignment(Qt.AlignCenter)
            label.setMinimumSize(100, 100)
            label.setStyleSheet("border: 1px solid #ccc; border-radius: 5px;")
            
            # 如果图像文件存在，加载图像
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                label.setPixmap(pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
            # 创建复选框
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self.on_face_checkbox_changed)
            
            # 创建垂直布局
            layout = QVBoxLayout()
            layout.addWidget(label)
            layout.addWidget(checkbox, 0, Qt.AlignCenter)
            
            # 创建容器部件
            container = QWidget()
            container.setLayout(layout)
            container.setProperty("image_path", image_path)
            
            # 添加到网格布局
            self.face_grid.addWidget(container, row, col)
            self.face_grid_widgets.append(container)
    
    def clear_face_grid(self):
        """清除人脸图像网格"""
        # 清除所有子部件
        for i in reversed(range(self.face_grid.count())):
            widget = self.face_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        self.face_grid_widgets.clear()
        self.selected_faces.clear()
        self.remove_face_button.setEnabled(False)
    
    def on_face_checkbox_changed(self, state):
        """人脸复选框状态变化事件"""
        checkbox = self.sender()
        container = checkbox.parent().parent()
        image_path = container.property("image_path")
        
        if state == Qt.Checked:
            self.selected_faces.append(image_path)
        else:
            if image_path in self.selected_faces:
                self.selected_faces.remove(image_path)
        
        self.remove_face_button.setEnabled(len(self.selected_faces) > 0)
    
    def add_face_image(self):
        """添加人脸图像"""
        if not self.selected_person:
            QMessageBox.warning(self, "警告", "请先选择一个人名")
            return
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择人脸图像", "", 
            "图像文件 (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        
        if file_paths:
            # 如果有API客户端，调用API添加人脸图像
            if self.api_client and self.api_client.is_connected():
                # 调用API添加人脸图像
                result = self.api_client.add_person_to_face_database(
                    self.selected_person, file_paths
                )
                
                if result and result.get("status") == "success":
                    self.status_message_changed.emit(f"已添加 {len(file_paths)} 个人脸图像")
                    # 重新加载人脸图像
                    self.load_person_faces(self.selected_person)
                else:
                    error_msg = result.get("message", "未知错误") if result else "API调用失败"
                    QMessageBox.critical(self, "错误", f"添加人脸图像失败: {error_msg}")
            else:
                self.status_message_changed.emit(f"已添加 {len(file_paths)} 个人脸图像（模拟）")
                # 重新加载人脸图像
                self.load_person_faces(self.selected_person)
    
    def remove_selected_face(self):
        """移除选中的人脸"""
        if not self.selected_faces:
            return
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除选中的 {len(self.selected_faces)} 个人脸图像吗？"
        )
        
        if reply == QMessageBox.Yes:
            # 如果有API客户端，调用API删除人脸图像
            if self.api_client and self.api_client.is_connected():
                # 这里应该调用API删除人脸图像
                pass
            
            # 更新UI
            for container in self.face_grid_widgets[:]:
                image_path = container.property("image_path")
                if image_path in self.selected_faces:
                    # 从网格中移除
                    self.face_grid.removeWidget(container)
                    container.setParent(None)
                    self.face_grid_widgets.remove(container)
            
            self.selected_faces.clear()
            self.remove_face_button.setEnabled(False)
            self.status_message_changed.emit(f"已删除 {len(self.selected_faces)} 个人脸图像")
    
    def refresh(self):
        """刷新界面"""
        # 清空输入
        self.image_path_input.clear()
        self.image_drop_area.setText("拖拽包含人脸的图像文件到此处")
        self.results_list.clear()
        self.person_list.clear()
        self.clear_face_grid()
        
        # 重置状态
        self.current_results.clear()
        self.current_persons.clear()
        self.selected_person = None
        self.selected_faces.clear()
        
        self.edit_person_button.setEnabled(False)
        self.delete_person_button.setEnabled(False)
        self.remove_face_button.setEnabled(False)
        
        self.status_message_changed.emit("人脸识别界面已刷新")