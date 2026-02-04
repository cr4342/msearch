#!/usr/bin/env python3
"""
测试文件监控功能
"""

import time
import subprocess
import sys
from pathlib import Path
import shutil


def test_file_monitor():
    """测试文件监控功能"""
    project_root = Path(__file__).parent
    testdata_dir = project_root / "testdata"
    test_image = project_root / "test_image.jpg"
    
    print("测试文件监控功能")
    print("="*50)
    
    # 检查是否存在测试图片，如果没有则创建一个简单的
    if not test_image.exists():
        # 创建一个简单的测试图片
        try:
            from PIL import Image
            img = Image.new('RGB', (100, 100), color='red')
            img.save(test_image)
            print("✓ 创建了测试图片")
        except ImportError:
            print("⚠ 无法创建测试图片（Pillow未安装），跳过测试")
            return
    
    # 启动服务
    print("启动msearch服务...")
    process = subprocess.Popen(
        [sys.executable, str(project_root / "src" / "main.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # 等待服务启动
    time.sleep(3)
    
    # 检查服务是否正常运行
    if process.poll() is not None:
        print("✗ 服务启动失败")
        output, _ = process.communicate()
        print(f"输出: {output}")
        return
    
    print("✓ 服务已启动，正在监控文件变化...")

    # 复制测试图片到testdata目录
    test_dest = testdata_dir / "test_monitor.jpg"
    if test_dest.exists():
        test_dest.unlink()  # 删除已存在的文件
    
    shutil.copy2(test_image, test_dest)
    print(f"✓ 已复制测试文件到: {test_dest}")
    
    print("等待文件监控器检测到新文件...")
    time.sleep(5)  # 等待监控器检测到文件
    
    # 终止服务
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    
    print("服务已停止")
    print("\n文件监控测试完成！")
    print("如果一切正常，新添加到testdata目录的文件应该会自动创建索引任务。")
    print("您可以在WebUI的任务管理器中查看这些任务。")


if __name__ == "__main__":
    test_file_monitor()
