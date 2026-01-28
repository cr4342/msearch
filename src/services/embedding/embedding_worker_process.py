"""
向量化工作进程 - 独立进程负责AI模型推理和向量化
"""
import time
import torch
import numpy as np
from typing import Dict, Any, List
from PIL import Image
import tempfile
import os

from src.ipc.redis_ipc import EmbeddingWorkerIPC
from src.core.embedding.embedding_engine import EmbeddingEngine
from src.core.models.model_manager import ModelManager


def embedding_worker_process(config: Dict[str, Any]):
    """向量化工作进程的主函数"""
    # 从配置中获取参数
    device = config.get("device", "cpu")
    batch_size = config.get("batch_size", 8)
    
    # 连接到Redis IPC
    ipc_client = EmbeddingWorkerIPC()
    if not ipc_client.connect():
        print("无法连接到Redis，向量化工作进程退出")
        return
    
    print(f"向量化工作进程启动，使用设备: {device}")
    
    try:
        # 初始化模型管理器和嵌入引擎
        model_manager = ModelManager()
        embedding_engine = EmbeddingEngine()
        
        # 初始化模型
        models_config = config.get("models", {
            "chinese_clip_base": {
                "model_name": "OFA-Sys/chinese-clip-vit-base-patch16",
                "device": device,
                "batch_size": batch_size
            }
        })
        
        print("正在初始化模型...")
        for model_name, model_config in models_config.items():
            model_config["device"] = device
            model_config["batch_size"] = batch_size
        
        model_manager.load_models(models_config)
        embedding_engine.model_manager = model_manager
        
        print("模型初始化完成，开始处理任务...")
        
        # 主循环：从任务队列获取任务并处理
        while True:
            # 尝试获取任务
            task = ipc_client.get_task(timeout=5)  # 5秒超时
            
            if task:
                task_id = task.get("task_id")
                task_data = task.get("data", {})
                task_type = task_data.get("type")
                
                print(f"处理任务 {task_id}: {task_type}")
                
                try:
                    result = None
                    
                    if task_type == "embed_text":
                        # 文本向量化
                        text = task_data.get("text", "")
                        result = embedding_engine.embed_text(text)
                        
                    elif task_type == "embed_image":
                        # 图像向量化
                        image_path = task_data.get("image_path", "")
                        result = embedding_engine.embed_image(image_path)
                        
                    elif task_type == "embed_video":
                        # 视频向量化
                        video_path = task_data.get("video_path", "")
                        start_time = task_data.get("start_time", 0.0)
                        end_time = task_data.get("end_time")
                        result = embedding_engine.embed_video_segment(
                            video_path, start_time, end_time
                        )
                        
                    elif task_type == "embed_audio":
                        # 音频向量化
                        audio_path = task_data.get("audio_path", "")
                        result = embedding_engine.embed_audio(audio_path)
                        
                    else:
                        raise ValueError(f"未知的任务类型: {task_type}")
                    
                    # 完成任务
                    ipc_client.complete_task(task_id, result)
                    print(f"任务 {task_id} 完成")
                    
                except Exception as e:
                    error_msg = f"任务处理失败: {str(e)}"
                    print(error_msg)
                    ipc_client.fail_task(task_id, error_msg)
            
            # 更新心跳
            ipc_client.update_heartbeat()
            
            # 短暂休息，避免过度占用CPU
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("向量化工作进程收到中断信号，正在停止...")
    except Exception as e:
        print(f"向量化工作进程发生错误: {e}")
    finally:
        # 清理资源
        ipc_client.disconnect()
        print("向量化工作进程已停止")


if __name__ == "__main__":
    # 用于测试的配置
    test_config = {
        "device": "cpu",  # 根据系统配置调整
        "batch_size": 8,
        "models": {
            "chinese_clip_base": {
                "model_name": "OFA-Sys/chinese-clip-vit-base-patch16",
                "local_path": "data/models/chinese-clip-vit-base-patch16",
                "device": "cpu",
                "batch_size": 8
            }
        }
    }
    
    embedding_worker_process(test_config)