#!/usr/bin/env python3
"""
简单模型加载测试脚本
"""
import os
import sys
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_model_paths():
    """测试模型路径是否存在"""
    print("=== 测试模型路径 ===")
    
    model_paths = [
        ("CLIP", "./data/models/clip"),
        ("CLAP", "./data/models/clap"),
        ("Whisper", "./data/models/whisper")
    ]
    
    for model_name, path in model_paths:
        abs_path = os.path.abspath(path)
        exists = os.path.exists(abs_path)
        print(f"{model_name}: {path}")
        print(f"  绝对路径: {abs_path}")
        print(f"  存在: {exists}")
        
        if exists:
            # 检查关键文件
            key_files = ["config.json", "pytorch_model.bin", "model.safetensors"]
            for file in key_files:
                file_path = os.path.join(abs_path, file)
                file_exists = os.path.exists(file_path)
                print(f"  {file}: {file_exists}")
        print()

def test_infinity_import():
    """测试infinity_emb导入"""
    print("=== 测试infinity_emb导入 ===")
    try:
        from infinity_emb import AsyncEngineArray, EngineArgs
        print("✓ infinity_emb导入成功")
        return True
    except ImportError as e:
        print(f"✗ infinity_emb导入失败: {e}")
        return False

def test_simple_model_loading():
    """测试简单模型加载"""
    print("=== 测试简单模型加载 ===")
    
    try:
        from infinity_emb import EngineArgs
        
        # 测试CLIP模型加载
        clip_path = os.path.abspath("./data/models/clip")
        if os.path.exists(clip_path):
            print(f"尝试加载CLIP模型: {clip_path}")
            
            # 使用简单的EngineArgs配置
            engine_args = EngineArgs(
                model_name_or_path=clip_path,
                device="cpu",
                model_warmup=False,  # 不预热以加快测试
                batch_size=1,
                dtype='float32'
            )
            print("✓ EngineArgs创建成功")
            print(f"EngineArgs属性: {engine_args.to_dict()}")
            
            # 尝试使用AsyncEngineArray.from_args方法
            from infinity_emb import AsyncEngineArray
            
            print("尝试使用AsyncEngineArray.from_args方法")
            engine_array = AsyncEngineArray.from_args([engine_args])
            print("✓ AsyncEngineArray.from_args创建成功")
            
            return True
            
        else:
            print("✗ CLIP模型路径不存在")
            return False
            
    except Exception as e:
        print(f"✗ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始模型加载测试...\n")
    
    # 测试1: 模型路径
    test_model_paths()
    
    # 测试2: infinity_emb导入
    if not test_infinity_import():
        print("infinity_emb导入失败，无法继续测试")
        return
    
    # 测试3: 简单模型加载
    test_simple_model_loading()
    
    print("\n测试完成")

if __name__ == "__main__":
    main()