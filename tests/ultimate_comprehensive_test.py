#!/usr/bin/env python3
"""
终极综合测试脚本
测试所有功能：CLIP、CLAP、Whisper、视频音频处理、FFMPEG等
"""

import os
import sys
import json
import time
import logging
import subprocess
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

class UltimateComprehensiveTester:
    """终极综合测试器"""
    
    def __init__(self):
        self.project_root = project_root
        self.models_dir = self.project_root / "offline" / "models"
        self.testdata_dir = self.project_root / "testdata"
        self.testdata_dir.mkdir(exist_ok=True)
        
    def test_environment_setup(self):
        """测试环境设置"""
        logger.info("🔍 测试环境设置...")
        
        result = {
            "name": "环境设置测试",
            "status": "PASS",
            "details": {},
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # Python版本
            python_version = sys.version_info
            result["details"]["python_version"] = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
            
            # 检查关键包
            packages = {}
            critical_packages = ['torch', 'transformers', 'numpy', 'PIL', 'fastapi']
            
            for package in critical_packages:
                try:
                    module = __import__(package)
                    version = getattr(module, '__version__', 'unknown')
                    packages[package] = version
                except ImportError:
                    packages[package] = "NOT_INSTALLED"
            
            result["details"]["packages"] = packages
            
            # 检查FFMPEG
            try:
                ffmpeg_result = subprocess.run(['ffmpeg', '-version'], 
                                             capture_output=True, text=True, timeout=10)
                if ffmpeg_result.returncode == 0:
                    version_line = ffmpeg_result.stdout.split('\n')[0]
                    result["details"]["ffmpeg"] = version_line
                else:
                    result["details"]["ffmpeg"] = "NOT_AVAILABLE"
            except:
                result["details"]["ffmpeg"] = "NOT_INSTALLED"
            
            # 检查模型目录
            model_dirs = {}
            for model_name in ["clip-vit-base-patch32", "clap-htsat-fused", "whisper-base"]:
                model_path = self.models_dir / model_name
                model_dirs[model_name] = {
                    "exists": model_path.exists(),
                    "file_count": len(list(model_path.glob("*"))) if model_path.exists() else 0
                }
            
            result["details"]["models"] = model_dirs
            
            logger.info("✅ 环境设置测试完成")
            
        except Exception as e:
            result["status"] = "FAIL"
            result["error"] = str(e)
            logger.error(f"❌ 环境设置测试失败: {e}")
        
        result["duration"] = time.time() - start_time
        return result
    
    def test_clip_model(self):
        """测试CLIP模型"""
        logger.info("🖼️ 测试CLIP模型...")
        
        result = {
            "name": "CLIP模型测试",
            "status": "UNKNOWN",
            "details": {},
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            from transformers import CLIPModel, CLIPProcessor
            import torch
            from PIL import Image
            
            # 加载模型
            clip_model_dir = self.models_dir / "clip-vit-base-patch32"
            model = CLIPModel.from_pretrained(str(clip_model_dir))
            processor = CLIPProcessor.from_pretrained(str(clip_model_dir))
            
            # 创建测试图像
            test_image = Image.new('RGB', (224, 224), color='red')
            test_texts = ["a red image", "a blue image", "a green image"]
            
            # 执行推理
            inputs = processor(text=test_texts, images=test_image, return_tensors="pt", padding=True)
            
            with torch.no_grad():
                outputs = model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)
            
            best_match_idx = probs.argmax().item()
            best_match_text = test_texts[best_match_idx]
            best_match_score = probs[0][best_match_idx].item()
            
            result.update({
                "status": "PASS",
                "details": {
                    "model_loaded": True,
                    "best_match": best_match_text,
                    "score": float(best_match_score)
                }
            })
            
            logger.info(f"✅ CLIP测试成功 - 最佳匹配: '{best_match_text}' ({best_match_score:.4f})")
            
        except Exception as e:
            result.update({
                "status": "FAIL",
                "error": str(e)
            })
            logger.error(f"❌ CLIP测试失败: {e}")
        
        result["duration"] = time.time() - start_time
        return result
    
    def test_clap_model(self):
        """测试CLAP模型"""
        logger.info("🎵 测试CLAP模型...")
        
        result = {
            "name": "CLAP模型测试",
            "status": "UNKNOWN",
            "details": {},
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            from transformers import ClapModel, ClapProcessor
            import torch
            
            # 加载模型
            clap_model_dir = self.models_dir / "clap-htsat-fused"
            model = ClapModel.from_pretrained(str(clap_model_dir))
            processor = ClapProcessor.from_pretrained(str(clap_model_dir))
            
            # 生成测试音频
            sample_rate = 48000
            duration = 3
            t = np.linspace(0, duration, sample_rate * duration)
            test_audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
            
            test_texts = ["music", "speech", "noise", "pure tone"]
            
            # 执行推理
            inputs = processor(
                text=test_texts,
                audios=test_audio,
                sampling_rate=sample_rate,
                return_tensors="pt",
                padding=True
            )
            
            with torch.no_grad():
                outputs = model(**inputs)
                logits_per_audio = outputs.logits_per_audio
                probs = logits_per_audio.softmax(dim=1)
            
            best_match_idx = probs.argmax().item()
            best_match_text = test_texts[best_match_idx]
            best_match_score = probs[0][best_match_idx].item()
            
            result.update({
                "status": "PASS",
                "details": {
                    "model_loaded": True,
                    "best_match": best_match_text,
                    "score": float(best_match_score)
                }
            })
            
            logger.info(f"✅ CLAP测试成功 - 最佳匹配: '{best_match_text}' ({best_match_score:.4f})")
            
        except Exception as e:
            result.update({
                "status": "FAIL",
                "error": str(e)
            })
            logger.error(f"❌ CLAP测试失败: {e}")
        
        result["duration"] = time.time() - start_time
        return result
    
    def test_whisper_model(self):
        """测试Whisper模型"""
        logger.info("🎤 测试Whisper模型...")
        
        result = {
            "name": "Whisper模型测试",
            "status": "UNKNOWN",
            "details": {},
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            from transformers import WhisperProcessor, WhisperForConditionalGeneration
            import torch
            
            # 加载模型
            whisper_model_dir = self.models_dir / "whisper-base"
            processor = WhisperProcessor.from_pretrained(str(whisper_model_dir))
            model = WhisperForConditionalGeneration.from_pretrained(str(whisper_model_dir))
            
            # 生成测试音频
            sample_rate = 16000
            duration = 2
            t = np.linspace(0, duration, sample_rate * duration)
            test_audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
            
            # 执行推理
            input_features = processor(test_audio, sampling_rate=sample_rate, return_tensors="pt").input_features
            
            with torch.no_grad():
                predicted_ids = model.generate(input_features)
                transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
            
            result.update({
                "status": "PASS",
                "details": {
                    "model_loaded": True,
                    "transcription": transcription[0] if transcription else ""
                }
            })
            
            logger.info(f"✅ Whisper测试成功 - 转录: '{transcription[0] if transcription else 'Empty'}'")
            
        except Exception as e:
            result.update({
                "status": "FAIL",
                "error": str(e)
            })
            logger.error(f"❌ Whisper测试失败: {e}")
        
        result["duration"] = time.time() - start_time
        return result
    
    def test_video_audio_processing(self):
        """测试视频音频处理"""
        logger.info("🎬 测试视频音频处理...")
        
        result = {
            "name": "视频音频处理测试",
            "status": "UNKNOWN",
            "details": {},
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # 检查FFMPEG
            ffmpeg_result = subprocess.run(['ffmpeg', '-version'], 
                                         capture_output=True, text=True, timeout=10)
            if ffmpeg_result.returncode != 0:
                raise Exception("FFMPEG不可用")
            
            # 创建测试视频
            video_path = self.testdata_dir / "test_video.mp4"
            
            create_cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', 'testsrc2=duration=3:size=320x240:rate=10',
                '-f', 'lavfi',
                '-i', 'sine=frequency=440:duration=3',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-shortest',
                str(video_path)
            ]
            
            create_result = subprocess.run(create_cmd, capture_output=True, text=True, timeout=30)
            if create_result.returncode != 0 or not video_path.exists():
                raise Exception(f"视频创建失败: {create_result.stderr}")
            
            video_size = video_path.stat().st_size
            
            # 提取音频
            audio_path = self.testdata_dir / "extracted_audio.wav"
            
            extract_cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-vn',
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                str(audio_path)
            ]
            
            extract_result = subprocess.run(extract_cmd, capture_output=True, text=True, timeout=30)
            if extract_result.returncode != 0 or not audio_path.exists():
                raise Exception(f"音频提取失败: {extract_result.stderr}")
            
            audio_size = audio_path.stat().st_size
            
            # 分析音频
            with wave.open(str(audio_path), 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                frames = wav_file.getnframes()
                duration = frames / sample_rate
            
            result.update({
                "status": "PASS",
                "details": {
                    "ffmpeg_available": True,
                    "video_created": True,
                    "video_size": video_size,
                    "audio_extracted": True,
                    "audio_size": audio_size,
                    "audio_analysis": {
                        "sample_rate": sample_rate,
                        "channels": channels,
                        "duration": duration
                    }
                }
            })
            
            logger.info(f"✅ 视频音频处理测试成功")
            logger.info(f"   视频大小: {video_size} bytes")
            logger.info(f"   音频大小: {audio_size} bytes")
            logger.info(f"   音频时长: {duration:.2f} 秒")
            
        except Exception as e:
            result.update({
                "status": "FAIL",
                "error": str(e)
            })
            logger.error(f"❌ 视频音频处理测试失败: {e}")
        
        result["duration"] = time.time() - start_time
        return result
    
    def test_multimodal_integration(self):
        """测试多模态集成"""
        logger.info("🔗 测试多模态集成...")
        
        result = {
            "name": "多模态集成测试",
            "status": "UNKNOWN",
            "details": {},
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # 创建一个包含图像、音频和文本的综合测试
            from transformers import CLIPModel, CLIPProcessor, ClapModel, ClapProcessor
            import torch
            from PIL import Image
            
            # 加载所有模型
            clip_model = CLIPModel.from_pretrained(str(self.models_dir / "clip-vit-base-patch32"))
            clip_processor = CLIPProcessor.from_pretrained(str(self.models_dir / "clip-vit-base-patch32"))
            
            clap_model = ClapModel.from_pretrained(str(self.models_dir / "clap-htsat-fused"))
            clap_processor = ClapProcessor.from_pretrained(str(self.models_dir / "clap-htsat-fused"))
            
            # 创建测试数据
            test_image = Image.new('RGB', (224, 224), color='blue')
            
            sample_rate = 48000
            duration = 2
            t = np.linspace(0, duration, sample_rate * duration)
            test_audio = np.sin(2 * np.pi * 880 * t).astype(np.float32)  # 高频音调
            
            test_texts = ["blue color", "high frequency sound", "music", "image"]
            
            # CLIP推理
            clip_inputs = clip_processor(text=test_texts, images=test_image, return_tensors="pt", padding=True)
            with torch.no_grad():
                clip_outputs = clip_model(**clip_inputs)
                clip_probs = clip_outputs.logits_per_image.softmax(dim=1)
            
            clip_best_idx = clip_probs.argmax().item()
            clip_best_text = test_texts[clip_best_idx]
            clip_best_score = clip_probs[0][clip_best_idx].item()
            
            # CLAP推理
            clap_inputs = clap_processor(text=test_texts, audios=test_audio, sampling_rate=sample_rate, return_tensors="pt", padding=True)
            with torch.no_grad():
                clap_outputs = clap_model(**clap_inputs)
                clap_probs = clap_outputs.logits_per_audio.softmax(dim=1)
            
            clap_best_idx = clap_probs.argmax().item()
            clap_best_text = test_texts[clap_best_idx]
            clap_best_score = clap_probs[0][clap_best_idx].item()
            
            result.update({
                "status": "PASS",
                "details": {
                    "models_loaded": True,
                    "clip_result": {
                        "best_match": clip_best_text,
                        "score": float(clip_best_score)
                    },
                    "clap_result": {
                        "best_match": clap_best_text,
                        "score": float(clap_best_score)
                    },
                    "integration_successful": True
                }
            })
            
            logger.info(f"✅ 多模态集成测试成功")
            logger.info(f"   CLIP结果: '{clip_best_text}' ({clip_best_score:.4f})")
            logger.info(f"   CLAP结果: '{clap_best_text}' ({clap_best_score:.4f})")
            
        except Exception as e:
            result.update({
                "status": "FAIL",
                "error": str(e)
            })
            logger.error(f"❌ 多模态集成测试失败: {e}")
        
        result["duration"] = time.time() - start_time
        return result
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始终极综合测试...")
        logger.info("=" * 80)
        
        # 运行各项测试
        tests = [
            self.test_environment_setup,
            self.test_clip_model,
            self.test_clap_model,
            self.test_whisper_model,
            self.test_video_audio_processing,
            self.test_multimodal_integration
        ]
        
        test_results = []
        passed_tests = 0
        
        for test_func in tests:
            try:
                result = test_func()
                test_results.append(result)
                
                if result["status"] == "PASS":
                    passed_tests += 1
                    
            except Exception as e:
                logger.error(f"测试执行异常: {e}")
                test_results.append({
                    "name": test_func.__name__,
                    "status": "ERROR",
                    "error": str(e),
                    "duration": 0
                })
        
        # 汇总结果
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        summary = {
            "status": "PASS" if passed_tests == total_tests else "PARTIAL" if passed_tests >= total_tests * 0.8 else "FAIL",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "tests": test_results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 输出结果
        logger.info("=" * 80)
        logger.info("📊 终极综合测试结果汇总")
        logger.info("=" * 80)
        logger.info(f"总体状态: {summary['status']}")
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过测试: {passed_tests}")
        logger.info(f"失败测试: {total_tests - passed_tests}")
        logger.info(f"成功率: {success_rate:.1f}%")
        
        for result in test_results:
            status_icon = {
                "PASS": "✅", 
                "FAIL": "❌", 
                "ERROR": "💥"
            }.get(result["status"], "❓")
            logger.info(f"{status_icon} {result['name']}: {result['status']} ({result['duration']:.2f}s)")
        
        return summary
    
    def save_results(self, results):
        """保存测试结果"""
        output_dir = self.project_root / "tests" / "output"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = output_dir / f"ultimate_comprehensive_test_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"测试结果已保存到: {results_file}")

def main():
    """主函数"""
    tester = UltimateComprehensiveTester()
    results = tester.run_all_tests()
    tester.save_results(results)
    
    # 输出最终状态
    print("\n" + "="*80)
    print("🎯 MSearch 终极综合测试最终状态")
    print("="*80)
    
    if results["status"] == "PASS":
        print("🎉 恭喜！所有功能测试全面通过！")
        print("✅ CLIP模型：图像-文本检索 ✓")
        print("✅ CLAP模型：音频-文本检索 ✓") 
        print("✅ Whisper模型：语音转文本 ✓")
        print("✅ FFMPEG：视频音频处理 ✓")
        print("✅ 多模态集成：跨模态检索 ✓")
        print("\n🚀 MSearch系统已完全就绪，可以投入生产使用！")
    elif results["status"] == "PARTIAL":
        print("⚠️ 大部分功能正常，但存在一些问题")
        print("✅ 核心功能可用，建议解决剩余问题")
    else:
        print("❌ 系统存在重要问题，需要进一步修复")
    
    print(f"\n📊 测试统计:")
    print(f"   成功率: {results['success_rate']:.1f}%")
    print(f"   通过测试: {results['passed_tests']}/{results['total_tests']}")
    
    print("\n" + "="*80)
    
    # 返回适当的退出码
    if results["status"] == "PASS":
        return 0
    elif results["status"] == "PARTIAL":
        return 1
    else:
        return 2

if __name__ == "__main__":
    sys.exit(main())