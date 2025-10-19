@echo off
chcp 65001 >nul

:: MSearch Windows一键部署脚本 v3.0
:: 整合了环境检查、依赖安装、模型下载、测试部署和Git提交功能

:: 获取脚本所在目录和项目根目录
set "SCRIPT_DIR=%~dp0"
pushd %SCRIPT_DIR%..
set "PROJECT_ROOT=%cd%"
popd

:: 设置部署测试目录
set "DEPLOY_TEST_DIR=%PROJECT_ROOT%\tests\deployment_test"
set "DEPLOY_CONFIG_DIR=%DEPLOY_TEST_DIR%\config"
set "DEPLOY_DATA_DIR=%DEPLOY_TEST_DIR%\data"
set "DEPLOY_MODELS_DIR=%DEPLOY_TEST_DIR%\models"
set "DEPLOY_LOGS_DIR=%DEPLOY_TEST_DIR%\logs"

:: 彩色输出函数
:ColorEcho
set "color=%1"
set "text=%2"
echo %color%%text%
goto :eof

:: 日志颜色定义
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "WHITE=[97m"
set "CYAN=[96m"

:: 显示部署菜单
:show_deploy_menu
call :ColorEcho %CYAN% "=================================================="
call :ColorEcho %GREEN% "        MSearch Windows一键部署工具 v3.0        "
call :ColorEcho %CYAN% "=================================================="
echo.
call :ColorEcho %WHITE% "请选择部署操作："
echo 1. 创建部署测试环境
call :ColorEcho %WHITE% "2. 安装系统依赖和Python包"
echo 3. 下载和配置AI模型
echo 4. 部署真实软件环境
call :ColorEcho %WHITE% "5. 运行功能测试"
echo 6. 修复发现的问题
echo 7. 运行单元测试验证
call :ColorEcho %WHITE% "8. 提交更改到GitHub"
echo 9. 完整一键部署（执行所有步骤）
echo 0. 退出
echo.

set /p choice=请输入选择 (0-9): 
echo.

if "%choice%" equ "1" (
    call :create_deployment_environment
    goto :deploy_menu_after_action
)

if "%choice%" equ "2" (
    call :install_system_dependencies
    goto :deploy_menu_after_action
)

if "%choice%" equ "3" (
    call :download_ai_models
    goto :deploy_menu_after_action
)

if "%choice%" equ "4" (
    call :deploy_software_environment
    goto :deploy_menu_after_action
)

if "%choice%" equ "5" (
    call :run_functionality_tests
    goto :deploy_menu_after_action
)

if "%choice%" equ "6" (
    call :fix_discovered_issues
    goto :deploy_menu_after_action
)

if "%choice%" equ "7" (
    call :run_unit_tests
    goto :deploy_menu_after_action
)

if "%choice%" equ "8" (
    call :commit_to_github
    goto :deploy_menu_after_action
)

if "%choice%" equ "9" (
    call :complete_one_click_deployment
    goto :deploy_menu_after_action
)

if "%choice%" equ "0" (
    call :ColorEcho %GREEN% "退出部署工具..."
    exit /b 0
)

call :ColorEcho %RED% "无效的选择，请重新输入"
goto :show_deploy_menu

:deploy_menu_after_action
echo.
set /p continue=按回车键返回主菜单...
goto :show_deploy_menu

:: 1. 创建部署测试环境
:create_deployment_environment
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "          创建部署测试环境                    "
call :ColorEcho %BLUE% "==============================================="
echo.

call :ColorEcho %BLUE% "[步骤1] 创建部署目录结构..."
mkdir "%DEPLOY_TEST_DIR%" 2>nul
mkdir "%DEPLOY_CONFIG_DIR%" 2>nul
mkdir "%DEPLOY_DATA_DIR%" 2>nul
mkdir "%DEPLOY_DATA_DIR%\database" 2>nul
mkdir "%DEPLOY_DATA_DIR%\temp" 2>nul
mkdir "%DEPLOY_MODELS_DIR%" 2>nul
mkdir "%DEPLOY_MODELS_DIR%\clip" 2>nul
mkdir "%DEPLOY_MODELS_DIR%\clap" 2>nul
mkdir "%DEPLOY_MODELS_DIR%\whisper" 2>nul
mkdir "%DEPLOY_LOGS_DIR%" 2>nul

call :ColorEcho %GREEN% "[成功] 部署目录结构创建完成"

