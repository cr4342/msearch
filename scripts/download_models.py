import os
import sys
import time
from pathlib import Path
from transformers import (
    CLIPModel, CLIPProcessor, 
    ClapModel, ClapProcessor, 
    WhisperForConditionalGeneration, WhisperProcessor,
    AutoModel, AutoProcessor, AutoTokenizer
)
import torch

def download_model(repo_id, local_path, components):
    """下载单个模型及其组件"""
    print(f"\n[INFO] 下载模型: {repo_id} 到 {local_path}")
    
    # 确保输出目录存在
    os.makedirs(local_path, exist_ok=True)
    
    # 下载模型组件
    success = True
    
    if 'model' in components:
        try:
            print("  - 下载模型组件...")
            model = AutoModel.from_pretrained(repo_id, cache_dir=local_path, trust_remote_code=True)
            model.save_pretrained(local_path)
            print("  ✓ 模型组件下载完成")
        except Exception as e:
            print(f"  ✗ 模型组件下载失败: {str(e)}")
            success = False
    
    if 'processor' in components:
        try:
            print("  - 下载处理器组件...")
            processor = AutoProcessor.from_pretrained(repo_id, cache_dir=local_path, trust_remote_code=True)
            processor.save_pretrained(local_path)
            print("  ✓ 处理器组件下载完成")
        except Exception as e:
            print(f"  ✗ 处理器组件下载失败: {str(e)}")
            success = False
    
    return success

def download_models(models_dir):
    """下载所有必要的模型"""
    print(f"[INFO] 模型下载目录: {models_dir}")
    
    # 模型列表
    models = [
        {
            'name': 'clip',
            'repo_id': 'openai/clip-vit-base-patch32',
            'local_path': os.path.join(models_dir, 'clip-vit-base-patch32'),
            'components': ['model', 'processor']
        },
        {
            'name': 'clap',
            'repo_id': 'laion/clap-htsat-unfused',
            'local_path': os.path.join(models_dir, 'clap-htsat-unfused'),
            'components': ['model', 'processor']
        },
        {
            'name': 'whisper',
            'repo_id': 'openai/whisper-base',
            'local_path': os.path.join(models_dir, 'whisper-base'),
            'components': ['model', 'processor']
        }
    ]
    
    # 下载每个模型
    success_count = 0
    total_count = len(models)
    
    for i, model_info in enumerate(models, 1):
        print(f"\n[{i}/{total_count}] 开始下载 {model_info['name']}...")
        
        # 检查是否已存在
        if os.path.exists(os.path.join(model_info['local_path'], 'config.json')):
            print(f"[INFO] {model_info['name']} 模型已存在，跳过下载")
            success_count += 1
            continue
        
        # 尝试下载，最多3次重试
        max_retries = 3
        for retry in range(max_retries):
            if download_model(
                model_info['repo_id'],
                model_info['local_path'],
                model_info['components']
            ):
                success_count += 1
                break
            else:
                if retry < max_retries - 1:
                    wait_time = (retry + 1) * 5
                    print(f"[WARNING] 下载失败，{wait_time}秒后重试 ({retry + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"[ERROR] {model_info['name']} 模型下载失败，达到最大重试次数")
    
    print(f"\n[INFO] 模型下载完成: {success_count}/{total_count} 个模型成功")
    
    return success_count == total_count

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 如果没有提供参数，使用默认的模型目录
        default_models_dir = os.path.join(Path(__file__).parent.parent, "data", "models")
        print(f"[INFO] 未提供模型目录参数，使用默认目录: {default_models_dir}")
        models_dir = default_models_dir
    else:
        models_dir = sys.argv[1]
    
    # 确保默认模型目录存在
    os.makedirs(models_dir, exist_ok=True)
    
    success = download_models(models_dir)
    sys.exit(0 if success else 1)