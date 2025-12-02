#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MSearch 模型下载脚本
自动从 Hugging Face 或 hf-mirror.com 下载所需模型到本地
"""

import os
import sys
import requests
from huggingface_hub import hf_hub_download, snapshot_download
import argparse

# 模型列表配置
MODELS_CONFIG = {
    "text_embedding": {
        "model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "local_dir": "models/text_embedding",
        "file_patterns": ["*.json", "*.bin", "*.txt", "*.model", "*.py"]
    },
    "image_embedding": {
        "model_name": "google/vit-base-patch16-224",
        "local_dir": "models/image_embedding",
        "file_patterns": ["*.json", "*.bin", "*.txt", "*.index", "*.py"]
    },
    "audio_embedding": {
        "model_name": "openai/whisper-small",
        "local_dir": "models/audio_embedding",
        "file_patterns": ["*.json", "*.bin", "*.txt", "*.model", "*.py"]
    }
}

def set_hf_mirror():
    """设置 HF_ENDPOINT 为镜像地址"""
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    print(f"设置 HF_ENDPOINT 为: {os.environ['HF_ENDPOINT']}")


def download_model_with_snapshot(model_name, local_dir, force_download=False):
    """使用 snapshot_download 下载整个模型仓库"""
    try:
        print(f"\n正在下载模型: {model_name}")
        print(f"保存路径: {local_dir}")
        
        # 确保本地目录存在
        os.makedirs(local_dir, exist_ok=True)
        
        # 下载模型
        snapshot_download(
            repo_id=model_name,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            force_download=force_download,
            resume_download=True
        )
        
        print(f"✓ 模型 {model_name} 下载完成")
        return True
    except Exception as e:
        print(f"✗ 模型 {model_name} 下载失败: {e}")
        return False


def download_model_with_hf_hub(model_name, local_dir, file_patterns, force_download=False):
    """使用 hf_hub_download 下载特定文件"""
    try:
        print(f"\n正在下载模型: {model_name}")
        print(f"保存路径: {local_dir}")
        
        # 确保本地目录存在
        os.makedirs(local_dir, exist_ok=True)
        
        # 下载指定文件
        for file_pattern in file_patterns:
            print(f"  下载文件: {file_pattern}")
            hf_hub_download(
                repo_id=model_name,
                filename=file_pattern,
                local_dir=local_dir,
                local_dir_use_symlinks=False,
                force_download=force_download,
                resume_download=True
            )
        
        print(f"✓ 模型 {model_name} 下载完成")
        return True
    except Exception as e:
        print(f"✗ 模型 {model_name} 下载失败: {e}")
        return False


def download_model(model_config, force_download=False):
    """下载单个模型"""
    model_name = model_config["model_name"]
    local_dir = model_config["local_dir"]
    file_patterns = model_config["file_patterns"]
    
    # 尝试使用 snapshot_download 下载整个模型
    success = download_model_with_snapshot(model_name, local_dir, force_download)
    
    # 如果失败，尝试使用 hf_hub_download 下载特定文件
    if not success:
        print("  尝试使用 hf_hub_download 下载特定文件...")
        success = download_model_with_hf_hub(model_name, local_dir, file_patterns, force_download)
    
    return success


def main(args):
    """主函数"""
    print("=== MSearch 模型下载脚本 ===")
    print("正在准备下载模型...")
    
    # 设置镜像地址
    set_hf_mirror()
    
    # 下载指定模型或所有模型
    all_success = True
    
    if args.model:
        # 下载指定模型
        if args.model in MODELS_CONFIG:
            model_config = MODELS_CONFIG[args.model]
            print(f"\n--- 下载 {args.model} 模型 ---")
            if not download_model(model_config, args.force):
                all_success = False
        else:
            print(f"✗ 未知模型类型: {args.model}")
            print(f"  可用模型类型: {list(MODELS_CONFIG.keys())}")
            return 1
    else:
        # 下载所有模型
        for model_type, model_config in MODELS_CONFIG.items():
            print(f"\n--- 下载 {model_type} 模型 ---")
            if not download_model(model_config, args.force):
                all_success = False
    
    print("\n=== 下载完成 ===")
    if all_success:
        print("✓ 所有模型下载成功!")
        print("\n模型保存位置:")
        for model_type, model_config in MODELS_CONFIG.items():
            print(f"  {model_type}: {model_config['local_dir']}")
        return 0
    else:
        print("✗ 部分模型下载失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MSearch 模型下载脚本")
    parser.add_argument("--force", action="store_true", help="强制重新下载所有模型")
    parser.add_argument("--model", type=str, help="指定要下载的模型类型 (text_embedding, image_embedding, audio_embedding)")
    args = parser.parse_args()
    
    sys.exit(main(args))
