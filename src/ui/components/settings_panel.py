"""
设置面板组件
提供系统设置功能
"""

from typing import Dict, Any, Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QGroupBox,
    QTabWidget,
    QFileDialog,
    QComboBox,
    QFormLayout,
    QDialogButtonBox,
)
from PySide6.QtCore import Signal, Qt


class SettingsPanel(QWidget):
    """设置面板组件"""

    # 信号定义
    settings_changed = Signal(dict)
    settings_reset = Signal()

    def __init__(self, config_manager, parent=None):
        """初始化设置面板"""
        super().__init__(parent)

        self.config_manager = config_manager
        self.settings: Dict[str, Any] = {}

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 设置面板容器
        container = QWidget()
        container.setStyleSheet(
            """
            QWidget {
                background-color: #FFFFFF;
                border-radius: 8px;
            }
        """
        )
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(20)

        # 标题
        title_label = QLabel("⚙️ 系统设置")
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #1D2129;
            }
        """
        )
        container_layout.addWidget(title_label)

        # 创建选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            """
            QTabWidget::pane {
                border: 1px solid #E5E6EB;
                border-radius: 6px;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #F2F3F5;
                color: #4E5969;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #165DFF;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background-color: #E5E6EB;
            }
        """
        )

        # 通用设置选项卡
        general_tab = self.create_general_tab()
        self.tab_widget.addTab(general_tab, "🔧 通用")

        # 搜索设置选项卡
        search_tab = self.create_search_tab()
        self.tab_widget.addTab(search_tab, "🔍 搜索")

        # 索引设置选项卡
        indexing_tab = self.create_indexing_tab()
        self.tab_widget.addTab(indexing_tab, "📁 索引")

        # 模型设置选项卡
        model_tab = self.create_model_tab()
        self.tab_widget.addTab(model_tab, "🤖 模型")

        container_layout.addWidget(self.tab_widget)

        # 按钮区域
        button_container = QWidget()
        button_container.setStyleSheet(
            """
            QWidget {
                background-color: #F2F3F5;
                border-radius: 6px;
                padding: 10px;
            }
        """
        )
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(10, 5, 10, 5)
        button_layout.setSpacing(15)

        reset_button = QPushButton("🔄 重置默认")
        reset_button.clicked.connect(self.on_reset_clicked)
        reset_button.setStyleSheet(
            """
            QPushButton {
                background-color: #F2F3F5;
                color: #4E5969;
                border: 1px solid #E5E6EB;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #E5E6EB;
                border-color: #C9CDD4;
            }
            QPushButton:pressed {
                background-color: #C9CDD4;
            }
        """
        )
        button_layout.addWidget(reset_button)

        button_layout.addStretch()

        apply_button = QPushButton("✓ 应用")
        apply_button.clicked.connect(self.on_apply_clicked)
        apply_button.setStyleSheet(
            """
            QPushButton {
                background-color: #165DFF;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0E42D2;
            }
            QPushButton:pressed {
                background-color: #0927B9;
            }
        """
        )
        button_layout.addWidget(apply_button)

        save_button = QPushButton("💾 保存")
        save_button.clicked.connect(self.on_save_clicked)
        save_button.setStyleSheet(
            """
            QPushButton {
                background-color: #00B42A;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #009A28;
            }
            QPushButton:pressed {
                background-color: #007A24;
            }
        """
        )
        button_layout.addWidget(save_button)

        container_layout.addWidget(button_container)

        layout.addWidget(container)

    def create_general_tab(self) -> QWidget:
        """创建通用设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 系统设置组
        system_group = QGroupBox("系统设置")
        system_layout = QFormLayout(system_group)

        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        system_layout.addRow("日志级别:", self.log_level_combo)

        # 最大工作线程数
        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(1, 16)
        self.max_workers_spin.setValue(4)
        system_layout.addRow("最大工作线程:", self.max_workers_spin)

        # 健康检查间隔
        self.health_check_interval_spin = QSpinBox()
        self.health_check_interval_spin.setRange(10, 300)
        self.health_check_interval_spin.setValue(30)
        self.health_check_interval_spin.setSuffix(" 秒")
        system_layout.addRow("健康检查间隔:", self.health_check_interval_spin)

        layout.addWidget(system_group)

        # 数据目录设置组
        data_group = QGroupBox("数据目录")
        data_layout = QFormLayout(data_group)

        # 数据目录
        self.data_dir_edit = QLineEdit()
        self.data_dir_edit.setPlaceholderText("选择数据目录")
        data_dir_browse_button = QPushButton("浏览...")
        data_dir_browse_button.clicked.connect(self.on_browse_data_dir)
        data_dir_layout = QHBoxLayout()
        data_dir_layout.addWidget(self.data_dir_edit)
        data_dir_layout.addWidget(data_dir_browse_button)
        data_layout.addRow("数据目录:", data_dir_layout)

        layout.addWidget(data_group)

        layout.addStretch()
        return widget

    def create_search_tab(self) -> QWidget:
        """创建搜索设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 搜索结果设置组
        results_group = QGroupBox("搜索结果")
        results_layout = QFormLayout(results_group)

        # 默认结果数量
        self.default_result_count_spin = QSpinBox()
        self.default_result_count_spin.setRange(5, 100)
        self.default_result_count_spin.setValue(20)
        results_layout.addRow("默认结果数量:", self.default_result_count_spin)

        # 最大结果数量
        self.max_result_count_spin = QSpinBox()
        self.max_result_count_spin.setRange(10, 500)
        self.max_result_count_spin.setValue(100)
        results_layout.addRow("最大结果数量:", self.max_result_count_spin)

        # 显示缩略图
        self.show_thumbnail_checkbox = QCheckBox("显示缩略图")
        self.show_thumbnail_checkbox.setChecked(True)
        results_layout.addRow("", self.show_thumbnail_checkbox)

        layout.addWidget(results_group)

        # 搜索性能设置组
        performance_group = QGroupBox("搜索性能")
        performance_layout = QFormLayout(performance_group)

        # 超时时间
        self.search_timeout_spin = QSpinBox()
        self.search_timeout_spin.setRange(1, 60)
        self.search_timeout_spin.setValue(10)
        self.search_timeout_spin.setSuffix(" 秒")
        performance_layout.addRow("搜索超时:", self.search_timeout_spin)

        layout.addWidget(performance_group)

        layout.addStretch()
        return widget

    def create_indexing_tab(self) -> QWidget:
        """创建索引设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 文件监控设置组
        monitoring_group = QGroupBox("文件监控")
        monitoring_layout = QFormLayout(monitoring_group)

        # 启用文件监控
        self.enable_monitoring_checkbox = QCheckBox("启用文件监控")
        self.enable_monitoring_checkbox.setChecked(True)
        monitoring_layout.addRow("", self.enable_monitoring_checkbox)

        # 检查间隔
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setRange(1, 60)
        self.check_interval_spin.setValue(5)
        self.check_interval_spin.setSuffix(" 秒")
        monitoring_layout.addRow("检查间隔:", self.check_interval_spin)

        # 防抖延迟
        self.debounce_delay_spin = QSpinBox()
        self.debounce_delay_spin.setRange(100, 5000)
        self.debounce_delay_spin.setValue(500)
        self.debounce_delay_spin.setSuffix(" 毫秒")
        monitoring_layout.addRow("防抖延迟:", self.debounce_delay_spin)

        layout.addWidget(monitoring_group)

        # 任务管理设置组
        task_group = QGroupBox("任务管理")
        task_layout = QFormLayout(task_group)

        # 最大并发任务数
        self.max_concurrent_tasks_spin = QSpinBox()
        self.max_concurrent_tasks_spin.setRange(1, 16)
        self.max_concurrent_tasks_spin.setValue(4)
        task_layout.addRow("最大并发任务:", self.max_concurrent_tasks_spin)

        # 最大重试次数
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(0, 10)
        self.max_retries_spin.setValue(3)
        task_layout.addRow("最大重试次数:", self.max_retries_spin)

        layout.addWidget(task_group)

        layout.addStretch()
        return widget

    def create_model_tab(self) -> QWidget:
        """创建模型设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        image_video_group = QGroupBox("图像/视频模型")
        image_video_layout = QFormLayout(image_video_group)

        self.image_model_combo = QComboBox()
        self.image_model_combo.addItems(
            [
                "chinese_clip_large",
                "chinese_clip_base",
                "colqwen3_turbo",
                "tomoro_colqwen3",
            ]
        )
        image_video_layout.addRow("模型:", self.image_model_combo)

        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 32)
        self.batch_size_spin.setValue(4)
        image_video_layout.addRow("批处理大小:", self.batch_size_spin)

        self.device_combo = QComboBox()
        self.device_combo.addItems(["auto", "cpu", "cuda"])
        image_video_layout.addRow("设备:", self.device_combo)

        layout.addWidget(image_video_group)

        audio_group = QGroupBox("音频模型")
        audio_layout = QFormLayout(audio_group)

        self.audio_model_combo = QComboBox()
        self.audio_model_combo.addItems(["audio_model"])
        audio_layout.addRow("模型:", self.audio_model_combo)

        self.audio_batch_size_spin = QSpinBox()
        self.audio_batch_size_spin.setRange(1, 32)
        self.audio_batch_size_spin.setValue(4)
        audio_layout.addRow("批处理大小:", self.audio_batch_size_spin)

        layout.addWidget(audio_group)

        # 模型缓存设置组
        cache_group = QGroupBox("模型缓存")
        cache_layout = QFormLayout(cache_group)

        # 模型缓存目录
        self.model_cache_dir_edit = QLineEdit()
        self.model_cache_dir_edit.setPlaceholderText("选择模型缓存目录")
        model_cache_dir_browse_button = QPushButton("浏览...")
        model_cache_dir_browse_button.clicked.connect(self.on_browse_model_cache_dir)
        model_cache_dir_layout = QHBoxLayout()
        model_cache_dir_layout.addWidget(self.model_cache_dir_edit)
        model_cache_dir_layout.addWidget(model_cache_dir_browse_button)
        cache_layout.addRow("缓存目录:", model_cache_dir_layout)

        # 启用模型预热
        self.enable_model_warmup_checkbox = QCheckBox("启用模型预热")
        self.enable_model_warmup_checkbox.setChecked(True)
        cache_layout.addRow("", self.enable_model_warmup_checkbox)

        layout.addWidget(cache_group)

        layout.addStretch()
        return widget

    def load_settings(self):
        """加载设置"""
        if not self.config_manager:
            return

        # 加载系统设置
        system_config = self.config_manager.get("system", {})
        self.log_level_combo.setCurrentText(system_config.get("log_level", "INFO"))
        self.max_workers_spin.setValue(system_config.get("max_workers", 4))
        self.health_check_interval_spin.setValue(
            system_config.get("health_check_interval", 30)
        )

        # 加载搜索设置
        # 这里应该加载实际的搜索设置
        self.default_result_count_spin.setValue(20)
        self.max_result_count_spin.setValue(100)
        self.show_thumbnail_checkbox.setChecked(True)

        # 加载索引设置
        task_manager_config = self.config_manager.get("task_manager", {})
        self.max_concurrent_tasks_spin.setValue(
            task_manager_config.get("max_concurrent_tasks", 4)
        )
        self.max_retries_spin.setValue(task_manager_config.get("max_retries", 3))

        monitoring_config = self.config_manager.get("monitoring", {})
        self.check_interval_spin.setValue(monitoring_config.get("check_interval", 5))
        self.debounce_delay_spin.setValue(monitoring_config.get("debounce_delay", 500))

        # 加载模型设置
        models_config = self.config_manager.get("models", {})
        self.enable_model_warmup_checkbox.setChecked(
            models_config.get("enable_model_warmup", True)
        )

    def save_settings(self) -> Dict[str, Any]:
        """保存设置"""
        settings = {
            "system": {
                "log_level": self.log_level_combo.currentText(),
                "max_workers": self.max_workers_spin.value(),
                "health_check_interval": self.health_check_interval_spin.value(),
            },
            "task_manager": {
                "max_concurrent_tasks": self.max_concurrent_tasks_spin.value(),
                "max_retries": self.max_retries_spin.value(),
            },
            "monitoring": {
                "check_interval": self.check_interval_spin.value(),
                "debounce_delay": self.debounce_delay_spin.value(),
            },
            "models": {
                "enable_model_warmup": self.enable_model_warmup_checkbox.isChecked()
            },
        }

        return settings

    def on_browse_data_dir(self):
        """浏览数据目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择数据目录")
        if directory:
            self.data_dir_edit.setText(directory)

    def on_browse_model_cache_dir(self):
        """浏览模型缓存目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择模型缓存目录")
        if directory:
            self.model_cache_dir_edit.setText(directory)

    def on_apply_clicked(self):
        """应用按钮点击事件"""
        settings = self.save_settings()
        self.settings_changed.emit(settings)

    def on_save_clicked(self):
        """保存按钮点击事件"""
        settings = self.save_settings()
        self.settings_changed.emit(settings)
        # 这里应该保存到配置文件
        # self.config_manager.update(settings)

    def on_reset_clicked(self):
        """重置按钮点击事件"""
        self.settings_reset.emit()
        self.load_settings()
