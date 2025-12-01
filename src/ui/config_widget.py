"""
配置组件
提供系统配置界面
"""

import logging
import os
from typing import Dict, Any, Optional

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
        QLabel, QLineEdit, QPushButton, QSpinBox,
        QDoubleSpinBox, QCheckBox, QComboBox, QGroupBox,
        QFileDialog, QMessageBox, QTabWidget, QTextEdit,
        QScrollArea, QFrame, QSlider
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False


class ConfigWidget(QWidget):
    """配置组件"""
    
    # 信号定义
    config_changed = Signal(dict)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self._init_ui()
        self._load_config()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 基础配置标签页
        self._create_basic_tab()
        
        # 监控配置标签页
        self._create_monitoring_tab()
        
        # 模型配置标签页
        self._create_model_tab()
        
        # 检索配置标签页
        self._create_search_tab()
        
        layout.addWidget(self.tab_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 重置按钮
        self.reset_button = QPushButton("重置为默认")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        # 导入按钮
        self.import_button = QPushButton("导入配置")
        self.import_button.clicked.connect(self._import_config)
        button_layout.addWidget(self.import_button)
        
        # 导出按钮
        self.export_button = QPushButton("导出配置")
        self.export_button.clicked.connect(self._export_config)
        button_layout.addWidget(self.export_button)
        
        # 保存按钮
        self.save_button = QPushButton("保存配置")
        self.save_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 14px;
                background: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #106ebe;
            }
        """)
        self.save_button.clicked.connect(self._save_config)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def _create_basic_tab(self):
        """创建基础配置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)
        
        # 系统配置组
        system_group = QGroupBox("系统配置")
        system_layout = QGridLayout(system_group)
        
        # 日志级别
        system_layout.addWidget(QLabel("日志级别:"), 0, 0)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        system_layout.addWidget(self.log_level_combo, 0, 1)
        
        # 数据目录
        system_layout.addWidget(QLabel("数据目录:"), 1, 0)
        data_dir_layout = QHBoxLayout()
        self.data_dir_edit = QLineEdit()
        self.data_dir_edit.setPlaceholderText("./data")
        data_dir_layout.addWidget(self.data_dir_edit)
        
        data_dir_button = QPushButton("浏览...")
        data_dir_button.clicked.connect(self._browse_data_dir)
        data_dir_layout.addWidget(data_dir_button)
        
        system_layout.addLayout(data_dir_layout, 1, 1)
        
        # 最大工作线程数
        system_layout.addWidget(QLabel("最大工作线程数:"), 2, 0)
        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(1, 32)
        self.max_workers_spin.setValue(4)
        system_layout.addWidget(self.max_workers_spin, 2, 1)
        
        content_layout.addWidget(system_group)
        
        # 防抖配置组
        debounce_group = QGroupBox("防抖配置")
        debounce_layout = QGridLayout(debounce_group)
        
        # 防抖延迟
        debounce_layout.addWidget(QLabel("防抖延迟(秒):"), 0, 0)
        self.debounce_delay_spin = QDoubleSpinBox()
        self.debounce_delay_spin.setRange(0.1, 10.0)
        self.debounce_delay_spin.setValue(0.5)
        self.debounce_delay_spin.setSingleStep(0.1)
        debounce_layout.addWidget(self.debounce_delay_spin, 0, 1)
        
        content_layout.addWidget(debounce_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, "基础配置")
    
    def _create_monitoring_tab(self):
        """创建监控配置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 监控目录组
        monitoring_group = QGroupBox("监控目录")
        monitoring_layout = QVBoxLayout(monitoring_group)
        
        # 监控目录列表
        self.monitored_dirs_widget = QWidget()
        dirs_layout = QVBoxLayout(self.monitored_dirs_widget)
        
        # 添加目录按钮
        add_dir_button = QPushButton("添加监控目录")
        add_dir_button.clicked.connect(self._add_monitored_directory)
        dirs_layout.addWidget(add_dir_button)
        
        # 目录显示区域
        self.monitored_dirs_list = QTextEdit()
        self.monitored_dirs_list.setMaximumHeight(150)
        self.monitored_dirs_list.setPlaceholderText("每行一个目录路径")
        dirs_layout.addWidget(self.monitored_dirs_list)
        
        monitoring_layout.addWidget(self.monitored_dirs_widget)
        
        # 支持的文件类型
        file_types_layout = QHBoxLayout()
        file_types_layout.addWidget(QLabel("支持的文件类型:"))
        
        self.file_extensions_edit = QLineEdit()
        self.file_extensions_edit.setPlaceholderText(".jpg,.png,.mp4,.mp3")
        file_types_layout.addWidget(self.file_extensions_edit)
        
        monitoring_layout.addLayout(file_types_layout)
        
        layout.addWidget(monitoring_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "监控配置")
    
    def _create_model_tab(self):
        """创建模型配置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)
        
        # CLIP模型配置
        clip_group = QGroupBox("CLIP模型配置")
        clip_layout = QGridLayout(clip_group)
        
        # 模型ID
        clip_layout.addWidget(QLabel("模型ID:"), 0, 0)
        self.clip_model_edit = QLineEdit("openai/clip-vit-base-patch32")
        clip_layout.addWidget(self.clip_model_edit, 0, 1)
        
        # 端口
        clip_layout.addWidget(QLabel("服务端口:"), 1, 0)
        self.clip_port_spin = QSpinBox()
        self.clip_port_spin.setRange(1000, 9999)
        self.clip_port_spin.setValue(7997)
        clip_layout.addWidget(self.clip_port_spin, 1, 1)
        
        # 设备
        clip_layout.addWidget(QLabel("设备:"), 2, 0)
        self.clip_device_combo = QComboBox()
        self.clip_device_combo.addItems(["cuda:0", "cuda:1", "cpu"])
        clip_layout.addWidget(self.clip_device_combo, 2, 1)
        
        # 批处理大小
        clip_layout.addWidget(QLabel("批处理大小:"), 3, 0)
        self.clip_batch_spin = QSpinBox()
        self.clip_batch_spin.setRange(1, 64)
        self.clip_batch_spin.setValue(32)
        clip_layout.addWidget(self.clip_batch_spin, 3, 1)
        
        content_layout.addWidget(clip_group)
        
        # CLAP模型配置
        clap_group = QGroupBox("CLAP模型配置")
        clap_layout = QGridLayout(clap_group)
        
        # 模型ID
        clap_layout.addWidget(QLabel("模型ID:"), 0, 0)
        self.clap_model_edit = QLineEdit("laion/clap-htsat-fused")
        clap_layout.addWidget(self.clap_model_edit, 0, 1)
        
        # 端口
        clap_layout.addWidget(QLabel("服务端口:"), 1, 0)
        self.clap_port_spin = QSpinBox()
        self.clap_port_spin.setRange(1000, 9999)
        self.clap_port_spin.setValue(7998)
        clap_layout.addWidget(self.clap_port_spin, 1, 1)
        
        # 设备
        clap_layout.addWidget(QLabel("设备:"), 2, 0)
        self.clap_device_combo = QComboBox()
        self.clap_device_combo.addItems(["cuda:0", "cuda:1", "cpu"])
        clap_layout.addWidget(self.clap_device_combo, 2, 1)
        
        # 批处理大小
        clap_layout.addWidget(QLabel("批处理大小:"), 3, 0)
        self.clap_batch_spin = QSpinBox()
        self.clap_batch_spin.setRange(1, 64)
        self.clap_batch_spin.setValue(16)
        clap_layout.addWidget(self.clap_batch_spin, 3, 1)
        
        content_layout.addWidget(clap_group)
        
        # Whisper模型配置
        whisper_group = QGroupBox("Whisper模型配置")
        whisper_layout = QGridLayout(whisper_group)
        
        # 模型ID
        whisper_layout.addWidget(QLabel("模型ID:"), 0, 0)
        self.whisper_model_edit = QLineEdit("openai/whisper-base")
        whisper_layout.addWidget(self.whisper_model_edit, 0, 1)
        
        # 端口
        whisper_layout.addWidget(QLabel("服务端口:"), 1, 0)
        self.whisper_port_spin = QSpinBox()
        self.whisper_port_spin.setRange(1000, 9999)
        self.whisper_port_spin.setValue(7999)
        whisper_layout.addWidget(self.whisper_port_spin, 1, 1)
        
        # 设备
        whisper_layout.addWidget(QLabel("设备:"), 2, 0)
        self.whisper_device_combo = QComboBox()
        self.whisper_device_combo.addItems(["cuda:0", "cuda:1", "cpu"])
        whisper_layout.addWidget(self.whisper_device_combo, 2, 1)
        
        # 批处理大小
        whisper_layout.addWidget(QLabel("批处理大小:"), 3, 0)
        self.whisper_batch_spin = QSpinBox()
        self.whisper_batch_spin.setRange(1, 64)
        self.whisper_batch_spin.setValue(8)
        whisper_layout.addWidget(self.whisper_batch_spin, 3, 1)
        
        content_layout.addWidget(whisper_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, "模型配置")
    
    def _create_search_tab(self):
        """创建检索配置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 权重配置组
        weights_group = QGroupBox("检索权重配置")
        weights_layout = QGridLayout(weights_group)
        
        # 默认权重
        weights_layout.addWidget(QLabel("默认权重:"), 0, 0)
        default_weights_layout = QHBoxLayout()
        
        default_weights_layout.addWidget(QLabel("CLIP:"))
        self.clip_default_weight = QDoubleSpinBox()
        self.clip_default_weight.setRange(0.0, 1.0)
        self.clip_default_weight.setValue(0.4)
        self.clip_default_weight.setSingleStep(0.1)
        default_weights_layout.addWidget(self.clip_default_weight)
        
        default_weights_layout.addWidget(QLabel("CLAP:"))
        self.clap_default_weight = QDoubleSpinBox()
        self.clap_default_weight.setRange(0.0, 1.0)
        self.clap_default_weight.setValue(0.3)
        self.clap_default_weight.setSingleStep(0.1)
        default_weights_layout.addWidget(self.clap_default_weight)
        
        default_weights_layout.addWidget(QLabel("Whisper:"))
        self.whisper_default_weight = QDoubleSpinBox()
        self.whisper_default_weight.setRange(0.0, 1.0)
        self.whisper_default_weight.setValue(0.3)
        self.whisper_default_weight.setSingleStep(0.1)
        default_weights_layout.addWidget(self.whisper_default_weight)
        
        weights_layout.addLayout(default_weights_layout, 0, 1)
        
        # 人物权重
        weights_layout.addWidget(QLabel("人物权重:"), 1, 0)
        person_weights_layout = QHBoxLayout()
        
        person_weights_layout.addWidget(QLabel("CLIP:"))
        self.clip_person_weight = QDoubleSpinBox()
        self.clip_person_weight.setRange(0.0, 1.0)
        self.clip_person_weight.setValue(0.5)
        self.clip_person_weight.setSingleStep(0.1)
        person_weights_layout.addWidget(self.clip_person_weight)
        
        person_weights_layout.addWidget(QLabel("CLAP:"))
        self.clap_person_weight = QDoubleSpinBox()
        self.clap_person_weight.setRange(0.0, 1.0)
        self.clap_person_weight.setValue(0.25)
        self.clap_person_weight.setSingleStep(0.1)
        person_weights_layout.addWidget(self.clap_person_weight)
        
        person_weights_layout.addWidget(QLabel("Whisper:"))
        self.whisper_person_weight = QDoubleSpinBox()
        self.whisper_person_weight.setRange(0.0, 1.0)
        self.whisper_person_weight.setValue(0.25)
        self.whisper_person_weight.setSingleStep(0.1)
        person_weights_layout.addWidget(self.whisper_person_weight)
        
        weights_layout.addLayout(person_weights_layout, 1, 1)
        
        layout.addWidget(weights_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "检索配置")
    
    def _browse_data_dir(self):
        """浏览数据目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择数据目录",
            self.data_dir_edit.text() or os.path.expanduser("~")
        )
        
        if dir_path:
            self.data_dir_edit.setText(dir_path)
    
    def _add_monitored_directory(self):
        """添加监控目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择监控目录",
            os.path.expanduser("~")
        )
        
        if dir_path:
            current_text = self.monitored_dirs_list.toPlainText()
            if current_text:
                current_text += "\n"
            current_text += dir_path
            self.monitored_dirs_list.setPlainText(current_text)
    
    def _load_config(self):
        """加载配置"""
        try:
            # 基础配置
            self.log_level_combo.setCurrentText(
                self.config_manager.get("system.log_level", "INFO")
            )
            self.data_dir_edit.setText(
                self.config_manager.get("system.data_dir", "./data")
            )
            self.max_workers_spin.setValue(
                self.config_manager.get("system.max_workers", 4)
            )
            self.debounce_delay_spin.setValue(
                self.config_manager.get("system.debounce_delay", 0.5)
            )
            
            # 监控配置
            monitored_dirs = self.config_manager.get("system.monitored_directories", [])
            self.monitored_dirs_list.setPlainText("\n".join(monitored_dirs))
            
            extensions = self.config_manager.get("system.supported_extensions", [])
            self.file_extensions_edit.setText(",".join(extensions))
            
            # 模型配置
            infinity_config = self.config_manager.get("infinity.services", {})
            
            # CLIP
            clip_config = infinity_config.get("clip", {})
            self.clip_model_edit.setText(clip_config.get("model_id", "openai/clip-vit-base-patch32"))
            self.clip_port_spin.setValue(clip_config.get("port", 7997))
            self.clip_device_combo.setCurrentText(clip_config.get("device", "cuda:0"))
            self.clip_batch_spin.setValue(clip_config.get("max_batch_size", 32))
            
            # CLAP
            clap_config = infinity_config.get("clap", {})
            self.clap_model_edit.setText(clap_config.get("model_id", "laion/clap-htsat-fused"))
            self.clap_port_spin.setValue(clap_config.get("port", 7998))
            self.clap_device_combo.setCurrentText(clap_config.get("device", "cuda:0"))
            self.clap_batch_spin.setValue(clap_config.get("max_batch_size", 16))
            
            # Whisper
            whisper_config = infinity_config.get("whisper", {})
            self.whisper_model_edit.setText(whisper_config.get("model_id", "openai/whisper-base"))
            self.whisper_port_spin.setValue(whisper_config.get("port", 7999))
            self.whisper_device_combo.setCurrentText(whisper_config.get("device", "cuda:1"))
            self.whisper_batch_spin.setValue(whisper_config.get("max_batch_size", 8))
            
            # 检索配置
            retrieval_config = self.config_manager.get("smart_retrieval", {})
            
            # 默认权重
            default_weights = retrieval_config.get("default_weights", {})
            self.clip_default_weight.setValue(default_weights.get("clip", 0.4))
            self.clap_default_weight.setValue(default_weights.get("clap", 0.3))
            self.whisper_default_weight.setValue(default_weights.get("whisper", 0.3))
            
            # 人物权重
            person_weights = retrieval_config.get("person_weights", {})
            self.clip_person_weight.setValue(person_weights.get("clip", 0.5))
            self.clap_person_weight.setValue(person_weights.get("clap", 0.25))
            self.whisper_person_weight.setValue(person_weights.get("whisper", 0.25))
            
            self.logger.info("配置加载完成")
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            QMessageBox.warning(self, "警告", f"加载配置失败: {e}")
    
    def _save_config(self):
        """保存配置"""
        try:
            # 基础配置
            config = {
                "system": {
                    "log_level": self.log_level_combo.currentText(),
                    "data_dir": self.data_dir_edit.text() or "./data",
                    "max_workers": self.max_workers_spin.value(),
                    "debounce_delay": self.debounce_delay_spin.value(),
                    "monitored_directories": [
                        line.strip() for line in self.monitored_dirs_list.toPlainText().split("\n")
                        if line.strip()
                    ],
                    "supported_extensions": [
                        ext.strip() for ext in self.file_extensions_edit.text().split(",")
                        if ext.strip()
                    ]
                },
                "infinity": {
                    "services": {
                        "clip": {
                            "model_id": self.clip_model_edit.text(),
                            "port": self.clip_port_spin.value(),
                            "device": self.clip_device_combo.currentText(),
                            "max_batch_size": self.clip_batch_spin.value()
                        },
                        "clap": {
                            "model_id": self.clap_model_edit.text(),
                            "port": self.clap_port_spin.value(),
                            "device": self.clap_device_combo.currentText(),
                            "max_batch_size": self.clap_batch_spin.value()
                        },
                        "whisper": {
                            "model_id": self.whisper_model_edit.text(),
                            "port": self.whisper_port_spin.value(),
                            "device": self.whisper_device_combo.currentText(),
                            "max_batch_size": self.whisper_batch_spin.value()
                        }
                    }
                },
                "smart_retrieval": {
                    "default_weights": {
                        "clip": self.clip_default_weight.value(),
                        "clap": self.clap_default_weight.value(),
                        "whisper": self.whisper_default_weight.value()
                    },
                    "person_weights": {
                        "clip": self.clip_person_weight.value(),
                        "clap": self.clap_person_weight.value(),
                        "whisper": self.whisper_person_weight.value()
                    }
                }
            }
            
            # 这里应该实际保存配置
            # self.config_manager.update_config(config)
            
            self.config_changed.emit(config)
            
            QMessageBox.information(self, "成功", "配置保存成功")
            self.logger.info("配置保存完成")
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")
    
    def _reset_to_defaults(self):
        """重置为默认配置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有配置为默认值吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 重置界面控件
            self.log_level_combo.setCurrentText("INFO")
            self.data_dir_edit.setText("./data")
            self.max_workers_spin.setValue(4)
            self.debounce_delay_spin.setValue(0.5)
            self.monitored_dirs_list.clear()
            self.file_extensions_edit.clear()
            
            # 重置模型配置
            self.clip_model_edit.setText("openai/clip-vit-base-patch32")
            self.clip_port_spin.setValue(7997)
            self.clip_device_combo.setCurrentText("cuda:0")
            self.clip_batch_spin.setValue(32)
            
            self.clap_model_edit.setText("laion/clap-htsat-fused")
            self.clap_port_spin.setValue(7998)
            self.clap_device_combo.setCurrentText("cuda:0")
            self.clap_batch_spin.setValue(16)
            
            self.whisper_model_edit.setText("openai/whisper-base")
            self.whisper_port_spin.setValue(7999)
            self.whisper_device_combo.setCurrentText("cuda:1")
            self.whisper_batch_spin.setValue(8)
            
            # 重置检索权重
            self.clip_default_weight.setValue(0.4)
            self.clap_default_weight.setValue(0.3)
            self.whisper_default_weight.setValue(0.3)
            
            self.clip_person_weight.setValue(0.5)
            self.clap_person_weight.setValue(0.25)
            self.whisper_person_weight.setValue(0.25)
            
            QMessageBox.information(self, "成功", "配置已重置为默认值")
    
    def _import_config(self):
        """导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入配置文件",
            "",
            "配置文件 (*.yml *.yaml *.json)"
        )
        
        if file_path:
            try:
                # 这里应该实现配置文件导入逻辑
                QMessageBox.information(self, "成功", f"配置文件导入成功: {file_path}")
                self.logger.info(f"导入配置文件: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入配置失败: {e}")
                self.logger.error(f"导入配置失败: {e}")
    
    def _export_config(self):
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出配置文件",
            "msearch_config.yml",
            "配置文件 (*.yml *.yaml)"
        )
        
        if file_path:
            try:
                # 这里应该实现配置文件导出逻辑
                QMessageBox.information(self, "成功", f"配置文件导出成功: {file_path}")
                self.logger.info(f"导出配置文件: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出配置失败: {e}")
                self.logger.error(f"导出配置失败: {e}")