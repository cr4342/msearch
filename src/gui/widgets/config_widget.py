#!/usr/bin/env python3
"""
msearch PySide6配置组件
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


class ConfigWidget(QWidget):
    """配置组件"""
    
    # 信号定义
    status_message_changed = Signal(str)
    config_updated = Signal(dict)  # 配置更新
    
    def __init__(self, api_client=None, config=None, parent=None):
        super().__init__(parent)
        
        # API客户端和配置
        self.api_client = api_client
        self.config = config or {}
        
        # 初始化UI
        self.init_ui()
        
        # 初始化状态
        self.init_state()
        
        # 连接信号
        self.connect_signals()
        
        # 应用样式
        self.apply_styles()
        
        logger.info("配置组件初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建系统配置选项卡
        self.create_system_config_tab()
        
        # 创建AI模型配置选项卡
        self.create_ai_model_config_tab()
        
        # 创建数据处理配置选项卡
        self.create_data_processing_config_tab()
        
        # 创建API配置选项卡
        self.create_api_config_tab()
    
    def create_system_config_tab(self):
        """创建系统配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 基础配置组
        basic_group = QGroupBox("基础配置")
        basic_layout = QFormLayout(basic_group)
        
        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        basic_layout.addRow("日志级别:", self.log_level_combo)
        
        # 数据目录
        data_dir_layout = QHBoxLayout()
        self.data_dir_input = QLineEdit()
        data_dir_layout.addWidget(self.data_dir_input)
        browse_data_dir_button = QPushButton("浏览...")
        browse_data_dir_button.clicked.connect(self.browse_data_dir)
        data_dir_layout.addWidget(browse_data_dir_button)
        basic_layout.addRow("数据目录:", data_dir_layout)
        
        layout.addWidget(basic_group)
        
        # 监控目录组
        monitoring_group = QGroupBox("文件监控配置")
        monitoring_layout = QVBoxLayout(monitoring_group)
        
        # 监控目录列表
        self.watch_dirs_list = QListWidget()
        monitoring_layout.addWidget(self.watch_dirs_list)
        
        # 监控目录操作按钮
        watch_dir_actions_layout = QHBoxLayout()
        
        self.add_watch_dir_button = QPushButton("添加监控目录")
        self.add_watch_dir_button.clicked.connect(self.add_watch_dir)
        watch_dir_actions_layout.addWidget(self.add_watch_dir_button)
        
        self.remove_watch_dir_button = QPushButton("移除选中目录")
        self.remove_watch_dir_button.clicked.connect(self.remove_watch_dir)
        watch_dir_actions_layout.addWidget(self.remove_watch_dir_button)
        
        monitoring_layout.addLayout(watch_dir_actions_layout)
        
        layout.addWidget(monitoring_group)
        
        # 保存配置按钮
        save_button = QPushButton("保存配置")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)
        
        self.tab_widget.addTab(tab, "系统配置")
    
    def create_ai_model_config_tab(self):
        """创建AI模型配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # CLIP模型配置
        clip_group = QGroupBox("CLIP模型配置")
        clip_layout = QFormLayout(clip_group)
        
        self.clip_model_input = QLineEdit()
        self.clip_device_combo = QComboBox()
        self.clip_device_combo.addItems(["auto", "cpu", "cuda"])
        self.clip_batch_size_spin = QSpinBox()
        self.clip_batch_size_spin.setRange(1, 64)
        self.clip_batch_size_spin.setValue(16)
        
        clip_layout.addRow("模型名称:", self.clip_model_input)
        clip_layout.addRow("设备:", self.clip_device_combo)
        clip_layout.addRow("批处理大小:", self.clip_batch_size_spin)
        
        layout.addWidget(clip_group)
        
        # CLAP模型配置
        clap_group = QGroupBox("CLAP模型配置")
        clap_layout = QFormLayout(clap_group)
        
        self.clap_model_input = QLineEdit()
        self.clap_device_combo = QComboBox()
        self.clap_device_combo.addItems(["auto", "cpu", "cuda"])
        self.clap_batch_size_spin = QSpinBox()
        self.clap_batch_size_spin.setRange(1, 64)
        self.clap_batch_size_spin.setValue(8)
        
        clap_layout.addRow("模型名称:", self.clap_model_input)
        clap_layout.addRow("设备:", self.clap_device_combo)
        clap_layout.addRow("批处理大小:", self.clap_batch_size_spin)
        
        layout.addWidget(clap_group)
        
        # Whisper模型配置
        whisper_group = QGroupBox("Whisper模型配置")
        whisper_layout = QFormLayout(whisper_group)
        
        self.whisper_model_input = QLineEdit()
        self.whisper_device_combo = QComboBox()
        self.whisper_device_combo.addItems(["auto", "cpu", "cuda"])
        self.whisper_batch_size_spin = QSpinBox()
        self.whisper_batch_size_spin.setRange(1, 64)
        self.whisper_batch_size_spin.setValue(4)
        
        whisper_layout.addRow("模型名称:", self.whisper_model_input)
        whisper_layout.addRow("设备:", self.whisper_device_combo)
        whisper_layout.addRow("批处理大小:", self.whisper_batch_size_spin)
        
        layout.addWidget(whisper_group)
        
        # 保存配置按钮
        save_button = QPushButton("保存配置")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)
        
        self.tab_widget.addTab(tab, "AI模型配置")
    
    def create_data_processing_config_tab(self):
        """创建数据处理配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 图像处理配置
        image_group = QGroupBox("图像处理配置")
        image_layout = QFormLayout(image_group)
        
        self.image_max_resolution_spin = QSpinBox()
        self.image_max_resolution_spin.setRange(128, 4096)
        self.image_max_resolution_spin.setValue(1920)
        self.image_batch_size_spin = QSpinBox()
        self.image_batch_size_spin.setRange(1, 64)
        self.image_batch_size_spin.setValue(32)
        
        image_layout.addRow("最大分辨率:", self.image_max_resolution_spin)
        image_layout.addRow("批处理大小:", self.image_batch_size_spin)
        
        layout.addWidget(image_group)
        
        # 视频处理配置
        video_group = QGroupBox("视频处理配置")
        video_layout = QFormLayout(video_group)
        
        self.video_max_resolution_spin = QSpinBox()
        self.video_max_resolution_spin.setRange(128, 4096)
        self.video_max_resolution_spin.setValue(1280)
        self.video_fps_spin = QSpinBox()
        self.video_fps_spin.setRange(1, 60)
        self.video_fps_spin.setValue(8)
        self.video_batch_size_spin = QSpinBox()
        self.video_batch_size_spin.setRange(1, 64)
        self.video_batch_size_spin.setValue(16)
        
        video_layout.addRow("最大分辨率:", self.video_max_resolution_spin)
        video_layout.addRow("目标帧率:", self.video_fps_spin)
        video_layout.addRow("批处理大小:", self.video_batch_size_spin)
        
        layout.addWidget(video_group)
        
        # 音频处理配置
        audio_group = QGroupBox("音频处理配置")
        audio_layout = QFormLayout(audio_group)
        
        self.audio_sample_rate_spin = QSpinBox()
        self.audio_sample_rate_spin.setRange(8000, 48000)
        self.audio_sample_rate_spin.setValue(16000)
        self.audio_channels_spin = QSpinBox()
        self.audio_channels_spin.setRange(1, 2)
        self.audio_channels_spin.setValue(1)
        self.audio_batch_size_spin = QSpinBox()
        self.audio_batch_size_spin.setRange(1, 64)
        self.audio_batch_size_spin.setValue(8)
        
        audio_layout.addRow("采样率:", self.audio_sample_rate_spin)
        audio_layout.addRow("声道数:", self.audio_channels_spin)
        audio_layout.addRow("批处理大小:", self.audio_batch_size_spin)
        
        layout.addWidget(audio_group)
        
        # 保存配置按钮
        save_button = QPushButton("保存配置")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)
        
        self.tab_widget.addTab(tab, "数据处理配置")
    
    def create_api_config_tab(self):
        """创建API配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # API服务配置
        api_group = QGroupBox("API服务配置")
        api_layout = QFormLayout(api_group)
        
        self.api_host_input = QLineEdit()
        self.api_port_spin = QSpinBox()
        self.api_port_spin.setRange(1024, 65535)
        self.api_port_spin.setValue(8000)
        
        api_layout.addRow("主机地址:", self.api_host_input)
        api_layout.addRow("端口号:", self.api_port_spin)
        
        layout.addWidget(api_group)
        
        # 数据库配置
        db_group = QGroupBox("数据库配置")
        db_layout = QFormLayout(db_group)
        
        self.db_path_input = QLineEdit()
        self.db_pool_size_spin = QSpinBox()
        self.db_pool_size_spin.setRange(1, 20)
        self.db_pool_size_spin.setValue(10)
        
        db_layout.addRow("数据库路径:", self.db_path_input)
        db_layout.addRow("连接池大小:", self.db_pool_size_spin)
        
        layout.addWidget(db_group)
        
        # 保存配置按钮
        save_button = QPushButton("保存配置")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)
        
        self.tab_widget.addTab(tab, "API配置")
    
    def init_state(self):
        """初始化状态"""
        # 加载当前配置
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            # 从配置中加载系统配置
            general_config = self.config.get('general', {})
            log_level = general_config.get('log_level', 'INFO')
            data_dir = general_config.get('data_dir', './data')
            watch_dirs = general_config.get('watch_directories', [])
            
            # 设置系统配置值
            self.log_level_combo.setCurrentText(log_level)
            self.data_dir_input.setText(data_dir)
            
            # 设置监控目录
            self.watch_dirs_list.clear()
            for dir_path in watch_dirs:
                self.watch_dirs_list.addItem(dir_path)
            
            # 从配置中加载AI模型配置
            models_config = self.config.get('models', {})
            
            clip_config = models_config.get('clip', {})
            self.clip_model_input.setText(clip_config.get('model_name', 'sentence-transformers/clip-ViT-B-32'))
            self.clip_device_combo.setCurrentText(clip_config.get('device', 'auto'))
            self.clip_batch_size_spin.setValue(clip_config.get('batch_size', 16))
            
            clap_config = models_config.get('clap', {})
            self.clap_model_input.setText(clap_config.get('model_name', 'sentence-transformers/clap-htsat-unfused'))
            self.clap_device_combo.setCurrentText(clap_config.get('device', 'auto'))
            self.clap_batch_size_spin.setValue(clap_config.get('batch_size', 8))
            
            whisper_config = models_config.get('whisper', {})
            self.whisper_model_input.setText(whisper_config.get('model_name', 'sentence-transformers/all-MiniLM-L6-v2'))
            self.whisper_device_combo.setCurrentText(whisper_config.get('device', 'auto'))
            self.whisper_batch_size_spin.setValue(whisper_config.get('batch_size', 4))
            
            # 从配置中加载数据处理配置
            processing_config = self.config.get('processing', {})
            
            image_config = processing_config.get('image', {})
            self.image_max_resolution_spin.setValue(image_config.get('preprocessing', {}).get('max_resolution', 1920))
            self.image_batch_size_spin.setValue(image_config.get('batch_size', 32))
            
            video_config = processing_config.get('video', {})
            self.video_max_resolution_spin.setValue(video_config.get('preprocessing', {}).get('target_resolution', 720))
            self.video_fps_spin.setValue(video_config.get('preprocessing', {}).get('max_fps', 30))
            self.video_batch_size_spin.setValue(video_config.get('batch_size', 16))
            
            audio_config = processing_config.get('audio', {})
            self.audio_sample_rate_spin.setValue(audio_config.get('preprocessing', {}).get('target_sample_rate', 16000))
            self.audio_channels_spin.setValue(audio_config.get('preprocessing', {}).get('target_channels', 1))
            self.audio_batch_size_spin.setValue(audio_config.get('batch_size', 8))
            
            # 从配置中加载API配置
            api_config = self.config.get('api', {})
            self.api_host_input.setText(api_config.get('host', '0.0.0.0'))
            self.api_port_spin.setValue(api_config.get('port', 8000))
            
            db_config = self.config.get('database', {}).get('sqlite', {})
            self.db_path_input.setText(db_config.get('path', './data/database/msearch.db'))
            self.db_pool_size_spin.setValue(db_config.get('connection_pool_size', 10))
            
            self.status_message_changed.emit("配置加载完成")
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            QMessageBox.critical(self, "错误", f"加载配置失败: {e}")
    
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
            
            QComboBox {
                padding: 8px;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
            }
            
            QSpinBox {
                padding: 8px;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
            }
        """)
    
    def browse_data_dir(self):
        """浏览数据目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择数据目录", self.data_dir_input.text() or ""
        )
        if dir_path:
            self.data_dir_input.setText(dir_path)
    
    def add_watch_dir(self):
        """添加监控目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择监控目录", ""
        )
        if dir_path:
            # 检查是否已存在
            for i in range(self.watch_dirs_list.count()):
                if self.watch_dirs_list.item(i).text() == dir_path:
                    QMessageBox.warning(self, "警告", "目录已存在")
                    return
            
            self.watch_dirs_list.addItem(dir_path)
    
    def remove_watch_dir(self):
        """移除监控目录"""
        current_item = self.watch_dirs_list.currentItem()
        if current_item:
            self.watch_dirs_list.takeItem(self.watch_dirs_list.row(current_item))
    
    def save_config(self):
        """保存配置"""
        # 构建配置字典
        updated_config = {
            'general': {
                'log_level': self.log_level_combo.currentText(),
                'data_dir': self.data_dir_input.text(),
                'watch_directories': [self.watch_dirs_list.item(i).text() for i in range(self.watch_dirs_list.count())]
            },
            'models': {
                'clip': {
                    'model_name': self.clip_model_input.text(),
                    'device': self.clip_device_combo.currentText(),
                    'batch_size': self.clip_batch_size_spin.value()
                },
                'clap': {
                    'model_name': self.clap_model_input.text(),
                    'device': self.clap_device_combo.currentText(),
                    'batch_size': self.clap_batch_size_spin.value()
                },
                'whisper': {
                    'model_name': self.whisper_model_input.text(),
                    'device': self.whisper_device_combo.currentText(),
                    'batch_size': self.whisper_batch_size_spin.value()
                }
            },
            'processing': {
                'image': {
                    'batch_size': self.image_batch_size_spin.value(),
                    'preprocessing': {
                        'max_resolution': self.image_max_resolution_spin.value()
                    }
                },
                'video': {
                    'batch_size': self.video_batch_size_spin.value(),
                    'preprocessing': {
                        'target_resolution': self.video_max_resolution_spin.value(),
                        'max_fps': self.video_fps_spin.value()
                    }
                },
                'audio': {
                    'batch_size': self.audio_batch_size_spin.value(),
                    'preprocessing': {
                        'target_sample_rate': self.audio_sample_rate_spin.value(),
                        'target_channels': self.audio_channels_spin.value()
                    }
                }
            },
            'api': {
                'host': self.api_host_input.text(),
                'port': self.api_port_spin.value()
            },
            'database': {
                'sqlite': {
                    'path': self.db_path_input.text(),
                    'connection_pool_size': self.db_pool_size_spin.value()
                }
            }
        }
        
        # 如果有API客户端，调用API保存配置
        if self.api_client and self.api_client.is_connected():
            try:
                result = self.api_client.update_system_config(updated_config)
                
                if result and result.get("status") == "success":
                    self.config = updated_config
                    self.config_updated.emit(updated_config)
                    self.status_message_changed.emit("配置保存成功")
                    QMessageBox.information(self, "成功", "配置保存成功")
                else:
                    error_msg = result.get("message", "未知错误") if result else "API调用失败"
                    QMessageBox.critical(self, "错误", f"配置保存失败: {error_msg}")
            except Exception as e:
                logger.error(f"保存配置失败: {e}")
                QMessageBox.critical(self, "错误", f"保存配置失败: {e}")
        else:
            # 模拟保存配置
            self.config = updated_config
            self.config_updated.emit(updated_config)
            self.status_message_changed.emit("配置保存成功（模拟）")
            QMessageBox.information(self, "成功", "配置保存成功（模拟）")
    
    def refresh(self):
        """刷新界面"""
        # 重新加载配置
        self.load_config()
        self.status_message_changed.emit("配置界面已刷新")