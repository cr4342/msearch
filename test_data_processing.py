#!/usr/bin/env python3
"""
测试脚本：验证程序是否能正常处理数据
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
src_root = project_root / "src"
sys.path.insert(0, str(src_root))
sys.path.insert(0, str(project_root))

from core.config.config_manager import ConfigManager
from core.task import CentralTaskManager
from services.media.media_processor import MediaProcessor


def test_config_loading():
    """测试配置加载"""
    print("=" * 50)
    print("测试1: 配置加载")
    print("=" * 50)
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_all()
        
        print(f"✓ 配置加载成功")
        print(f"  - 监控目录: {config.get('file_monitor', {}).get('watch_directories', [])}")
        print(f"  - 设备类型: {config.get('models', {}).get('device', 'cpu')}")
        print(f"  - 向量维度: {config.get('models', {}).get('image_video_model', {}).get('embedding_dim', 'N/A')}")
        
        return True, config
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_task_manager(config):
    """测试任务管理器"""
    print("\n" + "=" * 50)
    print("测试2: 任务管理器初始化")
    print("=" * 50)
    
    try:
        device = config.get('models', {}).get('device', 'cpu')
        task_manager = CentralTaskManager(config, device)
        
        if task_manager.initialize():
            print(f"✓ 任务管理器初始化成功")
            
            # 获取统计信息
            stats = task_manager.get_statistics()
            print(f"  - 队列大小: {stats.get('queue_size', 0)}")
            print(f"  - 运行中任务: {stats.get('running_count', 0)}")
            print(f"  - 资源状态: {stats.get('resource_state', 'unknown')}")
            
            return True, task_manager
        else:
            print(f"✗ 任务管理器初始化失败")
            return False, None
    except Exception as e:
        print(f"✗ 任务管理器初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_media_processor(config):
    """测试媒体处理器"""
    print("\n" + "=" * 50)
    print("测试3: 媒体处理器")
    print("=" * 50)
    
    try:
        media_processor = MediaProcessor(config)
        print(f"✓ 媒体处理器初始化成功")
        return True, media_processor
    except Exception as e:
        print(f"✗ 媒体处理器初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_file_scanning(testdata_dir):
    """测试文件扫描"""
    print("\n" + "=" * 50)
    print("测试4: 文件扫描")
    print("=" * 50)
    
    try:
        testdata_path = Path(testdata_dir)
        if not testdata_path.exists():
            print(f"✗ 测试目录不存在: {testdata_dir}")
            return False, []
        
        # 扫描支持的文件
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', 
                              '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv',
                              '.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'}
        
        files = []
        for ext in supported_extensions:
            files.extend(testdata_path.glob(f'*{ext}'))
            files.extend(testdata_path.glob(f'*{ext.upper()}'))
        
        print(f"✓ 找到 {len(files)} 个支持的文件")
        
        # 显示前5个文件
        for i, file in enumerate(files[:5]):
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"  {i+1}. {file.name} ({size_mb:.2f} MB)")
        
        if len(files) > 5:
            print(f"  ... 还有 {len(files) - 5} 个文件")
        
        return True, files
    except Exception as e:
        print(f"✗ 文件扫描失败: {e}")
        import traceback
        traceback.print_exc()
        return False, []


def test_task_creation(task_manager, files):
    """测试任务创建"""
    print("\n" + "=" * 50)
    print("测试5: 任务创建")
    print("=" * 50)
    
    try:
        # 为前3个文件创建任务
        created_tasks = []
        for file in files[:3]:
            task_id = task_manager.create_task(
                task_type='file_scan',
                task_data={'file_path': str(file)},
                priority=5
            )
            created_tasks.append(task_id)
            print(f"✓ 创建任务: {task_id} for {file.name}")
        
        print(f"✓ 成功创建 {len(created_tasks)} 个任务")
        
        # 等待任务完成
        print("\n等待任务完成...")
        time.sleep(5)
        
        # 检查任务状态
        for task_id in created_tasks:
            task_status = task_manager.get_task_status(task_id)
            if task_status:
                # task_status 是一个 Task 对象，不是字典
                status = task_status.status if hasattr(task_status, 'status') else 'unknown'
                progress = task_status.progress if hasattr(task_status, 'progress') else 0
                print(f"  任务 {task_id}: 状态={status}, 进度={progress}")
        
        return True
    except Exception as e:
        print(f"✗ 任务创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "=" * 48 + "╗")
    print("║" + " " * 10 + "msearch 数据处理验证测试" + " " * 16 + "║")
    print("╚" + "=" * 48 + "╝")
    print()
    
    # 测试1: 配置加载
    success, config = test_config_loading()
    if not success:
        print("\n✗ 配置加载失败，无法继续测试")
        return False
    
    # 测试2: 任务管理器
    success, task_manager = test_task_manager(config)
    if not success:
        print("\n✗ 任务管理器初始化失败，无法继续测试")
        return False
    
    # 测试3: 媒体处理器
    success, media_processor = test_media_processor(config)
    if not success:
        print("\n⚠ 媒体处理器初始化失败，继续其他测试")
    
    # 测试4: 文件扫描
    testdata_dir = config.get('file_monitor', {}).get('watch_directories', ['testdata'])[0]
    success, files = test_file_scanning(testdata_dir)
    if not success:
        print("\n✗ 文件扫描失败，无法继续测试")
        return False
    
    # 测试5: 任务创建
    success = test_task_creation(task_manager, files)
    if not success:
        print("\n✗ 任务创建失败")
        return False
    
    # 清理
    print("\n" + "=" * 50)
    print("清理资源")
    print("=" * 50)
    
    if task_manager:
        task_manager.shutdown()
        print("✓ 任务管理器已关闭")
    
    print("\n" + "╔" + "=" * 48 + "╗")
    print("║" + " " * 15 + "所有测试完成" + " " * 21 + "║")
    print("╚" + "=" * 48 + "╝")
    print()
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)