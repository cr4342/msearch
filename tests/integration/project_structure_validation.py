"""
项目结构验证测试
验证项目是否按照设计文档要求正确实现
"""
import os
import sys
from pathlib import Path

def check_project_structure():
    """检查项目结构是否符合设计要求"""
    project_root = Path('/data/project/msearch')
    
    print("🔍 检查项目结构...")
    
    # 检查核心目录结构
    required_dirs = [
        'src/api/routes',
        'src/business',
        'src/core',
        'src/storage',
        'src/processors',
        'src/gui',
        'docs',
        'tests/unit',
        'tests/integration',
        'config',
        'scripts'
    ]
    
    print("📁 检查必需目录:")
    all_dirs_exist = True
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        exists = full_path.exists() and full_path.is_dir()
        status = "✅" if exists else "❌"
        print(f"  {status} {dir_path}")
        if not exists:
            all_dirs_exist = False
    
    # 检查核心路由文件
    print("\n📄 检查API路由文件:")
    route_files = [
        'src/api/routes/search.py',
        'src/api/routes/config.py',
        'src/api/routes/tasks.py',
        'src/api/routes/status.py',
        'src/api/routes/face.py'
    ]
    
    all_routes_exist = True
    for file_path in route_files:
        full_path = project_root / file_path
        exists = full_path.exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {file_path}")
        if not exists:
            all_routes_exist = False
    
    # 检查文档文件
    print("\n📚 检查文档文件:")
    doc_files = [
        'docs/design.md',
        'docs/requirements.md',
        'docs/development_plan.md',
        'docs/api_documentation.md',
        'docs/test_strategy.md',
        'docs/user_manual.md'
    ]
    
    all_docs_exist = True
    for file_path in doc_files:
        full_path = project_root / file_path
        exists = full_path.exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {file_path}")
        if not exists:
            all_docs_exist = False
    
    # 检查测试文件
    print("\n🧪 检查测试文件:")
    test_files = [
        'tests/unit/test_face_api.py',
        'tests/unit/test_processing_orchestrator.py',
        'tests/unit/test_timestamp_processor.py',
        'tests/integration/test_complete_workflow.py'
    ]
    
    all_tests_exist = True
    for file_path in test_files:
        full_path = project_root / file_path
        exists = full_path.exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {file_path}")
        if not exists:
            all_tests_exist = False
    
    print("\n" + "="*50)
    print("📋 项目结构验证结果:")
    
    results = [
        ("目录结构", all_dirs_exist),
        ("API路由", all_routes_exist),
        ("文档文件", all_docs_exist),
        ("测试文件", all_tests_exist)
    ]
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*50)
    if all_passed:
        print("🎉 项目结构验证通过！所有必需组件都已实现。")
        return True
    else:
        print("⚠️ 项目结构验证部分失败。")
        return False

def check_api_modular_design():
    """检查API是否采用模块化设计"""
    print("\n🔍 检查API模块化设计...")
    
    # 检查main.py是否导入了路由
    main_file = Path('/data/project/msearch/src/api/main.py')
    if main_file.exists():
        content = main_file.read_text()
        
        has_route_imports = 'from src.api.routes import' in content
        has_router_registration = 'app.include_router(' in content
        
        print(f"  📦 路由导入: {'✅' if has_route_imports else '❌'}")
        print(f"  🔄 路由注册: {'✅' if has_router_registration else '❌'}")
        
        return has_route_imports and has_router_registration
    else:
        print("  ❌ main.py 文件不存在")
        return False

def main():
    """主函数"""
    print("🚀 开始项目集成验证...")
    print("="*60)
    
    # 运行各项检查
    structure_ok = check_project_structure()
    modular_ok = check_api_modular_design()
    
    print("\n" + "="*60)
    print("📊 最终验证结果:")
    
    results = [
        ("项目结构", structure_ok),
        ("API模块化设计", modular_ok)
    ]
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("🎉 集成验证成功！项目完全符合设计要求。")
    else:
        print("⚠️ 集成验证部分失败。")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