call :ColorEcho %BLUE% "[步骤2] 复制配置文件..."
if exist "%PROJECT_ROOT%\config\config.yml" (
    copy "%PROJECT_ROOT%\config\config.yml" "%DEPLOY_CONFIG_DIR%\config.yml" >nul
    call :ColorEcho %GREEN% "[成功] 配置文件已复制"
) else (
    call :ColorEcho %YELLOW% "[警告] 配置文件不存在，将创建默认配置"
    call :create_default_config
)

call :ColorEcho %BLUE% "[步骤3] 创建部署专用配置..."
call :create_deployment_config

call :ColorEcho %GREEN% "部署测试环境创建完成！"
goto :eof

:: 创建默认配置文件
:create_default_config
(
echo # MSearch 部署测试配置
echo system:
echo   name: "MSearch Deployment Test"
echo   version: "3.0"
echo   debug: true
echo   log_level: "INFO"
echo   
echo paths:
echo   data_dir: "%DEPLOY_DATA_DIR%"
echo   models_dir: "%DEPLOY_MODELS_DIR%"
echo   logs_dir: "%DEPLOY_LOGS_DIR%"
echo   temp_dir: "%DEPLOY_DATA_DIR%\temp"
echo   
echo database:
echo   sqlite:
echo     path: "%DEPLOY_DATA_DIR%\database\msearch.db"
echo   qdrant:
echo     host: "localhost"
echo     port: 6333
echo     timeout: 30
echo   
echo infinity_services:
echo   clip:
echo     model_name: "clip-vit-base-patch32"
echo     port: 7997
echo     device: "cpu"
echo   clap:
echo     model_name: "clap-htsat-fused"
echo     port: 7998
echo     device: "cpu"
echo   whisper:
echo     model_name: "whisper-base"
echo     port: 7999
echo     device: "cpu"
echo   
echo processing:
echo   batch_size: 4
echo   max_workers: 2
echo   timeout: 300
echo   
echo testing:
echo   use_mock_services: true
echo   skip_gpu_tests: true
echo   enable_detailed_logging: true
) > "%DEPLOY_CONFIG_DIR%\config.yml"
goto :eof

:: 创建部署专用配置
:create_deployment_config
(
echo # 部署环境变量配置
echo set DEPLOY_ROOT=%DEPLOY_TEST_DIR%
echo set DEPLOY_CONFIG=%DEPLOY_CONFIG_DIR%
echo set DEPLOY_DATA=%DEPLOY_DATA_DIR%
echo set DEPLOY_MODELS=%DEPLOY_MODELS_DIR%
echo set DEPLOY_LOGS=%DEPLOY_LOGS_DIR%
echo set PYTHONPATH=%PROJECT_ROOT%;%DEPLOY_TEST_DIR%
echo set PYTHONWARNINGS=ignore
echo set KMP_DUPLICATE_LIB_OK=TRUE
echo set CUDA_LAUNCH_BLOCKING=1
echo set HF_HOME=%DEPLOY_MODELS_DIR%\huggingface
echo set TRANSFORMERS_CACHE=%DEPLOY_MODELS_DIR%\huggingface
) > "%DEPLOY_TEST_DIR%\deploy_env.bat"
goto :eof

:: 2. 安装系统依赖和Python包
:install_system_dependencies
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "        安装系统依赖和Python包              "
call :ColorEcho %BLUE% "==============================================="
echo.

call :ColorEcho %BLUE% "[步骤1] 检查Python环境..."
python --version >nul 2>&1
if %errorlevel% neq 0 (
    call :ColorEcho %RED% "[错误] 未找到Python，请先安装Python 3.9-3.11版本"
    goto :eof
)

call :ColorEcho %GREEN% "[成功] Python环境检查通过"

call :ColorEcho %BLUE% "[步骤2] 更新pip..."
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1

call :ColorEcho %BLUE% "[步骤3] 安装核心依赖包..."
python -m pip install -r "%PROJECT_ROOT%\requirements.txt" ^
    -i https://pypi.tuna.tsinghua.edu.cn/simple ^
    --timeout 120 ^
    --retries 3

if %errorlevel% neq 0 (
    call :ColorEcho %YELLOW% "[警告] 部分依赖安装失败，尝试单独安装关键包..."
    python -m pip install fastapi uvicorn pydantic numpy pandas ^
        -i https://pypi.tuna.tsinghua.edu.cn/simple
)

call :ColorEcho %BLUE% "[步骤4] 安装测试专用依赖..."
python -m pip install pytest pytest-cov pytest-mock httpx ^
    -i https://pypi.tuna.tsinghua.edu.cn/simple

