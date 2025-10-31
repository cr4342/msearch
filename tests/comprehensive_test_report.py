#!/usr/bin/env python3
"""
综合测试报告生成器
整合简化功能测试和真实模型测试的结果
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveTestReporter:
    """综合测试报告生成器"""
    
    def __init__(self):
        self.project_root = project_root
        self.output_dir = self.project_root / "tests" / "output"
        self.output_dir.mkdir(exist_ok=True)
        
    def load_latest_test_results(self) -> Dict[str, Any]:
        """加载最新的测试结果"""
        results = {
            "simple_functionality": None,
            "real_model": None
        }
        
        # 查找最新的简化功能测试结果
        simple_files = list(self.output_dir.glob("test_run_*.log"))
        if simple_files:
            latest_simple = max(simple_files, key=lambda x: x.stat().st_mtime)
            logger.info(f"找到简化功能测试日志: {latest_simple}")
            results["simple_functionality"] = self.parse_simple_test_log(latest_simple)
        
        # 查找最新的真实模型测试结果
        model_files = list(self.output_dir.glob("real_model_test_*.json"))
        if model_files:
            latest_model = max(model_files, key=lambda x: x.stat().st_mtime)
            logger.info(f"找到真实模型测试结果: {latest_model}")
            with open(latest_model, 'r', encoding='utf-8') as f:
                results["real_model"] = json.load(f)
        
        return results
    
    def parse_simple_test_log(self, log_file: Path) -> Dict[str, Any]:
        """解析简化功能测试日志"""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取关键信息
            lines = content.split('\n')
            test_results = []
            summary_info = {}
            
            for line in lines:
                if "✅ PASS" in line or "❌ FAIL" in line:
                    # 解析测试结果行
                    if "✅ PASS" in line:
                        test_name = line.split("✅ PASS")[1].strip()
                        test_results.append({"name": test_name, "status": "PASS"})
                    elif "❌ FAIL" in line:
                        test_name = line.split("❌ FAIL")[1].strip()
                        test_results.append({"name": test_name, "status": "FAIL"})
                
                # 提取汇总信息
                if "总测试数:" in line:
                    summary_info["total_tests"] = int(line.split("总测试数:")[1].strip())
                elif "通过测试:" in line:
                    summary_info["passed_tests"] = int(line.split("通过测试:")[1].strip())
                elif "失败测试:" in line:
                    summary_info["failed_tests"] = int(line.split("失败测试:")[1].strip())
                elif "成功率:" in line:
                    rate_str = line.split("成功率:")[1].strip().replace("%", "")
                    summary_info["success_rate"] = float(rate_str)
            
            return {
                "status": "PASS" if summary_info.get("failed_tests", 1) == 0 else "PARTIAL",
                "tests": test_results,
                **summary_info
            }
            
        except Exception as e:
            logger.error(f"解析简化功能测试日志失败: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合测试报告"""
        logger.info("🔍 生成综合测试报告...")
        
        # 加载测试结果
        test_results = self.load_latest_test_results()
        
        # 系统信息
        system_info = {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project_root": str(self.project_root)
        }
        
        # 环境检查
        environment_status = self.check_environment()
        
        # 资源状态
        resource_status = self.check_resources()
        
        # 汇总统计
        overall_stats = self.calculate_overall_stats(test_results)
        
        # 生成报告
        report = {
            "report_info": {
                "title": "MSearch 综合测试报告",
                "generated_at": system_info["timestamp"],
                "version": "1.0.0"
            },
            "system_info": system_info,
            "environment_status": environment_status,
            "resource_status": resource_status,
            "test_results": test_results,
            "overall_stats": overall_stats,
            "recommendations": self.generate_recommendations(test_results, environment_status, resource_status)
        }
        
        return report
    
    def check_environment(self) -> Dict[str, Any]:
        """检查环境状态"""
        env_status = {
            "python_packages": {},
            "critical_packages_missing": [],
            "status": "UNKNOWN"
        }
        
        critical_packages = [
            "torch", "transformers", "numpy", "fastapi", 
            "qdrant_client", "PIL", "requests"
        ]
        
        missing_count = 0
        for package in critical_packages:
            try:
                __import__(package)
                env_status["python_packages"][package] = "✅ 已安装"
            except ImportError:
                env_status["python_packages"][package] = "❌ 缺失"
                env_status["critical_packages_missing"].append(package)
                missing_count += 1
        
        if missing_count == 0:
            env_status["status"] = "GOOD"
        elif missing_count <= 2:
            env_status["status"] = "WARNING"
        else:
            env_status["status"] = "CRITICAL"
        
        return env_status
    
    def check_resources(self) -> Dict[str, Any]:
        """检查资源状态"""
        resource_status = {
            "offline_packages": 0,
            "model_files": 0,
            "binary_files": 0,
            "testdata_files": 0,
            "status": "UNKNOWN"
        }
        
        # 检查离线包
        packages_dir = self.project_root / "offline" / "packages"
        if packages_dir.exists():
            resource_status["offline_packages"] = len(list(packages_dir.glob("*.whl")))
        
        # 检查模型文件
        models_dir = self.project_root / "offline" / "models"
        if models_dir.exists():
            resource_status["model_files"] = len(list(models_dir.rglob("*")))
        
        # 检查二进制文件
        bin_dir = self.project_root / "offline" / "bin"
        if bin_dir.exists():
            resource_status["binary_files"] = len(list(bin_dir.glob("*")))
        
        # 检查测试数据
        testdata_dir = self.project_root / "testdata"
        if testdata_dir.exists():
            resource_status["testdata_files"] = len(list(testdata_dir.glob("*")))
        
        # 评估状态
        if (resource_status["offline_packages"] > 200 and 
            resource_status["model_files"] > 50 and 
            resource_status["binary_files"] > 0):
            resource_status["status"] = "GOOD"
        elif (resource_status["offline_packages"] > 100 and 
              resource_status["model_files"] > 20):
            resource_status["status"] = "WARNING"
        else:
            resource_status["status"] = "CRITICAL"
        
        return resource_status
    
    def calculate_overall_stats(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """计算总体统计"""
        stats = {
            "total_test_suites": 0,
            "passed_test_suites": 0,
            "total_individual_tests": 0,
            "passed_individual_tests": 0,
            "overall_success_rate": 0.0,
            "status": "UNKNOWN"
        }
        
        # 统计测试套件
        for suite_name, suite_result in test_results.items():
            if suite_result:
                stats["total_test_suites"] += 1
                if suite_result.get("status") in ["PASS", "PARTIAL"]:
                    stats["passed_test_suites"] += 1
                
                # 统计个别测试
                if "total_tests" in suite_result:
                    stats["total_individual_tests"] += suite_result["total_tests"]
                    stats["passed_individual_tests"] += suite_result.get("passed_tests", 0)
                elif "tests" in suite_result:
                    suite_tests = len(suite_result["tests"])
                    suite_passed = len([t for t in suite_result["tests"] if t.get("status") == "PASS"])
                    stats["total_individual_tests"] += suite_tests
                    stats["passed_individual_tests"] += suite_passed
        
        # 计算成功率
        if stats["total_individual_tests"] > 0:
            stats["overall_success_rate"] = (stats["passed_individual_tests"] / stats["total_individual_tests"]) * 100
        
        # 确定总体状态
        if stats["overall_success_rate"] >= 90:
            stats["status"] = "EXCELLENT"
        elif stats["overall_success_rate"] >= 75:
            stats["status"] = "GOOD"
        elif stats["overall_success_rate"] >= 50:
            stats["status"] = "WARNING"
        else:
            stats["status"] = "CRITICAL"
        
        return stats
    
    def generate_recommendations(self, test_results: Dict[str, Any], 
                               env_status: Dict[str, Any], 
                               resource_status: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 环境建议
        if env_status["status"] == "CRITICAL":
            recommendations.append("🚨 关键包缺失过多，建议运行 ./scripts/install_offline.sh 重新安装依赖")
        elif env_status["status"] == "WARNING":
            recommendations.append("⚠️ 部分包缺失，建议检查并安装缺失的包")
        
        # 资源建议
        if resource_status["status"] == "CRITICAL":
            recommendations.append("🚨 离线资源不足，建议运行 ./scripts/download_all_resources.sh 下载资源")
        elif resource_status["status"] == "WARNING":
            recommendations.append("⚠️ 部分资源缺失，建议检查模型和依赖包完整性")
        
        # 测试结果建议
        real_model = test_results.get("real_model")
        if real_model:
            failed_tests = [t for t in real_model.get("tests", []) if t.get("status") == "FAIL"]
            if failed_tests:
                for test in failed_tests:
                    if "CLAP" in test["name"]:
                        recommendations.append("🔧 CLAP模型测试失败，建议重新下载CLAP模型文件")
                    elif "infinity" in str(test.get("error", "")).lower():
                        recommendations.append("🔧 infinity-emb相关问题，建议运行 ./scripts/fix_infinity_emb.sh")
        
        # 通用建议
        if not recommendations:
            recommendations.append("✅ 系统状态良好，可以正常使用MSearch功能")
        
        recommendations.append("📝 建议定期运行测试以确保系统稳定性")
        recommendations.append("🔄 如遇到问题，可查看 tests/output/ 目录下的详细日志")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any]) -> Path:
        """保存报告"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"comprehensive_test_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report_file
    
    def print_summary(self, report: Dict[str, Any]) -> None:
        """打印报告摘要"""
        print("\n" + "="*80)
        print("🧪 MSearch 综合测试报告摘要")
        print("="*80)
        
        # 系统信息
        sys_info = report["system_info"]
        print(f"📅 生成时间: {sys_info['timestamp']}")
        print(f"🐍 Python版本: {sys_info['python_version']}")
        print(f"💻 平台: {sys_info['platform']}")
        
        # 环境状态
        env_status = report["environment_status"]
        status_icon = {"GOOD": "✅", "WARNING": "⚠️", "CRITICAL": "🚨"}.get(env_status["status"], "❓")
        print(f"\n🔧 环境状态: {status_icon} {env_status['status']}")
        if env_status["critical_packages_missing"]:
            print(f"   缺失关键包: {', '.join(env_status['critical_packages_missing'])}")
        
        # 资源状态
        res_status = report["resource_status"]
        status_icon = {"GOOD": "✅", "WARNING": "⚠️", "CRITICAL": "🚨"}.get(res_status["status"], "❓")
        print(f"\n📦 资源状态: {status_icon} {res_status['status']}")
        print(f"   离线包: {res_status['offline_packages']} 个")
        print(f"   模型文件: {res_status['model_files']} 个")
        print(f"   二进制文件: {res_status['binary_files']} 个")
        
        # 测试结果
        overall = report["overall_stats"]
        status_icon = {"EXCELLENT": "🌟", "GOOD": "✅", "WARNING": "⚠️", "CRITICAL": "🚨"}.get(overall["status"], "❓")
        print(f"\n🧪 测试结果: {status_icon} {overall['status']}")
        print(f"   测试套件: {overall['passed_test_suites']}/{overall['total_test_suites']} 通过")
        print(f"   个别测试: {overall['passed_individual_tests']}/{overall['total_individual_tests']} 通过")
        print(f"   总体成功率: {overall['overall_success_rate']:.1f}%")
        
        # 详细测试结果
        test_results = report["test_results"]
        if test_results.get("simple_functionality"):
            simple = test_results["simple_functionality"]
            status_icon = "✅" if simple["status"] == "PASS" else "⚠️"
            print(f"\n   {status_icon} 简化功能测试: {simple.get('success_rate', 0):.1f}% 通过")
        
        if test_results.get("real_model"):
            model = test_results["real_model"]
            status_icon = {"PASS": "✅", "PARTIAL": "⚠️", "FAIL": "❌"}.get(model["status"], "❓")
            print(f"   {status_icon} 真实模型测试: {model.get('success_rate', 0):.1f}% 通过")
            
            # 显示具体模型测试结果
            for test in model.get("tests", []):
                test_icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}.get(test["status"], "❓")
                print(f"      {test_icon} {test['name']}: {test['status']}")
        
        # 建议
        recommendations = report["recommendations"]
        print(f"\n💡 建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        print("\n" + "="*80)

def main():
    """主函数"""
    reporter = ComprehensiveTestReporter()
    
    # 生成报告
    report = reporter.generate_comprehensive_report()
    
    # 保存报告
    report_file = reporter.save_report(report)
    logger.info(f"综合测试报告已保存到: {report_file}")
    
    # 打印摘要
    reporter.print_summary(report)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())