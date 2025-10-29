#!/usr/bin/env python3
"""
CLAP模型诊断脚本
专门检查CLAP模型文件的问题
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

def check_clap_model_specific():
    """专门检查CLAP模型的问题"""
    print("=== 专门检查CLAP模型 ===")
    
    clap_dir = "./data/models/clap"
    if not os.path.exists(clap_dir):
        print("✗ CLAP模型目录不存在")
        return False
    
    print(f"✓ CLAP模型目录存在: {clap_dir}")
    
    # 检查关键文件
    files_to_check = [
        "config.json",
        "pytorch_model.bin", 
        "model.safetensors",
        "preprocessor_config.json",
        "tokenizer.json",
        "tokenizer_config.json"
    ]
    
    for file_name in files_to_check:
        file_path = os.path.join(clap_dir, file_name)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"  ✓ {file_name} 存在 ({file_size:,} bytes)")
            
            # 检查文件是否为空
            if file_size == 0:
                print(f"    ⚠ 警告: {file_name} 文件大小为0")
        else:
            print(f"  ⚠ {file_name} 不存在")
    
    # 检查配置文件
    config_path = os.path.join(clap_dir, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"  ✓ config.json 可解析")
            print(f"    模型类型: {config.get('model_type', 'unknown')}")
            print(f"    架构: {config.get('architectures', ['unknown'])[0]}")
            print(f"    隐藏层大小: {config.get('hidden_size', 'unknown')}")
        except Exception as e:
            print(f"  ✗ config.json 解析失败: {e}")
    
    # 检查preprocessor_config.json
    preprocessor_path = os.path.join(clap_dir, "preprocessor_config.json")
    if os.path.exists(preprocessor_path):
        try:
            with open(preprocessor_path, 'r', encoding='utf-8') as f:
                preprocessor_config = json.load(f)
            print(f"  ✓ preprocessor_config.json 可解析")
            print(f"    特征提取器类型: {preprocessor_config.get('feature_extractor_type', 'unknown')}")
        except Exception as e:
            print(f"  ✗ preprocessor_config.json 解析失败: {e}")
    
    return True

def test_clap_model_loading():
    """测试CLAP模型加载"""
    print("\n=== 测试CLAP模型加载 ===")
    
    try:
        from infinity_emb import EngineArgs, AsyncEngineArray
        
        clap_path = os.path.abspath("./data/models/clap")
        if os.path.exists(clap_path):
            print(f"尝试加载CLAP模型: {clap_path}")
            
            # 使用简单的EngineArgs配置
            engine_args = EngineArgs(
                model_name_or_path=clap_path,
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
            print("✗ CLAP模型路径不存在")
            return False
            
    except Exception as e:
        print(f"✗ CLAP模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_clap_with_sentence_transformers():
    """使用sentence-transformers测试CLAP模型"""
    print("\n=== 使用sentence-transformers测试CLAP模型 ===")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        clap_path = os.path.abspath("./data/models/clap")
        if os.path.exists(clap_path):
            print(f"尝试使用sentence-transformers加载CLAP模型: {clap_path}")
            
            # 尝试加载模型
            model = SentenceTransformer(clap_path)
            print("✓ sentence-transformers加载成功")
            
            # 测试编码
            embeddings = model.encode(["测试文本"])
            print(f"✓ 编码成功，向量形状: {embeddings.shape}")
            
            return True
        else:
            print("✗ CLAP模型路径不存在")
            return False
            
    except Exception as e:
        print(f"✗ sentence-transformers加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始CLAP模型诊断...")
    
    # 检查CLAP模型文件
    if not check_clap_model_specific():
        print("❌ CLAP模型文件检查失败")
        return
    
    # 测试CLAP模型加载
    if not test_clap_model_loading():
        print("❌ CLAP模型加载失败")
        
        # 尝试使用sentence-transformers
        print("\n尝试使用sentence-transformers作为备选方案...")
        if test_clap_with_sentence_transformers():
            print("✅ sentence-transformers可以加载CLAP模型")
        else:
            print("❌ sentence-transformers也无法加载CLAP模型")
    else:
        print("✅ CLAP模型加载成功")
    
    print("\n诊断完成")

if __name__ == "__main__":
    main()