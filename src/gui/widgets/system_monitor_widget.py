#!/usr/bin/env python3
"""
msearch PySide6系统监控组件
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import psutil
import time

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget, QFrame,
    QScrollArea, QProgressBar, QComboBox, QSpinBox, QCheckBox, QSlider,
    QGroupBox, QSplitter, QToolButton, QButtonGroup, QRadioButton,
    QSizePolicy, QSpacerItem, QFileDialog, QMessageBox, QTabWidget,
    QListWidget, QListWidgetItem, QTextBrowser, QStackedWidget
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QObject, QUrl, QSize, QPropertyAnimation,
    QDateTime
)
from PySide6.QtGui import (
    QIcon, QPixmap, QFont, QAction, QPalette, QColor, QDesktopServices
)

from src.core.config import load_config
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class SystemMonitorWidget(QWidget):
    """系统监控组件"""
    
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
        
        # 启动监控
        self.start_monitoring()
        
        logger.info("系统监控组件初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建各个选项卡
        self.create_system_overview_tab()
        self.create_resource_usage_tab()
        self.create_process_monitor_tab()
        self.create_storage_monitor_tab()
        self.create_network_monitor_tab()
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.refresh_all)
        control_layout.addWidget(self.refresh_button)
        
        self.auto_refresh_checkbox = QCheckBox("自动刷新")
        self.auto_refresh_checkbox.setChecked(True)
        control_layout.addWidget(self.auto_refresh_checkbox)
        
        self.refresh_interval_combo = QComboBox()
        self.refresh_interval_combo.addItems(["1秒", "5秒", "10秒", "30秒", "1分钟"])
        self.refresh_interval_combo.setCurrentText("5秒")
        control_layout.addWidget(QLabel("刷新间隔:"))
        control_layout.addWidget(self.refresh_interval_combo)
        
        control_layout.addStretch()
        
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignRight)
        control_layout.addWidget(self.status_label)
        
        main_layout.addLayout(control_layout)
    
    def create_system_overview_tab(self):
        """创建系统概览选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 系统信息
        info_group = QGroupBox("系统信息")
        info_layout = QFormLayout(info_group)
        
        self.system_name_label = QLabel()
        info_layout.addRow("系统名称:", self.system_name_label)
        
        self.system_version_label = QLabel()
        info_layout.addRow("系统版本:", self.system_version_label)
        
        self.system_architecture_label = QLabel()
        info_layout.addRow("系统架构:", self.system_architecture_label)
        
        self.python_version_label = QLabel()
        info_layout.addRow("Python版本:", self.python_version_label)
        
        self.app_version_label = QLabel("0.1.0")
        info_layout.addRow("应用版本:", self.app_version_label)
        
        layout.addWidget(info_group)
        
        # 硬件信息
        hardware_group = QGroupBox("硬件信息")
        hardware_layout = QFormLayout(hardware_group)
        
        self.cpu_info_label = QLabel()
        hardware_layout.addRow("CPU:", self.cpu_info_label)
        
        self.memory_total_label = QLabel()
        hardware_layout.addRow("内存总量:", self.memory_total_label)
        
        self.gpu_info_label = QLabel("未检测到GPU")
        hardware_layout.addRow("GPU:", self.gpu_info_label)
        
        layout.addWidget(hardware_group)
        
        # 应用状态
        app_group = QGroupBox("应用状态")
        app_layout = QFormLayout(app_group)
        
        self.api_status_label = QLabel("未连接")
        app_layout.addRow("API服务:", self.api_status_label)
        
        self.database_status_label = QLabel("未知")
        app_layout.addRow("数据库:", self.database_status_label)
        
        self.index_status_label = QLabel("未知")
        app_layout.addRow("索引状态:", self.index_status_label)
        
        self.file_monitor_status_label = QLabel("未知")
        app_layout.addRow("文件监控:", self.file_monitor_status_label)
        
        layout.addWidget(app_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "系统概览")
    
    def create_resource_usage_tab(self):
        """创建资源使用选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # CPU使用情况
        cpu_group = QGroupBox("CPU使用情况")
        cpu_layout = QVBoxLayout(cpu_group)
        
        self.cpu_usage_label = QLabel("0%")
        self.cpu_usage_label.setAlignment(Qt.AlignCenter)
        self.cpu_usage_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #409EFF;")
        cpu_layout.addWidget(self.cpu_usage_label)
        
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        cpu_layout.addWidget(self.cpu_progress)
        
        # CPU核心使用情况
        self.cpu_cores_layout = QGridLayout()
        cpu_layout.addLayout(self.cpu_cores_layout)
        
        layout.addWidget(cpu_group)
        
        # 内存使用情况
        memory_group = QGroupBox("内存使用情况")
        memory_layout = QVBoxLayout(memory_group)
        
        self.memory_usage_label = QLabel("0%")
        self.memory_usage_label.setAlignment(Qt.AlignCenter)
        self.memory_usage_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #67C23A;")
        memory_layout.addWidget(self.memory_usage_label)
        
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        memory_layout.addWidget(self.memory_progress)
        
        # 内存详细信息
        self.memory_details_label = QLabel()
        memory_layout.addWidget(self.memory_details_label)
        
        layout.addWidget(memory_group)
        
        # 磁盘使用情况
        disk_group = QGroupBox("磁盘使用情况")
        disk_layout = QVBoxLayout(disk_group)
        
        self.disk_usage_label = QLabel("0%")
        self.disk_usage_label.setAlignment(Qt.AlignCenter)
        self.disk_usage_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #E6A23C;")
        disk_layout.addWidget(self.disk_usage_label)
        
        self.disk_progress = QProgressBar()
        self.disk_progress.setRange(0, 100)
        disk_layout.addWidget(self.disk_progress)
        
        # 磁盘详细信息
        self.disk_details_label = QLabel()
        disk_layout.addWidget(self.disk_details_label)
        
        layout.addWidget(disk_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "资源使用")
    
    def create_process_monitor_tab(self):
        """创建进程监控选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 进程列表
        process_group = QGroupBox("进程列表")
        process_layout = QVBoxLayout(process_group)
        
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(5)
        self.process_table.setHorizontalHeaderLabels([
            "进程ID", "名称", "CPU%", "内存%", "状态"
        ])
        process_layout.addWidget(self.process_table)
        
        layout.addWidget(process_group)
        
        # 进程操作
        process_action_layout = QHBoxLayout()
        
        self.kill_process_button = QPushButton("终止进程")
        self.kill_process_button.clicked.connect(self.kill_selected_process)
        self.kill_process_button.setEnabled(False)
        process_action_layout.addWidget(self.kill_process_button)
        
        process_action_layout.addStretch()
        
        self.refresh_processes_button = QPushButton("刷新进程")
        self.refresh_processes_button.clicked.connect(self.refresh_processes)
        process_action_layout.addWidget(self.refresh_processes_button)
        
        layout.addLayout(process_action_layout)
        
        self.tab_widget.addTab(tab, "进程监控")
    
    def create_storage_monitor_tab(self):
        """创建存储监控选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 存储使用情况
        storage_group = QGroupBox("存储使用情况")
        storage_layout = QVBoxLayout(storage_group)
        
        self.storage_table = QTableWidget()
        self.storage_table.setColumnCount(4)
        self.storage_table.setHorizontalHeaderLabels([
            "挂载点", "总大小", "已使用", "使用率"
        ])
        storage_layout.addWidget(self.storage_table)
        
        layout.addWidget(storage_group)
        
        # 数据库信息
        database_group = QGroupBox("数据库信息")
        database_layout = QFormLayout(database_group)
        
        self.database_size_label = QLabel("未知")
        database_layout.addRow("数据库大小:", self.database_size_label)
        
        self.index_count_label = QLabel("未知")
        database_layout.addRow("索引数量:", self.index_count_label)
        
        self.document_count_label = QLabel("未知")
        database_layout.addRow("文档数量:", self.document_count_label)
        
        layout.addWidget(database_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "存储监控")
    
    def create_network_monitor_tab(self):
        """创建网络监控选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 网络接口信息
        network_group = QGroupBox("网络接口")
        network_layout = QVBoxLayout(network_group)
        
        self.network_table = QTableWidget()
        self.network_table.setColumnCount(4)
        self.network_table.setHorizontalHeaderLabels([
            "接口", "发送", "接收", "状态"
        ])
        network_layout.addWidget(self.network_table)
        
        layout.addWidget(network_group)
        
        # API连接信息
        api_group = QGroupBox("API连接")
        api_layout = QFormLayout(api_group)
        
        self.api_response_time_label = QLabel("未知")
        api_layout.addRow("响应时间:", self.api_response_time_label)
        
        self.api_requests_label = QLabel("0")
        api_layout.addRow("请求数:", self.api_requests_label)
        
        self.api_errors_label = QLabel("0")
        api_layout.addRow("错误数:", self.api_errors_label)
        
        layout.addWidget(api_group)
        
        # 日志信息
        log_group = QGroupBox("系统日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextBrowser()
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "网络监控")
    
    def init_state(self):
        """初始化状态"""
        self.monitoring_timer = None
        self.last_net_io = {}
        self.system_info_loaded = False
    
    def connect_signals(self):
        """连接信号"""
        # 进程表格选择变化
        self.process_table.itemSelectionChanged.connect(self.on_process_selection_changed)
        
        # 刷新间隔变化
        self.refresh_interval_combo.currentTextChanged.connect(self.on_refresh_interval_changed)
    
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
            
            QProgressBar {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                text-align: center;
            }
            
            QProgressBar::chunk {
                background-color: #409EFF;
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
        """)
    
    def start_monitoring(self):
        """启动监控"""
        # 初始化系统信息
        self.load_system_info()
        
        # 设置监控定时器
        self.monitoring_timer = QTimer()
        self.monitoring_timer.timeout.connect(self.update_monitoring_data)
        self.on_refresh_interval_changed(self.refresh_interval_combo.currentText())
        
        self.status_message_changed.emit("系统监控已启动")
    
    def on_refresh_interval_changed(self, text):
        """刷新间隔变化事件"""
        if not self.monitoring_timer:
            return
        
        intervals = {
            "1秒": 1000,
            "5秒": 5000,
            "10秒": 10000,
            "30秒": 30000,
            "1分钟": 60000
        }
        
        interval = intervals.get(text, 5000)
        self.monitoring_timer.setInterval(interval)
        
        if self.auto_refresh_checkbox.isChecked():
            self.monitoring_timer.start()
        
        self.status_message_changed.emit(f"刷新间隔设置为 {text}")
    
    def load_system_info(self):
        """加载系统信息"""
        if self.system_info_loaded:
            return
        
        try:
            # 系统信息
            self.system_name_label.setText(f"{os.name}")
            self.system_version_label.setText(f"{sys.platform}")
            self.system_architecture_label.setText(f"{os.uname().machine if hasattr(os, 'uname') else 'Unknown'}")
            self.python_version_label.setText(f"{sys.version}")
            
            # CPU信息
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            cpu_info = f"{cpu_count} 核"
            if cpu_freq:
                cpu_info += f" @ {cpu_freq.max:.2f}MHz"
            self.cpu_info_label.setText(cpu_info)
            
            # 内存信息
            memory = psutil.virtual_memory()
            self.memory_total_label.setText(f"{memory.total / (1024**3):.2f} GB")
            
            self.system_info_loaded = True
            self.status_message_changed.emit("系统信息加载完成")
            
        except Exception as e:
            logger.error(f"加载系统信息失败: {e}")
            self.status_message_changed.emit(f"加载系统信息失败: {e}")
    
    def update_monitoring_data(self):
        """更新监控数据"""
        if not self.auto_refresh_checkbox.isChecked():
            return
        
        try:
            # 更新资源使用情况
            self.update_resource_usage()
            
            # 更新进程信息
            if self.tab_widget.currentIndex() == 2:  # 进程监控选项卡
                self.refresh_processes()
            
            # 更新存储信息
            if self.tab_widget.currentIndex() == 3:  # 存储监控选项卡
                self.refresh_storage()
            
            # 更新网络信息
            if self.tab_widget.currentIndex() == 4:  # 网络监控选项卡
                self.refresh_network()
            
            # 更新应用状态
            self.update_app_status()
            
        except Exception as e:
            logger.error(f"更新监控数据失败: {e}")
    
    def update_resource_usage(self):
        """更新资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.5)
            self.cpu_usage_label.setText(f"{cpu_percent:.1f}%")
            self.cpu_progress.setValue(int(cpu_percent))
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.memory_usage_label.setText(f"{memory_percent:.1f}%")
            self.memory_progress.setValue(int(memory_percent))
            self.memory_details_label.setText(
                f"已使用: {memory.used / (1024**3):.2f} GB / "
                f"可用: {memory.available / (1024**3):.2f} GB"
            )
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.disk_usage_label.setText(f"{disk_percent:.1f}%")
            self.disk_progress.setValue(int(disk_percent))
            self.disk_details_label.setText(
                f"总大小: {disk.total / (1024**3):.2f} GB / "
                f"已使用: {disk.used / (1024**3):.2f} GB"
            )
            
        except Exception as e:
            logger.error(f"更新资源使用情况失败: {e}")
    
    def refresh_processes(self):
        """刷新进程信息"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 按CPU使用率排序
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            # 更新表格
            self.process_table.setRowCount(min(len(processes), 50))  # 最多显示50个进程
            
            for row, proc in enumerate(processes[:50]):
                self.process_table.setItem(row, 0, self.create_table_item(str(proc['pid'])))
                self.process_table.setItem(row, 1, self.create_table_item(proc['name'][:30]))
                self.process_table.setItem(row, 2, self.create_table_item(f"{proc['cpu_percent']:.1f}"))
                self.process_table.setItem(row, 3, self.create_table_item(f"{proc['memory_percent']:.1f}"))
                self.process_table.setItem(row, 4, self.create_table_item(proc['status']))
            
            self.process_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"刷新进程信息失败: {e}")
    
    def refresh_storage(self):
        """刷新存储信息"""
        try:
            # 磁盘分区信息
            partitions = psutil.disk_partitions()
            self.storage_table.setRowCount(len(partitions))
            
            for row, partition in enumerate(partitions):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    total_gb = usage.total / (1024**3)
                    used_gb = usage.used / (1024**3)
                    percent = (usage.used / usage.total) * 100
                    
                    self.storage_table.setItem(row, 0, self.create_table_item(partition.mountpoint))
                    self.storage_table.setItem(row, 1, self.create_table_item(f"{total_gb:.2f} GB"))
                    self.storage_table.setItem(row, 2, self.create_table_item(f"{used_gb:.2f} GB"))
                    self.storage_table.setItem(row, 3, self.create_table_item(f"{percent:.1f}%"))
                except PermissionError:
                    # 某些分区可能没有访问权限
                    self.storage_table.setItem(row, 0, self.create_table_item(partition.mountpoint))
                    self.storage_table.setItem(row, 1, self.create_table_item("无权限"))
                    self.storage_table.setItem(row, 2, self.create_table_item("无权限"))
                    self.storage_table.setItem(row, 3, self.create_table_item("无权限"))
            
            self.storage_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"刷新存储信息失败: {e}")
    
    def refresh_network(self):
        """刷新网络信息"""
        try:
            # 网络接口信息
            net_io = psutil.net_io_counters(pernic=True)
            net_if_addrs = psutil.net_if_addrs()
            
            interfaces = list(net_io.keys())
            self.network_table.setRowCount(len(interfaces))
            
            for row, interface in enumerate(interfaces):
                io = net_io[interface]
                
                # 计算速度
                if interface in self.last_net_io:
                    last_io = self.last_net_io[interface]
                    time_delta = 1  # 假设1秒间隔
                    
                    bytes_sent_per_sec = (io.bytes_sent - last_io.bytes_sent) / time_delta
                    bytes_recv_per_sec = (io.bytes_recv - last_io.bytes_recv) / time_delta
                    
                    sent_str = f"{bytes_sent_per_sec / 1024:.2f} KB/s"
                    recv_str = f"{bytes_recv_per_sec / 1024:.2f} KB/s"
                else:
                    sent_str = "计算中"
                    recv_str = "计算中"
                
                self.network_table.setItem(row, 0, self.create_table_item(interface))
                self.network_table.setItem(row, 1, self.create_table_item(sent_str))
                self.network_table.setItem(row, 2, self.create_table_item(recv_str))
                
                # 接口状态
                if interface in net_if_addrs:
                    status = "已连接" if any(addr.family == 2 for addr in net_if_addrs[interface]) else "未连接"
                else:
                    status = "未知"
                self.network_table.setItem(row, 3, self.create_table_item(status))
            
            self.last_net_io = net_io
            self.network_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"刷新网络信息失败: {e}")
    
    def update_app_status(self):
        """更新应用状态"""
        try:
            # 检查API连接状态
            if self.api_client and self.api_client.is_connected():
                self.api_status_label.setText("已连接")
                self.api_status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.api_status_label.setText("未连接")
                self.api_status_label.setStyleSheet("color: red; font-weight: bold;")
            
            # TODO: 检查数据库状态
            # TODO: 检查索引状态
            # TODO: 检查文件监控状态
            
        except Exception as e:
            logger.error(f"更新应用状态失败: {e}")
    
    def create_table_item(self, text: str):
        """创建表格项"""
        from PySide6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item
    
    def on_process_selection_changed(self):
        """进程选择变化事件"""
        selected_items = self.process_table.selectedItems()
        self.kill_process_button.setEnabled(len(selected_items) > 0)
    
    def kill_selected_process(self):
        """终止选中进程"""
        selected_items = self.process_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        pid_item = self.process_table.item(row, 0)
        name_item = self.process_table.item(row, 1)
        
        if not pid_item or not name_item:
            return
        
        pid = int(pid_item.text())
        name = name_item.text()
        
        reply = QMessageBox.question(
            self, "确认终止", 
            f"确定要终止进程 '{name}' (PID: {pid}) 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                process = psutil.Process(pid)
                process.terminate()
                self.status_message_changed.emit(f"已发送终止信号到进程: {name}")
                # 延迟刷新进程列表
                QTimer.singleShot(1000, self.refresh_processes)
            except psutil.NoSuchProcess:
                QMessageBox.warning(self, "警告", "进程已不存在")
                self.refresh_processes()
            except psutil.AccessDenied:
                QMessageBox.critical(self, "错误", "没有权限终止该进程")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"终止进程失败: {e}")
    
    def refresh_all(self):
        """刷新所有监控信息"""
        try:
            self.load_system_info()
            self.update_resource_usage()
            self.refresh_processes()
            self.refresh_storage()
            self.refresh_network()
            self.update_app_status()
            
            self.status_message_changed.emit("所有监控信息已刷新")
        except Exception as e:
            logger.error(f"刷新所有监控信息失败: {e}")
            self.status_message_changed.emit(f"刷新监控信息失败: {e}")
    
    def stop_monitoring(self):
        """停止监控"""
        if self.monitoring_timer and self.monitoring_timer.isActive():
            self.monitoring_timer.stop()
            self.status_message_changed.emit("系统监控已停止")