#!/usr/bin/env python3
"""
部署验证脚本
验证MSearch系统是否已正确部署并可以投入使用
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeploymentVerifier:
    """部署验证器"""
    
    def __init__(self):
        self.project_root = project_root
        self.verification_results = []
        
    def verify_environment(self) -> Dict[str, Any]:
        """验证环境配置"""
        logger.info("🔍 验证环境配置...")
        
        result = {
            "name": "环境配置验证",
            "status": "UNKNOWN",
            "details": {},
            "issues": []
        }
        
        try:
            # 检查Python版本
            python_version = sys.version_info
            result["details"]["python_version"] = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
            
            if python_version.major != 3 or python_version.minor < 9:
                result["issues"].append("Python版本过低，建议使用Python 3.9+")
            
            # 检查关键包
            critical_packages = [
                "torch", "transformers", "numpy", "fastapi", 
                "qdrant_client", "PIL", "requests", "uvicorn"
            ]
            
            missing_packages = []
            installed_packages = {}
            
            for package in critical_packages:
                try:
                    module = __import__(package)
                    version = getattr(module, '__version__', 'unknown')
                    installed_packages[package] = version
                except ImportError:
                    missing_packages.append(package)
            
            result["details"]["installed_packages"] = installed_packages
            result["details"]["missing_packages"] = missing_packages
            
            if missing_packages:
                result["issues"].append(f"缺少关键包: {', '.join(missing_packages)}")
            
            # 检查项目结构
            required_dirs = ["src", "config", "offline", "tests"]
            missing_dirs = []
            
            for dir_name in required_dirs:
                if not (self.project_root / dir_name).exists():
                    missing_dirs.append(dir_name)
            
            if missing_dirs:
                result["issues"].append(f"缺少必要目录: {', '.join(missing_dirs)}")
            
            # 确定状态
            if not result["issues"]:
                result["status"] = "PASS"
            else:
                result["status"] = "FAIL"
                
        except Exception as e:
            result["status"] = "ERROR"
            result["issues"].append(f"环境检查异常: {e}")
        
        return result
    
    def verify_resources(self) -> Dict[str, Any]:
        """验证资源完整性"""
        logger.info("📦 验证资源完整性...")
        
        result = {
            "name": "资源完整性验证",
            "status": "UNKNOWN",
            "details": {},
            "issues": []
        }
        
        try:
            # 检查离线包
            packages_dir = self.project_root / "offline" / "packages"
            if packages_dir.exists():
                wheel_files = list(packages_dir.glob("*.whl"))
                result["details"]["offline_packages"] = len(wheel_files)
                
                if len(wheel_files) < 100:
                    result["issues"].append(f"离线包数量不足: {len(wheel_files)} < 100")
            else:
                result["issues"].append("离线包目录不存在")
            
            # 检查模型文件
            models_dir = self.project_root / "offline" / "models"
            if models_dir.exists():
                required_models = ["clip-vit-base-patch32", "whisper-base", "clap-htsat-fused"]
                available_models = []
                missing_models = []
                
                for model_name in required_models:
                    model_dir = models_dir / model_name
                    if model_dir.exists() and any(model_dir.iterdir()):
                        available_models.append(model_name)
                    else:
                        missing_models.append(model_name)
                
                result["details"]["available_models"] = available_models
                result["details"]["missing_models"] = missing_models
                
                if missing_models:
                    result["issues"].append(f"缺少模型: {', '.join(missing_models)}")
            else:
                result["issues"].append("模型目录不存在")
            
            # 检查Qdrant二进制文件
            bin_dir = self.project_root / "offline" / "bin"
            if bin_dir.exists():
                qdrant_binary = bin_dir / "qdrant"
                if qdrant_binary.exists() and qdrant_binary.is_file():
                    result["details"]["qdrant_binary"] = "available"
                else:
                    result["issues"].append("Qdrant二进制文件不存在")
            else:
                result["issues"].append("二进制文件目录不存在")
            
            # 检查配置文件
            config_dir = self.project_root / "config"
            if config_dir.exists():
                config_files = list(config_dir.glob("*.yml")) + list(config_dir.glob("*.yaml"))
                result["details"]["config_files"] = len(config_files)
                
                if len(config_files) == 0:
                    result["issues"].append("没有找到配置文件")
            else:
                result["issues"].append("配置目录不存在")
            
            # 确定状态
            if not result["issues"]:
                result["status"] = "PASS"
            else:
                result["status"] = "FAIL"
                
        except Exception as e:
            result["status"] = "ERROR"
            result["issues"].append(f"资源检查异常: {e}")
        
        return result
    
    def verify_scripts(self) -> Dict[str, Any]:
        """验证脚本可用性"""
        logger.info("📜 验证脚本可用性...")
        
        result = {
            "name": "脚本可用性验证",
            "status": "UNKNOWN",
            "details": {},
            "issues": []
        }
        
        try:
            scripts_dir = self.project_root / "scripts"
            required_scripts = [
                "install_offline.sh",
                "start_qdrant.sh", 
                "stop_qdrant.sh",
                "fix_infinity_emb.sh"
            ]
            
            available_scripts = []
            missing_scripts = []
            executable_scripts = []
            
            for script_name in required_scripts:
                script_path = scripts_dir / script_name
                if script_path.exists():
                    available_scripts.append(script_name)
                    if os.access(script_path, os.X_OK):
                        executable_scripts.append(script_name)
                else:
                    missing_scripts.append(script_name)
            
            result["details"]["available_scripts"] = available_scripts
            result["details"]["missing_scripts"] = missing_scripts
            result["details"]["executable_scripts"] = executable_scripts
            
            if missing_scripts:
                result["issues"].append(f"缺少脚本: {', '.join(missing_scripts)}")
            
            non_executable = set(available_scripts) - set(executable_scripts)
            if non_executable:
                result["issues"].append(f"脚本不可执行: {', '.join(non_executable)}")
            
            # 确定状态
            if not result["issues"]:
                result["status"] = "PASS"
            else:
                result["status"] = "FAIL"
                
        except Exception as e:
            result["status"] = "ERROR"
            result["issues"].append(f"脚本检查异常: {e}")
        
        return result
    
    def verify_model_loading(self) -> Dict[str, Any]:
        """验证模型加载能力"""
        logger.info("🧠 验证模型加载能力...")
        
        result = {
            "name": "模型加载验证",
            "status": "UNKNOWN",
            "details": {},
            "issues": []
        }
        
        try:
            models_tested = []
            models_failed = []
            
            # 测试CLIP模型加载
            try:
                from transformers import CLIPModel, CLIPProcessor
                clip_path = self.project_root / "offline" / "models" / "clip-vit-base-patch32"
                if clip_path.exists():
                    model = CLIPModel.from_pretrained(str(clip_path))
                    processor = CLIPProcessor.from_pretrained(str(clip_path))
                    models_tested.append("CLIP")
                    logger.info("✅ CLIP模型加载成功")
                else:
                    models_failed.append("CLIP (文件不存在)")
            except Exception as e:
                models_failed.append(f"CLIP ({str(e)[:50]}...)")
            
            # 测试Whisper模型加载
            try:
                from transformers import WhisperForConditionalGeneration, WhisperProcessor
                whisper_path = self.project_root / "offline" / "models" / "whisper-base"
                if whisper_path.exists():
                    model = WhisperForConditionalGeneration.from_pretrained(str(whisper_path))
                    processor = WhisperProcessor.from_pretrained(str(whisper_path))
                    models_tested.append("Whisper")
                    logger.info("✅ Whisper模型加载成功")
                else:
                    models_failed.append("Whisper (文件不存在)")
            except Exception as e:
                models_failed.append(f"Whisper ({str(e)[:50]}...)")
            
            result["details"]["models_loaded"] = models_tested
            result["details"]["models_failed"] = models_failed
            
            if models_failed:
                result["issues"].append(f"模型加载失败: {', '.join(models_failed)}")
            
            # 确定状态
            if len(models_tested) >= 2:  # 至少2个模型成功
                result["status"] = "PASS"
            elif len(models_tested) >= 1:  # 至少1个模型成功
                result["status"] = "PARTIAL"
            else:
                result["status"] = "FAIL"
                
        except Exception as e:
            result["status"] = "ERROR"
            result["issues"].append(f"模型加载检查异常: {e}")
        
        return result
    
    def verify_qdrant_readiness(self) -> Dict[str, Any]:
        """验证Qdrant就绪状态"""
        logger.info("🗄️ 验证Qdrant就绪状态...")
        
        result = {
            "name": "Qdrant就绪验证",
            "status": "UNKNOWN",
            "details": {},
            "issues": []
        }
        
        try:
            # 检查Qdrant二进制文件
            qdrant_binary = self.project_root / "offline" / "bin" / "qdrant"
            if qdrant_binary.exists():
                result["details"]["binary_available"] = True
                
                # 尝试获取版本信息
                try:
                    version_result = subprocess.run(
                        [str(qdrant_binary), "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if version_result.returncode == 0:
                        result["details"]["version_info"] = version_result.stdout.strip()
                    else:
                        result["issues"].append("无法获取Qdrant版本信息")
                except subprocess.TimeoutExpired:
                    result["issues"].append("Qdrant版本检查超时")
                except Exception as e:
                    result["issues"].append(f"Qdrant版本检查失败: {e}")
            else:
                result["details"]["binary_available"] = False
                result["issues"].append("Qdrant二进制文件不存在")
            
            # 检查配置文件
            config_file = self.project_root / "config" / "qdrant.yml"
            if config_file.exists():
                result["details"]["config_available"] = True
            else:
                result["details"]["config_available"] = False
                result["issues"].append("Qdrant配置文件不存在")
            
            # 检查数据目录
            data_dir = self.project_root / "offline" / "qdrant_data"
            result["details"]["data_dir_exists"] = data_dir.exists()
            
            # 确定状态
            if not result["issues"]:
                result["status"] = "PASS"
            else:
                result["status"] = "FAIL"
                
        except Exception as e:
            result["status"] = "ERROR"
            result["issues"].append(f"Qdrant检查异常: {e}")
        
        return result
    
    def run_verification(self) -> Dict[str, Any]:
        """运行完整验证"""
        logger.info("🚀 开始部署验证...")
        logger.info("=" * 60)
        
        # 运行各项验证
        verifications = [
            self.verify_environment,
            self.verify_resources,
            self.verify_scripts,
            self.verify_model_loading,
            self.verify_qdrant_readiness
        ]
        
        results = []
        passed_count = 0
        
        for verify_func in verifications:
            try:
                result = verify_func()
                results.append(result)
                
                if result["status"] == "PASS":
                    passed_count += 1
                    logger.info(f"✅ {result['name']}: 通过")
                elif result["status"] == "PARTIAL":
                    logger.info(f"⚠️ {result['name']}: 部分通过")
                else:
                    logger.info(f"❌ {result['name']}: 失败")
                    for issue in result.get("issues", []):
                        logger.info(f"   - {issue}")
                        
            except Exception as e:
                logger.error(f"验证执行异常: {e}")
                results.append({
                    "name": verify_func.__name__,
                    "status": "ERROR",
                    "error": str(e)
                })
        
        # 生成总体评估
        total_verifications = len(results)
        success_rate = (passed_count / total_verifications * 100) if total_verifications > 0 else 0
        
        if success_rate >= 90:
            overall_status = "READY"
        elif success_rate >= 70:
            overall_status = "MOSTLY_READY"
        elif success_rate >= 50:
            overall_status = "PARTIALLY_READY"
        else:
            overall_status = "NOT_READY"
        
        summary = {
            "overall_status": overall_status,
            "success_rate": success_rate,
            "total_verifications": total_verifications,
            "passed_verifications": passed_count,
            "failed_verifications": total_verifications - passed_count,
            "verifications": results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 输出结果
        logger.info("=" * 60)
        logger.info("📊 部署验证结果汇总")
        logger.info("=" * 60)
        logger.info(f"总体状态: {overall_status}")
        logger.info(f"成功率: {success_rate:.1f}%")
        logger.info(f"通过验证: {passed_count}/{total_verifications}")
        
        return summary
    
    def generate_deployment_status(self, summary: Dict[str, Any]) -> str:
        """生成部署状态报告"""
        status = summary["overall_status"]
        
        if status == "READY":
            return """
