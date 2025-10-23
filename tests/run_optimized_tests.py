"""
优化的测试运行脚本
支持不同测试模式和环境配置
"""
import os
import sys
import argparse
import subprocess
import time
import json
from pathlib import Path


def setup_test_environment():
    """设置测试环境"""
    print("设置测试环境...")
    
    # 设置环境变量
    os.environ['MSEARCH_TEST_MODE'] = '1'
    os.environ['PYTHONPATH'] = str(Path(__file__).parent.parent)
    
    # 创建必要的目录
    test_dirs = [
        'tests/output',
        'tests/logs',
        'tests/temp',
        'data/test_models',
        'logs'
    ]
    
    for dir_path in test_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("测试环境设置完成")


def check_dependencies():
    """检查测试依赖"""
    print("检查测试依赖...")
    
    required_packages = [
        'pytest',
        'pytest-asyncio',
        'pytest-cov',
        'pytest-mock',
        'numpy',
        'pillow'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install " + ' '.join(missing_packages))
        return False
    
    print("依赖检查通过")
    return True


def run_unit_tests(verbose=False, coverage=False):
    """运行单元测试"""
    print("运行单元测试...")
    
    cmd = ['python', '-m', 'pytest', 'tests/unit/', '-v']
    
    if coverage:
        cmd.extend(['--cov=src', '--cov-report=html', '--cov-report=term'])
    
    if verbose:
        cmd.append('-s')
    
    # 添加标记过滤
    cmd.extend(['-m', 'not slow'])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("单元测试输出:")
    print(result.stdout)
    
    if result.stderr:
        print("错误输出:")
        print(result.stderr)
    
    return result.returncode == 0


def run_integration_tests(verbose=False):
    """运行集成测试"""
    print("运行集成测试...")
    
    cmd = ['python', '-m', 'pytest', 'tests/integration/', '-v']
    
    if verbose:
        cmd.append('-s')
    
    # 添加标记过滤
    cmd.extend(['-m', 'not slow and not gpu'])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("集成测试输出:")
    print(result.stdout)
    
    if result.stderr:
        print("错误输出:")
        print(result.stderr)
    
    return result.returncode == 0


def run_performance_tests():
    """运行性能测试"""
    print("运行性能测试...")
    
    cmd = [
        'python', '-m', 'pytest', 
        'tests/', '-v',
        '-m', 'performance',
        '--tb=short'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("性能测试输出:")
    print(result.stdout)
    
    if result.stderr:
        print("错误输出:")
        print(result.stderr)
    
    return result.returncode == 0


def run_timestamp_tests():
    """运行时间戳精度测试"""
    print("运行时间戳精度测试...")
    
    cmd = [
        'python', '-m', 'pytest',
        'tests/', '-v',
        '-m', 'timestamp',
        '--tb=short'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("时间戳测试输出:")
    print(result.stdout)
    
    if result.stderr:
        print("错误输出:")
        print(result.stderr)
    
    return result.returncode == 0


def run_specific_test(test_path, verbose=False):
    """运行特定测试"""
    print(f"运行特定测试: {test_path}")
    
    cmd = ['python', '-m', 'pytest', test_path, '-v']
    
    if verbose:
        cmd.append('-s')
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"测试输出 ({test_path}):")
    print(result.stdout)
    
    if result.stderr:
        print("错误输出:")
        print(result.stderr)
    
    return result.returncode == 0


def generate_test_report(results):
    """生成测试报告"""
    print("生成测试报告...")
    
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'results': results,
        'summary': {
            'total_tests': len(results),
            'passed': sum(1 for r in results.values() if r),
            'failed': sum(1 for r in results.values() if not r)
        }
    }
    
    # 保存报告
    report_file = 'tests/output/test_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # 打印摘要
    print("\n" + "="*50)
    print("测试报告摘要")
    print("="*50)
    print(f"总测试套件: {report['summary']['total_tests']}")
    print(f"通过: {report['summary']['passed']}")
    print(f"失败: {report['summary']['failed']}")
    print(f"成功率: {report['summary']['passed']/report['summary']['total_tests']*100:.1f}%")
    print(f"详细报告: {report_file}")
    print("="*50)
    
    return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MSearch优化测试运行器')
    parser.add_argument('--unit', action='store_true', help='只运行单元测试')
    parser.add_argument('--integration', action='store_true', help='只运行集成测试')
    parser.add_argument('--performance', action='store_true', help='只运行性能测试')
    parser.add_argument('--timestamp', action='store_true', help='只运行时间戳测试')
    parser.add_argument('--test', type=str, help='运行特定测试文件')
    parser.add_argument('--coverage', action='store_true', help='生成覆盖率报告')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--setup-only', action='store_true', help='只设置环境')
    
    args = parser.parse_args()
    
    # 设置测试环境
    setup_test_environment()
    
    if args.setup_only:
        print("环境设置完成，退出")
        return
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 创建测试数据
    print("创建测试数据...")
    try:
        from tests.fixtures.create_test_data import main as create_test_data
        create_test_data()
    except Exception as e:
        print(f"创建测试数据失败: {e}")
    
    results = {}
    
    # 根据参数运行不同的测试
    if args.test:
        # 运行特定测试
        results['specific_test'] = run_specific_test(args.test, args.verbose)
    elif args.unit:
        # 只运行单元测试
        results['unit_tests'] = run_unit_tests(args.verbose, args.coverage)
    elif args.integration:
        # 只运行集成测试
        results['integration_tests'] = run_integration_tests(args.verbose)
    elif args.performance:
        # 只运行性能测试
        results['performance_tests'] = run_performance_tests()
    elif args.timestamp:
        # 只运行时间戳测试
        results['timestamp_tests'] = run_timestamp_tests()
    else:
        # 运行所有测试
        print("运行完整测试套件...")
        
        results['unit_tests'] = run_unit_tests(args.verbose, args.coverage)
        results['integration_tests'] = run_integration_tests(args.verbose)
        results['timestamp_tests'] = run_timestamp_tests()
        
        # 性能测试可选
        if not args.unit and not args.integration:
            results['performance_tests'] = run_performance_tests()
    
    # 生成测试报告
    report = generate_test_report(results)
    
    # 根据结果设置退出码
    if report['summary']['failed'] > 0:
        print(f"\n有 {report['summary']['failed']} 个测试套件失败")
        sys.exit(1)
    else:
        print("\n所有测试通过！")
        sys.exit(0)


if __name__ == '__main__':
    main()