#!/usr/bin/env python3
"""
简单的PyTorch测试脚本，用于验证PyTorch是否能正确导入和使用
"""

import sys
import os

# 添加虚拟环境的site-packages到Python路径
venv_path = os.path.join(os.path.dirname(__file__), 'venv')
site_packages = os.path.join(venv_path, 'Lib', 'site-packages')
if site_packages not in sys.path:
    sys.path.insert(0, site_packages)

print(f"Python版本: {sys.version}")
print(f"虚拟环境site-packages: {site_packages}")

# 尝试导入PyTorch
try:
    import torch
    print(f"\n✅ PyTorch导入成功！")
    print(f"   版本: {torch.__version__}")
    
    # 检查CUDA可用性
    if torch.cuda.is_available():
        print(f"   CUDA可用: {torch.cuda.is_available()}")
        print(f"   CUDA版本: {torch.version.cuda}")
        print(f"   GPU设备: {torch.cuda.get_device_name(0)}")
    else:
        print(f"   CUDA可用: {torch.cuda.is_available()}")
    
    # 尝试创建一个简单的张量并进行运算
    x = torch.tensor([1.0, 2.0, 3.0])
    y = x * 2
    print(f"   张量运算测试: {x} * 2 = {y}")
    
    print("\n✅ 所有测试通过！PyTorch可以正常使用。")
    sys.exit(0)
except Exception as e:
    print(f"\n❌ PyTorch导入失败: {e}")
    print(f"   错误类型: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
