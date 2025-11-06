"""
简化集成测试
测试API路由和核心功能
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_api_structure():
    """测试API结构"""
    try:
        # 测试路由文件是否存在
        route_files = [
            "src/api/routes/face.py",
            "src/api/routes/search.py", 
            "src/api/routes/config.py",
            "src/api/routes/tasks.py",
            "src/api/routes/status.py"
        ]
        
        missing_files = []
        for file_path in route_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if not missing_files:
            print("✅ 所有路由文件都存在")
        else:
            print(f"❌ 缺少路由文件: {missing_files}")
            
        return len(missing_files) == 0
        
    except Exception as e:
        print(f"❌ API结构测试失败: {e}")
        return False

def test_documentation_structure():
    """测试文档结构"""
    try:
        # 检查必需的文档文件
        doc_files = [
            "docs/design.md",
            "docs/requirements.md",
            "docs/development_plan.md",
            "docs/api_documentation.md",
            "docs/test_strategy.md",
            "docs/user_manual.md"
        ]
        
        missing_files = []
        for file_path in doc_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if not missing_files:
            print("✅ 所有必需文档文件都存在")
        else:
            print(f"❌ 缺少文档文件: {missing_files}")
            
        return len(missing_files) == 0
        
    except Exception as e:
        print(f"❌ 文档结构测试失败: {e}")
        return False

def test_core_components():
    """测试核心组件"""
    try:
        # 测试核心模块导入
        core_modules = [
            "src.core.config_manager",
            "src.core.logging_config",
            "src.business.orchestrator",
            "src.business.smart_retrieval",
            "src.storage.vector_store",
            "src.storage.db_adapter"
        ]
        
        failed_imports = []
        for module in core_modules:
            try:
                __import__(module)
            except ImportError as e:
                failed_imports.append(f"{module}: {e}")
        
        if not failed_imports:
            print("✅ 所有核心模块可以导入")
        else:
            print(f"❌ 以下模块导入失败: {failed_imports}")
            
        return len(failed_imports) == 0
        
    except Exception as e:
        print(f"❌ 核心组件测试失败: {e}")
        return False

def test_test_files():
    """测试测试文件结构"""
    try:
        # 检查测试目录结构
        test_dirs = [
            "tests/unit",
            "tests/integration"
        ]
        
        missing_dirs = []
        for dir_path in test_dirs:
            full_path = project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        if not missing_dirs:
            print("✅ 测试目录结构正确")
        else:
            print(f"❌ 缺少测试目录: {missing_dirs}")
            
        # 检查关键测试文件
        test_files = [
            "tests/unit/test_face_api.py",
            "tests/unit/test_processing_orchestrator.py",
            "tests/integration/test_complete_workflow.py"
        ]
        
        missing_files = []
        for file_path in test_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if not missing_files:
            print("✅ 关键测试文件存在")
        else:
            print(f"❌ 缺少测试文件: {missing_files}")
            
        return len(missing_dirs) == 0 and len(missing_files) == 0
        
    except Exception as e:
        print(f"❌ 测试文件结构测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始集成测试...")
    print("=" * 50)
    
    tests = [
        ("API结构测试", test_api_structure),
        ("文档结构测试", test_documentation_structure),
        ("核心组件测试", test_core_components),
        ("测试文件结构测试", test_test_files)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"集成测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有集成测试通过!")
        return True
    else:
        print("❌ 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
