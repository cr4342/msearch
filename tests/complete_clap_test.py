#!/usr/bin/env python3
"""
完整的CLAP模型测试脚本
测试CLAP模型的音频-文本检索功能
"""

import os
import sys
import json
import time
import logging
import numpy as np
import wave
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

def test_clap_model():
    """测试CLAP模型"""
    logger.info("🎵 开始CLAP模型测试...")
    
    try:
        # 检查CLAP模型目录
        clap_model_dir = project_root / "offline" / "models" / "clap-htsat-fused"
        if not clap_model_dir.exists():
            logger.error(f"CLAP模型目录不存在: {clap_model_dir}")
            return False
        
        # 检查必要文件
        required_files = ["config.json", "model.safetensors", "preprocessor_config.json"]
        missing_files = []
        
        for file_name in required_files:
            if not (clap_model_dir / file_name).exists():
                missing_files.append(file_name)
        
        if missing_files:
            logger.error(f"CLAP模型缺少文件: {missing_files}")
            return False
        
        logger.info("✅ CLAP模型文件检查通过")
        
        # 导入必要的库
        from transformers import ClapModel, ClapProcessor
        import torch
        
        logger.info("加载CLAP模型...")
        
        # 加载模型和处理器
        model = ClapModel.from_pretrained(str(clap_model_dir))
        processor = ClapProcessor.from_pretrained(str(clap_model_dir))
        
        logger.info("✅ CLAP模型加载成功")
        
        # 生成测试音频数据
        sample_rate = 48000  # CLAP使用48kHz
        duration = 3  # 3秒
        t = np.linspace(0, duration, sample_rate * duration)
        
        # 创建不同类型的测试音频
        test_audios = [
            ("pure_tone_440hz", np.sin(2 * np.pi * 440 * t).astype(np.float32)),
            ("low_tone_220hz", np.sin(2 * np.pi * 220 * t).astype(np.float32)),
            ("chord", (np.sin(2 * np.pi * 261.63 * t) + 
                      np.sin(2 * np.pi * 329.63 * t) + 
                      np.sin(2 * np.pi * 392.00 * t)).astype(np.float32) / 3),
            ("noise", np.random.normal(0, 0.1, len(t)).astype(np.float32)),
            ("sweep", np.sin(2 * np.pi * (200 + 400 * t / duration) * t).astype(np.float32))
        ]
        
        # 测试文本描述
        test_texts = [
            "music",
            "speech", 
            "noise",
            "singing",
            "instrumental music",
            "pure tone",
            "harmonic sound",
            "low frequency sound",
            "high frequency sound",
            "random noise"
        ]
        
        logger.info(f"开始测试 {len(test_audios)} 个音频样本...")
        
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
                
                # 获取前3个最相似的结果
                top3_indices = probs[0].argsort(descending=True)[:3]
                top3_results = [
                    {
                        "text": test_texts[idx],
                        "score": float(probs[0][idx])
                    }
                    for idx in top3_indices
                ]
                
                results.append({
                    "audio": audio_name,
                    "best_match": best_match_text,
                    "best_score": float(best_match_score),
                    "top3": top3_results,
                    "all_scores": [float(score) for score in probs[0]]
                })
                
                logger.info(f"  最佳匹配: '{best_match_text}' (得分: {best_match_score:.4f})")
                logger.info(f"  前3名: {', '.join([f'{r['text']}({r['score']:.3f})' for r in top3_results])}")
                
            except Exception as e:
                logger.error(f"处理音频 {audio_name} 时出错: {e}")
                results.append({
                    "audio": audio_name,
                    "error": str(e)
                })
        
        # 统计结果
        successful_tests = len([r for r in results if "error" not in r])
        
        logger.info("=" * 60)
        logger.info("📊 CLAP模型测试结果汇总")
        logger.info("=" * 60)
        logger.info(f"总测试音频: {len(test_audios)}")
        logger.info(f"成功测试: {successful_tests}")
        logger.info(f"失败测试: {len(test_audios) - successful_tests}")
        logger.info(f"成功率: {successful_tests / len(test_audios) * 100:.1f}%")
        
        # 保存详细结果
        output_dir = project_root / "tests" / "output"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = output_dir / f"clap_test_{timestamp}.json"
        
        test_result = {
            "name": "CLAP模型完整测试",
            "timestamp": timestamp,
            "model_path": str(clap_model_dir),
            "test_texts": test_texts,
            "total_tests": len(test_audios),
            "successful_tests": successful_tests,
            "success_rate": successful_tests / len(test_audios) * 100,
            "results": results
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"详细结果已保存到: {results_file}")
        
        if successful_tests > 0:
            logger.info("🎉 CLAP模型测试成功！")
            return True
        else:
            logger.error("💥 CLAP模型测试失败！")
            return False
        
    except Exception as e:
        logger.error(f"❌ CLAP模型测试异常: {e}")
        return False

