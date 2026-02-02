"""
任务队列面板组件
显示任务列表、优先级控制和进度信息
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
    QComboBox,
    QFrame,
    QProgressBar,
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QColor


class TaskListItem(QListWidgetItem):
    """任务列表项"""

    def __init__(self, task_data: Dict[str, Any], parent=None):
        """初始化任务列表项"""
        super().__init__(parent)
        self.task_data = task_data

        # 获取任务信息
        task_id = task_data.get("id", "")[:8]
        task_type = task_data.get("task_type", "unknown")
        status = task_data.get("status", "pending")
        priority = task_data.get("priority", 5)
        progress = task_data.get("progress", 0.0)

        # 状态图标
        status_icons = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "⚠️",
            "paused": "⏸️",
        }
        icon = status_icons.get(status, "⏳")

        # 优先级颜色
        priority_colors = {"high": "#F53F3F", "medium": "#FF7D00", "low": "#00B42A"}
        if priority <= 3:
            priority_text = "🔴 高"
            priority_color = priority_colors["high"]
        elif priority <= 7:
            priority_text = "🟡 中"
            priority_color = priority_colors["medium"]
        else:
            priority_text = "🟢 低"
            priority_color = priority_colors["low"]

        # 获取依赖信息
        depends_on = task_data.get("depends_on", [])
        dep_text = f" | 依赖: {len(depends_on)}" if depends_on else ""

        # 设置文本
        text = (
            f"{icon} {task_type} (优先级: {priority_text})\n"
            f"   ID: {task_id} | 进度: {progress * 100:.0f}%{dep_text}"
        )
        self.setText(text)
        self.setForeground(QColor(priority_color))

        # 设置数据
        self.setData(Qt.UserRole, task_data)


class TaskQueuePanel(QWidget):
    """任务队列面板"""

    tasks_paused = Signal()
    tasks_resumed = Signal()
    tasks_cancelled = Signal()
    priority_changed = Signal(dict)
    task_selected = Signal(dict)

    def __init__(self, api_client=None, parent=None):
        """初始化任务队列面板"""
        super().__init__(parent)
        self.tasks: List[Dict[str, Any]] = []
        self.api_client = api_client
        self.init_ui()

        # 模拟数据（暂时使用）
        self._load_mock_data()

        # 定时器更新进度
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_progress)
        self.update_timer.start(1000)  # 每秒更新一次

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("📋 任务队列")
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

        # 任务过滤
        filter_layout = QHBoxLayout()
        filter_label = QLabel("过滤:")
        filter_label.setStyleSheet("color: #86909C; font-size: 11px;")
        filter_layout.addWidget(filter_label)

        self.task_filter = QComboBox()
        self.task_filter.addItems(["全部", "待处理", "运行中", "已完成", "失败"])
        self.task_filter.setFixedHeight(28)
        self.task_filter.setStyleSheet(
            """
            QComboBox {
                background-color: white;
                border: 1px solid #E5E6EB;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
            }
            QComboBox:hover {
                border-color: #165DFF;
            }
        """
        )
        self.task_filter.currentTextChanged.connect(self._filter_tasks)
        filter_layout.addWidget(self.task_filter)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # 任务优先级控制
        priority_group = QFrame()
        priority_group.setStyleSheet(
            """
            QFrame {
                background-color: #F2F3F5;
                border-radius: 6px;
            }
        """
        )
        priority_layout = QVBoxLayout(priority_group)
        priority_layout.setContentsMargins(10, 10, 10, 10)
        priority_layout.setSpacing(5)

        priority_title = QLabel("文件类型优先级:")
        priority_title.setStyleSheet(
            "color: #4E5969; font-size: 12px; font-weight: 600;"
        )
        priority_layout.addWidget(priority_title)

        priority_settings_layout = QHBoxLayout()
        priority_settings_layout.setSpacing(10)

        # 视频优先级
        video_layout = QVBoxLayout()
        video_label = QLabel("视频:")
        video_label.setStyleSheet("color: #86909C; font-size: 11px;")
        video_layout.addWidget(video_label)
        self.video_priority = QComboBox()
        self.video_priority.addItems(["高", "中", "低"])
        self.video_priority.setCurrentText("中")
        self.video_priority.setFixedHeight(26)
        self.video_priority.setStyleSheet(
            """
            QComboBox {
                background-color: white;
                border: 1px solid #E5E6EB;
                border-radius: 4px;
                padding: 1px 6px;
                font-size: 11px;
            }
        """
        )
        video_layout.addWidget(self.video_priority)
        priority_settings_layout.addLayout(video_layout)

        # 音频优先级
        audio_layout = QVBoxLayout()
        audio_label = QLabel("音频:")
        audio_label.setStyleSheet("color: #86909C; font-size: 11px;")
        audio_layout.addWidget(audio_label)
        self.audio_priority = QComboBox()
        self.audio_priority.addItems(["高", "中", "低"])
        self.audio_priority.setCurrentText("中")
        self.audio_priority.setFixedHeight(26)
        self.audio_priority.setStyleSheet(self.video_priority.styleSheet())
        audio_layout.addWidget(self.audio_priority)
        priority_settings_layout.addLayout(audio_layout)

        # 图像优先级
        image_layout = QVBoxLayout()
        image_label = QLabel("图像:")
        image_label.setStyleSheet("color: #86909C; font-size: 11px;")
        image_layout.addWidget(image_label)
        self.image_priority = QComboBox()
        self.image_priority.addItems(["高", "中", "低"])
        self.image_priority.setCurrentText("中")
        self.image_priority.setFixedHeight(26)
        self.image_priority.setStyleSheet(self.video_priority.styleSheet())
        image_layout.addWidget(self.image_priority)
        priority_settings_layout.addLayout(image_layout)

        priority_layout.addLayout(priority_settings_layout)

        # 应用按钮
        apply_btn = QPushButton("应用设置")
        apply_btn.setFixedHeight(28)
        apply_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #165DFF;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
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
        apply_btn.clicked.connect(self._apply_priority_settings)
        priority_layout.addWidget(apply_btn)

        layout.addWidget(priority_group)

        # 任务列表
        self.task_list = QListWidget()
        self.task_list.setAlternatingRowColors(True)
        self.task_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.task_list.setStyleSheet(
            """
            QListWidget {
                background-color: white;
                border: 1px solid #E5E6EB;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 4px;
                margin: 2px 0;
                font-size: 11px;
            }
            QListWidget::item:hover {
                background-color: #F2F3F5;
            }
            QListWidget::item:selected {
                background-color: #165DFF;
                color: white;
            }
        """
        )
        layout.addWidget(self.task_list)

        # 批量操作按钮
        batch_layout = QHBoxLayout()
        batch_layout.setSpacing(10)

        self.raise_priority_btn = QPushButton("⬆️ 提升优先级")
        self.raise_priority_btn.setFixedHeight(28)
        self.raise_priority_btn.setStyleSheet(
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
        self.raise_priority_btn.clicked.connect(self._raise_priority)
        batch_layout.addWidget(self.raise_priority_btn)

        self.lower_priority_btn = QPushButton("⬇️ 降低优先级")
        self.lower_priority_btn.setFixedHeight(28)
        self.lower_priority_btn.setStyleSheet(
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
            QPushButton:pressed {
                background-color: #CC5500;
            }
        """
        )
        self.lower_priority_btn.clicked.connect(self._lower_priority)
        batch_layout.addWidget(self.lower_priority_btn)

        self.batch_cancel_btn = QPushButton("🗑️ 批量取消")
        self.batch_cancel_btn.setFixedHeight(28)
        self.batch_cancel_btn.setStyleSheet(
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
            QPushButton:pressed {
                background-color: #BD282E;
            }
        """
        )
        self.batch_cancel_btn.clicked.connect(self._batch_cancel)
        batch_layout.addWidget(self.batch_cancel_btn)

        batch_layout.addStretch()
        layout.addLayout(batch_layout)

        # 进度信息
        self.progress_label = QLabel("处理中: 0/0 | 预计剩余: 计算中...")
        self.progress_label.setStyleSheet(
            """
            QLabel {
                color: #86909C;
                font-size: 11px;
                padding: 5px 0;
            }
        """
        )
        layout.addWidget(self.progress_label)

        # 线程池状态信息
        self.threadpool_label = QLabel("线程池: 活跃 0/0 | 空闲 0/0 | 负载: 0%")
        self.threadpool_label.setStyleSheet(
            """
            QLabel {
                color: #86909C;
                font-size: 11px;
                padding: 5px 0;
            }
        """
        )
        layout.addWidget(self.threadpool_label)

        # 任务依赖信息
        self.dependency_label = QLabel("任务依赖: 未选择")
        self.dependency_label.setStyleSheet(
            """
            QLabel {
                color: #86909C;
                font-size: 11px;
                padding: 5px 0;
            }
        """
        )
        layout.addWidget(self.dependency_label)

        # 控制按钮
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        self.pause_btn = QPushButton("⏸️ 暂停")
        self.pause_btn.setFixedHeight(32)
        self.pause_btn.setStyleSheet(
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
            QPushButton:pressed {
                background-color: #CC5500;
            }
        """
        )
        self.pause_btn.clicked.connect(self._pause_tasks)
        controls_layout.addWidget(self.pause_btn)

        self.resume_btn = QPushButton("▶️ 恢复")
        self.resume_btn.setFixedHeight(32)
        self.resume_btn.setStyleSheet(
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
        self.resume_btn.clicked.connect(self._resume_tasks)
        controls_layout.addWidget(self.resume_btn)

        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.setFixedHeight(32)
        self.cancel_btn.setStyleSheet(
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
            QPushButton:pressed {
                background-color: #BD282E;
            }
        """
        )
        self.cancel_btn.clicked.connect(self._cancel_tasks)
        controls_layout.addWidget(self.cancel_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

    def _load_mock_data(self):
        """加载模拟数据"""
        import uuid

        task_types = [
            "video_embed",
            "audio_embed",
            "image_embed",
            "thumbnail_gen",
            "preview_gen",
        ]
        statuses = ["pending", "running", "completed", "failed"]

        self.tasks = []
        for i in range(10):
            task = {
                "id": str(uuid.uuid4()),
                "task_type": task_types[i % len(task_types)],
                "status": statuses[i % len(statuses)],
                "priority": 5,
                "progress": i * 0.1,
                "created_at": f"2026-01-30 10:{i:02d}:00",
            }
            self.tasks.append(task)

        self._refresh_tasks()
        self._update_progress()

    def _refresh_tasks(self):
        """刷新任务列表"""
        self.task_list.clear()

        filter_type = self.task_filter.currentText()

        for task in self.tasks:
            # 应用过滤
            if filter_type != "全部":
                status_map = {
                    "待处理": "pending",
                    "运行中": "running",
                    "已完成": "completed",
                    "失败": "failed",
                }
                if task.get("status") != status_map.get(filter_type):
                    continue

            item = TaskListItem(task)
            self.task_list.addItem(item)

        # 连接任务选择信号
        self.task_list.itemSelectionChanged.connect(self._on_task_selection_changed)

    def _filter_tasks(self, filter_type: str):
        """过滤任务"""
        self._refresh_tasks()

    def _update_progress(self):
        """更新进度信息"""
        total = len(self.tasks)
        running = sum(1 for t in self.tasks if t["status"] == "running")
        completed = sum(1 for t in self.tasks if t["status"] == "completed")

        # 更新运行中任务的进度
        for task in self.tasks:
            if task["status"] == "running":
                task["progress"] = min(1.0, task["progress"] + 0.1)
                if task["progress"] >= 1.0:
                    task["status"] = "completed"
                    task["progress"] = 1.0

        self._refresh_tasks()

        # 更新进度标签
        if running > 0:
            remaining = total - completed
            self.progress_label.setText(
                f"处理中: {running}/{total} | 预计剩余: {remaining * 2}秒"
            )
        else:
            self.progress_label.setText(f"处理中: {running}/{total} | 预计剩余: 无")

        # 更新线程池状态（模拟数据）
        max_threads = 8
        active_threads = running
        idle_threads = max_threads - active_threads
        load_percentage = (
            int((active_threads / max_threads) * 100) if max_threads > 0 else 0
        )

        self.threadpool_label.setText(
            f"线程池: 活跃 {active_threads}/{max_threads} | 空闲 {idle_threads}/{max_threads} | 负载: {load_percentage}%"
        )

        # 尝试从API获取真实的线程池状态
        if self.api_client:
            try:
                thread_pool_status = self.api_client.get_thread_pool_status()
                max_threads = thread_pool_status.get("max_workers", 8)
                active_threads = thread_pool_status.get("active_threads", 0)
                idle_threads = thread_pool_status.get("idle_threads", 8)
                load_percentage = thread_pool_status.get("load_percentage", 0)

                self.threadpool_label.setText(
                    f"线程池: 活跃 {active_threads}/{max_threads} | 空闲 {idle_threads}/{max_threads} | 负载: {load_percentage}%"
                )
            except Exception:
                # 如果API调用失败，使用本地计算的数据
                max_threads = 8
                active_threads = running
                idle_threads = max_threads - active_threads
                load_percentage = (
                    int((active_threads / max_threads) * 100) if max_threads > 0 else 0
                )

                self.threadpool_label.setText(
                    f"线程池: 活跃 {active_threads}/{max_threads} | 空闲 {idle_threads}/{max_threads} | 负载: {load_percentage}%"
                )

    def _apply_priority_settings(self):
        """应用优先级设置"""
        settings = {
            "video": self.video_priority.currentText(),
            "audio": self.audio_priority.currentText(),
            "image": self.image_priority.currentText(),
        }

        # 发射信号
        self.priority_changed.emit(settings)

        # 更新任务的优先级
        priority_map = {"高": 2, "中": 5, "低": 9}

        type_priority_map = {
            "video_embed": settings["video"],
            "audio_embed": settings["audio"],
            "image_embed": settings["image"],
        }

        for task in self.tasks:
            task_type = task["task_type"]
            if task_type in type_priority_map:
                priority_text = type_priority_map[task_type]
                task["priority"] = priority_map.get(priority_text, 5)

        self._refresh_tasks()

    def _pause_tasks(self):
        """暂停任务"""
        for task in self.tasks:
            if task["status"] == "running":
                task["status"] = "paused"
        self._refresh_tasks()
        self.tasks_paused.emit()

    def _resume_tasks(self):
        """恢复任务"""
        for task in self.tasks:
            if task["status"] == "paused":
                task["status"] = "pending"
        self._refresh_tasks()
        self.tasks_resumed.emit()

    def _cancel_tasks(self):
        """取消任务"""
        for task in self.tasks:
            if task["status"] in ["pending", "running", "paused"]:
                task["status"] = "cancelled"
        self._refresh_tasks()
        self.tasks_cancelled.emit()

    def _raise_priority(self):
        """批量提升优先级"""
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            task_data = item.data(Qt.ItemDataRole.UserRole)
            task_id = task_data.get("id", "")

            for task in self.tasks:
                if task["id"] == task_id:
                    task["priority"] = max(1, task["priority"] - 1)
                    break

        self._refresh_tasks()

    def _lower_priority(self):
        """批量降低优先级"""
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            task_data = item.data(Qt.ItemDataRole.UserRole)
            task_id = task_data.get("id", "")

            for task in self.tasks:
                if task["id"] == task_id:
                    task["priority"] = min(11, task["priority"] + 1)
                    break

        self._refresh_tasks()

    def _batch_cancel(self):
        """批量取消"""
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            task_data = item.data(Qt.ItemDataRole.UserRole)
            task_id = task_data.get("id", "")

            for task in self.tasks:
                if task["id"] == task_id:
                    if task["status"] in ["pending", "running", "paused"]:
                        task["status"] = "cancelled"
                    break

        self._refresh_tasks()

    def get_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        return self.tasks

    def get_stats(self) -> Dict[str, int]:
        """获取任务统计"""
        return {
            "pending": sum(1 for t in self.tasks if t["status"] == "pending"),
            "running": sum(1 for t in self.tasks if t["status"] == "running"),
            "completed": sum(1 for t in self.tasks if t["status"] == "completed"),
            "failed": sum(1 for t in self.tasks if t["status"] == "failed"),
        }

    def show_task_dependencies(self, task_id: str) -> Dict[str, Any]:
        """
        显示任务依赖信息

        Args:
            task_id: 任务ID

        Returns:
            任务依赖信息
        """
        for task in self.tasks:
            if task["id"] == task_id:
                depends_on = task.get("depends_on", [])

                # 查找依赖此任务的其他任务
                dependent_tasks = []
                for other_task in self.tasks:
                    other_depends_on = other_task.get("depends_on", [])
                    if task_id in other_depends_on:
                        dependent_tasks.append(other_task["id"])

                return {
                    "task_id": task_id,
                    "task_type": task.get("task_type", "unknown"),
                    "status": task.get("status", "unknown"),
                    "depends_on": depends_on,
                    "dependent_tasks": dependent_tasks,
                    "dependency_count": len(depends_on),
                    "dependent_count": len(dependent_tasks),
                }

        return {
            "task_id": task_id,
            "task_type": "unknown",
            "status": "not_found",
            "depends_on": [],
            "dependent_tasks": [],
            "dependency_count": 0,
            "dependent_count": 0,
        }

    def _on_task_selection_changed(self):
        """任务选择变更事件"""
        selected_items = self.task_list.selectedItems()

        if not selected_items:
            self.dependency_label.setText("任务依赖: 未选择")
            return

        if len(selected_items) > 1:
            self.dependency_label.setText(
                f"任务依赖: 已选择 {len(selected_items)} 个任务"
            )
            return

        # 获取选中任务的信息
        selected_item = selected_items[0]
        task_data = selected_item.data(Qt.ItemDataRole.UserRole)
        task_id = task_data.get("id", "")

        # 查找任务依赖信息
        depends_on = []
        dependent_tasks = []

        for task in self.tasks:
            if task["id"] == task_id:
                depends_on = task.get("depends_on", [])
                break

        # 查找依赖此任务的其他任务
        for task in self.tasks:
            task_depends_on = task.get("depends_on", [])
            if task_id in task_depends_on:
                dependent_tasks.append(task["id"])

        # 显示依赖信息
        if depends_on or dependent_tasks:
            dep_info = []
            if depends_on:
                dep_info.append(f"依赖 {len(depends_on)} 个任务")
            if dependent_tasks:
                dep_info.append(f"被 {len(dependent_tasks)} 个任务依赖")

            self.dependency_label.setText(
                f"任务依赖: {', '.join(dep_info) if dep_info else '无'}"
            )
        else:
            self.dependency_label.setText("任务依赖: 无依赖")
