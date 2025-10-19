#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实模型测试脚本
使用offline目录中的模型进行测试
"""

import sys
import os
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# 设置环境变量
os.environ["HF_HOME"] = str(PROJECT_ROOT / "offline" / "models")
os.environ["TRANSFORMERS_CACHE"] = str(PROJECT_ROOT / "offline" / "models")

print(f"项目根目录: {PROJECT_ROOT}")
print(f"模型目录: {PROJECT_ROOT / 'offline' / 'models'}")

# 测试模型加载
try:
    print("\n=== 测试CLIP模型加载 ===")
    from transformers import CLIPModel, CLIPProcessor
    
    clip_path = PROJECT_ROOT / "offline" / "models" / "clip-vit-base-patch32"
    print(f"CLIP模型路径: {clip_path}")
    print(f"CLIP模型路径存在: {clip_path.exists()}")
    
    if clip_path.exists():
        print("正在加载CLIP模型...")
        clip_model = CLIPModel.from_pretrained(str(clip_path), local_files_only=True)
        clip_processor = CLIPProcessor.from_pretrained(str(clip_path), local_files_only=True)
        print("✓ CLIP模型加载成功")
        print(f"  模型类型: {type(clip_model)}")
        print(f"  处理器类型: {type(clip_processor)}")
    else:
        print("✗ CLIP模型路径不存在")
        
except Exception as e:
    print(f"✗ CLIP模型加载失败: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n=== 测试CLAP模型加载 ===")
    from transformers import CLAPModel, CLAPProcessor
    
    clap_path = PROJECT_ROOT / "offline" / "models" / "clap-htsat-fused"
    print(f"CLAP模型路径: {clap_path}")
    print(f"CLAP模型路径存在: {clap_path.exists()}")
    
    if clap_path.exists():
        print("正在加载CLAP模型...")
        clap_model = CLAPModel.from_pretrained(str(clap_path), local_files_only=True)
        clap_processor = CLAPProcessor.from_pretrained(str(clap_path), local_files_only=True)
        print("✓ CLAP模型加载成功")
        print(f"  模型类型: {type(clap_model)}")
        print(f"  处理器类型: {type(clap_processor)}")
    else:
        print("✗ CLAP模型路径不存在")
        
except Exception as e:
    print(f"✗ CLAP模型加载失败: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n=== 测试Whisper模型加载 ===")
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    
    whisper_path = PROJECT_ROOT / "offline" / "models" / "whisper-base"
    print(f"Whisper模型路径: {whisper_path}")
    print(f"Whisper模型路径存在: {whisper_path.exists()}")
    
    if whisper_path.exists():
        print("正在加载Whisper模型...")
        whisper_model = WhisperForConditionalGeneration.from_pretrained(str(whisper_path), local_files_only=True)
        whisper_processor = WhisperProcessor.from_pretrained(str(whisper_path), local_files_only=True)
        print("✓ Whisper模型加载成功")
        print(f"  模型类型: {type(whisper_model)}")
        print(f"  处理器类型: {type(whisper_processor)}")
    else:
        print("✗ Whisper模型路径不存在")
        
except Exception as e:
    print(f"✗ Whisper模型加载失败: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 模型测试完成 ===")