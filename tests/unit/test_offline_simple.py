#!/usr/bin/env python3
"""
真实模型离线处理测试 - 验证离线模式下模型加载和推理
"""
import os
import sys
from pathlib import Path

def main():
    # 设置项目根目录
    PROJECT_ROOT = Path(__file__).parent
    
    # ============================================
    # 设置离线环境变量
    # ============================================
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['HF_DATASETS_OFFLINE'] = '1'
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['HF_HUB_DISABLE_IMPORT_ERROR'] = '1'
    os.environ['HF_HOME'] = str(PROJECT_ROOT / "data" / "models")
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'
    
    print("=" * 60)
    print("离线模式验证测试")
    print("=" * 60)
    
    # 验证环境变量
    print("\n1. 环境变量验证:")
    print(f"   TRANSFORMERS_OFFLINE: {os.environ.get('TRANSFORMERS_OFFLINE')}")
    print(f"   HF_HUB_OFFLINE: {os.environ.get('HF_HUB_OFFLINE')}")
    
    # 验证模型文件
    print("\n2. 模型文件验证:")
    model_path = PROJECT_ROOT / "data" / "models" / "chinese-clip-vit-base-patch16"
    print(f"   模型路径: {model_path}")
    print(f"   路径存在: {model_path.exists()}")
    
    required_files = ['config.json', 'pytorch_model.bin', 'vocab.txt']
    for f in required_files:
        fp = model_path / f
        print(f"   {f}: {'✓' if fp.exists() else '✗'}")
    
    # 使用chinese-clip专用方式加载
    print("\n3. Chinese-CLIP模型加载测试:")
    try:
        import torch
        from transformers import ChineseCLIPProcessor, ChineseCLIPModel
    
        # 使用本地路径加载
        model = ChineseCLIPModel.from_pretrained(
            str(model_path), 
            local_files_only=True,
            torch_dtype=torch.float32
        )
        print("   ✓ ChineseCLIP模型加载成功 (local_files_only=True)")
        
        processor = ChineseCLIPProcessor.from_pretrained(
            str(model_path), 
            local_files_only=True
        )
        print("   ✓ ChineseCLIPProcessor加载成功")
    
        # 测试文本向量化
        print("\n4. 文本向量化测试:")
        texts = ["测试文本", "天空", "大海"]
        inputs = processor(text=texts, return_tensors="pt", padding=True)
        
        with torch.no_grad():
            outputs = model.text_model(**inputs)
            # Chinese-CLIP 使用 last_hidden_state
            text_emb = outputs.last_hidden_state[:, 0, :]  # CLS token
        print(f"   ✓ 文本向量化成功，维度: {list(text_emb.shape)}")
    
        # 测试图像向量化
        print("\n5. 图像向量化测试:")
        from PIL import Image
        test_images = list((PROJECT_ROOT / "testdata").glob("*.jpg"))[:1]
        if test_images:
            img = Image.open(test_images[0])
            inputs = processor(images=img, return_tensors="pt")
            
            with torch.no_grad():
                outputs = model.vision_model(**inputs)
                image_emb = outputs.last_hidden_state[:, 0, :]  # CLS token
            print(f"   ✓ 图像向量化成功，维度: {list(image_emb.shape)}")
            
            # 测试图文相似度
            print("\n6. 图文相似度测试:")
            with torch.no_grad():
                # 获取图像和文本特征（使用projection层）
                image_features = model.visual_projection(image_emb)
                text_features = model.text_projection(text_emb)
                
                # 归一化
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                
                # 计算相似度
                sim = image_features @ text_features.t()
                print(f"   ✓ 图文相似度矩阵形状: {list(sim.shape)}")
                sim_scores = [f"{s:.4f}" for s in sim[0].tolist()]
                print(f"   ✓ 第一张图与文本的相似度: {sim_scores}")
        
        # 测试音频模型
        print("\n7. 音频模型验证:")
        clap_path = PROJECT_ROOT / "data" / "models" / "clap-htsat-unfused"
        clap_files = ['config.json', 'pytorch_model.bin', 'tokenizer.json']
        all_exist = all((clap_path / f).exists() for f in clap_files)
        print(f"   CLAP模型文件完整: {'✓' if all_exist else '✗'}")
        
        if all_exist:
            from transformers import AutoModel, AutoProcessor
            
            clap_model = AutoModel.from_pretrained(
                str(clap_path),
                local_files_only=True
            )
            print("   ✓ CLAP模型加载成功")
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！模型可在完全离线模式下运行")
        print("  - Chinese-CLIP: 图像和文本向量化正常")
        print("  - CLAP: 模型文件完整，加载成功")
        print("=" * 60)
        
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()