#!/usr/bin/env python3
"""
简化的CLAP模型测试
跳过重新下载，直接测试现有模型
"""

import os
import sys
import json
import time
import logging
import wave
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_clap_model_direct():
    """直接测试CLAP模型"""
    logger.info("🎵 直接测试CLAP模型...")
    
    try:
        # 尝试从在线加载CLAP模型（使用缓存）
        from transformers import ClapModel, ClapProcessor
        import torch
        
        logger.info("从HuggingFace加载CLAP模型...")
        
        # 设置离线模式，使用缓存
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        
        try:
            # 尝试加载本地模型
            clap_model_dir = project_root / "offline" / "models" / "clap-htsat-fused"
            if clap_model_dir.exists() and any(clap_model_dir.iterdir()):
                logger.info("使用本地模型文件...")
                model = ClapModel.from_pretrained(str(clap_model_dir))
                processor = ClapProcessor.from_pretrained(str(clap_model_dir))
            else:
                raise FileNotFoundError("本地模型不存在")
                
        except Exception as e:
            logger.warning(f"本地模型加载失败: {e}")
            logger.info("尝试使用缓存模型...")
            
            # 取消离线模式，尝试使用缓存
            if "TRANSFORMERS_OFFLINE" in os.environ:
                del os.environ["TRANSFORMERS_OFFLINE"]
            
            # 使用模型名称，让transformers自动查找缓存
            model = ClapModel.from_pretrained("laion/clap-htsat-fused", local_files_only=True)
            processor = ClapProcessor.from_pretrained("laion/clap-htsat-fused", local_files_only=True)
        
        logger.info("✅ CLAP模型加载成功")
        
        # 生成测试音频
        sample_rate = 48000  # CLAP使用48kHz
        duration = 3
        t = np.linspace(0, duration, sample_rate * duration)
        
        # 创建不同类型的测试音频
        test_audios = [
            ("pure_tone", np.sin(2 * np.pi * 440 * t).astype(np.float32)),
            ("chord", (np.sin(2 * np.pi * 261.63 * t) + 
                      np.sin(2 * np.pi * 329.63 * t) + 
                      np.sin(2 * np.pi * 392.00 * t)).astype(np.float32) / 3),
            ("noise", np.random.normal(0, 0.1, len(t)).astype(np.float32))
        ]
        
        # 测试文本
        test_texts = [
            "music",
            "speech", 
            "noise",
            "singing",
            "instrumental music",
            "pure tone",
            "harmonic sound"
        ]
        
        results = []
        
        for audio_name, audio_data in test_audios:
            logger.info(f"测试音频: {audio_name}")
            
            try:
                # 处理输入
                inputs = processor(
                    text=test_texts,
                    audios=audio_data,
                    sampling_rate=sample_rate,
                    return_tensors="pt",
                    padding=True
                )
                
                # 执行推理
                with torch.no_grad():
                    outputs = model(**inputs)
                    logits_per_audio = outputs.logits_per_audio
                    probs = logits_per_audio.softmax(dim=1)
                
                # 获取最相似的文本
                best_match_idx = probs.argmax().item()
                best_match_text = test_texts[best_match_idx]
                best_match_score = probs[0][best_match_idx].item()
                
                results.append({
                    "audio": audio_name,
                    "best_match": best_match_text,
                    "score": float(best_match_score),
                    "all_scores": [float(score) for score in probs[0]]
                })
                
                logger.info(f"  最佳匹配: '{best_match_text}' (得分: {best_match_score:.4f})")
                
            except Exception as e:
                logger.error(f"处理音频 {audio_name} 时出错: {e}")
                results.append({
                    "audio": audio_name,
                    "error": str(e)
                })
        
        # 输出结果
        successful_tests = len([r for r in results if "error" not in r])
        logger.info(f"✅ CLAP测试完成 - 成功测试了 {successful_tests}/{len(test_audios)} 个音频")
        
        # 保存结果
        output_dir = project_root / "tests" / "output"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = output_dir / f"clap_test_{timestamp}.json"
        
        test_result = {
            "name": "CLAP模型直接测试",
            "status": "PASS" if successful_tests > 0 else "FAIL",
            "timestamp": timestamp,
            "successful_tests": successful_tests,
            "total_tests": len(test_audios),
            "test_texts": test_texts,
            "results": results
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"测试结果已保存到: {results_file}")
        
        return successful_tests > 0
        
    except Exception as e:
        logger.error(f"❌ CLAP测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 开始简化CLAP模型测试...")
    
    success = test_clap_model_direct()
    
    if success:
        logger.info("🎉 CLAP模型测试成功！")
        return 0
    else:
        logger.error("💥 CLAP模型测试失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main())