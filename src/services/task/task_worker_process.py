"""
任务工作进程 - 独立进程负责非推理类任务（媒体预处理、文件转换等）
"""
import time
import os
import json
from typing import Dict, Any
from pathlib import Path

from src.ipc.redis_ipc import TaskWorkerIPC


def execute_preprocessing_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """执行预处理任务"""
    task_type = task_data.get("subtype", "")
    
    if task_type == "video_slice":
        # 视频切片任务
        video_path = task_data.get("video_path", "")
        start_time = task_data.get("start_time", 0.0)
        end_time = task_data.get("end_time", None)
        
        # 这里应该调用视频处理库进行切片
        # 由于依赖库可能未安装，这里只模拟
        result_path = f"{video_path}_slice_{start_time}_{end_time}.mp4"
        
        return {
            "success": True,
            "output_path": result_path,
            "start_time": start_time,
            "end_time": end_time
        }
        
    elif task_type == "audio_extract":
        # 音频提取任务
        video_path = task_data.get("video_path", "")
        
        # 模拟音频提取
        audio_path = video_path.replace(".mp4", ".wav").replace(".avi", ".wav")
        
        return {
            "success": True,
            "audio_path": audio_path
        }
        
    elif task_type == "thumbnail_generate":
        # 缩略图生成任务
        file_path = task_data.get("file_path", "")
        size = task_data.get("size", (256, 256))
        
        # 模拟缩略图生成
        thumbnail_path = file_path + f"_thumb_{size[0]}x{size[1]}.jpg"
        
        return {
            "success": True,
            "thumbnail_path": thumbnail_path
        }
        
    elif task_type == "file_convert":
        # 文件格式转换任务
        input_path = task_data.get("input_path", "")
        output_format = task_data.get("output_format", "mp4")
        
        # 模拟文件转换
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}.{output_format}"
        
        return {
            "success": True,
            "output_path": output_path
        }
        
    else:
        return {
            "success": False,
            "error": f"未知的任务子类型: {task_type}"
        }


def task_worker_process(config: Dict[str, Any]):
    """任务工作进程的主函数"""
    # 连接到Redis IPC
    ipc_client = TaskWorkerIPC()
    if not ipc_client.connect():
        print("无法连接到Redis，任务工作进程退出")
        return
    
    print("任务工作进程启动，开始处理任务...")
    
    try:
        # 主循环：从任务队列获取任务并处理
        while True:
            # 尝试获取任务
            task = ipc_client.get_task(timeout=5)  # 5秒超时
            
            if task:
                task_id = task.get("task_id")
                task_data = task.get("data", {})
                task_type = task_data.get("type", "")
                
                print(f"处理任务 {task_id}: {task_type}")
                
                if task_type == "preprocessing":
                    # 执行预处理任务
                    result = execute_preprocessing_task(task_data)
                else:
                    result = {
                        "success": False,
                        "error": f"未知的任务类型: {task_type}"
                    }
                
                # 根据结果完成或失败任务
                if result.get("success"):
                    ipc_client.complete_task(task_id, result)
                    print(f"任务 {task_id} 完成")
                else:
                    ipc_client.fail_task(task_id, result.get("error", "未知错误"))
                    print(f"任务 {task_id} 失败: {result.get('error', '未知错误')}")
            
            # 更新心跳
            ipc_client.update_heartbeat()
            
            # 短暂休息，避免过度占用CPU
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("任务工作进程收到中断信号，正在停止...")
    except Exception as e:
        print(f"任务工作进程发生错误: {e}")
    finally:
        # 清理资源
        ipc_client.disconnect()
        print("任务工作进程已停止")


if __name__ == "__main__":
    # 用于测试的配置
    test_config = {
        "worker_id": 1,
        "max_concurrent_tasks": 4
    }
    
    task_worker_process(test_config)