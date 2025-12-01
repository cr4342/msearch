"""
搜索组件
提供多模态搜索界面
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
        QLineEdit, QPushButton, QLabel, QTextEdit,
        QScrollArea, QFrame, QProgressBar, QComboBox,
        QFileDialog, QMessageBox, QTabWidget, QSplitter
    )
    from PySide6.QtCore import Qt, QThread, Signal, QObject
    from PySide6.QtGui import QPixmap, QFont, QDragEnterEvent, QDropEvent
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False


class SearchWorker(QObject):
    """搜索工作线程"""
    
    # 信号定义
    finished = Signal(list)
    error = Signal(str)
    progress = Signal(int)
    
    def __init__(self, query, query_type="text", top_k=10):
        super().__init__()
        self.query = query
        self.query_type = query_type
        self.top_k = top_k
    
    def run(self):
        """运行搜索任务"""
        try:
            # 这里应该调用实际的搜索API
            # 现在使用模拟数据
            import time
            import random
            
            # 模拟搜索进度
            for i in range(0, 101, 20):
                self.progress.emit(i)
                time.sleep(0.1)
            
            # 模拟搜索结果
            results = []
            categories = ["动物", "风景", "人物", "建筑", "音乐"]
            
            for i in range(self.top_k):
                score = random.uniform(0.3, 0.95)
                category = random.choice(categories)
                
                results.append({
                    "file_id": f"file_{i}",
                    "score": score,
                    "file_path": f"/path/to/{category}_{i}.jpg",
                    "file_name": f"{category}_{i}.jpg",
                    "file_type": ".jpg",
                    "file_size": random.randint(1000, 10000),
                    "created_at": random.uniform(1600000000, 1700000000)
                })
            
            # 按分数排序
            results.sort(key=lambda x: x['score'], reverse=True)
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))


class SearchResultWidget(QWidget):
    """搜索结果组件"""
    
    def __init__(self):
        super().__init__()
        self.results = []
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 结果网格
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.results_widget = QWidget()
        self.results_layout = QGridLayout(self.results_widget)
        self.results_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.results_widget)
        layout.addWidget(self.scroll_area)
    
    def set_results(self, results: List[Dict[str, Any]]):
        """设置搜索结果"""
        self.results = results
        self._update_results_display()
    
    def _update_results_display(self):
        """更新结果显示"""
        # 清除现有结果
        for i in reversed(range(self.results_layout.count())):
            child = self.results_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not self.results:
            # 显示无结果提示
            no_results_label = QLabel("没有找到相关结果")
            no_results_label.setAlignment(Qt.AlignCenter)
            no_results_label.setStyleSheet("color: #666; font-size: 16px; padding: 20px;")
            self.results_layout.addWidget(no_results_label, 0, 0)
            return
        
        # 显示结果
        columns = 4
        for i, result in enumerate(self.results):
            row = i // columns
            col = i % columns
            
            result_item = self._create_result_item(result)
            self.results_layout.addWidget(result_item, row, col)
    
    def _create_result_item(self, result: Dict[str, Any]) -> QWidget:
        """创建结果项"""
        item = QFrame()
        item.setFrameStyle(QFrame.Box)
        item.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                background: white;
                padding: 5px;
            }
            QFrame:hover {
                border-color: #0078d4;
                background: #f8f9ff;
            }
        """)
        
        layout = QVBoxLayout(item)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 缩略图
        thumbnail = QLabel()
        thumbnail.setFixedSize(150, 150)
        thumbnail.setAlignment(Qt.AlignCenter)
        thumbnail.setStyleSheet("""
            QLabel {
                border: 1px solid #eee;
                border-radius: 4px;
                background: #f8f8f8;
            }
        """)
        
        # 根据文件类型显示不同的占位符
        file_type = result.get('file_type', '')
        if file_type in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
            thumbnail.setText("🖼️")
        elif file_type in ['.mp4', '.avi', '.mov']:
            thumbnail.setText("🎬")
        elif file_type in ['.mp3', '.wav', '.flac']:
            thumbnail.setText("🎵")
        else:
            thumbnail.setText("📄")
        
        thumbnail.setFont(QFont("Arial", 48))
        layout.addWidget(thumbnail)
        
        # 文件名
        name_label = QLabel(result.get('file_name', '未知文件'))
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setMaximumHeight(40)
        layout.addWidget(name_label)
        
        # 相似度分数
        score = result.get('score', 0)
        score_label = QLabel(f"相似度: {score:.1%}")
        score_label.setAlignment(Qt.AlignCenter)
        score_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        layout.addWidget(score_label)
        
        # 文件大小
        file_size = result.get('file_size', 0)
        size_text = self._format_file_size(file_size)
        size_label = QLabel(size_text)
        size_label.setAlignment(Qt.AlignCenter)
        size_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(size_label)
        
        return item
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"


