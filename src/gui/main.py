#!/usr/bin/env python3
"""
msearch PySide6桌面应用程序主入口
"""

import sys
import os
from pathlib import Path
from typing import Optional

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QSettings, Qt
from PySide6.QtGui import QIcon

from src.core.config import load_config
from src.core.logging_config import setup_logging, get_logger
from src.gui.app import MSearchApplication

# 获取日志记录器
logger = get_logger(__name__)


def setup_application() -> QApplication:
    """设置应用程序实例"""
    # 设置应用程序属性
    QApplication.setApplicationName("msearch")
    QApplication.setApplicationVersion("0.1.0")
    QApplication.setOrganizationName("msearch")
    QApplication.setOrganizationDomain("msearch.local")
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用程序图标
    icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # 设置高DPI支持
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    return app


def load_settings() -> dict:
    """加载应用程序设置"""
    settings = QSettings()
    
    return {
        "window_geometry": settings.value("window_geometry", ""),
        "window_state": settings.value("window_state", ""),
        "theme": settings.value("theme", "light"),
        "language": settings.value("language", "zh_CN"),
        "auto_start": settings.value("auto_start", False, type=bool),
        "minimize_to_tray": settings.value("minimize_to_tray", True, type=bool),
        "api_base_url": settings.value("api_base_url", "http://localhost:8000"),
        "auto_connect": settings.value("auto_connect", True, type=bool)
    }


def save_settings(settings_dict: dict) -> None:
    """保存应用程序设置"""
    settings = QSettings()
    
    for key, value in settings_dict.items():
        settings.setValue(key, value)
    
    settings.sync()
    logger.info("应用程序设置已保存")


def setup_single_instance(app: QApplication) -> bool:
    """设置单实例应用程序"""
    # 检查是否已经有实例在运行
    import socket
    
    socket_path = "/tmp/msearch_socket"
    
    try:
        # 尝试连接到已存在的实例
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(socket_path)
        sock.close()
        
        # 如果连接成功，说明已经有实例在运行
        logger.info("msearch已经在运行中")
        return False
    except (FileNotFoundError, ConnectionRefusedError):
        # 创建socket文件
        try:
            os.unlink(socket_path)
        except FileNotFoundError:
            pass
        
        # 创建socket服务器
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(socket_path)
        sock.listen(1)
        
        # 设置定时器检查新实例请求
        def check_new_instance():
            try:
                conn, _ = sock.accept()
                conn.close()
                # 当有新实例请求时，将当前窗口置于前台
                for widget in app.topLevelWidgets():
                    if widget.isVisible():
                        widget.raise_()
                        widget.activateWindow()
                        break
            except OSError:
                pass
        
        timer = QTimer()
        timer.timeout.connect(check_new_instance)
        timer.start(1000)  # 每秒检查一次
        
        # 确保在应用程序退出时删除socket文件
        def cleanup():
            try:
                os.unlink(socket_path)
            except FileNotFoundError:
                pass
        
        import atexit
        atexit.register(cleanup)
        
        return True
    except Exception as e:
        logger.error(f"设置单实例应用程序失败: {e}")
        return True  # 出错时仍然允许启动


def main() -> int:
    """主函数"""
    try:
        # 加载配置
        config = load_config()
        
        # 设置日志
        setup_logging(config)
        logger.info("启动msearch桌面应用程序")
        
        # 设置应用程序
        app = setup_application()
        
        # 设置单实例应用程序
        if not setup_single_instance(app):
            return 1
        
        # 加载设置
        settings = load_settings()
        logger.info(f"加载设置: {settings}")
        
        # 创建主应用程序窗口
        main_window = MSearchApplication(config, settings)
        main_window.show()
        
        # 如果有保存的窗口几何信息，恢复窗口状态
        if settings["window_geometry"]:
            main_window.restoreGeometry(settings["window_geometry"])
        
        if settings["window_state"]:
            main_window.restoreState(settings["window_state"])
        
        # 设置退出处理
        def handle_exit():
            # 保存窗口状态
            settings["window_geometry"] = main_window.saveGeometry()
            settings["window_state"] = main_window.saveState()
            
            # 保存设置
            save_settings(settings)
            
            logger.info("msearch桌面应用程序已退出")
        
        app.aboutToQuit.connect(handle_exit)
        
        # 运行应用程序
        return app.exec()
    
    except Exception as e:
        logger.error(f"启动应用程序失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())