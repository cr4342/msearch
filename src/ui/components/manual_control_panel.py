"""
手动操作控制面板组件
提供手动触发扫描、向量化等操作的控制界面
"""

from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QFrame,
    QCheckBox,
    QGroupBox,
    QMessageBox,
)
from PySide6.QtCore import Signal, Qt


class ManualControlPanel(QWidget):
    """手动操作控制面板"""

    scan_triggered = Signal(dict)
    vectorization_triggered = Signal(dict)
    control_changed = Signal(dict)

    def __init__(self, parent=None):
        """初始化手动操作控制面板"""
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 扫描控制
        scan_group = self._create_scan_control_group()
        layout.addWidget(scan_group)

        # 向量化控制
        vectorization_group = self._create_vectorization_control_group()
        layout.addWidget(vectorization_group)

        # 任务控制
        task_control_group = self._create_task_control_group()
        layout.addWidget(task_control_group)

        layout.addStretch()

    def _create_scan_control_group(self) -> QGroupBox:
        """创建扫描控制组"""
        group = QGroupBox("扫描控制")
        group.setStyleSheet(
            """
            QGroupBox {
                background-color: white;
                border: 1px solid #E5E6EB;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                color: #4E5969;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """
        )

        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # 全量扫描
        full_scan_layout = QHBoxLayout()
        full_scan_btn = QPushButton("🔍 全量扫描")
        full_scan_btn.setFixedHeight(32)
        full_scan_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #165DFF;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0E42D2;
            }
            QPushButton:pressed {
                background-color: #0924A8;
            }
        """
        )
        full_scan_btn.clicked.connect(self._on_full_scan)
        full_scan_layout.addWidget(full_scan_btn)
        layout.addLayout(full_scan_layout)

        # 指定目录扫描
        dir_scan_layout = QHBoxLayout()
        dir_scan_layout.addWidget(QLabel("目录:"))

        self.scan_directory_combo = QComboBox()
        self.scan_directory_combo.setFixedHeight(28)
        self.scan_directory_combo.setStyleSheet(
            """
            QComboBox {
                background-color: white;
                border: 1px solid #E5E6EB;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
            }
        """
        )
        self.scan_directory_combo.setEditable(True)
        self.scan_directory_combo.addItem("所有监控目录")
        dir_scan_layout.addWidget(self.scan_directory_combo)

        scan_dir_btn = QPushButton("扫描")
        scan_dir_btn.setFixedHeight(28)
        scan_dir_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #00B42A;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #00994E;
            }
            QPushButton:pressed {
                background-color: #008045;
            }
        """
        )
        scan_dir_btn.clicked.connect(self._on_directory_scan)
        dir_scan_layout.addWidget(scan_dir_btn)

        layout.addLayout(dir_scan_layout)

        return group

    def _create_vectorization_control_group(self) -> QGroupBox:
        """创建向量化控制组"""
        group = QGroupBox("向量化控制")
        group.setStyleSheet(
            """
            QGroupBox {
                background-color: white;
                border: 1px solid #E5E6EB;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                color: #4E5969;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """
        )

        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # 文件类型选择
        type_layout = QHBoxLayout()
        type_label = QLabel("文件类型:")
        type_label.setStyleSheet("color: #86909C; font-size: 11px;")
        type_layout.addWidget(type_label)

        self.file_type_combo = QComboBox()
        self.file_type_combo.addItems(["全部", "图像", "视频", "音频"])
        self.file_type_combo.setFixedHeight(28)
        self.file_type_combo.setStyleSheet(
            """
            QComboBox {
                background-color: white;
                border: 1px solid #E5E6EB;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
            }
        """
        )
        type_layout.addWidget(self.file_type_combo)
        layout.addLayout(type_layout)

        # 启动向量化
        vectorize_btn = QPushButton("▶️ 开始向量化")
        vectorize_btn.setFixedHeight(32)
        vectorize_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #FF7D00;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #E56500;
            }
            QPushButton:pressed {
                background-color: #CC5500;
            }
        """
        )
        vectorize_btn.clicked.connect(self._on_vectorize)
        layout.addWidget(vectorize_btn)

        # 重新向量化失败文件
        revectorize_btn = QPushButton("🔄 重新向量化失败文件")
        revectorize_btn.setFixedHeight(28)
        revectorize_btn.setStyleSheet(
            """
            QPushButton {
                background-color: white;
                border: 1px solid #E5E6EB;
                color: #4E5969;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #F2F3F5;
                border-color: #165DFF;
            }
        """
        )
        revectorize_btn.clicked.connect(self._on_revectorize_failed)
        layout.addWidget(revectorize_btn)

        return group

    def _create_task_control_group(self) -> QGroupBox:
        """创建任务控制组"""
        group = QGroupBox("任务控制")
        group.setStyleSheet(
            """
            QGroupBox {
                background-color: white;
                border: 1px solid #E5E6EB;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                color: #4E5969;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """
        )

        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # 资源控制
        resource_layout = QHBoxLayout()
        resource_label = QLabel("并发数:")
        resource_label.setStyleSheet("color: #86909C; font-size: 11px;")
        resource_layout.addWidget(resource_label)

        self.concurrent_spinbox = QSpinBox()
        self.concurrent_spinbox.setRange(1, 16)
        self.concurrent_spinbox.setValue(4)
        self.concurrent_spinbox.setFixedHeight(28)
        self.concurrent_spinbox.setStyleSheet(
            """
            QSpinBox {
                background-color: white;
                border: 1px solid #E5E6EB;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
            }
        """
        )
        self.concurrent_spinbox.valueChanged.connect(self._on_control_changed)
        resource_layout.addWidget(self.concurrent_spinbox)

        resource_layout.addStretch()
        layout.addLayout(resource_layout)

        # GPU使用控制
        gpu_layout = QHBoxLayout()
        gpu_label = QLabel("GPU:")
        gpu_label.setStyleSheet("color: #86909C; font-size: 11px;")
        gpu_layout.addWidget(gpu_label)

        self.gpu_checkbox = QCheckBox("启用GPU加速")
        self.gpu_checkbox.setStyleSheet(
            """
            QCheckBox {
                color: #4E5969;
                font-size: 11px;
            }
        """
        )
        self.gpu_checkbox.stateChanged.connect(self._on_control_changed)
        gpu_layout.addWidget(self.gpu_checkbox)

        gpu_layout.addStretch()
        layout.addLayout(gpu_layout)

        # 控制按钮
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        self.pause_all_btn = QPushButton("⏸️ 暂停全部")
        self.pause_all_btn.setFixedHeight(28)
        self.pause_all_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #FF7D00;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #E56500;
            }
        """
        )
        self.pause_all_btn.clicked.connect(self._on_pause_all)
        controls_layout.addWidget(self.pause_all_btn)

        self.resume_all_btn = QPushButton("▶️ 恢复全部")
        self.resume_all_btn.setFixedHeight(28)
        self.resume_all_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #00B42A;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #00994E;
            }
        """
        )
        self.resume_all_btn.clicked.connect(self._on_resume_all)
        controls_layout.addWidget(self.resume_all_btn)

        self.cancel_all_btn = QPushButton("❌ 取消全部")
        self.cancel_all_btn.setFixedHeight(28)
        self.cancel_all_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #F53F3F;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #D9363E;
            }
        """
        )
        self.cancel_all_btn.clicked.connect(self._on_cancel_all)
        controls_layout.addWidget(self.cancel_all_btn)

        layout.addLayout(controls_layout)

        return group

    def _on_full_scan(self):
        """全量扫描"""
        config = {"type": "full_scan", "directory": None}
        self.scan_triggered.emit(config)
        QMessageBox.information(self, "扫描", "已启动全量扫描")

    def _on_directory_scan(self):
        """指定目录扫描"""
        directory = self.scan_directory_combo.currentText()
        config = {
            "type": "directory_scan",
            "directory": directory if directory != "所有监控目录" else None,
        }
        self.scan_triggered.emit(config)
        QMessageBox.information(self, "扫描", f"已启动目录扫描: {directory}")

    def _on_vectorize(self):
        """开始向量化"""
        file_type = self.file_type_combo.currentText()
        config = {
            "file_type": file_type if file_type != "全部" else None,
            "concurrent": self.concurrent_spinbox.value(),
            "use_gpu": self.gpu_checkbox.isChecked(),
        }
        self.vectorization_triggered.emit(config)
        QMessageBox.information(self, "向量化", f"已启动向量化: {file_type}")

    def _on_revectorize_failed(self):
        """重新向量化失败文件"""
        config = {"file_type": None, "revectorize_failed": True}
        self.vectorization_triggered.emit(config)
        QMessageBox.information(self, "向量化", "已启动重新向量化失败文件")

    def _on_pause_all(self):
        """暂停全部任务"""
        self.control_changed.emit({"action": "pause_all"})
        QMessageBox.information(self, "任务控制", "已暂停所有任务")

    def _on_resume_all(self):
        """恢复全部任务"""
        self.control_changed.emit({"action": "resume_all"})
        QMessageBox.information(self, "任务控制", "已恢复所有任务")

    def _on_cancel_all(self):
        """取消全部任务"""
        reply = QMessageBox.question(
            self,
            "确认取消",
            "确定要取消所有任务吗？已处理的结果将被保留。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.control_changed.emit({"action": "cancel_all"})
            QMessageBox.information(self, "任务控制", "已取消所有任务")

    def _on_control_changed(self):
        """控制参数变更"""
        config = {
            "concurrent": self.concurrent_spinbox.value(),
            "use_gpu": self.gpu_checkbox.isChecked(),
        }
        self.control_changed.emit(config)

    def get_control_config(self) -> Dict[str, Any]:
        """获取当前控制配置"""
        return {
            "concurrent": self.concurrent_spinbox.value(),
            "use_gpu": self.gpu_checkbox.isChecked(),
            "scan_directory": self.scan_directory_combo.currentText(),
            "file_type": self.file_type_combo.currentText(),
        }
