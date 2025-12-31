#!/usr/bin/env python3
"""
MSearch硬件分析脚本
用于检测系统硬件配置并生成推荐配置
"""

import os
import sys
import json
import platform
from pathlib import Path

# 尝试导入必要的库
try:
    import psutil
except ImportError:
    print("psutil库未安装，尝试安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

try:
    import torch
except ImportError:
    torch = None

try:
    import GPUtil
except ImportError:
    GPUtil = None


def get_cpu_info():
    """获取CPU信息"""
    cpu_info = {
        "model": platform.processor(),
        "physical_cores": psutil.cpu_count(logical=False),
        "total_cores": psutil.cpu_count(logical=True),
        "cpu_freq": f"{psutil.cpu_freq().current:.2f} MHz",
        "cpu_percent": f"{psutil.cpu_percent(interval=1)}%",
        "architecture": platform.machine()
    }
    return cpu_info


def get_memory_info():
    """获取内存信息"""
    memory = psutil.virtual_memory()
    memory_info = {
        "total": f"{memory.total / (1024 ** 3):.2f} GB",
        "available": f"{memory.available / (1024 ** 3):.2f} GB",
        "used": f"{memory.used / (1024 ** 3):.2f} GB",
        "percent": f"{memory.percent}%",
        "total_bytes": memory.total,
        "available_bytes": memory.available
    }
    return memory_info


def get_disk_info():
    """获取磁盘信息"""
    disk_info = []
    for partition in psutil.disk_partitions():
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
            disk_info.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "file_system": partition.fstype,
                "total": f"{partition_usage.total / (1024 ** 3):.2f} GB",
                "used": f"{partition_usage.used / (1024 ** 3):.2f} GB",
                "free": f"{partition_usage.free / (1024 ** 3):.2f} GB",
                "percent": f"{partition_usage.percent}%"
            })
        except (PermissionError, FileNotFoundError):
            continue
    return disk_info


def get_gpu_info():
    """获取GPU信息"""
    gpu_info = []
    has_gpu = False
    is_cuda_available = False
    is_mps_available = False
    is_openvino_available = False
    
    # 检查CUDA可用性
    if torch:
        is_cuda_available = torch.cuda.is_available()
        is_mps_available = torch.backends.mps.is_available()
    
    # 尝试检查OpenVINO可用性
    try:
        from openvino.runtime import Core
        is_openvino_available = True
    except ImportError:
        pass
    
    # 使用GPUtil获取GPU详细信息
    if GPUtil:
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            has_gpu = True
            gpu_info.append({
                "name": gpu.name,
                "memory_total": f"{gpu.memoryTotal / 1024:.2f} GB",
                "memory_used": f"{gpu.memoryUsed / 1024:.2f} GB",
                "memory_free": f"{gpu.memoryFree / 1024:.2f} GB",
                "temperature": f"{gpu.temperature}°C",
                "utilization": f"{gpu.load * 100:.2f}%",
                "driver": gpu.driver
            })
    elif torch and is_cuda_available:
        # 如果没有GPUtil，但有CUDA，使用torch获取基本信息
        has_gpu = True
        for i in range(torch.cuda.device_count()):
            gpu_info.append({
                "name": torch.cuda.get_device_name(i),
                "memory_total": f"{torch.cuda.get_device_properties(i).total_memory / (1024 ** 3):.2f} GB"
            })
    
    return {
        "has_gpu": has_gpu,
        "is_cuda_available": is_cuda_available,
        "is_mps_available": is_mps_available,
        "is_openvino_available": is_openvino_available,
        "gpus": gpu_info
    }


def get_system_info():
    """获取系统信息"""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "python_executable": sys.executable
    }