🎉 恭喜！MSearch系统已成功部署并可以投入使用！

✅ 所有关键组件都已正确配置
✅ 模型文件完整且可以正常加载
✅ 依赖包已正确安装
✅ 脚本文件可执行

🚀 快速启动指南:
1. 启动Qdrant服务: ./scripts/start_qdrant.sh
2. 运行功能测试: python3 tests/simple_functionality_test.py
3. 启动API服务: python3 src/api/main.py

📝 系统已准备就绪，可以开始使用MSearch的多模态检索功能！
"""
        elif status == "MOSTLY_READY":
            return """
⚠️ MSearch系统基本就绪，但存在一些小问题需要注意

✅ 核心功能可以正常使用
⚠️ 部分组件可能需要额外配置

🔧 建议操作:
1. 检查上述验证失败的项目
2. 运行相应的修复脚本
3. 重新验证系统状态

📝 系统可以使用，但建议先解决警告问题以获得最佳体验。
"""
        elif status == "PARTIALLY_READY":
            return """
⚠️ MSearch系统部分就绪，需要解决一些问题才能正常使用

❌ 存在影响功能的关键问题
⚠️ 建议先解决这些问题再使用

🔧 必要操作:
1. 运行 ./scripts/install_offline.sh 安装依赖
2. 运行 ./scripts/download_all_resources.sh 下载资源
3. 检查并修复上述失败的验证项目
4. 重新运行验证

