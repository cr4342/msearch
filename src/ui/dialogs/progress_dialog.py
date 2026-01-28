"""
进度对话框
显示长时间操作的进度
"""

from typing import Optional, Callable
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QTextEdit
)
from PySide6.QtCore import Signal, Qt


class ProgressDialog(QDialog):
    """进度对话框"""
    
    # 信号定义
    cancelled = Signal()
    
    def __init__(self, title: str = "进度", parent=None):
        """初始化进度对话框"""
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(500, 300)
        
        self.current_progress = 0
        self.total_progress = 100
        self.is_cancellable = True
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 标题标签
        self.title_label = QLabel("正在处理...")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # 状态标签
        self.status_label = QLabel("准备中...")
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 详细信息文本框
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(100)
        layout.addWidget(self.details_text)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def set_title(self, title: str):
        """设置标题"""
        self.title_label.setText(title)
    
    def set_status(self, status: str):
        """设置状态"""
        self.status_label.setText(status)
    
    def set_progress(self, current: int, total: Optional[int] = None):
        """设置进度"""
        self.current_progress = current
        if total is not None:
            self.total_progress = total
        
        if self.total_progress > 0:
            percentage = int((self.current_progress / self.total_progress) * 100)
            self.progress_bar.setValue(percentage)
        else:
            self.progress_bar.setValue(0)
    
    def set_indeterminate(self, indeterminate: bool = True):
        """设置不确定进度模式"""
        if indeterminate:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
    
    def add_detail(self, detail: str):
        """添加详细信息"""
        self.details_text.append(detail)
        # 自动滚动到底部
        scrollbar = self.details_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_details(self):
        """清除详细信息"""
        self.details_text.clear()
    
    def set_cancellable(self, cancellable: bool):
        """设置是否可取消"""
        self.is_cancellable = cancellable
        self.cancel_button.setEnabled(cancellable)
    
    def on_cancel_clicked(self):
        """取消按钮点击事件"""
        if self.is_cancellable:
            self.cancelled.emit()
            self.reject()
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.is_cancellable:
            self.cancelled.emit()
        event.accept()


class IndexingProgressDialog(ProgressDialog):
    """索引进度对话框"""
    
    def __init__(self, parent=None):
        """初始化索引进度对话框"""
        super().__init__("索引进度", parent)
        self.set_title("正在索引文件...")
        self.files_processed = 0
        self.files_total = 0
    
    def set_files_count(self, processed: int, total: int):
        """设置文件数量"""
        self.files_processed = processed
        self.files_total = total
        self.set_status(f"已处理 {processed} / {total} 个文件")
        self.set_progress(processed, total)
    
    def add_file_result(self, file_path: str, success: bool, message: str = ""):
        """添加文件处理结果"""
        status = "成功" if success else "失败"
        detail = f"{status}: {file_path}"
        if message:
            detail += f" - {message}"
        self.add_detail(detail)


class SearchProgressDialog(ProgressDialog):
    """搜索进度对话框"""
    
    def __init__(self, parent=None):
        """初始化搜索进度对话框"""
        super().__init__("搜索进度", parent)
        self.set_title("正在搜索...")
        self.set_indeterminate(True)
    
    def set_search_status(self, status: str):
        """设置搜索状态"""
        self.set_status(status)
        self.add_detail(status)


class DownloadProgressDialog(ProgressDialog):
    """下载进度对话框"""
    
    def __init__(self, parent=None):
        """初始化下载进度对话框"""
        super().__init__("下载进度", parent)
        self.set_title("正在下载模型...")
        self.downloaded_bytes = 0
        self.total_bytes = 0
    
    def set_download_progress(self, downloaded: int, total: int):
        """设置下载进度"""
        self.downloaded_bytes = downloaded
        self.total_bytes = total
        
        # 计算进度百分比
        if total > 0:
            percentage = int((downloaded / total) * 100)
            self.set_progress(percentage)
            self.set_status(f"已下载 {self._format_bytes(downloaded)} / {self._format_bytes(total)} ({percentage}%)")
        else:
            self.set_status(f"已下载 {self._format_bytes(downloaded)}")
    
    def _format_bytes(self, bytes_count: int) -> str:
        """格式化字节数"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.2f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.2f} TB"