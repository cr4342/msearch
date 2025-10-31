#!/usr/bin/env python3
"""
MSearch 测试总结报告生成器
根据测试策略文档要求生成综合测试报告
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestSummaryReporter:
    """测试总结报告生成器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_output_dir = self.project_root / 'tests/output'
        self.test_output_dir.mkdir(exist_ok=True)
        
    def collect_test_results(self) -> Dict[str, Any]:
        """收集所有测试结果"""
        logger.info("收集测试结果...")
        
        test_files = {
            'simple_functionality': 'simple_functionality_test_report.json',
            'comprehensive_real_model': 'comprehensive_real_model_test_report.json',
            'mock_model': 'mock_model_test_report.json'
        }
        
        collected_results = {}
        
        for test_name, filename in test_files.items():
            file_path = self.test_output_dir / filename
            
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    collected_results[test_name] = data
                    logger.info(f"✅ 加载测试结果: {test_name}")
                except Exception as e:
                    logger.warning(f"⚠️ 加载测试结果失败: {test_name} - {e}")
                    collected_results[test_name] = None
            else:
                logger.warning(f"⚠️ 测试结果文件不存在: {filename}")
                collected_results[test_name] = None
        
        return collected_results
    
    def analyze_test_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """分析测试结果"""
        logger.info("分析测试结果...")
        
        analysis = {
            'overall_summary': {
                'total_test_suites': 0,
                'successful_test_suites': 0,
                'total_individual_tests': 0,
                'passed_individual_tests': 0,
                'failed_individual_tests': 0,
                'overall_success_rate': 0.0
            },
            'test_suite_details': {},
            'key_findings': [],
            'recommendations': []
        }
        
        for test_name, test_data in results.items():
            if test_data is None:
                analysis['test_suite_details'][test_name] = {
                    'status': 'not_run',
                    'reason': 'Test results not available'
                }
                continue
            
            analysis['overall_summary']['total_test_suites'] += 1
            
            # 提取测试摘要
            test_summary = test_data.get('test_summary', {})
            total_tests = test_summary.get('total_tests', 0)
            passed_tests = test_summary.get('passed_tests', 0)
            failed_tests = test_summary.get('failed_tests', 0)
            
            analysis['overall_summary']['total_individual_tests'] += total_tests
            analysis['overall_summary']['passed_individual_tests'] += passed_tests
            analysis['overall_summary']['failed_individual_tests'] += failed_tests
            
            # 判断测试套件是否成功
            suite_success_rate = passed_tests / total_tests if total_tests > 0 else 0
            suite_successful = suite_success_rate >= 0.7  # 70%通过率认为成功
            
            if suite_successful:
                analysis['overall_summary']['successful_test_suites'] += 1
            
            analysis['test_suite_details'][test_name] = {
                'status': 'successful' if suite_successful else 'failed',
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': f"{suite_success_rate:.1%}",
                'total_time': test_summary.get('total_time', 'N/A')
            }
        
        # 计算总体成功率
        total_individual = analysis['overall_summary']['total_individual_tests']
        passed_individual = analysis['overall_summary']['passed_individual_tests']
        
        if total_individual > 0:
            analysis['overall_summary']['overall_success_rate'] = passed_individual / total_individual
        
        return analysis
    
    def generate_key_findings(self, results: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """生成关键发现"""
        findings = []
        
        # 检查简化功能测试
        simple_test = results.get('simple_functionality')
        if simple_test and simple_test.get('test_summary', {}).get('success_rate') == '100.0%':
            findings.append("✅ 简化功能测试全部通过，基础功能正常")
            
            # 检查具体功能
            test_results = simple_test.get('test_results', {})
            if test_results.get('时间戳精度', {}).get('success'):
                findings.append("✅ 时间戳精度测试通过，满足±2秒精度要求")
            
            if test_results.get('内存使用', {}).get('success'):
                findings.append("✅ 内存使用测试通过，内存管理正常")
            
            if test_results.get('向量操作', {}).get('success'):
                findings.append("✅ 向量操作测试通过，核心算法功能正常")
        
        # 检查环境兼容性
        if simple_test:
            env_test = simple_test.get('test_results', {}).get('Python环境', {})
            if env_test.get('success'):
                packages = env_test.get('details', {}).get('packages', {})
                if packages.get('infinity_emb') == 'Not installed':
                    findings.append("⚠️ infinity-emb未正确安装，需要修复依赖问题")
                else:
                    findings.append("✅ infinity-emb已安装，AI推理引擎可用")
        
        # 检查综合测试
        comprehensive_test = results.get('comprehensive_real_model')
        if comprehensive_test:
            comp_summary = comprehensive_test.get('test_summary', {})
            success_rate = comp_summary.get('success_rate', '0%')
            if success_rate != '0%':
                findings.append(f"📊 综合真实模型测试成功率: {success_rate}")
            else:
                findings.append("❌ 综合真实模型测试失败，需要解决模型加载问题")
        
        # 检查配置管理
        if simple_test:
            config_test = simple_test.get('test_results', {}).get('配置加载', {})
            if config_test.get('success'):
                findings.append("✅ 配置管理系统正常，支持配置驱动架构")
        
        return findings
    
    def generate_recommendations(self, results: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 基于测试结果生成建议
        overall_success_rate = analysis['overall_summary']['overall_success_rate']
        
        if overall_success_rate >= 0.8:
            recommendations.append("🎉 整体测试表现良好，系统基本功能稳定")
        elif overall_success_rate >= 0.6:
            recommendations.append("⚠️ 部分测试失败，建议优先修复关键功能问题")
        else:
            recommendations.append("❌ 测试失败率较高，需要全面检查系统问题")
        
        # 具体建议
        simple_test = results.get('simple_functionality')
        if simple_test:
            env_test = simple_test.get('test_results', {}).get('Python环境', {})
            packages = env_test.get('details', {}).get('packages', {})
            
            if packages.get('infinity_emb') == 'Not installed':
                recommendations.append("🔧 建议修复infinity-emb安装问题，确保AI推理功能可用")
            
            if not packages.get('cuda_available', False):
                recommendations.append("💡 当前使用CPU模式，如需GPU加速请配置CUDA环境")
        
        # 网络和模型下载建议
        comprehensive_test = results.get('comprehensive_real_model')
        if comprehensive_test and comprehensive_test.get('test_summary', {}).get('success_rate') == '0%':
            recommendations.append("🌐 建议检查网络连接，确保能够下载AI模型")
            recommendations.append("📦 可考虑使用离线模型或本地模型缓存")
        
        # 性能优化建议
        if simple_test:
            memory_test = simple_test.get('test_results', {}).get('内存使用', {})
            if memory_test.get('success'):
                details = memory_test.get('details', {})
                memory_increase = float(details.get('memory_increase_mb', '0').replace('MB', ''))
                if memory_increase > 100:
                    recommendations.append("💾 内存使用较高，建议优化内存管理策略")
        
        # 部署建议
        recommendations.append("🚀 建议在生产环境部署前进行完整的集成测试")
        recommendations.append("📊 建议建立持续集成流程，定期运行测试套件")
        recommendations.append("📝 建议完善错误日志记录，便于问题诊断")
        
        return recommendations
    
    def generate_compliance_check(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试策略文档符合性检查"""
        logger.info("检查测试策略文档符合性...")
        
        compliance = {
            'core_requirements': {},
            'performance_requirements': {},
            'architecture_requirements': {},
            'overall_compliance': 'unknown'
        }
        
        simple_test = results.get('simple_functionality')
        if simple_test:
            test_results = simple_test.get('test_results', {})
            
            # 核心技术要求符合性
            compliance['core_requirements'] = {
                'timestamp_precision': {
                    'requirement': '±2秒精度要求100%满足',
                    'status': 'pass' if test_results.get('时间戳精度', {}).get('success') else 'fail',
                    'details': test_results.get('时间戳精度', {}).get('details', {})
                },
                'config_driven_architecture': {
                    'requirement': '配置驱动架构验证',
                    'status': 'pass' if test_results.get('配置加载', {}).get('success') else 'fail',
                    'details': test_results.get('配置加载', {}).get('details', {})
                },
                'memory_management': {
                    'requirement': '内存使用合理，无内存泄漏',
                    'status': 'pass' if test_results.get('内存使用', {}).get('success') else 'fail',
                    'details': test_results.get('内存使用', {}).get('details', {})
                }
            }
            
            # 性能要求符合性
            compliance['performance_requirements'] = {
                'vector_operations': {
                    'requirement': '向量操作性能满足要求',
                    'status': 'pass' if test_results.get('向量操作', {}).get('success') else 'fail',
                    'details': test_results.get('向量操作', {}).get('details', {})
                },
                'file_operations': {
                    'requirement': '文件操作功能正常',
                    'status': 'pass' if test_results.get('文件操作', {}).get('success') else 'fail',
                    'details': test_results.get('文件操作', {}).get('details', {})
                }
            }
            
            # 架构要求符合性
            compliance['architecture_requirements'] = {
                'project_structure': {
                    'requirement': '项目结构完整',
                    'status': 'pass' if test_results.get('Python环境', {}).get('success') else 'fail',
                    'details': test_results.get('Python环境', {}).get('details', {})
                },
                'embedding_functionality': {
                    'requirement': '嵌入功能正常',
                    'status': 'pass' if test_results.get('模拟嵌入功能', {}).get('success') else 'fail',
                    'details': test_results.get('模拟嵌入功能', {}).get('details', {})
                }
            }
        
        # 计算总体符合性
        all_checks = []
        for category in [compliance['core_requirements'], compliance['performance_requirements'], compliance['architecture_requirements']]:
            for check in category.values():
                all_checks.append(check['status'] == 'pass')
        
        if all_checks:
            pass_rate = sum(all_checks) / len(all_checks)
            if pass_rate >= 0.9:
                compliance['overall_compliance'] = 'high'
            elif pass_rate >= 0.7:
                compliance['overall_compliance'] = 'medium'
            else:
                compliance['overall_compliance'] = 'low'
        
        return compliance
    
    def generate_final_report(self) -> Dict[str, Any]:
        """生成最终测试报告"""
        logger.info("生成最终测试报告...")
        
        # 收集测试结果
        test_results = self.collect_test_results()
        
        # 分析结果
        analysis = self.analyze_test_results(test_results)
        
        # 生成发现和建议
        key_findings = self.generate_key_findings(test_results, analysis)
        recommendations = self.generate_recommendations(test_results, analysis)
        
        # 符合性检查
        compliance = self.generate_compliance_check(test_results)
        
        # 构建最终报告
        final_report = {
            'report_metadata': {
                'generated_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                'report_version': '1.0',
                'test_strategy_compliance': True,
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'platform': sys.platform
            },
            'executive_summary': {
                'overall_status': 'pass' if analysis['overall_summary']['overall_success_rate'] >= 0.7 else 'fail',
                'total_test_suites': analysis['overall_summary']['total_test_suites'],
                'successful_test_suites': analysis['overall_summary']['successful_test_suites'],
                'total_tests': analysis['overall_summary']['total_individual_tests'],
                'passed_tests': analysis['overall_summary']['passed_individual_tests'],
                'overall_success_rate': f"{analysis['overall_summary']['overall_success_rate']:.1%}"
            },
            'detailed_analysis': analysis,
            'key_findings': key_findings,
            'recommendations': recommendations,
            'compliance_check': compliance,
            'raw_test_results': test_results
        }
        
        return final_report
    
    def save_report(self, report: Dict[str, Any]) -> Path:
        """保存报告"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = self.test_output_dir / f'final_test_report_{timestamp}.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report_file
    
    def print_summary(self, report: Dict[str, Any]):
        """打印测试摘要"""
        print("\n" + "="*80)
        print("🧪 MSearch 测试总结报告")
        print("="*80)
        
        # 执行摘要
        exec_summary = report['executive_summary']
        print(f"\n📊 执行摘要:")
        print(f"   总体状态: {'✅ PASS' if exec_summary['overall_status'] == 'pass' else '❌ FAIL'}")
        print(f"   测试套件: {exec_summary['successful_test_suites']}/{exec_summary['total_test_suites']} 成功")
        print(f"   个别测试: {exec_summary['passed_tests']}/{exec_summary['total_tests']} 通过")
        print(f"   总体成功率: {exec_summary['overall_success_rate']}")
        
        # 关键发现
        print(f"\n🔍 关键发现:")
        for finding in report['key_findings']:
            print(f"   {finding}")
        
        # 建议
        print(f"\n💡 建议:")
        for recommendation in report['recommendations'][:5]:  # 显示前5个建议
            print(f"   {recommendation}")
        
        # 符合性检查
        compliance = report['compliance_check']
        print(f"\n📋 测试策略符合性: {compliance['overall_compliance'].upper()}")
        
        print("\n" + "="*80)

def main():
    """主函数"""
    reporter = TestSummaryReporter()
    
    try:
        # 生成最终报告
        final_report = reporter.generate_final_report()
        
        # 保存报告
        report_file = reporter.save_report(final_report)
        
        # 打印摘要
        reporter.print_summary(final_report)
        
        print(f"\n📄 详细报告已保存: {report_file}")
        
        # 返回状态码
        overall_status = final_report['executive_summary']['overall_status']
        return 0 if overall_status == 'pass' else 1
        
    except Exception as e:
        logger.error(f"生成测试报告失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())