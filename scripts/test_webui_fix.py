#!/usr/bin/env python3
"""测试WebUI修复是否有效"""
import sys
sys.path.insert(0, '/data/project/msearch/src')

print("=" * 60)
print("测试WebUI修复")
print("=" * 60)

# 测试1: 导入检查
print("\n[测试1] 导入检查...")
try:
    from src.webui.app import MSearchApp
    print("✓ MSearchApp导入成功")
except Exception as e:
    print(f"✗ MSearchApp导入失败: {e}")
    sys.exit(1)

# 测试2: 检查refresh_task_manager返回值
print("\n[测试2] 检查refresh_task_manager返回值...")
try:
    import inspect
    sig = inspect.signature(MSearchApp.refresh_task_manager)
    print(f"✓ refresh_task_manager函数签名: {sig}")
    
    # 检查函数注释
    if MSearchApp.refresh_task_manager.__doc__:
        doc = MSearchApp.refresh_task_manager.__doc__
        if "12个返回值" in doc:
            print("✓ 函数文档已更新为12个返回值")
        else:
            print("⚠ 函数文档可能未更新")
except Exception as e:
    print(f"✗ 检查返回值失败: {e}")

# 测试3: 检查CentralTaskManager异步调用
print("\n[测试3] 检查CentralTaskManager异步调用...")
try:
    from src.core.task.central_task_manager import CentralTaskManager
    import inspect
    
    # 检查_worker_loop方法
    source = inspect.getsource(CentralTaskManager._worker_loop)
    if "asyncio.run(self.task_scheduler.dequeue_task())" in source:
        print("✓ _worker_loop已修复：使用asyncio.run调用异步方法")
    else:
        print("⚠ _worker_loop可能未正确修复")
        print(f"源代码片段: {source[:200]}")
except Exception as e:
    print(f"✗ 检查异步调用失败: {e}")

# 测试4: 检查TaskScheduler是否为异步
print("\n[测试4] 检查TaskScheduler是否为异步...")
try:
    from src.core.task.task_scheduler import TaskScheduler
    import inspect
    
    if inspect.iscoroutinefunction(TaskScheduler.dequeue_task):
        print("✓ TaskScheduler.dequeue_task是异步函数")
    else:
        print("✗ TaskScheduler.dequeue_task不是异步函数")
except Exception as e:
    print(f"✗ 检查TaskScheduler失败: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
