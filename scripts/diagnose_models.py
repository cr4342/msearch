#!/usr/bin/env python3
"""
模型文件完整性诊断脚本
检查模型文件是否完整且可加载
"""

import os
import sys
import json
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_model_files(model_dir, model_name):
    """检查模型文件完整性"""
    print(f"\n=== 检查 {model_name} 模型文件 ===")
    
    if not os.path.exists(model_dir):
        print(f"✗ {model_name} 模型目录不存在: {model_dir}")
        return False
    
    print(f"✓ {model_name} 模型目录存在: {model_dir}")
    
    # 检查关键文件
    required_files = {
        "clip": ["config.json", "pytorch_model.bin", "preprocessor_config.json", "tokenizer.json"],
        "clap": ["config.json", "pytorch_model.bin", "preprocessor_config.json", "tokenizer.json"],
        "whisper": ["config.json", "pytorch_model.bin", "tokenizer.json", "generation_config.json"]
    }
    
    missing_files = []
    for file_name in required_files.get(model_name, []):
        file_path = os.path.join(model_dir, file_name)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"  ✓ {file_name} 存在 ({file_size:,} bytes)")
            
            # 检查文件是否为空
            if file_size == 0:
                print(f"    ⚠ 警告: {file_name} 文件大小为0")
        else:
            print(f"  ✗ {file_name} 不存在")
            missing_files.append(file_name)
    
    # 检查配置文件是否可解析
    config_path = os.path.join(model_dir, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"  ✓ config.json 可解析，模型类型: {config.get('model_type', 'unknown')}")
        except Exception as e:
            print(f"  ✗ config.json 解析失败: {e}")
    
    if missing_files:
        print(f"✗ {model_name} 模型缺少关键文件: {missing_files}")
        return False
    else:
        print(f"✓ {model_name} 模型文件完整")
        return True

def test_model_loading_with_simple_config():
    """使用简单配置测试模型加载"""
    print("\n=== 测试模型加载 ===")
    
    try:
        from infinity_emb import EngineArgs, AsyncEngineArray
        
        # 创建简单的配置
        config = {
            'models_storage': {
                'models_dir': './data/models',
                'offline_mode': True,
                'force_local': True
            },
            'models': {
                'clip': {
                    'model_name': './data/models/clip',
                    'local_path': './data/models/clip',
                    'device': 'cpu',
                    'batch_size': 1
                }
            }
        }
        
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
            
            # 尝试使用AsyncEngineArray.from_args方法
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

def check_infinity_version():
    """检查infinity_emb版本"""
    print("\n=== 检查infinity_emb版本 ===")
    
    try:
        import infinity_emb
        print(f"✓ infinity_emb版本: {infinity_emb.__version__}")
        
        # 检查可用方法
        from infinity_emb import EngineArgs
        methods = [x for x in dir(EngineArgs) if not x.startswith('_')]
        print(f"✓ EngineArgs可用方法: {len(methods)}个")
        
        return True
    except Exception as e:
        print(f"✗ 检查infinity_emb版本失败: {e}")
        return False

def main():
    """主函数"""
    print("开始模型文件完整性诊断...")
    
    # 检查infinity_emb版本
    if not check_infinity_version():
        print("❌ infinity_emb版本检查失败")
        return
    
    # 检查模型文件
    models_to_check = [
        ("clip", "./data/models/clip"),
        ("clap", "./data/models/clap"),
        ("whisper", "./data/models/whisper")
    ]
    
    all_models_ok = True
    for model_name, model_path in models_to_check:
        if not check_model_files(model_path, model_name):
            all_models_ok = False
    
    # 测试模型加载
    if all_models_ok:
        print("\n所有模型文件检查通过，开始测试模型加载...")
        if test_model_loading_with_simple_config():
            print("✅ 模型加载测试成功！")
        else:
            print("❌ 模型加载测试失败")
    else:
        print("❌ 模型文件检查失败，无法进行加载测试")
    
    print("\n诊断完成")

if __name__ == "__main__":
    main()