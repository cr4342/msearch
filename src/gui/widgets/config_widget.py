#!/usr/bin/env python3
"""
msearch PySide6配置管理对话框
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import yaml

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget, QFrame,
    QScrollArea, QProgressBar, QComboBox, QSpinBox, QCheckBox, QSlider,
    QGroupBox, QSplitter, QToolButton, QButtonGroup, QRadioButton,
    QSizePolicy, QSpacerItem, QFileDialog, QMessageBox, QTabWidget,
    QListWidget, QListWidgetItem, QTextBrowser, QStackedWidget, QDialog,
    QDialogButtonBox
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QObject, QUrl, QSize, QPropertyAnimation,
    QSettings
)
from PySide6.QtGui import (
    QIcon, QPixmap, QFont, QAction, QPalette, QColor, QDesktopServices
)

from src.core.config import load_config
from src.core.config_manager import get_config_manager
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ConfigDialog(QDialog):
    """配置管理对话框"""
    
    def __init__(self, parent=None, api_client=None):
        super().__init__(parent)
        
        # API客户端
        self.api_client = api_client
        
        # 当前配置
        self.current_config = load_config()
        self.original_config = self.current_config.copy()
        
        # 初始化UI
        self.init_ui()
        
        # 加载配置
        self.load_config_values()
        
        # 连接信号
        self.connect_signals()
        
        # 应用样式
        self.apply_styles()
        
        logger.info("配置对话框初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("系统配置")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建各个配置选项卡
        self.create_general_config_tab()
        self.create_search_config_tab()
        self.create_indexing_config_tab()
        self.create_models_config_tab()
        self.create_logging_config_tab()
        self.create_advanced_config_tab()
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("重置")
        self.reset_button.clicked.connect(self.reset_config)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_config)
        button_layout.addWidget(self.button_box)
        
        main_layout.addLayout(button_layout)
    
    def create_general_config_tab(self):
        """创建通用配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 基本设置
        basic_group = QGroupBox("基本设置")
        basic_layout = QFormLayout(basic_group)
        
        # 数据目录
        self.data_dir_input = QLineEdit()
        self.data_dir_input.setReadOnly(True)
        browse_data_dir = QPushButton("浏览...")
        browse_data_dir.clicked.connect(self.browse_data_dir)
        data_dir_layout = QHBoxLayout()
        data_dir_layout.addWidget(self.data_dir_input)
        data_dir_layout.addWidget(browse_data_dir)
        basic_layout.addRow("数据目录:", data_dir_layout)
        
        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        basic_layout.addRow("日志级别:", self.log_level_combo)
        
        layout.addWidget(basic_group)
        
        # 文件监控设置
        monitoring_group = QGroupBox("文件监控设置")
        monitoring_layout = QFormLayout(monitoring_group)
        
        # 监控目录
        self.watch_dirs_text = QTextEdit()
        self.watch_dirs_text.setMaximumHeight(100)
        self.watch_dirs_text.setPlaceholderText("每行一个目录路径")
        monitoring_layout.addRow("监控目录:", self.watch_dirs_text)
        
        # 监控间隔
        self.monitor_interval_spin = QSpinBox()
        self.monitor_interval_spin.setRange(1, 3600)
        self.monitor_interval_spin.setValue(60)
        self.monitor_interval_spin.setSuffix(" 秒")
        monitoring_layout.addRow("监控间隔:", self.monitor_interval_spin)
        
        layout.addWidget(monitoring_group)
        
        # 系统设置
        system_group = QGroupBox("系统设置")
        system_layout = QFormLayout(system_group)
        
        # 最大并发任务数
        self.max_concurrent_tasks_spin = QSpinBox()
        self.max_concurrent_tasks_spin.setRange(1, 16)
        self.max_concurrent_tasks_spin.setValue(4)
        system_layout.addRow("最大并发任务数:", self.max_concurrent_tasks_spin)
        
        # 批处理大小
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 128)
        self.batch_size_spin.setValue(16)
        system_layout.addRow("批处理大小:", self.batch_size_spin)
        
        layout.addWidget(system_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "通用配置")
    
    def create_search_config_tab(self):
        """创建搜索配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 搜索设置
        search_group = QGroupBox("搜索设置")
        search_layout = QFormLayout(search_group)
        
        # 默认结果数量
        self.search_limit_spin = QSpinBox()
        self.search_limit_spin.setRange(10, 100)
        self.search_limit_spin.setValue(20)
        self.search_limit_spin.setSuffix(" 个")
        search_layout.addRow("默认结果数量:", self.search_limit_spin)
        
        # 相似度阈值
        self.similarity_threshold_slider = QSlider(Qt.Horizontal)
        self.similarity_threshold_slider.setRange(0, 100)
        self.similarity_threshold_slider.setValue(70)
        self.similarity_threshold_label = QLabel("0.70")
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(self.similarity_threshold_slider)
        threshold_layout.addWidget(self.similarity_threshold_label)
        search_layout.addRow("相似度阈值:", threshold_layout)
        
        # 启用分层检索
        self.layered_search_checkbox = QCheckBox("启用分层检索（人名搜索优化）")
        self.layered_search_checkbox.setChecked(True)
        search_layout.addRow("", self.layered_search_checkbox)
        
        layout.addWidget(search_group)
        
        # 人脸搜索设置
        face_search_group = QGroupBox("人脸搜索设置")
        face_search_layout = QFormLayout(face_search_group)
        
        # 人脸检测阈值
        self.face_detection_threshold_slider = QSlider(Qt.Horizontal)
        self.face_detection_threshold_slider.setRange(0, 100)
        self.face_detection_threshold_slider.setValue(80)
        self.face_detection_threshold_label = QLabel("0.80")
        face_threshold_layout = QHBoxLayout()
        face_threshold_layout.addWidget(self.face_detection_threshold_slider)
        face_threshold_layout.addWidget(self.face_detection_threshold_label)
        face_search_layout.addRow("人脸检测阈值:", face_threshold_layout)
        
        # 人脸匹配阈值
        self.face_match_threshold_slider = QSlider(Qt.Horizontal)
        self.face_match_threshold_slider.setRange(0, 100)
        self.face_match_threshold_slider.setValue(85)
        self.face_match_threshold_label = QLabel("0.85")
        match_threshold_layout = QHBoxLayout()
        match_threshold_layout.addWidget(self.face_match_threshold_slider)
        match_threshold_layout.addWidget(self.face_match_threshold_label)
        face_search_layout.addRow("人脸匹配阈值:", match_threshold_layout)
        
        layout.addWidget(face_search_group)
        
        # 时间精度设置
        time_precision_group = QGroupBox("时间精度设置")
        time_precision_layout = QFormLayout(time_precision_group)
        
        # 时间戳精度
        self.timestamp_precision_spin = QSpinBox()
        self.timestamp_precision_spin.setRange(1, 10)
        self.timestamp_precision_spin.setValue(2)
        self.timestamp_precision_spin.setSuffix(" 秒")
        time_precision_layout.addRow("时间戳精度:", self.timestamp_precision_spin)
        
        layout.addWidget(time_precision_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "搜索配置")
    
    def create_indexing_config_tab(self):
        """创建索引配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 媒体处理设置
        media_group = QGroupBox("媒体处理设置")
        media_layout = QFormLayout(media_group)
        
        # 视频分辨率限制
        self.video_resolution_combo = QComboBox()
        self.video_resolution_combo.addItems([
            "保持原样", "720p (1280x720)", "480p (854x480)", "360p (640x360)"
        ])
        media_layout.addRow("视频分辨率限制:", self.video_resolution_combo)
        
        # 音频采样率
        self.audio_sample_rate_combo = QComboBox()
        self.audio_sample_rate_combo.addItems(["保持原样", "44100Hz", "22050Hz", "16000Hz", "8000Hz"])
        media_layout.addRow("音频采样率:", self.audio_sample_rate_combo)
        
        # 最小分段时长
        self.min_segment_duration_spin = QSpinBox()
        self.min_segment_duration_spin.setRange(1, 60)
        self.min_segment_duration_spin.setValue(5)
        self.min_segment_duration_spin.setSuffix(" 秒")
        media_layout.addRow("最小分段时长:", self.min_segment_duration_spin)
        
        # 质量过滤
        self.quality_filter_checkbox = QCheckBox("启用质量过滤")
        self.quality_filter_checkbox.setChecked(True)
        media_layout.addRow("", self.quality_filter_checkbox)
        
        layout.addWidget(media_group)
        
        # 索引优化设置
        index_opt_group = QGroupBox("索引优化设置")
        index_opt_layout = QFormLayout(index_opt_group)
        
        # 向量维度
        self.vector_dimensions_spin = QSpinBox()
        self.vector_dimensions_spin.setRange(128, 2048)
        self.vector_dimensions_spin.setValue(512)
        index_opt_layout.addRow("向量维度:", self.vector_dimensions_spin)
        
        # 索引类型
        self.index_type_combo = QComboBox()
        self.index_type_combo.addItems(["HNSW", "Plain", "IVF"])
        index_opt_layout.addRow("索引类型:", self.index_type_combo)
        
        # 索引参数
        self.index_params_text = QTextEdit()
        self.index_params_text.setMaximumHeight(100)
        self.index_params_text.setPlaceholderText("索引参数配置（JSON格式）")
        index_opt_layout.addRow("索引参数:", self.index_params_text)
        
        layout.addWidget(index_opt_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "索引配置")
    
    def create_models_config_tab(self):
        """创建模型配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 模型选择设置
        model_selection_group = QGroupBox("模型选择设置")
        model_selection_layout = QFormLayout(model_selection_group)
        
        # CLIP模型
        self.clip_model_combo = QComboBox()
        self.clip_model_combo.addItems([
            "openai/clip-vit-base-patch32",
            "openai/clip-vit-large-patch14",
            "laion/CLIP-ViT-B-32-laion2B-s34B-b79K"
        ])
        model_selection_layout.addRow("CLIP模型:", self.clip_model_combo)
        
        # CLAP模型
        self.clap_model_combo = QComboBox()
        self.clap_model_combo.addItems([
            "laion/clap-htsat-fused",
            "laion/clap-htsat-tiny",
            "laion/clap-wav2vec2"
        ])
        model_selection_layout.addRow("CLAP模型:", self.clap_model_combo)
        
        # Whisper模型
        self.whisper_model_combo = QComboBox()
        self.whisper_model_combo.addItems([
            "openai/whisper-base",
            "openai/whisper-small",
            "openai/whisper-medium",
            "openai/whisper-large"
        ])
        model_selection_layout.addRow("Whisper模型:", self.whisper_model_combo)
        
        layout.addWidget(model_selection_group)
        
        # 模型加载设置
        model_loading_group = QGroupBox("模型加载设置")
        model_loading_layout = QFormLayout(model_loading_group)
        
        # 设备选择
        self.device_combo = QComboBox()
        self.device_combo.addItems(["auto", "cpu", "cuda"])
        model_loading_layout.addRow("计算设备:", self.device_combo)
        
        # 显存优化
        self.memory_optimization_checkbox = QCheckBox("启用显存优化")
        self.memory_optimization_checkbox.setChecked(True)
        model_loading_layout.addRow("", self.memory_optimization_checkbox)
        
        # 批处理优化
        self.batch_optimization_checkbox = QCheckBox("启用批处理优化")
        self.batch_optimization_checkbox.setChecked(True)
        model_loading_layout.addRow("", self.batch_optimization_checkbox)
        
        layout.addWidget(model_loading_group)
        
        # 模型路径设置
        model_path_group = QGroupBox("模型路径设置")
        model_path_layout = QFormLayout(model_path_group)
        
        # 本地模型路径
        self.local_model_path_input = QLineEdit()
        self.local_model_path_input.setReadOnly(True)
        browse_model_path = QPushButton("浏览...")
        browse_model_path.clicked.connect(self.browse_model_path)
        model_path_layout.addRow("本地模型路径:", self.create_hbox_with_button(self.local_model_path_input, browse_model_path))
        
        layout.addWidget(model_path_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "模型配置")
    
    def create_logging_config_tab(self):
        """创建日志配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 日志设置
        log_group = QGroupBox("日志设置")
        log_layout = QFormLayout(log_group)
        
        # 日志级别
        self.log_level_global_combo = QComboBox()
        self.log_level_global_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_layout.addRow("全局日志级别:", self.log_level_global_combo)
        
        # 日志文件大小限制
        self.log_file_size_spin = QSpinBox()
        self.log_file_size_spin.setRange(1, 100)
        self.log_file_size_spin.setValue(10)
        self.log_file_size_spin.setSuffix(" MB")
        log_layout.addRow("日志文件大小限制:", self.log_file_size_spin)
        
        # 日志文件数量
        self.log_file_count_spin = QSpinBox()
        self.log_file_count_spin.setRange(1, 10)
        self.log_file_count_spin.setValue(5)
        self.log_file_count_spin.setSuffix(" 个")
        log_layout.addRow("日志文件数量:", self.log_file_count_spin)
        
        layout.addWidget(log_group)
        
        # 组件日志设置
        component_log_group = QGroupBox("组件日志设置")
        component_log_layout = QVBoxLayout(component_log_group)
        
        # 日志配置表格
        self.log_config_table = QTableWidget()
        self.log_config_table.setColumnCount(2)
        self.log_config_table.setHorizontalHeaderLabels(["组件", "日志级别"])
        self.log_config_table.setRowCount(5)
        
        components = [
            "msearch.core", "msearch.business", "msearch.processors",
            "msearch.storage", "msearch.api"
        ]
        
        for i, component in enumerate(components):
            self.log_config_table.setItem(i, 0, self.create_table_item(component))
            combo = QComboBox()
            combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
            self.log_config_table.setCellWidget(i, 1, combo)
        
        component_log_layout.addWidget(self.log_config_table)
        
        layout.addWidget(component_log_group)
        
        # 日志输出设置
        output_group = QGroupBox("日志输出设置")
        output_layout = QVBoxLayout(output_group)
        
        # 输出格式
        self.log_format_combo = QComboBox()
        self.log_format_combo.addItems([
            "标准格式", "详细格式（包含文件名和行号）", "简化格式"
        ])
        output_layout.addWidget(QLabel("日志格式:"))
        output_layout.addWidget(self.log_format_combo)
        
        # 输出位置
        self.log_output_group = QButtonGroup()
        console_radio = QRadioButton("控制台")
        file_radio = QRadioButton("文件")
        both_radio = QRadioButton("控制台和文件")
        both_radio.setChecked(True)
        
        self.log_output_group.addButton(console_radio, 0)
        self.log_output_group.addButton(file_radio, 1)
        self.log_output_group.addButton(both_radio, 2)
        
        output_radio_layout = QHBoxLayout()
        output_radio_layout.addWidget(console_radio)
        output_radio_layout.addWidget(file_radio)
        output_radio_layout.addWidget(both_radio)
        output_layout.addLayout(output_radio_layout)
        
        layout.addWidget(output_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "日志配置")
    
    def create_advanced_config_tab(self):
        """创建高级配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 数据库设置
        db_group = QGroupBox("数据库设置")
        db_layout = QFormLayout(db_group)
        
        # SQLite设置
        self.sqlite_cache_size_spin = QSpinBox()
        self.sqlite_cache_size_spin.setRange(1, 1000)
        self.sqlite_cache_size_spin.setValue(100)
        self.sqlite_cache_size_spin.setSuffix(" MB")
        db_layout.addRow("SQLite缓存大小:", self.sqlite_cache_size_spin)
        
        self.sqlite_journal_mode_combo = QComboBox()
        self.sqlite_journal_mode_combo.addItems(["WAL", "DELETE", "TRUNCATE", "PERSIST", "MEMORY", "OFF"])
        db_layout.addRow("SQLite日志模式:", self.sqlite_journal_mode_combo)
        
        # Qdrant设置
        self.qdrant_url_input = QLineEdit()
        self.qdrant_url_input.setPlaceholderText("http://localhost:6333")
        db_layout.addRow("Qdrant URL:", self.qdrant_url_input)
        
        layout.addWidget(db_group)
        
        # 网络设置
        network_group = QGroupBox("网络设置")
        network_layout = QFormLayout(network_group)
        
        # API端口
        self.api_port_spin = QSpinBox()
        self.api_port_spin.setRange(1024, 65535)
        self.api_port_spin.setValue(8000)
        network_layout.addRow("API端口:", self.api_port_spin)
        
        # 超时设置
        self.request_timeout_spin = QSpinBox()
        self.request_timeout_spin.setRange(1, 300)
        self.request_timeout_spin.setValue(30)
        self.request_timeout_spin.setSuffix(" 秒")
        network_layout.addRow("请求超时:", self.request_timeout_spin)
        
        layout.addWidget(network_group)
        
        # 性能设置
        performance_group = QGroupBox("性能设置")
        performance_layout = QFormLayout(performance_group)
        
        # 并发连接数
        self.max_concurrent_connections_spin = QSpinBox()
        self.max_concurrent_connections_spin.setRange(1, 100)
        self.max_concurrent_connections_spin.setValue(10)
        performance_layout.addRow("最大并发连接数:", self.max_concurrent_connections_spin)
        
        # 连接池大小
        self.connection_pool_size_spin = QSpinBox()
        self.connection_pool_size_spin.setRange(1, 50)
        self.connection_pool_size_spin.setValue(20)
        performance_layout.addRow("连接池大小:", self.connection_pool_size_spin)
        
        layout.addWidget(performance_group)
        
        # 自定义配置
        custom_group = QGroupBox("自定义配置")
        custom_layout = QVBoxLayout(custom_group)
        
        self.custom_config_text = QTextEdit()
        self.custom_config_text.setPlaceholderText("在此添加自定义配置项（YAML格式）")
        custom_layout.addWidget(self.custom_config_text)
        
        layout.addWidget(custom_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "高级配置")
    
    def connect_signals(self):
        """连接信号"""
        # 相似度阈值滑块
        self.similarity_threshold_slider.valueChanged.connect(
            lambda v: self.similarity_threshold_label.setText(f"{v/100:.2f}")
        )
        
        # 人脸检测阈值滑块
        self.face_detection_threshold_slider.valueChanged.connect(
            lambda v: self.face_detection_threshold_label.setText(f"{v/100:.2f}")
        )
        
        # 人脸匹配阈值滑块
        self.face_match_threshold_slider.valueChanged.connect(
            lambda v: self.face_match_threshold_label.setText(f"{v/100:.2f}")
        )
    
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
            
            QComboBox {
                padding: 8px;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                min-width: 150px;
            }
            
            QSpinBox {
                padding: 8px;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                min-width: 100px;
            }
            
            QSlider {
                min-height: 20px;
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
            
            QTableWidget {
                gridline-color: #e4e7ed;
                selection-background-color: #f5f7fa;
            }
            
            QHeaderView::section {
                background-color: #f5f7fa;
                padding: 8px;
                border: 1px solid #e4e7ed;
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
            
            QDialogButtonBox {
                spacing: 10px;
            }
        """)
    
    def load_config_values(self):
        """加载配置值"""
        try:
            config = self.current_config
            
            # 通用配置
            self.data_dir_input.setText(config.get("general.data_dir", ""))
            self.log_level_combo.setCurrentText(config.get("logging.level", "INFO"))
            self.watch_dirs_text.setPlainText("\n".join(config.get("file_monitoring.watch_directories", [])))
            self.monitor_interval_spin.setValue(config.get("file_monitoring.check_interval", 60))
            self.max_concurrent_tasks_spin.setValue(config.get("processing.max_concurrent_tasks", 4))
            self.batch_size_spin.setValue(config.get("processing.batch_size", 16))
            
            # 搜索配置
            self.search_limit_spin.setValue(config.get("search.default_limit", 20))
            self.similarity_threshold_slider.setValue(int(config.get("search.similarity_threshold", 0.7) * 100))
            self.layered_search_checkbox.setChecked(config.get("search.enable_layered_search", True))
            self.face_detection_threshold_slider.setValue(int(config.get("face_detection.threshold", 0.8) * 100))
            self.face_match_threshold_slider.setValue(int(config.get("face_matching.threshold", 0.85) * 100))
            self.timestamp_precision_spin.setValue(config.get("temporal.precision", 2))
            
            # 索引配置
            self.video_resolution_combo.setCurrentText(config.get("processing.video_resolution_limit", "保持原样"))
            self.audio_sample_rate_combo.setCurrentText(config.get("processing.audio_sample_rate", "保持原样"))
            self.min_segment_duration_spin.setValue(config.get("processing.min_segment_duration", 5))
            self.quality_filter_checkbox.setChecked(config.get("processing.quality_filter", True))
            self.vector_dimensions_spin.setValue(config.get("indexing.vector_dimensions", 512))
            self.index_type_combo.setCurrentText(config.get("indexing.index_type", "HNSW"))
            self.index_params_text.setPlainText(json.dumps(config.get("indexing.index_params", {}), indent=2))
            
            # 模型配置
            self.clip_model_combo.setCurrentText(config.get("models.clip_model", "openai/clip-vit-base-patch32"))
            self.clap_model_combo.setCurrentText(config.get("models.clap_model", "laion/clap-htsat-fused"))
            self.whisper_model_combo.setCurrentText(config.get("models.whisper_model", "openai/whisper-base"))
            self.device_combo.setCurrentText(config.get("models.device", "auto"))
            self.memory_optimization_checkbox.setChecked(config.get("models.memory_optimization", True))
            self.batch_optimization_checkbox.setChecked(config.get("models.batch_optimization", True))
            self.local_model_path_input.setText(config.get("models.local_model_path", ""))
            
            # 日志配置
            self.log_level_global_combo.setCurrentText(config.get("logging.level", "INFO"))
            self.log_file_size_spin.setValue(config.get("logging.file_size_limit", 10))
            self.log_file_count_spin.setValue(config.get("logging.file_count", 5))
            self.log_format_combo.setCurrentText(config.get("logging.format", "标准格式"))
            
            # 数据库和网络配置
            self.sqlite_cache_size_spin.setValue(config.get("database.sqlite.cache_size", 100))
            self.sqlite_journal_mode_combo.setCurrentText(config.get("database.sqlite.journal_mode", "WAL"))
            self.qdrant_url_input.setText(config.get("database.qdrant.url", "http://localhost:6333"))
            self.api_port_spin.setValue(config.get("api.port", 8000))
            self.request_timeout_spin.setValue(config.get("api.timeout", 30))
            self.max_concurrent_connections_spin.setValue(config.get("api.max_connections", 10))
            self.connection_pool_size_spin.setValue(config.get("api.connection_pool_size", 20))
            
        except Exception as e:
            logger.error(f"加载配置值失败: {e}")
            QMessageBox.critical(self, "错误", f"加载配置值失败: {e}")
    
    def save_config_values(self):
        """保存配置值"""
        try:
            config = self.current_config
            
            # 通用配置
            config["general"]["data_dir"] = self.data_dir_input.text()
            config["logging"]["level"] = self.log_level_combo.currentText()
            watch_dirs = self.watch_dirs_text.toPlainText().strip()
            if watch_dirs:
                config["file_monitoring"]["watch_directories"] = [
                    line.strip() for line in watch_dirs.split("\n") if line.strip()
                ]
            else:
                config["file_monitoring"]["watch_directories"] = []
            config["file_monitoring"]["check_interval"] = self.monitor_interval_spin.value()
            config["processing"]["max_concurrent_tasks"] = self.max_concurrent_tasks_spin.value()
            config["processing"]["batch_size"] = self.batch_size_spin.value()
            
            # 搜索配置
            config["search"]["default_limit"] = self.search_limit_spin.value()
            config["search"]["similarity_threshold"] = self.similarity_threshold_slider.value() / 100.0
            config["search"]["enable_layered_search"] = self.layered_search_checkbox.isChecked()
            config["face_detection"]["threshold"] = self.face_detection_threshold_slider.value() / 100.0
            config["face_matching"]["threshold"] = self.face_match_threshold_slider.value() / 100.0
            config["temporal"]["precision"] = self.timestamp_precision_spin.value()
            
            # 索引配置
            config["processing"]["video_resolution_limit"] = self.video_resolution_combo.currentText()
            config["processing"]["audio_sample_rate"] = self.audio_sample_rate_combo.currentText()
            config["processing"]["min_segment_duration"] = self.min_segment_duration_spin.value()
            config["processing"]["quality_filter"] = self.quality_filter_checkbox.isChecked()
            config["indexing"]["vector_dimensions"] = self.vector_dimensions_spin.value()
            config["indexing"]["index_type"] = self.index_type_combo.currentText()
            
            try:
                index_params = json.loads(self.index_params_text.toPlainText())
                config["indexing"]["index_params"] = index_params
            except json.JSONDecodeError:
                QMessageBox.warning(self, "警告", "索引参数格式错误，将使用默认值")
                config["indexing"]["index_params"] = {}
            
            # 模型配置
            config["models"]["clip_model"] = self.clip_model_combo.currentText()
            config["models"]["clap_model"] = self.clap_model_combo.currentText()
            config["models"]["whisper_model"] = self.whisper_model_combo.currentText()
            config["models"]["device"] = self.device_combo.currentText()
            config["models"]["memory_optimization"] = self.memory_optimization_checkbox.isChecked()
            config["models"]["batch_optimization"] = self.batch_optimization_checkbox.isChecked()
            config["models"]["local_model_path"] = self.local_model_path_input.text()
            
            # 日志配置
            config["logging"]["level"] = self.log_level_global_combo.currentText()
            config["logging"]["file_size_limit"] = self.log_file_size_spin.value()
            config["logging"]["file_count"] = self.log_file_count_spin.value()
            
            # 数据库和网络配置
            config["database"]["sqlite"]["cache_size"] = self.sqlite_cache_size_spin.value()
            config["database"]["sqlite"]["journal_mode"] = self.sqlite_journal_mode_combo.currentText()
            config["database"]["qdrant"]["url"] = self.qdrant_url_input.text()
            config["api"]["port"] = self.api_port_spin.value()
            config["api"]["timeout"] = self.request_timeout_spin.value()
            config["api"]["max_connections"] = self.max_concurrent_connections_spin.value()
            config["api"]["connection_pool_size"] = self.connection_pool_size_spin.value()
            
            return True
            
        except Exception as e:
            logger.error(f"保存配置值失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置值失败: {e}")
            return False
    
    def browse_data_dir(self):
        """浏览数据目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择数据目录", self.data_dir_input.text()
        )
        if dir_path:
            self.data_dir_input.setText(dir_path)
    
    def browse_model_path(self):
        """浏览模型路径"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择本地模型路径", self.local_model_path_input.text()
        )
        if dir_path:
            self.local_model_path_input.setText(dir_path)
    
    def create_hbox_with_button(self, widget, button):
        """创建包含控件和按钮的水平布局"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)
        layout.addWidget(button)
        container = QWidget()
        container.setLayout(layout)
        return container
    
    def create_table_item(self, text: str):
        """创建表格项"""
        from PySide6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item
    
    def reset_config(self):
        """重置配置"""
        reply = QMessageBox.question(
            self, "确认重置", 
            "确定要重置所有配置为默认值吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.current_config = self.original_config.copy()
            self.load_config_values()
            QMessageBox.information(self, "重置完成", "配置已重置为默认值")
    
    def apply_config(self):
        """应用配置"""
        if not self.save_config_values():
            return
        
        try:
            # 保存配置到文件
            config_manager = get_config_manager()
            # 直接更新内部配置
            config_manager.config = self.current_config
            
            # 如果有API客户端，尝试更新服务器配置
            if self.api_client:
                try:
                    result = self.api_client.update_system_config(self.current_config)
                    if result:
                        QMessageBox.information(self, "成功", "配置已应用并保存到服务器")
                    else:
                        QMessageBox.warning(self, "警告", "配置已保存到本地，但未成功更新到服务器")
                except Exception as e:
                    logger.error(f"更新服务器配置失败: {e}")
                    QMessageBox.warning(self, "警告", f"配置已保存到本地，但更新服务器配置失败: {e}")
            else:
                QMessageBox.information(self, "成功", "配置已保存到本地")
            
            # 更新当前配置
            self.original_config = self.current_config.copy()
            
        except Exception as e:
            logger.error(f"应用配置失败: {e}")
            QMessageBox.critical(self, "错误", f"应用配置失败: {e}")
    
    def accept(self):
        """确认配置"""
        if not self.save_config_values():
            return
        
        try:
            # 保存配置到文件
            save_config(self.current_config)
            
            # 如果有API客户端，尝试更新服务器配置
            if self.api_client:
                try:
                    result = self.api_client.update_system_config(self.current_config)
                    if not result:
                        logger.warning("配置已保存到本地，但未成功更新到服务器")
                except Exception as e:
                    logger.error(f"更新服务器配置失败: {e}")
            
            # 更新当前配置
            self.original_config = self.current_config.copy()
            
            super().accept()
            
        except Exception as e:
            logger.error(f"确认配置失败: {e}")
            QMessageBox.critical(self, "错误", f"确认配置失败: {e}")
    
    def reject(self):
        """取消配置"""
        # 恢复原始配置
        self.current_config = self.original_config.copy()
        self.load_config_values()
        
        super().reject()


class ConfigManagerWidget(QWidget):
    """配置管理组件"""
    
    # 信号定义
    status_message_changed = Signal(str)
    
    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        
        # API客户端
        self.api_client = api_client
        
        # 初始化UI
        self.init_ui()
        
        # 连接信号
        self.connect_signals()
        
        # 应用样式
        self.apply_styles()
        
        logger.info("配置管理组件初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 配置概览
        overview_group = QGroupBox("配置概览")
        overview_layout = QFormLayout(overview_group)
        
        self.current_config_path_label = QLabel("未知")
        overview_layout.addRow("当前配置文件:", self.current_config_path_label)
        
        self.data_dir_label = QLabel("未知")
        overview_layout.addRow("数据目录:", self.data_dir_label)
        
        self.model_dir_label = QLabel("未知")
        overview_layout.addRow("模型目录:", self.model_dir_label)
        
        main_layout.addWidget(overview_group)
        
        # 配置操作按钮
        button_layout = QHBoxLayout()
        
        self.edit_config_button = QPushButton("编辑配置")
        self.edit_config_button.clicked.connect(self.edit_config)
        button_layout.addWidget(self.edit_config_button)
        
        self.load_config_button = QPushButton("加载配置")
        self.load_config_button.clicked.connect(self.load_config)
        button_layout.addWidget(self.load_config_button)
        
        self.save_config_button = QPushButton("保存配置")
        self.save_config_button.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_config_button)
        
        self.reset_config_button = QPushButton("重置配置")
        self.reset_config_button.clicked.connect(self.reset_config)
        button_layout.addWidget(self.reset_config_button)
        
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # 配置文件管理
        file_group = QGroupBox("配置文件管理")
        file_layout = QVBoxLayout(file_group)
        
        file_operation_layout = QHBoxLayout()
        
        self.backup_config_button = QPushButton("备份配置")
        self.backup_config_button.clicked.connect(self.backup_config)
        file_operation_layout.addWidget(self.backup_config_button)
        
        self.restore_config_button = QPushButton("恢复配置")
        self.restore_config_button.clicked.connect(self.restore_config)
        file_operation_layout.addWidget(self.restore_config_button)
        
        self.import_config_button = QPushButton("导入配置")
        self.import_config_button.clicked.connect(self.import_config)
        file_operation_layout.addWidget(self.import_config_button)
        
        self.export_config_button = QPushButton("导出配置")
        self.export_config_button.clicked.connect(self.export_config)
        file_operation_layout.addWidget(self.export_config_button)
        
        file_layout.addLayout(file_operation_layout)
        
        main_layout.addWidget(file_group)
        
        # 加载当前配置信息
        self.refresh_config_info()
    
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
        """)
    
    def refresh_config_info(self):
        """刷新配置信息"""
        try:
            # 加载当前配置
            config = load_config()
            
            # 更新显示信息
            config_path = Path("config/config.yml")
            self.current_config_path_label.setText(str(config_path.absolute()))
            
            self.data_dir_label.setText(config.get("general.data_dir", "未知"))
            self.model_dir_label.setText(config.get("models.model_dir", "未知"))
            
        except Exception as e:
            logger.error(f"刷新配置信息失败: {e}")
            self.status_message_changed.emit(f"刷新配置信息失败: {e}")
    
    def edit_config(self):
        """编辑配置"""
        dialog = ConfigDialog(self, self.api_client)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_config_info()
            self.status_message_changed.emit("配置已更新")
    
    def load_config(self):
        """加载配置"""
        try:
            # 重新加载配置
            config = load_config()
            self.refresh_config_info()
            self.status_message_changed.emit("配置已重新加载")
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            self.status_message_changed.emit(f"加载配置失败: {e}")
    
    def save_config(self):
        """保存配置"""
        try:
            # 获取当前配置
            config = load_config()
            config_manager = get_config_manager()
            # 直接更新内部配置
            config_manager.config = config
            self.status_message_changed.emit("配置已保存")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            self.status_message_changed.emit(f"保存配置失败: {e}")
    
    def reset_config(self):
        """重置配置"""
        reply = QMessageBox.question(
            self, "确认重置", 
            "确定要重置为默认配置吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 重置为默认配置
                default_config = load_config()  # 这会加载默认配置
                config_manager = get_config_manager()
                # 直接更新内部配置
                config_manager.config = default_config
                self.refresh_config_info()
                self.status_message_changed.emit("配置已重置为默认值")
            except Exception as e:
                logger.error(f"重置配置失败: {e}")
                self.status_message_changed.emit(f"重置配置失败: {e}")
    
    def backup_config(self):
        """备份配置"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = Path(f"config_backup_{timestamp}.yml")
            
            # 复制当前配置
            current_config = load_config()
            with open(backup_file, 'w', encoding='utf-8') as f:
                yaml.dump(current_config, f, default_flow_style=False, allow_unicode=True)
            
            self.status_message_changed.emit(f"配置已备份到: {backup_file}")
        except Exception as e:
            logger.error(f"备份配置失败: {e}")
            self.status_message_changed.emit(f"备份配置失败: {e}")
    
    def restore_config(self):
        """恢复配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择备份配置文件", "", "YAML文件 (*.yml *.yaml)"
        )
        
        if file_path:
            try:
                # 读取备份配置
                with open(file_path, 'r', encoding='utf-8') as f:
                    backup_config = yaml.safe_load(f)
                
                # 保存配置
                config_manager = get_config_manager()
                # 直接更新内部配置
                config_manager.config = backup_config
                self.refresh_config_info()
                self.status_message_changed.emit(f"配置已从 {file_path} 恢复")
            except Exception as e:
                logger.error(f"恢复配置失败: {e}")
                self.status_message_changed.emit(f"恢复配置失败: {e}")
    
    def import_config(self):
        """导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择配置文件", "", "YAML文件 (*.yml *.yaml);;JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                # 根据文件扩展名读取配置
                if file_path.lower().endswith('.json'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        imported_config = json.load(f)
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        imported_config = yaml.safe_load(f)
                
                # 保存配置
                config_manager = get_config_manager()
                # 直接更新内部配置
                config_manager.config = imported_config
                self.refresh_config_info()
                self.status_message_changed.emit(f"配置已从 {file_path} 导入")
            except Exception as e:
                logger.error(f"导入配置失败: {e}")
                self.status_message_changed.emit(f"导入配置失败: {e}")
    
    def export_config(self):
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存配置文件", "msearch_config.yml", "YAML文件 (*.yml *.yaml)"
        )
        
        if file_path:
            try:
                # 获取当前配置
                current_config = load_config()
                
                # 保存配置
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(current_config, f, default_flow_style=False, allow_unicode=True)
                
                self.status_message_changed.emit(f"配置已导出到: {file_path}")
            except Exception as e:
                logger.error(f"导出配置失败: {e}")
                self.status_message_changed.emit(f"导出配置失败: {e}")