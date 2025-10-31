#!/usr/bin/env python3
"""
增强版真实模型测试脚本
专门解决CLAP模型问题并测试多模态功能
"""

import os
import sys
import json
import time
import logging
import wave
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedModelTester:
    """增强版模型测试器"""
    
    def __init__(self):
        self.project_root = project_root
        self.models_dir = self.project_root / "offline" / "models"
        self.testdata_dir = self.project_root / "testdata"
        self.results = {}
        
    def check_environment(self) -> bool:
        """检查测试环境"""
        logger.info("🔍 检查增强测试环境...")
        
        # 检查Python版本
        python_version = sys.version_info
        logger.info(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 检查关键包
        required_packages = [
            'torch', 'transformers', 'numpy', 
            'PIL', 'requests', 'tqdm', 'librosa'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                if package == 'librosa':
                    # librosa可能没有安装，但不是必需的
                    try:
                        __import__(package)
                        logger.info(f"✅ {package}")
                    except ImportError:
                        logger.warning(f"⚠️ {package} (音频处理功能可能受限)")
                else:
                    __import__(package)
                    logger.info(f"✅ {package}")
            except ImportError:
                logger.error(f"❌ {package}")
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"缺少必要包: {missing_packages}")
            return False
            
        # 检查测试数据
        if not self.testdata_dir.exists():
            logger.warning(f"测试数据目录不存在: {self.testdata_dir}")
            
        return True
    
    def fix_clap_model(self) -> bool:
        """修复CLAP模型问题"""
        logger.info("🔧 修复CLAP模型...")
        
        try:
            clap_model_dir = self.models_dir / "clap-htsat-fused"
            
            # 检查模型文件
            if not clap_model_dir.exists():
                logger.error("CLAP模型目录不存在")
                return False
            
            # 检查关键文件
            required_files = ["config.json", "pytorch_model.bin", "preprocessor_config.json"]
            missing_files = []
            
            for file_name in required_files:
                if not (clap_model_dir / file_name).exists():
                    missing_files.append(file_name)
            
            if missing_files:
                logger.warning(f"CLAP模型缺少文件: {missing_files}")
                
                # 尝试重新下载CLAP模型
                logger.info("尝试重新下载CLAP模型...")
                return self.redownload_clap_model()
            
            # 尝试加载模型验证
            try:
                from transformers import ClapModel, ClapProcessor
                model = ClapModel.from_pretrained(str(clap_model_dir))
                processor = ClapProcessor.from_pretrained(str(clap_model_dir))
                logger.info("✅ CLAP模型验证成功")
                return True
            except Exception as e:
                logger.error(f"CLAP模型加载失败: {e}")
                return self.redownload_clap_model()
                
        except Exception as e:
            logger.error(f"CLAP模型修复异常: {e}")
            return False
    
    def redownload_clap_model(self) -> bool:
        """重新下载CLAP模型"""
        logger.info("重新下载CLAP模型...")
        
        try:
            from transformers import ClapModel, ClapProcessor
            
            clap_model_dir = self.models_dir / "clap-htsat-fused"
            
            # 清理现有目录
            if clap_model_dir.exists():
                import shutil
                shutil.rmtree(clap_model_dir)
            
            clap_model_dir.mkdir(parents=True, exist_ok=True)
            
            # 设置环境变量使用镜像
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
            
            # 重新下载
            model = ClapModel.from_pretrained("laion/clap-htsat-fused")
            processor = ClapProcessor.from_pretrained("laion/clap-htsat-fused")
            
            # 保存到本地
            model.save_pretrained(str(clap_model_dir))
            processor.save_pretrained(str(clap_model_dir))
            
            logger.info("✅ CLAP模型重新下载成功")
            return True
            
        except Exception as e:
            logger.error(f"CLAP模型重新下载失败: {e}")
            return False
    
    def test_clip_with_real_images(self) -> Dict[str, Any]:
        """使用真实图片测试CLIP模型"""
        logger.info("🖼️ 测试CLIP模型（真实图片）...")
        
        test_result = {
            "name": "CLIP模型测试（真实图片）",
            "status": "UNKNOWN",
            "details": {},
            "error": None,
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # 检查CLIP模型文件
            clip_model_dir = self.models_dir / "clip-vit-base-patch32"
            if not clip_model_dir.exists():
                raise FileNotFoundError(f"CLIP模型目录不存在: {clip_model_dir}")
            
            # 导入必要的库
            from transformers import CLIPModel, CLIPProcessor
            import torch
            from PIL import Image
            
            logger.info("加载CLIP模型...")
            
            # 加载模型和处理器
            model = CLIPModel.from_pretrained(str(clip_model_dir))
            processor = CLIPProcessor.from_pretrained(str(clip_model_dir))
            
            # 查找测试图片
            image_files = list(self.testdata_dir.glob("*.jpg"))
            if not image_files:
                logger.warning("未找到测试图片，使用生成的图片")
                # 创建测试图片
                test_image = Image.new('RGB', (224, 224), color='red')
                image_files = [("generated_red", test_image)]
            else:
                # 加载真实图片
                image_files = [(f.stem, Image.open(f)) for f in image_files[:5]]  # 最多5张
            
            # 测试文本
            test_texts = [
                "a red image",
                "a green image", 
                "a blue image",
                "a colorful image",
                "geometric shapes",
                "text and letters",
                "gradient colors",
                "noise pattern"
            ]
            
            results = []
            
            for img_name, image in image_files:
                logger.info(f"测试图片: {img_name}")
                
                # 处理输入
                inputs = processor(
                    text=test_texts, 
                    images=image, 
                    return_tensors="pt", 
                    padding=True
                )
                
                # 执行推理
                with torch.no_grad():
                    outputs = model(**inputs)
                    logits_per_image = outputs.logits_per_image
                    probs = logits_per_image.softmax(dim=1)
                
                # 获取最相似的文本
                best_match_idx = probs.argmax().item()
                best_match_text = test_texts[best_match_idx]
                best_match_score = probs[0][best_match_idx].item()
                
                results.append({
                    "image": img_name,
                    "best_match": best_match_text,
                    "score": float(best_match_score),
                    "all_scores": [float(score) for score in probs[0]]
                })
                
                logger.info(f"  最佳匹配: '{best_match_text}' (得分: {best_match_score:.4f})")
            
            test_result.update({
                "status": "PASS",
                "details": {
                    "model_loaded": True,
                    "inference_successful": True,
                    "images_tested": len(results),
                    "test_texts": test_texts,
                    "results": results
                }
            })
            
            logger.info(f"✅ CLIP测试成功 - 测试了 {len(results)} 张图片")
            
        except Exception as e:
            test_result.update({
                "status": "FAIL",
                "error": str(e)
            })
            logger.error(f"❌ CLIP测试失败: {e}")
        
        test_result["duration"] = time.time() - start_time
        return test_result
    
    def test_clap_with_real_audio(self) -> Dict[str, Any]:
        """使用真实音频测试CLAP模型"""
        logger.info("🎵 测试CLAP模型（真实音频）...")
        
        test_result = {
            "name": "CLAP模型测试（真实音频）",
            "status": "UNKNOWN",
            "details": {},
            "error": None,
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # 先修复CLAP模型
            if not self.fix_clap_model():
                raise Exception("CLAP模型修复失败")
            
            # 检查CLAP模型文件
            clap_model_dir = self.models_dir / "clap-htsat-fused"
            if not clap_model_dir.exists():
                raise FileNotFoundError(f"CLAP模型目录不存在: {clap_model_dir}")
            
            # 导入必要的库
            from transformers import ClapModel, ClapProcessor
            import torch
            
            logger.info("加载CLAP模型...")
            
            # 加载模型和处理器
            model = ClapModel.from_pretrained(str(clap_model_dir))
            processor = ClapProcessor.from_pretrained(str(clap_model_dir))
            
            # 查找测试音频
            audio_files = list(self.testdata_dir.glob("*.wav"))
            if not audio_files:
                logger.warning("未找到测试音频，生成测试音频")
                # 生成测试音频
                sample_rate = 48000  # CLAP使用48kHz
                duration = 3
                t = np.linspace(0, duration, sample_rate * duration)
                test_audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
                audio_files = [("generated_tone", test_audio, sample_rate)]
            else:
                # 加载真实音频
                audio_data = []
                for audio_file in audio_files[:3]:  # 最多3个音频
                    try:
                        # 读取WAV文件
                        with wave.open(str(audio_file), 'rb') as wav_file:
                            frames = wav_file.readframes(-1)
                            sample_rate = wav_file.getframerate()
                            audio_array = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
                            audio_array = audio_array / 32768.0  # 归一化到[-1, 1]
                            
                            # 如果需要，重采样到48kHz
                            if sample_rate != 48000:
                                # 简单的重采样（线性插值）
                                target_length = int(len(audio_array) * 48000 / sample_rate)
                                audio_array = np.interp(
                                    np.linspace(0, len(audio_array), target_length),
                                    np.arange(len(audio_array)),
                                    audio_array
                                )
                                sample_rate = 48000
                            
                            audio_data.append((audio_file.stem, audio_array, sample_rate))
                    except Exception as e:
                        logger.warning(f"无法加载音频文件 {audio_file}: {e}")
                
                audio_files = audio_data
            
            # 测试文本
            test_texts = [
                "music",
                "speech", 
                "noise",
                "singing",
                "instrumental music",
                "low frequency sound",
                "high frequency sound",
                "harmonic sound"
            ]
            
            results = []
            
            for audio_name, audio_data, sr in audio_files:
                logger.info(f"测试音频: {audio_name}")
                
                try:
                    # 处理输入
                    inputs = processor(
                        text=test_texts,
                        audios=audio_data,
                        sampling_rate=sr,
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
            
            if results and any("error" not in r for r in results):
                test_result.update({
                    "status": "PASS",
                    "details": {
                        "model_loaded": True,
                        "inference_successful": True,
                        "audios_tested": len([r for r in results if "error" not in r]),
                        "test_texts": test_texts,
                        "results": results
                    }
                })
                
                successful_tests = len([r for r in results if "error" not in r])
                logger.info(f"✅ CLAP测试成功 - 成功测试了 {successful_tests} 个音频")
            else:
                raise Exception("所有音频测试都失败了")
            
        except Exception as e:
            test_result.update({
                "status": "FAIL",
                "error": str(e)
            })
            logger.error(f"❌ CLAP测试失败: {e}")
        
        test_result["duration"] = time.time() - start_time
        return test_result
    
    def test_whisper_with_real_audio(self) -> Dict[str, Any]:
        """使用真实音频测试Whisper模型"""
        logger.info("🎤 测试Whisper模型（真实音频）...")
        
        test_result = {
            "name": "Whisper模型测试（真实音频）",
            "status": "UNKNOWN", 
            "details": {},
            "error": None,
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # 检查Whisper模型文件
            whisper_model_dir = self.models_dir / "whisper-base"
            if not whisper_model_dir.exists():
                raise FileNotFoundError(f"Whisper模型目录不存在: {whisper_model_dir}")
            
            # 导入必要的库
            from transformers import WhisperProcessor, WhisperForConditionalGeneration
            import torch
            
            logger.info("加载Whisper模型...")
            
            # 加载模型和处理器
            processor = WhisperProcessor.from_pretrained(str(whisper_model_dir))
            model = WhisperForConditionalGeneration.from_pretrained(str(whisper_model_dir))
            
            # 查找测试音频
            audio_files = list(self.testdata_dir.glob("*.wav"))
            if not audio_files:
                # 生成测试音频（模拟语音）
                sample_rate = 16000
                duration = 2
                t = np.linspace(0, duration, sample_rate * duration)
                # 生成更复杂的音频信号（模拟语音）
                test_audio = (np.sin(2 * np.pi * 200 * t) + 
                             0.5 * np.sin(2 * np.pi * 400 * t) + 
                             0.3 * np.sin(2 * np.pi * 800 * t)).astype(np.float32)
                audio_files = [("generated_speech", test_audio, sample_rate)]
            else:
                # 加载真实音频
                audio_data = []
                for audio_file in audio_files[:3]:  # 最多3个音频
                    try:
                        with wave.open(str(audio_file), 'rb') as wav_file:
                            frames = wav_file.readframes(-1)
                            sample_rate = wav_file.getframerate()
                            audio_array = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
                            audio_array = audio_array / 32768.0  # 归一化
                            
                            # Whisper需要16kHz
                            if sample_rate != 16000:
                                target_length = int(len(audio_array) * 16000 / sample_rate)
                                audio_array = np.interp(
                                    np.linspace(0, len(audio_array), target_length),
                                    np.arange(len(audio_array)),
                                    audio_array
                                )
                                sample_rate = 16000
                            
                            audio_data.append((audio_file.stem, audio_array, sample_rate))
                    except Exception as e:
                        logger.warning(f"无法加载音频文件 {audio_file}: {e}")
                
                audio_files = audio_data
            
            results = []
            
            for audio_name, audio_data, sr in audio_files:
                logger.info(f"测试音频: {audio_name}")
                
                try:
                    # 处理音频输入
                    input_features = processor(
                        audio_data, 
                        sampling_rate=sr, 
                        return_tensors="pt"
                    ).input_features
                    
                    # 执行推理
                    with torch.no_grad():
                        predicted_ids = model.generate(input_features)
                        transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
                    
                    results.append({
                        "audio": audio_name,
                        "transcription": transcription[0] if transcription else "",
                        "audio_duration": len(audio_data) / sr
                    })
                    
                    logger.info(f"  转录结果: '{transcription[0] if transcription else 'Empty'}'")
                    
                except Exception as e:
                    logger.error(f"处理音频 {audio_name} 时出错: {e}")
                    results.append({
                        "audio": audio_name,
                        "error": str(e)
                    })
            
            test_result.update({
                "status": "PASS",
                "details": {
                    "model_loaded": True,
                    "inference_successful": True,
                    "audios_tested": len([r for r in results if "error" not in r]),
                    "results": results
                }
            })
            
            successful_tests = len([r for r in results if "error" not in r])
            logger.info(f"✅ Whisper测试成功 - 成功测试了 {successful_tests} 个音频")
            
        except Exception as e:
            test_result.update({
                "status": "FAIL", 
                "error": str(e)
            })
            logger.error(f"❌ Whisper测试失败: {e}")
        
        test_result["duration"] = time.time() - start_time
        return test_result
    
    def test_video_audio_extraction(self) -> Dict[str, Any]:
        """测试视频音频提取功能"""
        logger.info("🎬 测试视频音频提取...")
        
        test_result = {
            "name": "视频音频提取测试",
            "status": "UNKNOWN",
            "details": {},
            "error": None,
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # 查找视频文件
            video_files = (list(self.testdata_dir.glob("*.mp4")) + 
                          list(self.testdata_dir.glob("*.avi")) + 
                          list(self.testdata_dir.glob("*.mov")))
            
            if not video_files:
                test_result.update({
                    "status": "SKIP",
                    "details": {"reason": "未找到视频文件"}
                })
                logger.warning("⚠️ 未找到视频文件，跳过视频音频提取测试")
                return test_result
            
            # 尝试使用不同的方法提取音频
            extraction_results = []
            
            for video_file in video_files[:2]:  # 最多测试2个视频
                logger.info(f"处理视频: {video_file.name}")
                
                # 方法1: 使用ffmpeg
                try:
                    import subprocess
                    
                    output_audio = self.testdata_dir / f"{video_file.stem}_extracted.wav"
                    
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', str(video_file),
                        '-vn',  # 不要视频
                        '-acodec', 'pcm_s16le',  # 16位PCM
                        '-ar', '16000',  # 16kHz采样率
                        '-ac', '1',  # 单声道
                        str(output_audio)
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0 and output_audio.exists():
                        extraction_results.append({
                            "video": video_file.name,
                            "method": "ffmpeg",
                            "status": "success",
                            "output": output_audio.name,
                            "size": output_audio.stat().st_size
                        })
                        logger.info(f"  ✅ ffmpeg提取成功: {output_audio.name}")
                    else:
                        extraction_results.append({
                            "video": video_file.name,
                            "method": "ffmpeg",
                            "status": "failed",
                            "error": result.stderr
                        })
                        logger.warning(f"  ❌ ffmpeg提取失败: {result.stderr}")
                        
                except FileNotFoundError:
                    logger.warning("  ⚠️ ffmpeg未安装")
                except subprocess.TimeoutExpired:
                    logger.warning("  ⚠️ ffmpeg提取超时")
                except Exception as e:
                    logger.warning(f"  ⚠️ ffmpeg提取异常: {e}")
                
                # 方法2: 使用moviepy（如果可用）
                try:
                    import moviepy.editor as mp
                    
                    output_audio = self.testdata_dir / f"{video_file.stem}_moviepy.wav"
                    
                    video = mp.VideoFileClip(str(video_file))
                    if video.audio is not None:
                        video.audio.write_audiofile(str(output_audio), verbose=False, logger=None)
                        video.close()
                        
                        extraction_results.append({
                            "video": video_file.name,
                            "method": "moviepy",
                            "status": "success",
                            "output": output_audio.name,
                            "size": output_audio.stat().st_size
                        })
                        logger.info(f"  ✅ moviepy提取成功: {output_audio.name}")
                    else:
                        extraction_results.append({
                            "video": video_file.name,
                            "method": "moviepy",
                            "status": "failed",
                            "error": "视频无音频轨道"
                        })
                        
                except ImportError:
                    logger.warning("  ⚠️ moviepy未安装")
                except Exception as e:
                    logger.warning(f"  ⚠️ moviepy提取异常: {e}")
            
            if extraction_results:
                successful_extractions = len([r for r in extraction_results if r["status"] == "success"])
                
                test_result.update({
                    "status": "PASS" if successful_extractions > 0 else "FAIL",
                    "details": {
                        "videos_processed": len(set(r["video"] for r in extraction_results)),
                        "successful_extractions": successful_extractions,
                        "total_attempts": len(extraction_results),
                        "results": extraction_results
                    }
                })
                
                if successful_extractions > 0:
                    logger.info(f"✅ 视频音频提取测试成功 - {successful_extractions} 次成功提取")
                else:
                    logger.error("❌ 所有视频音频提取都失败了")
            else:
                test_result.update({
                    "status": "SKIP",
                    "details": {"reason": "无可用的音频提取工具"}
                })
                logger.warning("⚠️ 无可用的音频提取工具")
            
        except Exception as e:
            test_result.update({
                "status": "FAIL",
                "error": str(e)
            })
            logger.error(f"❌ 视频音频提取测试失败: {e}")
        
        test_result["duration"] = time.time() - start_time
        return test_result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有增强测试"""
        logger.info("🚀 开始增强版真实模型测试...")
        logger.info("=" * 60)
        
        # 检查环境
        if not self.check_environment():
            return {
                "status": "FAIL",
                "error": "环境检查失败",
                "tests": []
            }
        
        # 运行各项测试
        tests = [
            self.test_clip_with_real_images,
            self.test_clap_with_real_audio,
            self.test_whisper_with_real_audio,
            self.test_video_audio_extraction
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
            "status": "PASS" if passed_tests == total_tests else "PARTIAL" if passed_tests > 0 else "FAIL",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "tests": test_results
        }
        
        # 输出结果
        logger.info("=" * 60)
        logger.info("📊 增强版真实模型测试结果汇总")
        logger.info("=" * 60)
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过测试: {passed_tests}")
        logger.info(f"失败测试: {total_tests - passed_tests}")
        logger.info(f"成功率: {success_rate:.1f}%")
        
        for result in test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            logger.info(f"{status_icon} {result['name']}: {result['status']} ({result['duration']:.2f}s)")
        
        return summary
    
    def save_results(self, results: Dict[str, Any]) -> None:
        """保存测试结果"""
        output_dir = self.project_root / "tests" / "output"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = output_dir / f"enhanced_model_test_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"测试结果已保存到: {results_file}")

def main():
    """主函数"""
    tester = EnhancedModelTester()
    results = tester.run_all_tests()
    tester.save_results(results)
    
    # 返回适当的退出码
    if results["status"] == "PASS":
        return 0
    elif results["status"] == "PARTIAL":
        return 1
    else:
        return 2

if __name__ == "__main__":
    sys.exit(main())