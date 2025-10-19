@echo off
chcp 65001 >nul

:: msearch 本地优先依赖解决和集成测试运行脚本
:: 优先使用本地离线目录中的依赖包，确保集成测试能正确运行

:: 获取脚本所在目录和项目根目录（使用绝对路径）
set "SCRIPT_DIR=%~dp0"
pushd %SCRIPT_DIR%..
set "PROJECT_ROOT=%cd%"
popd

:: 创建日志函数
echo [INFO] 开始解决依赖并运行集成测试...

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到Python，请先安装Python 3.9-3.11版本
    pause
    exit /b 1
)

:: 检查pip是否可用
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到pip，请确保Python正确安装
    pause
    exit /b 1
)

:: 确保使用标准模式运行，不使用兼容模式
if defined COMPATIBILITY_MODE (
    echo [INFO] 移除COMPATIBILITY_MODE环境变量，确保在标准模式下运行
    set "COMPATIBILITY_MODE="
)

:: 设置环境变量来抑制警告和确保正确执行
set "PYTHONWARNINGS=ignore"
set "KMP_DUPLICATE_LIB_OK=True"
set "CUDA_LAUNCH_BLOCKING=1"
set "TEMP_TEST_DIR=%PROJECT_ROOT%\tests\temp"

:: 创建测试临时目录
mkdir "%TEMP_TEST_DIR%" 2>nul

:: 本地优先安装依赖函数
:install_dependency
set "pkg_name=%~1"
set "extra_args=%~2"
set "offline_path=%PROJECT_ROOT%\offline\packages\requirements"
set "online_installed=0"

:: 检查本地是否存在依赖包
if exist "%offline_path%\%pkg_name%*.whl" (
    echo [INFO] 使用本地离线包安装 %pkg_name%
    python -m pip install --no-index --find-links="%offline_path%" %pkg_name% %extra_args% >nul 2>&1
    if %errorlevel% equ 0 (
        echo [SUCCESS] 成功安装本地包: %pkg_name%
        goto :eof
    ) else (
        echo [WARNING] 本地安装失败，尝试在线安装: %pkg_name%
    )
)

:: 本地包不存在或安装失败，尝试在线安装
echo [INFO] 尝试在线安装 %pkg_name%
python -m pip install %pkg_name% %extra_args% -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] 成功在线安装: %pkg_name%
) else (
    echo [ERROR] 安装失败: %pkg_name%
)

goto :eof

:: 特殊处理Python版本兼容性问题
echo [INFO] 检查PyTorch版本...
python -c "import torch; print(f'PyTorch版本: {torch.__version__}')" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] PyTorch未安装，将使用CPU版本安装
    call :install_dependency torch==1.13.1+cpu "--index-url https://download.pytorch.org/whl/cpu"
    call :install_dependency torchvision==0.14.1+cpu "--index-url https://download.pytorch.org/whl/cpu"
) else (
    echo [INFO] PyTorch已安装，跳过安装
)

:: 安装核心依赖
echo [INFO] 安装核心依赖包...
call :install_dependency "transformers>=4.30.0"
call :install_dependency "numpy>=1.24.0"
call :install_dependency "pandas>=2.0.0"
call :install_dependency "fastapi>=0.100.0"
call :install_dependency "uvicorn>=0.23.0"
call :install_dependency "pydantic>=2.0.0"
call :install_dependency "starlette>=0.27.0"

:: 安装媒体处理依赖
echo [INFO] 安装媒体处理依赖包...
call :install_dependency "pillow>=10.0.0"
call :install_dependency "opencv-python>=4.8.0"
call :install_dependency "librosa>=0.10.0"
call :install_dependency "soundfile>=0.12.0"
call :install_dependency "pydub>=0.25.0"

:: 安装AI模型和嵌入引擎
echo [INFO] 安装AI模型相关依赖包...
call :install_dependency "openai-whisper>=20230314"
call :install_dependency "facenet-pytorch>=2.5.0"
call :install_dependency "mtcnn>=0.1.1"
call :install_dependency "scikit-learn>=1.3.0"

:: 特殊处理infinity-emb包
echo [INFO] 特殊处理infinity-emb包...
python -m pip show infinity-emb >nul 2>&1
if %errorlevel% neq 0 (
    call :install_dependency "infinity-emb>=0.0.20"
)

:: 特殊处理insightface包，可能导致问题
echo [INFO] 特殊处理insightface包（可选）...
python -m pip show insightface >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] insightface未安装，测试中可能需要跳过相关功能
)

