#!/usr/bin/env python3
"""
修复CLAP模型下载脚本
使用多种方法确保CLAP模型正确下载
"""

import os
import sys
import time
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def download_clap_model():
    """下载CLAP模型"""
    print("🔧 开始修复CLAP模型...")
    
    clap_model_dir = project_root / "offline" / "models" / "clap-htsat-fused"
    
    # 清理现有目录
    if clap_model_dir.exists():
        shutil.rmtree(clap_model_dir)
    
    clap_model_dir.mkdir(parents=True, exist_ok=True)
    
    # 方法1: 使用transformers直接下载
    try:
        print("方法1: 使用transformers下载...")
        from transformers import ClapModel, ClapProcessor
        
        # 设置环境变量
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        
        print("  下载CLAP模型...")
        model = ClapModel.from_pretrained("laion/clap-htsat-fused")
        print("  下载CLAP处理器...")
        processor = ClapProcessor.from_pretrained("laion/clap-htsat-fused")
        
        print("  保存模型到本地...")
        model.save_pretrained(str(clap_model_dir))
        processor.save_pretrained(str(clap_model_dir))
        
        print("✅ 方法1成功：CLAP模型下载完成")
        return True
        
    except Exception as e:
        print(f"❌ 方法1失败: {e}")
    
    # 方法2: 使用huggingface_hub下载
    try:
        print("方法2: 使用huggingface_hub下载...")
        from huggingface_hub import snapshot_download
        
        print("  下载模型快照...")
        snapshot_download(
            repo_id="laion/clap-htsat-fused",
            local_dir=str(clap_model_dir),
            local_dir_use_symlinks=False
        )
        
        print("✅ 方法2成功：CLAP模型下载完成")
        return True
        
    except Exception as e:
        print(f"❌ 方法2失败: {e}")
    
    # 方法3: 使用git clone
    try:
        print("方法3: 使用git clone...")
        import subprocess
        
        # 删除现有目录
        if clap_model_dir.exists():
            shutil.rmtree(clap_model_dir)
        
        cmd = [
            "git", "clone", 
            "https://huggingface.co/laion/clap-htsat-fused",
            str(clap_model_dir)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            # 删除.git目录
            git_dir = clap_model_dir / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir)
            
            print("✅ 方法3成功：CLAP模型下载完成")
            return True
        else:
            print(f"❌ 方法3失败: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 方法3失败: {e}")
    
    print("❌ 所有下载方法都失败了")
    return False

def verify_clap_model():
    """验证CLAP模型"""
    print("🔍 验证CLAP模型...")
    
    clap_model_dir = project_root / "offline" / "models" / "clap-htsat-fused"
    
    if not clap_model_dir.exists():
        print("❌ CLAP模型目录不存在")
        return False
    
    # 检查必要文件
    required_files = [
        "config.json",
        "preprocessor_config.json",
        "tokenizer_config.json"
    ]
    
    model_files = ["model.safetensors", "pytorch_model.bin"]
    
    missing_files = []
    for file_name in required_files:
        if not (clap_model_dir / file_name).exists():
            missing_files.append(file_name)
    
    # 检查模型文件（至少要有一个）
    has_model_file = any((clap_model_dir / f).exists() for f in model_files)
    if not has_model_file:
        missing_files.extend(model_files)
    
    if missing_files:
        print(f"❌ 缺少文件: {missing_files}")
        return False
    
    # 尝试加载模型
    try:
        from transformers import ClapModel, ClapProcessor
        
        print("  加载CLAP模型...")
        model = ClapModel.from_pretrained(str(clap_model_dir))
        print("  加载CLAP处理器...")
        processor = ClapProcessor.from_pretrained(str(clap_model_dir))
        
        print("✅ CLAP模型验证成功")
        return True
        
    except Exception as e:
        print(f"❌ CLAP模型加载失败: {e}")
        return False

def test_clap_model():
    """测试CLAP模型功能"""
    print("🧪 测试CLAP模型功能...")
    
    try:
        from transformers import ClapModel, ClapProcessor
        import torch
        import numpy as np
        
        clap_model_dir = project_root / "offline" / "models" / "clap-htsat-fused"
        
        # 加载模型
        model = ClapModel.from_pretrained(str(clap_model_dir))
        processor = ClapProcessor.from_pretrained(str(clap_model_dir))
        
        # 生成测试音频
        sample_rate = 48000
        duration = 3
        t = np.linspace(0, duration, sample_rate * duration)
        test_audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        
        # 测试文本
        test_texts = ["music", "speech", "noise"]
        
        # 处理输入
        inputs = processor(
            text=test_texts,
            audios=test_audio,
            sampling_rate=sample_rate,
            return_tensors="pt",
            padding=True
        )
        
        # 执行推理
        with torch.no_grad():
            outputs = model(**inputs)
            logits_per_audio = outputs.logits_per_audio
            probs = logits_per_audio.softmax(dim=1)
        
        # 获取结果
        best_match_idx = probs.argmax().item()
        best_match_text = test_texts[best_match_idx]
        best_match_score = probs[0][best_match_idx].item()
        
        print(f"✅ CLAP模型测试成功")
        print(f"   最佳匹配: '{best_match_text}' (得分: {best_match_score:.4f})")
        return True
        
    except Exception as e:
        print(f"❌ CLAP模型测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始CLAP模型修复流程...")
    print("=" * 50)
    
    # 步骤1: 下载模型
    if not download_clap_model():
        print("💥 CLAP模型下载失败，退出")
        return 1
    
    # 步骤2: 验证模型
    if not verify_clap_model():
        print("💥 CLAP模型验证失败，退出")
        return 1
    
    # 步骤3: 测试模型
    if not test_clap_model():
        print("💥 CLAP模型测试失败，退出")
        return 1
    
    print("=" * 50)
    print("🎉 CLAP模型修复完成！")
    print("✅ 模型已下载、验证并测试成功")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())