class SearchWidget(QWidget):
    """搜索组件"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.current_worker = None
        self.current_thread = None
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 搜索类型选择
        search_type_layout = QHBoxLayout()
        
        type_label = QLabel("搜索类型:")
        search_type_layout.addWidget(type_label)
        
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["文本搜索", "图像搜索", "音频搜索"])
        search_type_layout.addWidget(self.search_type_combo)
        
        search_type_layout.addStretch()
        layout.addLayout(search_type_layout)
        
        # 分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 搜索区域
        search_widget = QWidget()
        search_layout = QVBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        # 文本搜索
        self.text_search_widget = QWidget()
        text_search_layout = QVBoxLayout(self.text_search_widget)
        text_search_layout.setContentsMargins(0, 0, 0, 0)
        
        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索关键词...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 8px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)
        self.search_input.returnPressed.connect(self._on_search)
        text_search_layout.addWidget(self.search_input)
        
        # 搜索按钮
        self.search_button = QPushButton("搜索")
        self.search_button.setStyleSheet("""
            QPushButton {
                padding: 12px 24px;
                font-size: 14px;
                background: #0078d4;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #106ebe;
            }
            QPushButton:pressed {
                background: #005a9e;
            }
            QPushButton:disabled {
                background: #ccc;
            }
        """)
        self.search_button.clicked.connect(self._on_search)
        text_search_layout.addWidget(self.search_button)
        
        search_layout.addWidget(self.text_search_widget)
        
        # 文件搜索（占位符）
        self.file_search_widget = QWidget()
        file_search_layout = QVBoxLayout(self.file_search_widget)
        
        # 文件拖放区域
        self.drop_area = QLabel()
        self.drop_area.setText("拖拽文件到这里\n或点击选择文件")
        self.drop_area.setAlignment(Qt.AlignCenter)
        self.drop_area.setMinimumHeight(200)
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ddd;
                border-radius: 8px;
                background: #f8f9ff;
                color: #666;
                font-size: 16px;
            }
            QLabel:hover {
                border-color: #0078d4;
                background: #e8f0ff;
            }
        """)
        self.drop_area.setAcceptDrops(True)
        self.drop_area.dragEnterEvent = self._drag_enter_event
        self.drop_area.dropEvent = self._drop_event
        self.drop_area.mousePressEvent = self._select_file
        
        file_search_layout.addWidget(self.drop_area)
        
        # 文件搜索按钮（初始隐藏）
        self.file_search_button = QPushButton("搜索")
        self.file_search_button.setStyleSheet(self.search_button.styleSheet())
        self.file_search_button.clicked.connect(self._on_file_search)
        self.file_search_button.hide()
        file_search_layout.addWidget(self.file_search_button)
        
        search_layout.addWidget(self.file_search_widget)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        search_layout.addWidget(self.progress_bar)
        
        splitter.addWidget(search_widget)
        
        # 结果区域
        self.result_widget = SearchResultWidget()
        splitter.addWidget(self.result_widget)
        
        # 设置分割器比例
        splitter.setSizes([200, 600])
        layout.addWidget(splitter)
        
        # 连接搜索类型变化信号
        self.search_type_combo.currentTextChanged.connect(self._on_search_type_changed)
        
        # 默认显示文本搜索
        self.file_search_widget.hide()
    
    def _on_search_type_changed(self, text):
        """搜索类型变化处理"""
        if text == "文本搜索":
            self.text_search_widget.show()
            self.file_search_widget.hide()
        elif text in ["图像搜索", "音频搜索"]:
            self.text_search_widget.hide()
            self.file_search_widget.show()
            # 更新拖放区域文本
            if text == "图像搜索":
                self.drop_area.setText("拖拽图像文件到这里\n或点击选择图像文件")
            else:
                self.drop_area.setText("拖拽音频文件到这里\n或点击选择音频文件")
    
    def _on_search(self):
        """文本搜索处理"""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "警告", "请输入搜索关键词")
            return
        
        self._start_search(query, "text")
    
    def _on_file_search(self):
        """文件搜索处理"""
        if not hasattr(self, 'selected_file_path'):
            QMessageBox.warning(self, "警告", "请先选择文件")
            return
        
        search_type = self.search_type_combo.currentText()
        query_type = "image" if search_type == "图像搜索" else "audio"
        
        self._start_search(self.selected_file_path, query_type)
    
    def _start_search(self, query, query_type):
        """开始搜索"""
        # 如果有正在进行的搜索，取消它
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.quit()
            self.current_thread.wait()
        
        # 禁用搜索控件
        self.search_button.setEnabled(False)
        self.file_search_button.setEnabled(False)
        self.search_input.setEnabled(False)
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 清除之前的结果
        self.result_widget.set_results([])
        
        # 创建工作线程
        self.current_worker = SearchWorker(query, query_type)
        self.current_thread = QThread()
        self.current_worker.moveToThread(self.current_thread)
        
        # 连接信号
        self.current_thread.started.connect(self.current_worker.run)
        self.current_worker.finished.connect(self._on_search_finished)
        self.current_worker.error.connect(self._on_search_error)
        self.current_worker.progress.connect(self._on_search_progress)
        self.current_worker.finished.connect(self.current_thread.quit)
        self.current_thread.finished.connect(self.current_thread.deleteLater)
        
        # 启动搜索
        self.current_thread.start()
    
    def _on_search_finished(self, results):
        """搜索完成处理"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        # 启用搜索控件
        self.search_button.setEnabled(True)
        self.file_search_button.setEnabled(True)
        self.search_input.setEnabled(True)
        
        # 显示结果
        self.result_widget.set_results(results)
        
        self.logger.info(f"搜索完成，找到 {len(results)} 个结果")
    
    def _on_search_error(self, error):
        """搜索错误处理"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        # 启用搜索控件
        self.search_button.setEnabled(True)
        self.file_search_button.setEnabled(True)
        self.search_input.setEnabled(True)
        
        # 显示错误
        QMessageBox.critical(self, "搜索错误", f"搜索失败: {error}")
        
        self.logger.error(f"搜索失败: {error}")
    
    def _on_search_progress(self, value):
        """搜索进度更新"""
        self.progress_bar.setValue(value)
    
    def _drag_enter_event(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_area.setStyleSheet("""
                QLabel {
                    border: 2px dashed #0078d4;
                    border-radius: 8px;
                    background: #e8f0ff;
                    color: #0078d4;
                    font-size: 16px;
                }
            """)
        else:
            event.ignore()
    
    def _drop_event(self, event: QDropEvent):
        """拖拽放下事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                self._handle_file_selected(file_path)
        
        # 恢复样式
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ddd;
                border-radius: 8px;
                background: #f8f9ff;
                color: #666;
                font-size: 16px;
            }
            QLabel:hover {
                border-color: #0078d4;
                background: #e8f0ff;
            }
        """)
    
    def _select_file(self, event):
        """选择文件"""
        search_type = self.search_type_combo.currentText()
        
        if search_type == "图像搜索":
            file_filter = "图像文件 (*.jpg *.jpeg *.png *.bmp *.webp)"
        else:  # 音频搜索
            file_filter = "音频文件 (*.mp3 *.wav *.flac *.aac)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"选择{search_type.replace('搜索', '')}文件",
            "",
            file_filter
        )
        
        if file_path:
            self._handle_file_selected(file_path)
    
    def _handle_file_selected(self, file_path: str):
        """处理文件选择"""
        # 验证文件类型
        search_type = self.search_type_combo.currentText()
        file_ext = file_path.lower().split('.')[-1]
        
        if search_type == "图像搜索":
            valid_extensions = ['jpg', 'jpeg', 'png', 'bmp', 'webp']
        else:  # 音频搜索
            valid_extensions = ['mp3', 'wav', 'flac', 'aac']
        
        if file_ext not in valid_extensions:
            QMessageBox.warning(self, "警告", f"不支持的文件类型: .{file_ext}")
            return
        
        # 存储选择的文件路径
        self.selected_file_path = file_path
        
        # 更新拖放区域显示
        file_name = file_path.split('/')[-1]
        self.drop_area.setText(f"已选择文件:\n{file_name}")
        
        # 显示搜索按钮
        self.file_search_button.show()
        
        self.logger.info(f"选择文件: {file_path}")