def test_clap_with_real_audio():
    """使用真实音频文件测试CLAP"""
    logger.info("🎧 使用真实音频文件测试CLAP...")
    
    testdata_dir = project_root / "testdata"
    audio_files = list(testdata_dir.glob("*.wav"))
    
    if not audio_files:
        logger.warning("未找到真实音频文件，跳过此测试")
        return True
    
    try:
        from transformers import ClapModel, ClapProcessor
        import torch
        
        clap_model_dir = project_root / "offline" / "models" / "clap-htsat-fused"
        model = ClapModel.from_pretrained(str(clap_model_dir))
        processor = ClapProcessor.from_pretrained(str(clap_model_dir))
        
        test_texts = [
            "music", "speech", "noise", "singing", "instrumental",
            "low frequency", "high frequency", "harmonic", "pure tone"
        ]
        
        results = []
        
        for audio_file in audio_files[:3]:  # 最多测试3个文件
            logger.info(f"测试真实音频: {audio_file.name}")
            
            try:
                # 读取音频文件
                with wave.open(str(audio_file), 'rb') as wav_file:
                    frames = wav_file.readframes(-1)
                    sample_rate = wav_file.getframerate()
                    audio_array = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # 重采样到48kHz（如果需要）
                    if sample_rate != 48000:
                        target_length = int(len(audio_array) * 48000 / sample_rate)
                        audio_array = np.interp(
                            np.linspace(0, len(audio_array), target_length),
                            np.arange(len(audio_array)),
                            audio_array
                        )
                        sample_rate = 48000
                
                # 处理输入
                inputs = processor(
                    text=test_texts,
                    audios=audio_array,
                    sampling_rate=sample_rate,
                    return_tensors="pt",
                    padding=True
                )
                
                # 执行推理
                with torch.no_grad():
                    outputs = model(**inputs)
                    logits_per_audio = outputs.logits_per_audio
                    probs = logits_per_audio.softmax(dim=1)
                
                best_match_idx = probs.argmax().item()
                best_match_text = test_texts[best_match_idx]
                best_match_score = probs[0][best_match_idx].item()
                
                results.append({
                    "file": audio_file.name,
                    "best_match": best_match_text,
                    "score": float(best_match_score)
                })
                
                logger.info(f"  最佳匹配: '{best_match_text}' (得分: {best_match_score:.4f})")
                
            except Exception as e:
                logger.error(f"处理 {audio_file.name} 时出错: {e}")
                results.append({
                    "file": audio_file.name,
                    "error": str(e)
                })
        
        successful_tests = len([r for r in results if "error" not in r])
        logger.info(f"真实音频测试: {successful_tests}/{len(results)} 成功")
        
        return successful_tests > 0
        
    except Exception as e:
        logger.error(f"真实音频测试异常: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 开始完整CLAP模型测试...")
    logger.info("=" * 60)
    
    # 测试1: 基础CLAP模型功能
    test1_success = test_clap_model()
    
    # 测试2: 真实音频文件测试
    test2_success = test_clap_with_real_audio()
    
    # 汇总结果
    logger.info("=" * 60)
    logger.info("🏁 CLAP模型测试完成")
    logger.info("=" * 60)
    logger.info(f"基础功能测试: {'✅ 通过' if test1_success else '❌ 失败'}")
    logger.info(f"真实音频测试: {'✅ 通过' if test2_success else '❌ 失败'}")
    
    if test1_success and test2_success:
        logger.info("🎉 所有CLAP测试都通过了！")
        return 0
    elif test1_success:
        logger.info("⚠️ CLAP基础功能正常，但真实音频测试有问题")
        return 1
    else:
        logger.error("💥 CLAP模型测试失败")
        return 2

if __name__ == "__main__":
    sys.exit(main())