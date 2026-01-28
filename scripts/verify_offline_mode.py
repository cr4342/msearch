#!/usr/bin/env python3
"""
离线模式验证脚本

验证项目是否可以在完全离线的情况下运行，检查：
1. 环境变量是否正确设置
2. 模型文件是否完整
3. 配置文件是否正确
"""

import os
import sys
from pathlib import Path
import yaml

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_environment_variables():
    """检查离线模式环境变量"""
    print("=" * 60)
    print("1. 检查离线模式环境变量")
    print("=" * 60)
    
    required_vars = {
        'TRANSFORMERS_OFFLINE': '1',
        'HF_DATASETS_OFFLINE': '1',
        'HF_HUB_OFFLINE': '1',
        'HF_HUB_DISABLE_TELEMETRY': '1',
    }
    
    optional_vars = {
        'HF_HOME': None,
        'HUGGINGFACE_HUB_CACHE': None,
        'NO_PROXY': '*',
    }
    
    all_ok = True
    
    for var, expected in required_vars.items():
        value = os.environ.get(var)
        status = "✓" if value == expected else "✗"
        print(f"{status} {var}: {value} (期望: {expected})")
        if value != expected:
            all_ok = False
    
    for var, expected in optional_vars.items():
        value = os.environ.get(var)
        if expected is None:
            status = "✓" if value else "⚠"
            print(f"{status} {var}: {value or '未设置'}")
        else:
            status = "✓" if value == expected else "⚠"
            print(f"{status} {var}: {value} (期望: {expected})")
    
    print()
    return all_ok

def check_config_file():
    """检查配置文件"""
    print("=" * 60)
    print("2. 检查配置文件")
    print("=" * 60)
    
    config_path = PROJECT_ROOT / "config" / "config.yml"
    
    if not config_path.exists():
        print(f"✗ 配置文件不存在: {config_path}")
        return False
    
    print(f"✓ 配置文件存在: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 检查离线模式配置
        offline_enabled = config.get('models', {}).get('offline_mode', {}).get('enabled', False)
        status = "✓" if offline_enabled else "✗"
        print(f"{status} 离线模式启用: {offline_enabled}")
        
        # 检查模型缓存目录
        model_cache_dir = config.get('models', {}).get('offline_mode', {}).get('model_cache_dir')
        if model_cache_dir:
            cache_path = PROJECT_ROOT / model_cache_dir
            status = "✓" if cache_path.exists() else "✗"
            print(f"{status} 模型缓存目录: {cache_path} ({'存在' if cache_path.exists() else '不存在'})")
        
        # 检查活跃模型
        active_models = config.get('models', {}).get('active_models', [])
        print(f"✓ 活跃模型: {active_models}")
        
        # 检查可用模型
        available_models = config.get('models', {}).get('available_models', {})
        print(f"✓ 可用模型: {list(available_models.keys())}")
        
        return True
    except Exception as e:
        print(f"✗ 配置文件解析失败: {e}")
        return False

def check_model_files():
    """检查模型文件完整性"""
    print("=" * 60)
    print("3. 检查模型文件完整性")
    print("=" * 60)
    
    config_path = PROJECT_ROOT / "config" / "config.yml"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        available_models = config.get('models', {}).get('available_models', {})
        all_ok = True
        
        for model_type, model_config in available_models.items():
            print(f"\n模型: {model_type}")
            print("-" * 40)
            
            local_path = model_config.get('local_path')
            if not local_path:
                print(f"✗ 未配置本地路径")
                all_ok = False
                continue
            
            model_path = PROJECT_ROOT / local_path
            status = "✓" if model_path.exists() else "✗"
            print(f"{status} 模型路径: {model_path}")
            
            if not model_path.exists():
                all_ok = False
                continue
            
            # 检查必需文件
            required_files = [
                "config.json",
                "tokenizer.json",
                "tokenizer_config.json",
            ]
            
            # 检查模型权重文件
            weight_files = ["pytorch_model.bin", "model.safetensors", "adapter_model.safetensors"]
            has_weight_file = any((model_path / wf).exists() for wf in weight_files)
            
            for file in required_files:
                file_path = model_path / file
                status = "✓" if file_path.exists() else "✗"
                print(f"{status} {file}")
                if not file_path.exists():
                    all_ok = False
            
            weight_status = "✓" if has_weight_file else "✗"
            print(f"{weight_status} 模型权重文件: {'存在' if has_weight_file else '不存在'}")
            if not has_weight_file:
                all_ok = False
        
        print()
        return all_ok
    except Exception as e:
        print(f"✗ 检查模型文件失败: {e}")
        return False

def check_imports():
    """检查必要的导入"""
    print("=" * 60)
    print("4. 检查必要的导入")
    print("=" * 60)
    
    all_ok = True
    
    try:
        import infinity_emb
        print(f"✓ infinity_emb: {infinity_emb.__version__}")
    except ImportError as e:
        print(f"✗ infinity_emb: {e}")
        all_ok = False
    
    try:
        import transformers
        print(f"✓ transformers: {transformers.__version__}")
    except ImportError as e:
        print(f"✗ transformers: {e}")
        all_ok = False
    
    try:
        import torch
        print(f"✓ torch: {torch.__version__}")
    except ImportError as e:
        print(f"✗ torch: {e}")
        all_ok = False
    
    print()
    return all_ok

def main():
    """主函数"""
    print("\n")
    print("=" * 60)
    print("离线模式验证工具")
    print("=" * 60)
    print()
    
    # 检查环境变量
    env_ok = check_environment_variables()
    
    # 检查配置文件
    config_ok = check_config_file()
    
    # 检查模型文件
    model_ok = check_model_files()
    
    # 检查导入
    import_ok = check_imports()
    
    # 总结
    print("=" * 60)
    print("验证总结")
    print("=" * 60)
    print(f"环境变量: {'✓ 通过' if env_ok else '✗ 失败'}")
    print(f"配置文件: {'✓ 通过' if config_ok else '✗ 失败'}")
    print(f"模型文件: {'✓ 通过' if model_ok else '✗ 失败'}")
    print(f"依赖导入: {'✓ 通过' if import_ok else '✗ 失败'}")
    print()
    
    all_ok = env_ok and config_ok and model_ok and import_ok
    
    if all_ok:
        print("✓ 所有检查通过！项目可以在完全离线模式下运行。")
        return 0
    else:
        print("✗ 部分检查失败，请参考上述信息进行修复。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
