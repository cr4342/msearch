@echo off
chcp 65001 >nul

:: MSearch 自动化部署测试脚本
:: 用于真实环境下的部署测试，优先使用离线资源

:: 获取项目根目录
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

:: 设置环境变量
set "PYTHONPATH=%PROJECT_ROOT%;%DEPLOY_TEST_DIR%"
set "PYTHONWARNINGS=ignore"
set "KMP_DUPLICATE_LIB_OK=TRUE"
set "CUDA_LAUNCH_BLOCKING=1"
set "HF_HOME=%DEPLOY_MODELS_DIR%\huggingface"
set "TRANSFORMERS_CACHE=%DEPLOY_MODELS_DIR%\huggingface"

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

call :ColorEcho %CYAN% "=================================================="
call :ColorEcho %GREEN% "        MSearch 自动化部署测试开始             "
call :ColorEcho %CYAN% "=================================================="
echo.

:: 1. 创建部署测试环境
call :ColorEcho %BLUE% "[步骤 1/6] 创建部署测试环境..."
call :create_deployment_environment

:: 2. 安装系统依赖和Python包
call :ColorEcho %BLUE% "[步骤 2/6] 安装系统依赖和Python包..."
call :install_system_dependencies

:: 3. 配置AI模型（使用离线模型）
call :ColorEcho %BLUE% "[步骤 3/6] 配置AI模型..."
call :configure_ai_models

:: 4. 部署真实软件环境
call :ColorEcho %BLUE% "[步骤 4/6] 部署真实软件环境..."
call :deploy_software_environment

:: 5. 运行功能测试
call :ColorEcho %BLUE% "[步骤 5/6] 运行功能测试..."
call :run_functionality_tests

:: 6. 运行单元测试验证
call :ColorEcho %BLUE% "[步骤 6/6] 运行单元测试验证..."
call :run_unit_tests

call :ColorEcho %CYAN% "=================================================="
call :ColorEcho %GREEN% "            自动化部署测试完成                 "
call :ColorEcho %CYAN% "=================================================="
echo.
call :ColorEcho %GREEN% "[部署信息]"
call :ColorEcho %YELLOW% "- 部署目录: %DEPLOY_TEST_DIR%"
call :ColorEcho %YELLOW% "- 日志目录: %DEPLOY_LOGS_DIR%"
echo.
call :ColorEcho %GREEN% "[下一步]"
call :ColorEcho %BLUE% "1. 检查测试结果"
call :ColorEcho %BLUE% "2. 修复发现的问题"
call :ColorEcho %BLUE% "3. 提交更改到GitHub"

goto :eof

:: 1. 创建部署测试环境
:create_deployment_environment
call :ColorEcho %BLUE% "  创建部署目录结构..."
powershell -Command "cd %PROJECT_ROOT%; New-Item -ItemType Directory -Force -Path 'tests\deployment_test\config', 'tests\deployment_test\data\database', 'tests\deployment_test\data\temp', 'tests\deployment_test\models\clip', 'tests\deployment_test\models\clap', 'tests\deployment_test\models\whisper', 'tests\deployment_test\logs' | Out-Null"

call :ColorEcho %BLUE% "  复制配置文件..."
if exist "%PROJECT_ROOT%\config\config.yml" (
    copy "%PROJECT_ROOT%\config\config.yml" "%DEPLOY_CONFIG_DIR%\config.yml" >nul
    call :ColorEcho %GREEN% "  [成功] 配置文件已复制"
) else (
    call :ColorEcho %YELLOW% "  [警告] 配置文件不存在，创建默认配置"
    call :create_default_config
)

call :ColorEcho %BLUE% "  创建部署专用配置..."
call :create_deployment_config

call :ColorEcho %GREEN% "  [完成] 部署测试环境创建完成"
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
echo     model_path: "%PROJECT_ROOT%\offline\models\clip-vit-base-patch32"
echo   clap:
echo     model_name: "clap-htsat-fused"
echo     port: 7998
echo     device: "cpu"
echo     model_path: "%PROJECT_ROOT%\offline\models\clap-htsat-fused"
echo   whisper:
echo     model_name: "whisper-base"
echo     port: 7999
echo     device: "cpu"
echo     model_path: "%PROJECT_ROOT%\offline\models\whisper-base"
echo   
echo processing:
echo   batch_size: 4
echo   max_workers: 2
echo   timeout: 300
echo   
echo testing:
echo   use_mock_services: false
echo   use_offline_models: true
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
call :ColorEcho %BLUE% "  检查Python环境..."
python --version >nul 2>&1
if %errorlevel% neq 0 (
    call :ColorEcho %RED% "  [错误] 未找到Python，请先安装Python 3.9-3.11版本"
    goto :eof
)

call :ColorEcho %GREEN% "  [成功] Python环境检查通过"

call :ColorEcho %BLUE% "  更新pip..."
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1

