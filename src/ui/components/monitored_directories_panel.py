"""
监控目录面板组件
显示监控目录列表、状态和文件统计
"""

from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QFrame,
    QMenu,
    QMessageBox,
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QColor


class DirectoryListItem(QListWidgetItem):
    """目录列表项"""

    def __init__(self, directory_data: Dict[str, Any], parent=None):
        """初始化目录列表项"""
        super().__init__(parent)
        self.directory_data = directory_data

        # 设置状态图标
        status = directory_data.get("status", "unknown")
        status_icons = {
            "monitoring": "🟢",
            "paused": "🟡",
            "error": "🔴",
            "initializing": "🔵",
            "unknown": "⚪",
        }
        icon = status_icons.get(status, "⚪")

        # 设置文本
        path = directory_data.get("path", "")
        file_count = directory_data.get("file_count", 0)
        image_count = directory_data.get("image_count", 0)
        video_count = directory_data.get("video_count", 0)
        audio_count = directory_data.get("audio_count", 0)

        text = f"{icon} {path}\n   文件: {file_count} | 图像: {image_count} | 视频: {video_count} | 音频: {audio_count}"
        self.setText(text)

        # 设置样式
        self.setData(Qt.UserRole, directory_data)


class MonitoredDirectoriesPanel(QWidget):
    """监控目录面板"""

    directory_added = Signal(str)
    directory_removed = Signal(str)
    directory_paused = Signal(str)
    directory_resumed = Signal(str)
    directory_error = Signal(str, str)

    def __init__(self, parent=None):
        """初始化监控目录面板"""
        super().__init__(parent)
        self.directories: List[Dict[str, Any]] = []
        self.init_ui()

        # 模拟数据（暂时使用）
        self._load_mock_data()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("📁 监控目录")
        title_label.setStyleSheet(
            """
            QLabel {
                color: #4E5969;
                font-size: 14px;
                font-weight: 600;
            }
        """
        )
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # 目录列表
        self.directory_list = QListWidget()
        self.directory_list.setAlternatingRowColors(True)
        self.directory_list.setSelectionMode(QListWidget.NoSelection)
        self.directory_list.setStyleSheet(
            """
            QListWidget {
                background-color: white;
                border: 1px solid #E5E6EB;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px 0;
            }
            QListWidget::item:hover {
                background-color: #F2F3F5;
            }
        """
        )
        layout.addWidget(self.directory_list)

        # 控制按钮
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        self.add_btn = QPushButton("+ 添加")
        self.add_btn.setFixedHeight(32)
        self.add_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #00B42A;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
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
        self.add_btn.clicked.connect(self._add_directory)
        controls_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("- 移除")
        self.remove_btn.setFixedHeight(32)
        self.remove_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #F53F3F;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #D9363E;
            }
            QPushButton:pressed {
                background-color: #BD282E;
            }
        """
        )
        self.remove_btn.clicked.connect(self._remove_directory)
        controls_layout.addWidget(self.remove_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # 文件统计
        self.stats_label = QLabel("总文件: 0 | 图像: 0 | 视频: 0 | 音频: 0")
        self.stats_label.setStyleSheet(
            """
            QLabel {
                color: #86909C;
                font-size: 11px;
                padding: 5px 0;
            }
        """
        )
        layout.addWidget(self.stats_label)

        # 添加目录右键菜单
        self.directory_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.directory_list.customContextMenuRequested.connect(self._show_context_menu)

    def _load_mock_data(self):
        """加载模拟数据"""
        self.directories = [
            {
                "path": "/data/project/msearch/testdata",
                "status": "monitoring",
                "file_count": 125,
                "image_count": 80,
                "video_count": 30,
                "audio_count": 15,
            },
            {
                "path": "/home/user/MediaLibrary",
                "status": "monitoring",
                "file_count": 342,
                "image_count": 200,
                "video_count": 100,
                "audio_count": 42,
            },
            {
                "path": "/home/user/TempFiles",
                "status": "error",
                "file_count": 0,
                "image_count": 0,
                "video_count": 0,
                "audio_count": 0,
                "error_message": "目录不可访问",
            },
        ]
        self._refresh_directories()
        self._refresh_stats()

    def _add_directory(self):
        """添加监控目录"""
        from PySide6.QtWidgets import QFileDialog

        new_dir = QFileDialog.getExistingDirectory(self, "选择要监控的目录")
        if not new_dir:
            return

        # 检查是否已存在
        for d in self.directories:
            if d["path"] == new_dir:
                QMessageBox.warning(self, "警告", f"目录 {new_dir} 已存在")
                return

        # 添加新目录
        new_directory = {
            "path": new_dir,
            "status": "initializing",
            "file_count": 0,
            "image_count": 0,
            "video_count": 0,
            "audio_count": 0,
        }

        self.directories.append(new_directory)
        self._refresh_directories()
        self._refresh_stats()

        # 发射信号
        self.directory_added.emit(new_dir)

    def _remove_directory(self):
        """移除监控目录"""
        # 获取当前选中的项
        current_row = self.directory_list.currentRow()
        if current_row < 0 or current_row >= len(self.directories):
            QMessageBox.warning(self, "警告", "请先选择要移除的目录")
            return

        removed_dir = self.directories.pop(current_row)
        self._refresh_directories()
        self._refresh_stats()

        # 发射信号
        self.directory_removed.emit(removed_dir["path"])

    def _refresh_directories(self):
        """刷新目录列表"""
        self.directory_list.clear()

        for dir_data in self.directories:
            item = DirectoryListItem(dir_data)
            self.directory_list.addItem(item)

    def _refresh_stats(self):
        """刷新文件统计"""
        total = sum(d["file_count"] for d in self.directories)
        total_image = sum(d["image_count"] for d in self.directories)
        total_video = sum(d["video_count"] for d in self.directories)
        total_audio = sum(d["audio_count"] for d in self.directories)

        new_count = sum(1 for d in self.directories if d["status"] == "initializing")
        processing_count = sum(
            1 for d in self.directories if d["status"] == "monitoring"
        )
        pending_count = len(self.directories) - processing_count - new_count

        self.stats_label.setText(
            f"总计: {total} | 图像: {total_image} | 视频: {total_video} | 音频: {total_audio}\n"
            f"新文件: {new_count} | 处理中: {processing_count} | 待处理: {pending_count}"
        )

    def _show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.directory_list.itemAt(pos)
        if not item:
            return

        directory_data = item.data(Qt.UserRole)

        menu = QMenu(self)

        if directory_data["status"] == "monitoring":
            pause_action = menu.addAction("⏸️ 暂停监控")
            pause_action.triggered.connect(
                lambda: self._pause_directory(directory_data["path"])
            )
        elif directory_data["status"] == "paused":
            resume_action = menu.addAction("▶️ 恢复监控")
            resume_action.triggered.connect(
                lambda: self._resume_directory(directory_data["path"])
            )

        remove_action = menu.addAction("🗑️ 移除目录")
        remove_action.triggered.connect(
            lambda: self._remove_directory_by_path(directory_data["path"])
        )

        menu.exec(self.directory_list.mapToGlobal(pos))

    def _pause_directory(self, path: str):
        """暂停目录监控"""
        for d in self.directories:
            if d["path"] == path and d["status"] == "monitoring":
                d["status"] = "paused"
                self._refresh_directories()
                self.directory_paused.emit(path)
                break

    def _resume_directory(self, path: str):
        """恢复目录监控"""
        for d in self.directories:
            if d["path"] == path and d["status"] == "paused":
                d["status"] = "monitoring"
                self._refresh_directories()
                self.directory_resumed.emit(path)
                break

    def _remove_directory_by_path(self, path: str):
        """根据路径移除目录"""
        self.directories = [d for d in self.directories if d["path"] != path]
        self._refresh_directories()
        self._refresh_stats()
        self.directory_removed.emit(path)

    def get_directories(self) -> List[Dict[str, Any]]:
        """获取所有监控目录"""
        return self.directories

    def get_stats(self) -> Dict[str, int]:
        """获取文件统计"""
        return {
            "total": sum(d["file_count"] for d in self.directories),
            "image": sum(d["image_count"] for d in self.directories),
            "video": sum(d["video_count"] for d in self.directories),
            "audio": sum(d["audio_count"] for d in self.directories),
        }