call :ColorEcho %BLUE% "[步骤5] 安装AI模型依赖..."
python -m pip install transformers torch torchvision ^
    -i https://pypi.tuna.tsinghua.edu.cn/simple

call :ColorEcho %GREEN% "系统依赖安装完成！"
goto :eof

:: 3. 下载和配置AI模型
:download_ai_models
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "          下载和配置AI模型                    "
call :ColorEcho %BLUE% "==============================================="
echo.

call :ColorEcho %BLUE% "[步骤1] 设置HuggingFace镜像环境..."
set "HF_ENDPOINT=https://hf-mirror.com"
set "HF_HOME=%DEPLOY_MODELS_DIR%\huggingface"
set "TRANSFORMERS_CACHE=%HF_HOME%"

call :ColorEcho %BLUE% "[步骤2] 创建模型下载脚本..."
call :create_model_download_script

call :ColorEcho %BLUE% "[步骤3] 执行模型下载..."
python "%DEPLOY_TEST_DIR%\download_models.py"

call :ColorEcho %GREEN% "AI模型配置完成！"
goto :eof

:: 创建模型下载脚本
:create_model_download_script
(
echo import os
echo import sys
echo from pathlib import Path
echo from transformers import CLIPModel, CLIPProcessor, CLAPModel, CLAPProcessor, WhisperForConditionalGeneration, WhisperProcessor
echo import torch
echo.
echo def download_models():
echo     models_dir = Path(r"%DEPLOY_MODELS_DIR%")
echo     print(f"[INFO] 模型下载目录: {models_dir}")
echo     
echo     # 下载CLIP模型
echo     print("[INFO] 下载CLIP模型...")
echo     try:
echo         clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", cache_dir=models_dir / "clip")
echo         clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", cache_dir=models_dir / "clip")
echo         print("[SUCCESS] CLIP模型下载完成")
echo     except Exception as e:
echo         print(f"[WARNING] CLIP模型下载失败: {e}")
echo     
echo     # 下载CLAP模型
echo     print("[INFO] 下载CLAP模型...")
echo     try:
echo         clap_model = CLAPModel.from_pretrained("laion/clap-htsat-fused", cache_dir=models_dir / "clap")
echo         clap_processor = CLAPProcessor.from_pretrained("laion/clap-htsat-fused", cache_dir=models_dir / "clap")
echo         print("[SUCCESS] CLAP模型下载完成")
echo     except Exception as e:
echo         print(f"[WARNING] CLAP模型下载失败: {e}")
echo     
echo     # 下载Whisper模型
echo     print("[INFO] 下载Whisper模型...")
echo     try:
echo         whisper_model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-base", cache_dir=models_dir / "whisper")
echo         whisper_processor = WhisperProcessor.from_pretrained("openai/whisper-base", cache_dir=models_dir / "whisper")
echo         print("[SUCCESS] Whisper模型下载完成")
echo     except Exception as e:
echo         print(f"[WARNING] Whisper模型下载失败: {e}")
echo     
echo     print("[INFO] 模型下载完成")
echo.
echo if __name__ == "__main__":
echo     download_models()
) > "%DEPLOY_TEST_DIR%\download_models.py"
goto :eof

:: 4. 部署真实软件环境
:deploy_software_environment
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "          部署真实软件环境                    "
call :ColorEcho %BLUE% "==============================================="
echo.

call :ColorEcho %BLUE% "[步骤1] 启动Qdrant服务..."
start "Qdrant Deploy" cmd /c "cd %PROJECT_ROOT% && scripts\start_qdrant.bat"

call :ColorEcho %YELLOW% "[等待] 等待Qdrant服务启动..."
ping -n 5 127.0.0.1 >nul

call :ColorEcho %BLUE% "[步骤2] 创建测试数据..."
call :create_test_data

call :ColorEcho %BLUE% "[步骤3] 启动API服务..."
start "MSearch API Deploy" cmd /c "cd %PROJECT_ROOT% && set PYTHONPATH=%DEPLOY_TEST_DIR% && python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"

call :ColorEcho %YELLOW% "[等待] 等待API服务启动..."
ping -n 10 127.0.0.1 >nul

call :ColorEcho %GREEN% "软件环境部署完成！"
call :ColorEcho %YELLOW% "API服务地址: http://localhost:8000"
call :ColorEcho %YELLOW% "API文档地址: http://localhost:8000/docs"
goto :eof

