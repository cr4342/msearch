#!/usr/bin/env python3
"""
真实模型测试脚本
使用下载的模型进行实际功能测试
"""

import os
import sys
import json
import time
import logging
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

class RealModelTester:
    """真实模型测试器"""
    
    def __init__(self):
        self.project_root = project_root
        self.models_dir = self.project_root / "offline" / "models"
        self.testdata_dir = self.project_root / "testdata"
        self.results = {}
        
    def check_environment(self) -> bool:
        """检查测试环境"""
        logger.info("🔍 检查测试环境...")
        
        # 检查Python版本
        python_version = sys.version_info
        logger.info(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 检查关键包
        required_packages = [
            'torch', 'transformers', 'numpy', 
            'PIL', 'requests', 'tqdm'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"✅ {package}")
            except ImportError:
                logger.error(f"❌ {package}")
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"缺少必要包: {missing_packages}")
            return False
            
        # 检查模型目录
        if not self.models_dir.exists():
            logger.error(f"模型目录不存在: {self.models_dir}")
            return False
            
        model_count = len(list(self.models_dir.glob("*")))
        logger.info(f"发现 {model_count} 个模型目录")
        
        # 检查测试数据
        if not self.testdata_dir.exists():
            logger.warning(f"测试数据目录不存在: {self.testdata_dir}")
            
        return True
    
    def test_clip_model(self) -> Dict[str, Any]:
        """测试CLIP模型"""
        logger.info("🖼️ 测试CLIP模型...")
        
        test_result = {
            "name": "CLIP模型测试",
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
            import numpy as np
            
            logger.info("加载CLIP模型...")
            
            # 加载模型和处理器
            model = CLIPModel.from_pretrained(str(clip_model_dir))
            processor = CLIPProcessor.from_pretrained(str(clip_model_dir))
            
            # 创建测试图像（简单的彩色图像）
            test_image = Image.new('RGB', (224, 224), color='red')
            
            # 测试文本
            test_texts = [
                "a red image",
                "a blue image", 
                "a green image",
                "红色的图片",
                "蓝色的图片"
            ]
            
            logger.info("执行CLIP推理...")
            
            # 处理输入
            inputs = processor(
                text=test_texts, 
                images=test_image, 
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
            
            test_result.update({
                "status": "PASS",
                "details": {
                    "model_loaded": True,
                    "inference_successful": True,
                    "best_match_text": best_match_text,
                    "best_match_score": float(best_match_score),
                    "all_scores": [float(score) for score in probs[0]],
                    "test_texts": test_texts
                }
            })
            
            logger.info(f"✅ CLIP测试成功 - 最佳匹配: '{best_match_text}' (得分: {best_match_score:.4f})")
            
        except Exception as e:
            test_result.update({
                "status": "FAIL",
                "error": str(e)
            })
            logger.error(f"❌ CLIP测试失败: {e}")
        
        test_result["duration"] = time.time() - start_time
        return test_result
    
    def test_whisper_model(self) -> Dict[str, Any]:
        """测试Whisper模型"""
        logger.info("🎤 测试Whisper模型...")
        
        test_result = {
            "name": "Whisper模型测试",
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
            import numpy as np
            
            logger.info("加载Whisper模型...")
            
            # 加载模型和处理器
            processor = WhisperProcessor.from_pretrained(str(whisper_model_dir))
            model = WhisperForConditionalGeneration.from_pretrained(str(whisper_model_dir))
            
            # 创建测试音频数据（模拟16kHz采样率的音频）
            sample_rate = 16000
            duration = 2  # 2秒
            # 生成简单的正弦波作为测试音频
            t = np.linspace(0, duration, sample_rate * duration)
            test_audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)  # 440Hz正弦波
            
            logger.info("执行Whisper推理...")
            
            # 处理音频输入
            input_features = processor(
                test_audio, 
                sampling_rate=sample_rate, 
                return_tensors="pt"
            ).input_features
            
            # 执行推理
            with torch.no_grad():
                predicted_ids = model.generate(input_features)
                transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
            
            test_result.update({
                "status": "PASS",
                "details": {
                    "model_loaded": True,
                    "inference_successful": True,
                    "transcription": transcription[0] if transcription else "",
                    "audio_duration": duration,
                    "sample_rate": sample_rate
                }
            })
            
            logger.info(f"✅ Whisper测试成功 - 转录结果: '{transcription[0] if transcription else 'Empty'}'")
            
        except Exception as e:
            test_result.update({
                "status": "FAIL", 
                "error": str(e)
            })
            logger.error(f"❌ Whisper测试失败: {e}")
        
        test_result["duration"] = time.time() - start_time
        return test_result
    
    def test_clap_model(self) -> Dict[str, Any]:
        """测试CLAP模型"""
        logger.info("🎵 测试CLAP模型...")
        
        test_result = {
            "name": "CLAP模型测试",
            "status": "UNKNOWN",
            "details": {},
            "error": None,
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # 检查CLAP模型文件
            clap_model_dir = self.models_dir / "clap-htsat-fused"
            if not clap_model_dir.exists():
                raise FileNotFoundError(f"CLAP模型目录不存在: {clap_model_dir}")
            
            # 导入必要的库
            from transformers import ClapModel, ClapProcessor
            import torch
            import numpy as np
            
            logger.info("加载CLAP模型...")
            
            # 加载模型和处理器
            model = ClapModel.from_pretrained(str(clap_model_dir))
            processor = ClapProcessor.from_pretrained(str(clap_model_dir))
            
            # 创建测试音频数据
            sample_rate = 48000  # CLAP通常使用48kHz
            duration = 3  # 3秒
            t = np.linspace(0, duration, sample_rate * duration)
            test_audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)  # 440Hz正弦波
            
            # 测试文本
            test_texts = [
                "music",
                "speech", 
                "noise",
                "singing",
                "instrumental music"
            ]
            
            logger.info("执行CLAP推理...")
            
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
            
            # 获取最相似的文本
            best_match_idx = probs.argmax().item()
            best_match_text = test_texts[best_match_idx]
            best_match_score = probs[0][best_match_idx].item()
            
            test_result.update({
                "status": "PASS",
                "details": {
                    "model_loaded": True,
                    "inference_successful": True,
                    "best_match_text": best_match_text,
                    "best_match_score": float(best_match_score),
                    "all_scores": [float(score) for score in probs[0]],
                    "test_texts": test_texts,
                    "audio_duration": duration,
                    "sample_rate": sample_rate
                }
            })
            
            logger.info(f"✅ CLAP测试成功 - 最佳匹配: '{best_match_text}' (得分: {best_match_score:.4f})")
            
        except Exception as e:
            test_result.update({
                "status": "FAIL",
                "error": str(e)
            })
            logger.error(f"❌ CLAP测试失败: {e}")
        
        test_result["duration"] = time.time() - start_time
        return test_result
    
    def test_text_queries(self) -> Dict[str, Any]:
        """测试文本查询功能"""
        logger.info("📝 测试文本查询功能...")
        
        test_result = {
            "name": "文本查询测试",
            "status": "UNKNOWN",
            "details": {},
            "error": None,
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # 加载测试查询
            queries_file = self.testdata_dir / "test_queries.json"
            if queries_file.exists():
                with open(queries_file, 'r', encoding='utf-8') as f:
                    queries_data = json.load(f)
                
                text_queries = queries_data.get('text_queries', [])
                test_scenarios = queries_data.get('test_scenarios', [])
                
                test_result.update({
                    "status": "PASS",
                    "details": {
                        "queries_loaded": True,
                        "text_queries_count": len(text_queries),
                        "test_scenarios_count": len(test_scenarios),
                        "sample_queries": text_queries[:3],
                        "sample_scenarios": [s['name'] for s in test_scenarios[:3]]
                    }
                })
                
                logger.info(f"✅ 文本查询测试成功 - 加载了 {len(text_queries)} 个查询和 {len(test_scenarios)} 个场景")
            else:
                test_result.update({
                    "status": "SKIP",
                    "details": {"reason": "测试查询文件不存在"}
                })
                logger.warning("⚠️ 测试查询文件不存在，跳过测试")
                
        except Exception as e:
            test_result.update({
                "status": "FAIL",
                "error": str(e)
            })
            logger.error(f"❌ 文本查询测试失败: {e}")
        
        test_result["duration"] = time.time() - start_time
        return test_result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        logger.info("🚀 开始真实模型测试...")
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
            self.test_clip_model,
            self.test_whisper_model, 
            self.test_clap_model,
            self.test_text_queries
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
        logger.info("📊 真实模型测试结果汇总")
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
        results_file = output_dir / f"real_model_test_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"测试结果已保存到: {results_file}")

def main():
    """主函数"""
    tester = RealModelTester()
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