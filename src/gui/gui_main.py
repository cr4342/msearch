#!/usr/bin/env python3
"""
msearch GUI应用程序启动脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QSettings, Qt
    from PySide6.QtGui import QIcon
    from src.gui.main_window import MainWindow
    from src.core.config import load_config
    from src.core.logging_config import setup_logging, get_logger
    
    logger = get_logger(__name__)
    
    def main():
        """主函数"""
        try:
            # 加载配置
            config = load_config()
            
            # 设置日志
            setup_logging(config)
            logger.info("启动msearch GUI应用程序")
            
            # 创建应用程序
            app = QApplication(sys.argv)
            app.setApplicationName("mSearch")
            app.setApplicationVersion("0.1.0")
            app.setOrganizationName("mSearch Team")
            app.setOrganizationDomain("msearch.local")
            
            # 设置高DPI支持
            app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
            
            # 设置应用程序图标
            icon_path = project_root / "webui" / "src" / "assets" / "icon.png"
            if icon_path.exists():
                app.setWindowIcon(QIcon(str(icon_path)))
            
            # 创建主窗口
            main_window = MainWindow()
            
            # 加载窗口状态
            settings = QSettings("mSearch", "MainWindow")
            if settings.contains("geometry"):
                main_window.restoreGeometry(settings.value("geometry"))
            if settings.contains("windowState"):
                main_window.restoreState(settings.value("windowState"))
            
            # 显示主窗口
            main_window.show()
            
            # 运行应用程序
            exit_code = app.exec()
            logger.info(f"msearch GUI应用程序退出，退出码: {exit_code}")
            return exit_code
            
        except Exception as e:
            print(f"启动GUI应用程序失败: {e}")
            return 1
    
    if __name__ == "__main__":
        sys.exit(main())
        
except ImportError as e:
    print(f"导入PySide6失败: {e}")
    print("请确保已安装PySide6: pip install PySide6")
    sys.exit(1)