def generate_recommendations(hardware_info):
    """根据硬件信息生成配置建议"""
    recommendations = {
        "model_selection": {
            "clip": "openai/clip-vit-base-patch32",
            "clap": "laion/clap-htsat-fused",
            "whisper": "openai/whisper-base",
            "facenet": "facenet-pytorch"
        },
        "optimization": {
            "batch_size": 16,
            "num_workers": 4,
            "use_half_precision": False,
            "max_concurrent_tasks": 3
        },
        "configuration": {
            "check_interval": 5.0
        }
    }
    
    # 获取内存信息，用于调整配置
    total_memory = hardware_info['memory']['total_bytes']
    has_gpu = hardware_info['gpu']['has_gpu']
    is_cuda_available = hardware_info['gpu']['is_cuda_available']
    is_mps_available = hardware_info['gpu']['is_mps_available']
    gpu_count = len(hardware_info['gpu']['gpus'])
    
    # 根据GPU情况调整模型选择和优化参数
    if has_gpu:
        # 有GPU，使用更高精度的模型
        recommendations['model_selection']['clip'] = "openai/clip-vit-base-patch32"
        recommendations['model_selection']['clap'] = "laion/clap-htsat-fused"
        recommendations['model_selection']['whisper'] = "openai/whisper-base"
        
        # 根据GPU数量调整并发任务数
        recommendations['optimization']['max_concurrent_tasks'] = min(gpu_count * 2, 8)
        
        if is_cuda_available or is_mps_available:
            # CUDA或MPS可用，使用半精度
            recommendations['optimization']['use_half_precision'] = True
            # 增加批处理大小
            recommendations['optimization']['batch_size'] = 32
    
    # 根据内存大小调整参数
    if total_memory < 8 * 1024 ** 3:  # 小于8GB内存
        recommendations['optimization']['batch_size'] = 8
        recommendations['optimization']['num_workers'] = 2
        recommendations['optimization']['max_concurrent_tasks'] = 2
        # 使用更小的模型
        recommendations['model_selection']['clip'] = "openai/clip-vit-base-patch32"
        recommendations['model_selection']['whisper'] = "openai/whisper-tiny"
    elif total_memory < 16 * 1024 ** 3:  # 8-16GB内存
        recommendations['optimization']['batch_size'] = 16
        recommendations['optimization']['num_workers'] = 4
        recommendations['optimization']['max_concurrent_tasks'] = 3
    else:  # 大于16GB内存
        recommendations['optimization']['batch_size'] = 32
        recommendations['optimization']['num_workers'] = 8
        recommendations['optimization']['max_concurrent_tasks'] = 5
    
    return recommendations


def main(output_path):
    """主函数"""
    print("===============================================")
    print("        MSearch 硬件分析工具")
    print("===============================================")
    
    # 获取硬件信息
    print("正在检测系统硬件配置...")
    print("1. 检测CPU信息...")
    cpu_info = get_cpu_info()
    print("2. 检测内存信息...")
    memory_info = get_memory_info()
    print("3. 检测磁盘信息...")
    disk_info = get_disk_info()
    print("4. 检测GPU信息...")
    gpu_info = get_gpu_info()
    print("5. 检测系统信息...")
    system_info = get_system_info()
    
    # 生成配置建议
    print("6. 生成配置建议...")
    hardware_info = {
        "cpu": cpu_info,
        "memory": memory_info,
        "disk": disk_info,
        "gpu": gpu_info,
        "system": system_info
    }
    
    recommendations = generate_recommendations(hardware_info)
    hardware_info["recommendations"] = recommendations
    
    # 保存结果到文件
    print(f"7. 保存硬件分析结果到: {output_path}")
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(hardware_info, f, indent=2, ensure_ascii=False)
    
    print("===============================================")
    print("硬件分析完成！")
    print("===============================================")
    print(f"CPU: {cpu_info['model']}")
    print(f"物理核心: {cpu_info['physical_cores']}")
    print(f"总核心: {cpu_info['total_cores']}")
    print(f"内存: {memory_info['total']}")
    print(f"磁盘: {disk_info[0]['total']} ({disk_info[0]['file_system']})")
    
    if gpu_info["has_gpu"]:
        print(f"GPU: {gpu_info['gpus'][0]['name']}")
        print(f"GPU内存: {gpu_info['gpus'][0]['memory_total']}")
    else:
        print("GPU: 未检测到独立GPU")
    
    print("推荐配置:")
    print(f"  CLIP模型: {recommendations['model_selection']['clip']}")
    print(f"  CLAP模型: {recommendations['model_selection']['clap']}")
    print(f"  Whisper模型: {recommendations['model_selection']['whisper']}")
    print(f"  批处理大小: {recommendations['optimization']['batch_size']}")
    print(f"  工作线程数: {recommendations['optimization']['num_workers']}")
    print(f"  使用半精度: {'是' if recommendations['optimization']['use_half_precision'] else '否'}")
    print(f"  最大并发任务数: {recommendations['optimization']['max_concurrent_tasks']}")
    print("===============================================")
    
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = os.path.join(os.getcwd(), "hardware_info.json")
    
    sys.exit(main(output_path))