call :ColorEcho %BLUE% "  优先使用离线包安装依赖..."
set "OFFLINE_PACKAGES=%PROJECT_ROOT%\offline\packages\requirements"
if exist "%OFFLINE_PACKAGES%" (
    call :ColorEcho %BLUE% "  [离线] 从离线包安装核心依赖..."
    python -m pip install --no-index --find-links="%OFFLINE_PACKAGES%" ^
        fastapi uvicorn pydantic numpy pandas ^
        -q >nul 2>&1
    
    call :ColorEcho %BLUE% "  [离线] 从离线包安装AI依赖..."
    python -m pip install --no-index --find-links="%OFFLINE_PACKAGES%" ^
        torch torchvision transformers ^
        -q >nul 2>&1
    
    call :ColorEcho %BLUE% "  [离线] 从离线包安装媒体处理依赖..."
    python -m pip install --no-index --find-links="%OFFLINE_PACKAGES%" ^
        pillow opencv-python librosa soundfile ^
        -q >nul 2>&1
    
    call :ColorEcho %BLUE% "  [离线] 从离线包安装其他依赖..."
    python -m pip install --no-index --find-links="%OFFLINE_PACKAGES%" ^
        pytest httpx qdrant-client sqlalchemy ^
        -q >nul 2>&1
    
    call :ColorEcho %GREEN% "  [成功] 离线包安装完成"
) else (
    call :ColorEcho %YELLOW% "  [警告] 离线包目录不存在，使用在线安装"
    goto install_online
)

call :ColorEcho %BLUE% "  检查并安装缺失的依赖..."
python -c "
import importlib
missing_packages = []

# 检查关键包
packages_to_check = ['fastapi', 'uvicorn', 'pydantic', 'numpy', 'pandas', 
                    'torch', 'transformers', 'pillow', 'cv2', 'librosa',
                    'pytest', 'httpx', 'qdrant_client', 'sqlalchemy']

for pkg in packages_to_check:
    try:
        importlib.import_module(pkg)
        print(f'[✓] {pkg}')
    except ImportError:
        print(f'[✗] {pkg}')
        missing_packages.append(pkg)

if missing_packages:
    print(f'需要安装缺失的包: {missing_packages}')
    exit(1)
else:
    print('所有关键依赖已安装')
    exit(0)
" >nul 2>&1

if %errorlevel% neq 0 (
    call :ColorEcho %YELLOW% "  [警告] 部分依赖缺失，尝试在线安装..."
    goto install_online
) else (
    call :ColorEcho %GREEN% "  [成功] 所有依赖检查通过"
    goto install_complete
)

:install_online
call :ColorEcho %BLUE% "  [在线] 安装缺失的依赖..."
python -m pip install -r "%PROJECT_ROOT%\requirements.txt" ^
    -i https://pypi.tuna.tsinghua.edu.cn/simple ^
    --timeout 120 ^
    --retries 3 ^
    -q >nul 2>&1

:install_complete
call :ColorEcho %GREEN% "  [完成] 系统依赖安装完成"
goto :eof

:: 3. 配置AI模型
:configure_ai_models
call :ColorEcho %BLUE% "  配置离线AI模型..."

call :ColorEcho %BLUE% "  [模型] 检查CLIP模型..."
if exist "%PROJECT_ROOT%\offline\models\clip-vit-base-patch32" (
    call :ColorEcho %GREEN% "  [成功] CLIP模型存在"
    
    :: 创建符号链接或复制模型配置
    if not exist "%DEPLOY_MODELS_DIR%\clip\clip-vit-base-patch32" (
        mklink /D "%DEPLOY_MODELS_DIR%\clip\clip-vit-base-patch32" "%PROJECT_ROOT%\offline\models\clip-vit-base-patch32" >nul 2>&1
        if %errorlevel% neq 0 (
            xcopy /E /I /Y "%PROJECT_ROOT%\offline\models\clip-vit-base-patch32" "%DEPLOY_MODELS_DIR%\clip\clip-vit-base-patch32" >nul 2>&1
        )
    )
) else (
    call :ColorEcho %YELLOW% "  [警告] CLIP模型不存在"
)

call :ColorEcho %BLUE% "  [模型] 检查CLAP模型..."
if exist "%PROJECT_ROOT%\offline\models\clap-htsat-fused" (
    call :ColorEcho %GREEN% "  [成功] CLAP模型存在"
    
    if not exist "%DEPLOY_MODELS_DIR%\clap\clap-htsat-fused" (
        mklink /D "%DEPLOY_MODELS_DIR%\clap\clap-htsat-fused" "%PROJECT_ROOT%\offline\models\clap-htsat-fused" >nul 2>&1
        if %errorlevel% neq 0 (
            xcopy /E /I /Y "%PROJECT_ROOT%\offline\models\clap-htsat-fused" "%DEPLOY_MODELS_DIR%\clap\clap-htsat-fused" >nul 2>&1
        )
    )
) else (
    call :ColorEcho %YELLOW% "  [警告] CLAP模型不存在"
)

