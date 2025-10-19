#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyTorch 2.2.0 兼容性测试脚本
"""

import sys
import traceback

def test_pytorch():
    """测试PyTorch基本功能"""
    print("=" * 50)
    print("PyTorch 2.2.0 兼容性测试")
    print("=" * 50)
    
    # 1. 导入PyTorch
    try:
        import torch
        print(f"✓ PyTorch版本: {torch.__version__}")
    except Exception as e:
        print(f"✗ PyTorch导入失败: {e}")
        return False
    
    # 2. 检查CUDA可用性
    try:
        cuda_available = torch.cuda.is_available()
        print(f"✓ CUDA可用性: {cuda_available}")
    except Exception as e:
        print(f"✗ CUDA检查失败: {e}")
    
    # 3. 测试基本张量操作
    try:
        x = torch.randn(3, 3)
        y = torch.randn(3, 3)
        z = x + y
        print("✓ 基本张量操作正常")
    except Exception as e:
        print(f"✗ 张量操作失败: {e}")
        return False
    
    # 4. 测试torch.utils._pytree模块
    try:
        from torch.utils._pytree import tree_map
        print("✓ torch.utils._pytree模块正常")
    except Exception as e:
        print(f"✗ torch.utils._pytree模块异常: {e}")
        # 这可能是一个兼容性问题
    
    # 5. 测试与infinity_emb相关的功能
    try:
        # 尝试导入可能有问题的模块
        import torch.utils._pytree as pytree
        # 检查register_pytree_node是否存在
        if hasattr(pytree, 'register_pytree_node'):
            print("✓ register_pytree_node函数存在")
        else:
            print("⚠ register_pytree_node函数不存在（可能是兼容性问题）")
    except Exception as e:
        print(f"✗ PyTree测试失败: {e}")
    
    print("=" * 50)
    print("测试完成")
    return True

if __name__ == "__main__":
    try:
        success = test_pytorch()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"测试过程中发生未预期错误: {e}")
        traceback.print_exc()
        sys.exit(1)