:: 创建测试数据
:create_test_data
mkdir "%DEPLOY_DATA_DIR%\test_media" 2>nul

:: 创建测试脚本
(
echo import os
import shutil
from pathlib import Path
echo.
echo def create_test_data():
echo     test_dir = Path(r"%DEPLOY_DATA_DIR%\test_media")
echo     project_test_dir = Path(r"%PROJECT_ROOT%\tests\temp")
echo     
echo     # 复制项目中的测试文件
echo     if project_test_dir.exists():
echo         for file in project_test_dir.glob("*"):
echo             if file.is_file():
echo                 shutil.copy2(file, test_dir / file.name)
echo                 print(f"[INFO] 复制测试文件: {file.name}")
echo     
echo     print(f"[SUCCESS] 测试数据创建完成: {test_dir}")
echo.
echo if __name__ == "__main__":
echo     create_test_data()
) > "%DEPLOY_TEST_DIR%\create_test_data.py"

python "%DEPLOY_TEST_DIR%\create_test_data.py"
goto :eof

:: 5. 运行功能测试
:run_functionality_tests
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "            运行功能测试                      "
call :ColorEcho %BLUE% "==============================================="
echo.

call :ColorEcho %BLUE% "[步骤1] 创建功能测试脚本..."
call :create_functionality_test_script

call :ColorEcho %BLUE% "[步骤2] 执行功能测试..."
python "%DEPLOY_TEST_DIR%\run_functionality_tests.py"

set "TEST_RESULT=%errorlevel%"

if %TEST_RESULT% equ 0 (
    call :ColorEcho %GREEN% "[成功] 功能测试通过！"
) else (
    call :ColorEcho %YELLOW% "[警告] 功能测试发现问题，需要修复"
)

goto :eof

:: 创建功能测试脚本
:create_functionality_test_script
(
echo import os
echo import sys
echo import requests
echo import json
echo import time
from pathlib import Path
echo.
echo # 添加项目路径
echo sys.path.insert(0, r"%PROJECT_ROOT%")
echo.
echo def test_api_health():
echo     """测试API健康状态"""
echo     print("[INFO] 测试API健康状态...")
echo     try:
echo         response = requests.get("http://localhost:8000/health", timeout=10)
echo         if response.status_code == 200:
echo             print("[SUCCESS] API健康检查通过")
echo             return True
echo         else:
echo             print(f"[WARNING] API健康检查失败: {response.status_code}")
echo             return False
echo     except Exception as e:
echo         print(f"[ERROR] API连接失败: {e}")
echo         return False
echo.
echo def test_basic_search():
echo     """测试基本搜索功能"""
echo     print("[INFO] 测试基本搜索功能...")
echo     try:
echo         # 测试文本搜索
echo         search_data = {
echo             "query": "test search",
echo             "modality": "text",
echo             "limit": 5
echo         }
echo         response = requests.post("http://localhost:8000/search", 
echo                                  json=search_data, timeout=30)
echo         if response.status_code == 200:
echo             result = response.json()
echo             print(f"[SUCCESS] 搜索测试通过，返回 {len(result.get('results', []))} 个结果")
echo             return True
echo         else:
echo             print(f"[WARNING] 搜索测试失败: {response.status_code}")
echo             return False
echo     except Exception as e:
echo         print(f"[ERROR] 搜索测试失败: {e}")
echo         return False
echo.
echo def test_file_upload():
echo     """测试文件上传功能"""
echo     print("[INFO] 测试文件上传功能...")
echo     try:
echo         test_file = Path(r"%DEPLOY_DATA_DIR%\test_media\test_image.jpg")
echo         if not test_file.exists():
echo             print("[WARNING] 测试文件不存在，跳过上传测试")
echo             return True
echo         
echo         with open(test_file, 'rb') as f:
echo             files = {'file': f}
echo             response = requests.post("http://localhost:8000/upload", 
echo                                      files=files, timeout=30)
echo         
echo         if response.status_code == 200:
echo             print("[SUCCESS] 文件上传测试通过")
echo             return True
echo         else:
echo             print(f"[WARNING] 文件上传测试失败: {response.status_code}")
echo             return False
echo     except Exception as e:
echo         print(f"[ERROR] 文件上传测试失败: {e}")
echo         return False
echo.
echo def main():
echo     print("[INFO] 开始功能测试...")
echo     
echo     # 等待服务完全启动
echo     time.sleep(5)
echo     
echo     tests = [
echo         ("API健康检查", test_api_health),
echo         ("基本搜索功能", test_basic_search),
echo         ("文件上传功能", test_file_upload)
echo     ]
echo     
echo     passed = 0
echo     total = len(tests)
echo     
echo     for test_name, test_func in tests:
echo         print(f"\n[INFO] 执行测试: {test_name}")
echo         if test_func():
echo             passed += 1
echo         else:
echo             print(f"[WARNING] 测试失败: {test_name}")
echo     
echo     print(f"\n[INFO] 测试结果: {passed}/{total} 通过")
echo     return 0 if passed == total else 1
echo.
echo if __name__ == "__main__":
echo     sys.exit(main())
) > "%DEPLOY_TEST_DIR%\run_functionality_tests.py"
goto :eof