call :ColorEcho %BLUE% "  [模型] 检查Whisper模型..."
if exist "%PROJECT_ROOT%\offline\models\whisper-base" (
    call :ColorEcho %GREEN% "  [成功] Whisper模型存在"
    
    if not exist "%DEPLOY_MODELS_DIR%\whisper\whisper-base" (
        mklink /D "%DEPLOY_MODELS_DIR%\whisper\whisper-base" "%PROJECT_ROOT%\offline\models\whisper-base" >nul 2>&1
        if %errorlevel% neq 0 (
            xcopy /E /I /Y "%PROJECT_ROOT%\offline\models\whisper-base" "%DEPLOY_MODELS_DIR%\whisper\whisper-base" >nul 2>&1
        )
    )
) else (
    call :ColorEcho %YELLOW% "  [警告] Whisper模型不存在"
)

call :ColorEcho %GREEN% "  [完成] AI模型配置完成"
goto :eof

:: 4. 部署真实软件环境
:deploy_software_environment
call :ColorEcho %BLUE% "  启动Qdrant服务..."
start "Qdrant Deploy" cmd /c "cd %PROJECT_ROOT% && scripts\start_qdrant.bat"

call :ColorEcho %YELLOW% "  [等待] 等待Qdrant服务启动..."
timeout /t 5 /nobreak >nul

call :ColorEcho %BLUE% "  创建测试数据..."
call :create_test_data

call :ColorEcho %BLUE% "  启动API服务..."
start "MSearch API Deploy" cmd /c "cd %PROJECT_ROOT% && set PYTHONPATH=%DEPLOY_TEST_DIR% && python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"

call :ColorEcho %YELLOW% "  [等待] 等待API服务启动..."
timeout /t 10 /nobreak >nul

call :ColorEcho %GREEN% "  [完成] 软件环境部署完成"
call :ColorEcho %YELLOW% "  API服务地址: http://localhost:8000"
call :ColorEcho %YELLOW% "  API文档地址: http://localhost:8000/docs"
goto :eof

:: 创建测试数据
:create_test_data
mkdir "%DEPLOY_DATA_DIR%\test_media" 2>nul

:: 复制项目中的测试文件
if exist "%PROJECT_ROOT%\tests\temp" (
    xcopy /Y "%PROJECT_ROOT%\tests\temp\*" "%DEPLOY_DATA_DIR%\test_media\" >nul 2>&1
    call :ColorEcho %GREEN% "  [成功] 测试数据已复制"
) else (
    call :ColorEcho %YELLOW% "  [警告] 测试数据不存在"
)
goto :eof

:: 5. 运行功能测试
:run_functionality_tests
call :ColorEcho %BLUE% "  创建功能测试脚本..."
call :create_functionality_test_script

call :ColorEcho %BLUE% "  执行功能测试..."
python "%DEPLOY_TEST_DIR%\run_functionality_tests.py"

set "TEST_RESULT=%errorlevel%"

if %TEST_RESULT% equ 0 (
    call :ColorEcho %GREEN% "  [成功] 功能测试通过！"
) else (
    call :ColorEcho %YELLOW% "  [警告] 功能测试发现问题，需要修复"
)
goto :eof

:: 创建功能测试脚本
:create_functionality_test_script
(
echo import os
echo import sys
import requests
import json
import time
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
echo def test_model_loading():
echo     """测试模型加载"""
echo     print("[INFO] 测试模型加载...")
echo     try:
echo         # 测试CLIP模型
echo         from transformers import CLIPModel, CLIPProcessor
echo         clip_model = CLIPModel.from_pretrained(r"%PROJECT_ROOT%\offline\models\clip-vit-base-patch32", local_files_only=True)
echo         print("[SUCCESS] CLIP模型加载成功")
echo         
echo         # 测试CLAP模型
echo         from transformers import CLAPModel, CLAPProcessor
echo         clap_model = CLAPModel.from_pretrained(r"%PROJECT_ROOT%\offline\models\clap-htsat-fused", local_files_only=True)
echo         print("[SUCCESS] CLAP模型加载成功")
echo         
echo         # 测试Whisper模型
echo         from transformers import WhisperForConditionalGeneration, WhisperProcessor
echo         whisper_model = WhisperForConditionalGeneration.from_pretrained(r"%PROJECT_ROOT%\offline\models\whisper-base", local_files_only=True)
echo         print("[SUCCESS] Whisper模型加载成功")
echo         
echo         return True
echo     except Exception as e:
echo         print(f"[ERROR] 模型加载失败: {e}")
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
echo         ("模型加载测试", test_model_loading)
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

:: 6. 运行单元测试验证
:run_unit_tests
call :ColorEcho %BLUE% "  设置测试环境..."
call :ColorEcho %BLUE% "  运行单元测试..."
cd "%PROJECT_ROOT%"
python -m pytest tests/unit/ -v --tb=short --maxfail=5 -q

set "TEST_RESULT=%errorlevel%"

if %TEST_RESULT% equ 0 (
    call :ColorEcho %GREEN% "  [成功] 所有单元测试通过！"
) else (
    call :ColorEcho %YELLOW% "  [警告] 部分单元测试失败"
)

call :ColorEcho %BLUE% "  生成测试报告..."
python -m pytest tests/unit/ --cov=src --cov-report=html:%DEPLOY_LOGS_DIR%\coverage --cov-report=term-missing -q

call :ColorEcho %GREEN% "  [完成] 单元测试验证完成"
goto :eof