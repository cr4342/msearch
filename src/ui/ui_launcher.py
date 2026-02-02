#!/usr/bin/env python3
"""
msearch UI启动器
用于启动PySide6桌面应用
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
except ImportError:
    print("错误: PySide6未安装")
    print("请运行: pip install PySide6")
    sys.exit(1)

from src.ui.main_window import MainWindow

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_application():
    """设置应用程序"""
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("msearch")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("msearch Team")

    # 设置默认字体
    font = QFont("Arial", 10)
    app.setFont(font)

    # 启用高DPI缩放
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    return app


def main():
    """主函数"""
    logger.info("启动 msearch UI...")

    try:
        # 设置应用程序
        app = setup_application()

        # 创建主窗口
        logger.info("创建主窗口...")
        main_window = MainWindow()
        main_window.show()

        logger.info("msearch UI 启动成功")

        # 运行应用程序
        sys.exit(app.exec())

    except KeyboardInterrupt:
        logger.info("用户中断，正在退出...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