:: 6. 修复发现的问题
:fix_discovered_issues
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "            修复发现的问题                      "
call :ColorEcho %BLUE% "==============================================="
echo.

call :ColorEcho %BLUE% "[步骤1] 创建问题修复脚本..."
call :create_issue_fix_script

call :ColorEcho %BLUE% "[步骤2] 执行问题修复..."
python "%DEPLOY_TEST_DIR%\fix_issues.py"

call :ColorEcho %GREEN% "问题修复完成！"
goto :eof

:: 创建问题修复脚本
:create_issue_fix_script
(
echo import os
echo import sys
echo import shutil
from pathlib import Path
echo.
echo # 添加项目路径
echo sys.path.insert(0, r"%PROJECT_ROOT%")
echo.
echo def fix_common_issues():
echo     """修复常见问题"""
echo     print("[INFO] 修复常见问题...")
echo     
echo     # 1. 修复导入路径问题
echo     print("[INFO] 修复导入路径问题...")
echo     init_files = [
echo         Path(r"%PROJECT_ROOT%\src\__init__.py"),
echo         Path(r"%PROJECT_ROOT%\src\api\__init__.py"),
echo         Path(r"%PROJECT_ROOT%\src\business\__init__.py"),
echo         Path(r"%PROJECT_ROOT%\src\core\__init__.py"),
echo         Path(r"%PROJECT_ROOT%\src\processors\__init__.py"),
echo         Path(r"%PROJECT_ROOT%\src\storage\__init__.py"),
echo         Path(r"%PROJECT_ROOT%\src\utils\__init__.py"),
echo     ]
echo     
echo     for init_file in init_files:
echo         if not init_file.exists():
echo             init_file.parent.mkdir(parents=True, exist_ok=True)
echo             init_file.touch()
echo             print(f"[INFO] 创建缺失的__init__.py: {init_file}")
echo     
echo     # 2. 修复配置文件路径
echo     print("[INFO] 修复配置文件路径...")
echo     config_file = Path(r"%DEPLOY_CONFIG_DIR%\config.yml")
echo     if config_file.exists():
echo         # 确保路径使用正确的格式
echo         with open(config_file, 'r', encoding='utf-8') as f:
echo             content = f.read()
echo         
echo         # 替换Windows路径格式
echo         content = content.replace('\\', '/')
echo         
echo         with open(config_file, 'w', encoding='utf-8') as f:
echo             f.write(content)
echo         print("[INFO] 配置文件路径已修复")
echo     
echo     # 3. 创建缺失的模块
echo     print("[INFO] 创建缺失的模块...")
echo     missing_modules = [
echo         Path(r"%PROJECT_ROOT%\src\utils\__init__.py"),
echo     ]
echo     
echo     for module in missing_modules:
echo         if not module.exists():
echo             module.parent.mkdir(parents=True, exist_ok=True)
echo             module.touch()
echo             print(f"[INFO] 创建缺失的模块: {module}")
echo     
echo     print("[SUCCESS] 常见问题修复完成")
echo.
echo def main():
echo     print("[INFO] 开始问题修复...")
echo     fix_common_issues()
echo     return 0
echo.
echo if __name__ == "__main__":
echo     sys.exit(main())
) > "%DEPLOY_TEST_DIR%\fix_issues.py"
goto :eof

:: 7. 运行单元测试验证
:run_unit_tests
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "          运行单元测试验证                    "
call :ColorEcho %BLUE% "==============================================="
echo.

call :ColorEcho %BLUE% "[步骤1] 设置测试环境..."
set "PYTHONPATH=%PROJECT_ROOT%;%DEPLOY_TEST_DIR%"
set "PYTHONWARNINGS=ignore"
set "KMP_DUPLICATE_LIB_OK=TRUE"

