#!/usr/bin/env python3
"""
测试UI改进效果
验证桌面UI的改进是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    
    # 导入UI组件
    from src.ui.main_window import MainWindow
    
    def test_ui():
        """测试UI"""
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        # 5秒后自动关闭
        QTimer.singleShot(5000, app.quit)
        
        # 运行应用
        sys.exit(app.exec())
    
    if __name__ == "__main__":
        print("启动UI测试...")
        print("测试内容:")
        print("1. 主窗口布局 - 顶部工具栏（蓝色背景，功能按钮）")
        print("2. 搜索面板UI - 现代扁平化风格和配色方案")
        print("3. 结果面板 - 时间轴视图和网格视图切换功能")
        print("4. 设置面板 - 系统设置功能")
        print("5. 状态栏 - 实时状态监控和进度显示")
        print("6. 任务管理器 - 任务进度和历史记录")
        print("\n应用将在5秒后自动关闭...")
        test_ui()
        
except ImportError as e:
    print(f"导入失败: {e}")
    print("请确保已安装PySide6: pip install PySide6")
    sys.exit(1)
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)