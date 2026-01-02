#!/usr/bin/env python3
"""
测试模型加载和向量生成
验证安装脚本是否成功安装了可用的模型
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_clip_model_loading():
    """测试CLIP模型加载和向量生成"""
    logger.info("测试CLIP模型加载和向量生成...")
    
    try:
        # 检查模型目录是否存在
        models_dir = Path("data/models/clip")
        if not models_dir.exists():
            logger.error(f"CLIP模型目录不存在: {models_dir}")
            return False
        
        # 列出模型目录内容
        model_files = list(models_dir.glob("*"))
        logger.info(f"CLIP模型目录内容: {[f.name for f in model_files]}")
        
        # 检查必要的模型文件
        required_files = ["config.json", "pytorch_model.bin"]
        for file in required_files:
            if not (models_dir / file).exists():
                logger.error(f"CLIP模型缺少必要文件: {file}")
                return False
        
        # 尝试加载模型
        logger.info("加载CLIP模型...")
        from transformers import CLIPModel, CLIPProcessor
        import torch
        
        # 加载模型
        model = CLIPModel.from_pretrained(str(models_dir), local_files_only=True)
        processor = CLIPProcessor.from_pretrained(str(models_dir), local_files_only=True)
        
        logger.info("CLIP模型加载成功！")
        
        # 使用GPU或CPU
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        logger.info(f"使用设备: {device}")
        
        # 生成测试文本向量
        logger.info("生成文本向量测试...")
        text = "a photo of a cat"
        inputs = processor(text=text, return_tensors="pt").to(device)
        text_features = model.get_text_features(**inputs)
        
        logger.info(f"文本向量生成成功，维度: {text_features.shape}")
        logger.info(f"向量示例: {text_features[0][:5]}")
        
        # 生成测试图像向量
        logger.info("生成图像向量测试...")
        
        # 创建一个简单的测试图像
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (200, 200), color=(100, 150, 50))
        d = ImageDraw.Draw(img)
        d.text((10,10), "Test Image", fill=(255,255,255))
        
        # 处理图像
        image_inputs = processor(images=img, return_tensors="pt").to(device)
        image_features = model.get_image_features(**image_inputs)
        
        logger.info(f"图像向量生成成功，维度: {image_features.shape}")
        logger.info(f"向量示例: {image_features[0][:5]}")
        
        # 验证向量不是全零
        if torch.all(text_features == 0):
            logger.error("文本向量全部为零，模型可能存在问题")
            return False
        
        if torch.all(image_features == 0):
            logger.error("图像向量全部为零，模型可能存在问题")
            return False
        
        logger.info("✅ CLIP模型测试成功完成！")
        logger.info("模型可以正常生成向量，安装脚本工作正常。")
        return True
        
    except Exception as e:
        logger.error(f"❌ CLIP模型测试失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return False

def test_embedding_engine():
    """测试向量化引擎"""
    logger.info("测试向量化引擎...")
    
    try:
        # 导入向量化引擎
        from src.common.embedding.embedding_engine import get_embedding_engine
        
        # 获取引擎实例
        embedding_engine = get_embedding_engine()
        
        logger.info(f"向量化引擎初始化成功，可用模型: {embedding_engine.get_available_models()}")
        
        # 检查引擎状态
        logger.info("检查引擎健康状态...")
        health_status = embedding_engine.health_check()
        logger.info(f"引擎健康状态: {health_status}")
        
        logger.info("✅ 向量化引擎测试成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 向量化引擎测试失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("开始安装验证测试...")
    
    # 运行测试
    clip_test = test_clip_model_loading()
    embedding_test = test_embedding_engine()
    
    # 汇总结果
    logger.info("\n=== 测试结果汇总 ===")
    logger.info(f"CLIP模型测试: {'通过' if clip_test else '失败'}")
    logger.info(f"向量化引擎测试: {'通过' if embedding_test else '失败'}")
    
    if clip_test and embedding_test:
        logger.info("✅ 所有测试通过！安装脚本工作正常，模型可以正常使用。")
        sys.exit(0)
    else:
        logger.error("❌ 部分测试失败！")
        sys.exit(1)