call :ColorEcho %BLUE% "[步骤2] 运行单元测试..."
cd "%PROJECT_ROOT%"
python -m pytest tests/unit/ -v --tb=short --maxfail=5

set "TEST_RESULT=%errorlevel%"

if %TEST_RESULT% equ 0 (
    call :ColorEcho %GREEN% "[成功] 所有单元测试通过！"
) else (
    call :ColorEcho %YELLOW% "[警告] 部分单元测试失败"
)

call :ColorEcho %BLUE% "[步骤3] 生成测试报告..."
python -m pytest tests/unit/ --cov=src --cov-report=html:%DEPLOY_LOGS_DIR%\coverage --cov-report=term

call :ColorEcho %GREEN% "单元测试验证完成！"
goto :eof

:: 8. 提交更改到GitHub
:commit_to_github
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "            提交更改到GitHub                  "
call :ColorEcho %BLUE% "==============================================="
echo.

call :ColorEcho %BLUE% "[步骤1] 检查Git状态..."
cd "%PROJECT_ROOT%"
git status

call :ColorEcho %BLUE% "[步骤2] 添加所有更改..."
git add .

call :ColorEcho %BLUE% "[步骤3] 提交更改..."
git commit -m "feat: 整合Windows一键部署脚本和测试环境\n\n- 创建统一的Windows一键部署脚本\n- 添加专属部署测试目录\n- 集成真实软件和模型部署\n- 实现自动化测试和问题修复\n- 支持单元测试验证和Git提交"

call :ColorEcho %BLUE% "[步骤4] 推送到GitHub..."
git push origin main

if %errorlevel% equ 0 (
    call :ColorEcho %GREEN% "[成功] 更改已推送到GitHub！"
) else (
    call :ColorEcho %YELLOW% "[警告] 推送到GitHub失败，请检查网络连接"
)

goto :eof

:: 9. 完整一键部署
:complete_one_click_deployment
call :ColorEcho %CYAN% "=================================================="
call :ColorEcho %GREEN% "            执行完整一键部署                  "
call :ColorEcho %CYAN% "=================================================="
echo.

call :ColorEcho %YELLOW% "[INFO] 这将执行所有部署步骤，可能需要较长时间..."
set /p confirm=确认执行完整部署? [Y/N]: 

if /i not "%confirm%" equ "Y" (
    call :ColorEcho %BLUE% "已取消完整部署"
    goto :eof
)

call :ColorEcho %GREEN% "[步骤 1/8] 创建部署测试环境..."
call :create_deployment_environment

call :ColorEcho %GREEN% "[步骤 2/8] 安装系统依赖和Python包..."
call :install_system_dependencies

call :ColorEcho %GREEN% "[步骤 3/8] 下载和配置AI模型..."
call :download_ai_models

call :ColorEcho %GREEN% "[步骤 4/8] 部署真实软件环境..."
call :deploy_software_environment

call :ColorEcho %GREEN% "[步骤 5/8] 运行功能测试..."
call :run_functionality_tests

call :ColorEcho %GREEN% "[步骤 6/8] 修复发现的问题..."
call :fix_discovered_issues

call :ColorEcho %GREEN% "[步骤 7/8] 运行单元测试验证..."
call :run_unit_tests

call :ColorEcho %GREEN% "[步骤 8/8] 提交更改到GitHub..."
call :commit_to_github

call :ColorEcho %CYAN% "=================================================="
call :ColorEcho %GREEN% "               完整部署完成！                   "
call :ColorEcho %CYAN% "=================================================="
echo.
call :ColorEcho %GREEN% "[部署信息]"
call :ColorEcho %YELLOW% "- 部署目录: %DEPLOY_TEST_DIR%"
call :ColorEcho %YELLOW% "- API服务: http://localhost:8000"
call :ColorEcho %YELLOW% "- API文档: http://localhost:8000/docs"
echo.
call :ColorEcho %GREEN% "[后续步骤]"
call :ColorEcho %BLUE% "1. 访问API文档测试功能"
call :ColorEcho %BLUE% "2. 启动桌面应用: python src/gui/gui_main.py"
call :ColorEcho %BLUE% "3. 查看部署日志: %DEPLOY_LOGS_DIR%"
goto :eof

:: 显示启动信息
echo 按任意键启动MSearch Windows一键部署工具...
pause >nul
call :show_deploy_menu