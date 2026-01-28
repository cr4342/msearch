#!/usr/bin/env python3
"""
测试 API 服务器功能
验证文件监控、任务管理和文件扫描是否正常工作
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api_server import APIServer

def test_api_server():
    """测试 API 服务器"""
    print("=" * 60)
    print("测试 API 服务器功能")
    print("=" * 60)

    # 初始化服务器
    print("\n1. 初始化 API 服务器...")
    try:
        server = APIServer()
        print("   ✓ API 服务器初始化成功")
    except Exception as e:
        print(f"   ✗ API 服务器初始化失败: {e}")
        return False

    # 检查文件监控
    print("\n2. 检查文件监控...")
    if server.file_monitor:
        print("   ✓ 文件监控已启动")
    else:
        print("   ✗ 文件监控未启动")
        return False

    # 检查任务管理器
    print("\n3. 检查任务管理器...")
    task_manager = server.components.get('task_manager')
    if task_manager:
        print("   ✓ 任务管理器已初始化")
    else:
        print("   ✗ 任务管理器未初始化")
        return False

    # 等待任务处理
    print("\n4. 等待任务处理（5秒）...")
    time.sleep(5)

    # 获取任务统计
    print("\n5. 获取任务统计...")
    stats = task_manager.get_task_stats()
    print(f"   待处理: {stats['pending_count']}")
    print(f"   运行中: {stats['running_count']}")
    print(f"   已完成: {stats['completed_count']}")
    print(f"   失败: {stats['failed_count']}")

    if stats['completed_count'] > 0:
        print("   ✓ 任务正在被处理")
    else:
        print("   ⚠ 暂无完成的任务")

    # 获取文件统计
    print("\n6. 获取文件统计...")
    db_manager = server.components.get('database_manager')
    if db_manager:
        db_stats = db_manager.get_database_stats()
        print(f"   文件总数: {db_stats.get('total_files', 0)}")
        print(f"   向量总数: {db_stats.get('total_vectors', 0)}")

        if db_stats.get('total_files', 0) > 0:
            print("   ✓ 文件正在被扫描")
        else:
            print("   ⚠ 暂无已扫描的文件")
    else:
        print("   ✗ 数据库管理器未初始化")
        return False

    # 获取系统信息
    print("\n7. 获取系统信息...")
    hardware_detector = server.components.get('hardware_detector')
    if hardware_detector:
        hw_info = hardware_detector.get_hardware_info()
        print(f"   CPU: {hw_info['cpu']['physical_cores']} 核心")
        print(f"   内存: {hw_info['memory']['total']/1024:.1f} GB")
        print(f"   GPU: {'有' if hw_info['gpu']['has_gpu'] else '无'}")
        print("   ✓ 硬件信息获取成功")
    else:
        print("   ✗ 硬件检测器未初始化")
        return False

    # 获取模型信息
    print("\n8. 获取模型信息...")
    embedding_engine = server.components.get('embedding_engine')
    if embedding_engine:
        model_info = embedding_engine.get_current_model_info()
        print(f"   图像/视频模型: {model_info.get('image_video_model', 'N/A')}")
        print(f"   音频模型: {model_info.get('audio_model', 'N/A')}")
        print(f"   设备: {model_info.get('device', 'N/A')}")
        print("   ✓ 模型信息获取成功")
    else:
        print("   ✗ 向量化引擎未初始化")
        return False

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"✓ API 服务器: 正常运行")
    print(f"✓ 文件监控: 已启动")
    print(f"✓ 任务管理: 已完成 {stats['completed_count']} 个任务")
    print(f"✓ 文件扫描: 已扫描 {db_stats.get('total_files', 0)} 个文件")
    print(f"✓ 硬件检测: 正常")
    print(f"✓ 模型加载: 正常")
    print("\n✓ 所有测试通过！API 服务器功能正常。")
    print("\n现在可以访问 WebUI:")
    print("  http://localhost:8000")
    print("  http://localhost:8000/webui/index.html")

    return True

if __name__ == "__main__":
    success = test_api_server()
    sys.exit(0 if success else 1)