:: 特殊处理inaSpeechSegmenter包
echo [INFO] 尝试安装inaSpeechSegmenter包...
python -m pip show inaspeechsegmenter >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] inaspeechsegmenter未安装，将在测试中跳过相关功能
)

:: 特殊处理python-magic包，Windows上需要特殊处理
echo [INFO] 特殊处理python-magic包（文件类型检测必需）...
call :install_dependency "python-magic"
call :install_dependency "python-magic-bin"

:: 安装系统工具和工具库
echo [INFO] 安装系统工具和工具库...
call :install_dependency "pyyaml>=6.0.0"
call :install_dependency "colorama>=0.4.0"
call :install_dependency "tqdm>=4.65.0"
call :install_dependency "watchdog>=3.0.0"
call :install_dependency "psutil>=5.9.0"

:: 安装测试相关依赖
echo [INFO] 安装测试相关依赖...
call :install_dependency "pytest>=7.0.0"
call :install_dependency "httpx>=0.25.0"
call :install_dependency "requests>=2.31.0"
call :install_dependency "sqlalchemy>=2.0.0"

:: 特殊处理向量数据库客户端（如无法连接实际服务器，测试会失败）
echo [INFO] 特殊处理向量数据库客户端...
call :install_dependency "qdrant-client>=1.6.0"

:: 创建一个mock的qdrant客户端，解决连接问题
echo [INFO] 创建mock Qdrant客户端...
mkdir "%PROJECT_ROOT%\tests\mocks" 2>nul
(echo import sys
echo sys.modules['qdrant_client'] = type('MockQdrantClient', (object,), {})
echo sys.modules['qdrant_client.QdrantClient'] = type('MockQdrantClient', (object,), {})) > "%PROJECT_ROOT%\tests\mocks\mock_qdrant.py"

:: 修改run_integration_tests_fixed.py，添加mock Qdrant客户端支持
echo [INFO] 准备集成测试环境...
python -c "
import os
import re
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
test_script_path = os.path.join(project_root, 'tests', 'run_integration_tests_fixed.py')

with open(test_script_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 确保脚本不使用兼容模式
if 'COMPATIBILITY_MODE' in content:
    content = re.sub(r'COMPATIBILITY_MODE\s*=\s*.*', '', content)

# 添加mock Qdrant客户端导入
if 'mock_qdrant' not in content:
    mock_import_lines = ''.join([
        'try:\n',
        '    # 添加mock模块路径\n',
        '    sys.path.insert(0, str(Path(__file__).parent / "mocks"))\n',
        '    import mock_qdrant\n',
        '    print("已启用Qdrant客户端mock")\n',
        'except Exception as e:\n',
        '    print(f"Qdrant mock加载失败: {e}")\n',
    ])
    # 在已有的try导入块后添加
    content = re.sub(r'try:\s+from mock_file_type_detector import detect_file_type, get_test_file_path\s+.*?except Exception as e:\s+print\(f"mock加载失败: {e}"\)\s+print\(f"当前Python路径: {sys.path}"\)',
                   lambda m: m.group(0) + '\n\n' + mock_import_lines,
                   content, flags=re.DOTALL)

# 保存修改后的文件
with open(test_script_path, 'w', encoding='utf-8') as f:
    f.write(content)
" >nul 2>&1

if %errorlevel% equ 0 (
    echo [SUCCESS] 成功准备测试环境
) else (
    echo [WARNING] 准备测试环境时出现问题，但将继续尝试运行测试
)

:: 运行集成测试
echo [INFO] 运行集成测试（标准模式）...
echo ===================================================
pushd "%PROJECT_ROOT%"
python tests\run_integration_tests_fixed.py
set "TEST_RESULT=%errorlevel%"
popd

:: 输出测试结果总结
echo ===================================================
if %TEST_RESULT% equ 0 (
    echo [SUCCESS] 集成测试通过！
) else (
    echo [FAILURE] 集成测试失败，退出代码: %TEST_RESULT%
)

echo [INFO] 测试完成。
echo [INFO] 注意事项：
echo [INFO] 1. 如果遇到依赖问题，请确保已运行 download_model_resources.bat 下载离线资源
if not exist "%PROJECT_ROOT%\offline\packages\requirements" (
    echo [WARNING] 离线包目录不存在，请先运行 download_model_resources.bat
)

echo [INFO] 2. 测试结果不包含API基础测试，因为它需要额外的服务支持

echo [INFO] 3. 如果需要完整测试，请确保启动相关服务：
echo [INFO]    - Qdrant向量数据库: scripts\start_qdrant.bat

echo [INFO] 脚本执行完成！
pause