📝 请先解决关键问题，然后重新验证系统状态。
"""
        else:
            return """
🚨 MSearch系统尚未准备就绪，需要完成初始化设置

❌ 存在多个关键问题阻止系统正常运行
❌ 系统当前无法使用

🔧 必要操作:
1. 运行 ./scripts/download_all_resources.sh 下载所有资源
2. 运行 ./scripts/install_offline.sh 安装所有依赖
3. 运行 ./scripts/fix_infinity_emb.sh 修复兼容性问题
4. 检查Python环境和项目结构
5. 重新运行验证

📝 请按照上述步骤完成系统初始化，然后重新验证。
"""

def main():
    """主函数"""
    verifier = DeploymentVerifier()
    
    # 运行验证
    summary = verifier.run_verification()
    
    # 保存结果
    output_dir = verifier.project_root / "tests" / "output"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    result_file = output_dir / f"deployment_verification_{timestamp}.json"
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"验证结果已保存到: {result_file}")
    
    # 生成部署状态报告
    status_report = verifier.generate_deployment_status(summary)
    print(status_report)
    
    # 返回适当的退出码
    if summary["overall_status"] == "READY":
        return 0
    elif summary["overall_status"] in ["MOSTLY_READY", "PARTIALLY_READY"]:
        return 1
    else:
        return 2

if __name__ == "__main__":
    sys.exit(main())