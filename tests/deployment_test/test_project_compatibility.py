#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyTorch 2.2.0 与项目依赖兼容性测试脚本
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

def test_project_compatibility():
    """测试PyTorch 2.2.0与项目依赖的兼容性"""
    print("=" * 60)
    print("PyTorch 2.2.0 与项目依赖兼容性测试")
    print("=" * 60)
    
    # 1. 测试PyTorch版本
    try:
        import torch
        print(f"✓ PyTorch版本: {torch.__version__}")
    except Exception as e:
        print(f"✗ PyTorch导入失败: {e}")
        return False
    
    # 2. 测试transformers库
    try:
        import transformers
        print(f"✓ Transformers版本: {transformers.__version__}")
        
        # 尝试导入CLIPProcessor
        try:
            from transformers import CLIPProcessor
            print("✓ CLIPProcessor导入成功")
        except Exception as e:
            print(f"⚠ CLIPProcessor导入失败: {e}")
    except Exception as e:
        print(f"✗ Transformers导入失败: {e}")
    
    # 3. 测试infinity_emb库
    try:
        import infinity_emb
        print(f"✓ Infinity-emb版本: {infinity_emb.__version__}")
        
        # 尝试导入关键类
        try:
            from infinity_emb import AsyncEngineArray, EngineArgs
            print("✓ Infinity-emb核心类导入成功")
        except Exception as e:
            print(f"⚠ Infinity-emb核心类导入失败: {e}")
            
    except Exception as e:
        print(f"✗ Infinity-emb导入失败: {e}")
    
    # 4. 测试项目中的EmbeddingEngine
    try:
        from src.business.embedding_engine import EmbeddingEngine
        print("✓ 项目EmbeddingEngine导入成功")
        
        # 尝试初始化（使用模拟配置）
        try:
            config = {
                'models': {
                    'clip': {
                        'model_name': 'openai/clip-vit-base-patch32',
                        'device': 'cpu'
                    }
                }
            }
            engine = EmbeddingEngine(config)
            print("✓ EmbeddingEngine初始化成功")
        except Exception as e:
            print(f"⚠ EmbeddingEngine初始化失败: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"✗ 项目EmbeddingEngine导入失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. 测试torch.utils._pytree兼容性
    try:
        import torch.utils._pytree as pytree
        
        # 检查关键函数是否存在
        functions_to_check = [
            'register_pytree_node',
            'tree_map',
            'tree_flatten',
            'tree_unflatten'
        ]
        
        for func_name in functions_to_check:
            if hasattr(pytree, func_name):
                print(f"✓ {func_name}函数存在")
            else:
                print(f"✗ {func_name}函数缺失")
                
    except Exception as e:
        print(f"✗ PyTree测试失败: {e}")
    
    print("=" * 60)
    print("兼容性测试完成")
    return True

if __name__ == "__main__":
    try:
        success = test_project_compatibility()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"测试过程中发生未预期错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)