@echo off
chcp 65001 >nul

:: MSearch 环境依赖和模型依赖安装脚本
:: 一键安装所有Python库依赖和模型资源
:: 优化集成测试环境配置

:: 获取脚本所在目录和项目根目录（使用绝对路径）
set "SCRIPT_DIR=%~dp0"
pushd %SCRIPT_DIR%..
set "PROJECT_ROOT=%cd%"
popd

:: 彩色输出函数
:ColorEcho
set "color=%1"
set "text=%2"
for /f "tokens=1,2 delims=#" %%a in ('"prompt $h&for %%b in (1) do rem"') do (
  <nul set /p ".=%%a"
)
echo %color%%text%
for /f "tokens=1,2 delims=#" %%a in ('"prompt $h&for %%b in (1) do rem"') do (
  <nul set /p ".=%%a"
)
echo.
goto :eof

:: 日志函数
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "WHITE=[97m"

call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "          MSearch 依赖安装脚本 v1.0            "
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %WHITE% ""

:: 检查Python是否安装
call :ColorEcho %BLUE% "[步骤 1] 检查Python环境..."
python --version >nul 2>&1
if %errorlevel% neq 0 (
    call :ColorEcho %RED% "[错误] 未找到Python，请先安装Python 3.9-3.11版本"
    pause
    exit /b 1
)

:: 获取Python版本并检查兼容性
for /f "tokens=2 delims= " %%v in ('python --version') do (
    set "PYTHON_VERSION=%%v"
)
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set "PY_MAJOR=%%a"
    set "PY_MINOR=%%b"
)

if %PY_MAJOR% neq 3 (
    call :ColorEcho %RED% "[错误] Python版本必须为3.x，当前版本: %PYTHON_VERSION%"
    pause
    exit /b 1
)

if %PY_MINOR% lss 9 (    
    call :ColorEcho %YELLOW% "[警告] Python版本低于3.9，推荐使用Python 3.9-3.11，当前版本: %PYTHON_VERSION%"
) else if %PY_MINOR% gtr 11 (
    call :ColorEcho %YELLOW% "[警告] Python版本高于3.11，可能存在兼容性问题，当前版本: %PYTHON_VERSION%"
)

call :ColorEcho %GREEN% "[成功] Python环境检测完成: %PYTHON_VERSION%"

:: 检查pip是否可用
call :ColorEcho %BLUE% "[步骤 2] 检查pip环境..."
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    call :ColorEcho %RED% "[错误] 未找到pip，请确保Python正确安装"
    pause
    exit /b 1
)

:: 更新pip到最新版本
call :ColorEcho %BLUE% "[步骤 3] 更新pip..."
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
if %errorlevel% equ 0 (
    call :ColorEcho %GREEN% "[成功] pip更新完成"
) else (
    call :ColorEcho %YELLOW% "[警告] pip更新失败，但将继续执行"
)

:: 安装基础下载工具
echo.
call :ColorEcho %BLUE% "[步骤 4] 安装基础下载工具..."
python -m pip install huggingface_hub requests -i https://pypi.tuna.tsinghua.edu.cn/simple

:: 创建必要的目录结构
echo.
call :ColorEcho %BLUE% "[步骤 5] 创建目录结构..."
mkdir "%PROJECT_ROOT%\offline\packages\requirements" 2>nul
mkdir "%PROJECT_ROOT%\offline\packages\test_deps" 2>nul
mkdir "%PROJECT_ROOT%\offline\packages\pyside6" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\clip-vit-base-patch32" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\clap-htsat-fused" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\whisper-base" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\insightface\models\buffalo_l" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\insightface\models\buffalo_sc" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\huggingface" 2>nul
mkdir "%PROJECT_ROOT%\offline\github" 2>nul
mkdir "%PROJECT_ROOT%\offline\qdrant_data" 2>nul

call :ColorEcho %GREEN% "[成功] 目录结构创建完成"

:: 安装项目核心依赖
echo.
call :ColorEcho %BLUE% "[步骤 6] 安装项目核心依赖包..."

:: 定义集成测试中常用的额外依赖
sets "TEST_DEPS=\
    pytest pytest-cov pytest-html pytest-mock pytest-xdist coverage\
    httpx pytest-httpx pytest-timeout pytest-docker\
    ipython jupyter matplotlib numpy scipy pandas\
    opencv-python-headless pillow scikit-learn scikit-image\
    transformers datasets torch torchvision torchaudio\
    librosa moviepy ffmpeg-python\
    python-multipart uvicorn gunicorn"

:: 首先安装requirements.txt中的依赖
call :ColorEcho %BLUE% "[步骤 6.1] 安装requirements.txt中的依赖..."
python -m pip install -r "%PROJECT_ROOT%\requirements.txt" ^
    -i https://pypi.tuna.tsinghua.edu.cn/simple ^
    --timeout 60 ^
    --retries 3

if %errorlevel% neq 0 (
    call :ColorEcho %RED% "[错误] requirements.txt依赖安装失败"
    call :ColorEcho %YELLOW% "[尝试] 尝试单独安装可能缺失的关键依赖..."
    
    :: 尝试安装常见缺失的关键包
    python -m pip install fastapi uvicorn pydantic pillow opencv-python ^
        -i https://pypi.tuna.tsinghua.edu.cn/simple
)

:: 安装测试所需的额外依赖
echo.
call :ColorEcho %BLUE% "[步骤 6.2] 安装测试环境所需的额外依赖..."
python -m pip install %TEST_DEPS% ^
    -i https://pypi.tuna.tsinghua.edu.cn/simple ^
    --timeout 60 ^
    --retries 3

:: 特别处理inaSpeechSegmenter包
echo.
call :ColorEcho %BLUE% "[步骤 6.3] 特别处理inaSpeechSegmenter包..."
python -m pip install inaspeechsegmenter ^
    -i https://pypi.tuna.tsinghua.edu.cn/simple ^
    --timeout 60 ^
    --retries 3

:: 安装PySide6 GUI框架
echo.
call :ColorEcho %BLUE% "[步骤 7] 安装PySide6 GUI框架..."
python -m pip install PySide6 ^
    -i https://pypi.tuna.tsinghua.edu.cn/simple ^
    --timeout 120 ^
    --retries 3

:: 设置HuggingFace镜像（国内优化）
echo.
call :ColorEcho %BLUE% "[步骤 8] 配置HuggingFace下载环境..."
set "HF_ENDPOINT=https://hf-mirror.com"
set "HF_HOME=%PROJECT_ROOT%\offline\models\huggingface"
set "TRANSFORMERS_CACHE=%HF_HOME%"

:: 检查并安装infinity_emb（用于模型服务）
echo.
call :ColorEcho %BLUE% "[步骤 9] 检查并安装infinity_emb..."
python -c "import infinity_emb" >nul 2>&1
if %errorlevel% neq 0 (
    call :ColorEcho %BLUE% "[安装] 正在安装infinity_emb..."
    python -m pip install infinity-emb ^
        -i https://pypi.tuna.tsinghua.edu.cn/simple ^
        --timeout 60 ^
        --retries 3
    
    if %errorlevel% neq 0 (
        call :ColorEcho %YELLOW% "[警告] infinity_emb安装失败，某些功能可能受限"
    ) else (
        call :ColorEcho %GREEN% "[成功] infinity_emb安装完成"
    )
)

:: 可选下载模型
echo.
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "环境依赖安装基本完成！"
echo.
call :ColorEcho %YELLOW% "注意：如需下载完整模型资源，请运行："
call :ColorEcho %WHITE% "    scripts\download_model_resources.bat"
echo.
call :ColorEcho %BLUE% "==============================================="

:: 生成环境检查脚本
call :ColorEcho %BLUE% "[步骤 10] 生成环境检查脚本..."

python -c "
lines = [
    '@echo off',
    'chcp 65001 >nul',
    '',
    ':: MSearch 环境检查脚本',
    'echo 检查MSearch运行环境...',
    'echo.',
    '',
    ':: 检查Python版本',
    'echo [检查] Python版本...',
    'for /f \"tokens=2 delims= \" %%v in (\'python --version\') do (',
    '    echo Python %%v',
    ')',
    '',
    ':: 检查关键库是否安装',
    'echo.',
    'echo [检查] 核心依赖库...',
    'python -c \"import sys; print(f'Python路径: {sys.path}')\"',
    'echo.',
    'python -c \"',
    'import importlib',
    'import sys',
    '',
    'def check_import(module_name):',
    '    try:',
    '        importlib.import_module(module_name)',
    '        print(f'[✓] {module_name}')',
    '        return True',
    '    except ImportError as e:',
    '        print(f'[✗] {module_name} - {e}')',
    '        return False',
    '',
    'modules = [',
    '    # 核心框架',
    '    \'fastapi\', \'uvicorn\', \'pydantic\',',
    '    # 图像处理',
    '    \'PIL\', \'cv2\',',
    '    # 机器学习',
    '    \'numpy\', \'scipy\',',
    '    # NLP相关',
    '    \'transformers\',',
    '    # GUI相关',
    '    \'PySide6\',',
    '    # 测试框架',
    '    \'pytest\',',
    '    # 可选组件',
    '    \'infinity_emb\',',
    ']',
    '',
    'success_count = 0',
    'for module in modules:',
    '    if check_import(module):',
    '        success_count += 1',
    '',
    'print(f'\n成功加载: {success_count}/{len(modules)} 个模块')',
    '',
    'if success_count == len(modules):',
    '    print('\n[✓] 所有依赖库检查通过!')',
    'else:',
    '    print('\n[!] 有依赖库缺失，建议重新运行安装脚本')',
    '\"'
    '',
    'echo.',
    'echo [检查] 项目配置文件...',
    'if exist \"%~dp0..\config\config.yml\" (',
    '    echo [✓] config.yml 文件存在',
    ') else (',
    '    echo [!] config.yml 文件不存在，请创建配置文件',
    ')',
    '',
    'echo.',
    'echo 环境检查完成！',
    'echo 提示: 如需重新安装依赖，请运行 scripts\install_dependencies.bat',
    'echo 如需下载模型资源，请运行 scripts\download_model_resources.bat',
    'echo.',
    'pause'
]
with open(r'%PROJECT_ROOT%\\scripts\\check_environment.bat', 'w', encoding='utf-8') as f:',
    f.write('\n'.join(lines))
"

:: 生成测试运行脚本
call :ColorEcho %BLUE% "[步骤 11] 生成测试运行脚本..."

python -c "
lines = [
    '@echo off',
    'chcp 65001 >nul',
    '',
    ':: MSearch 测试运行脚本',
    '',
    ':: 获取脚本所在目录',
    'set \"SCRIPT_DIR=%~dp0\"',
    'pushd %SCRIPT_DIR%..',
    'set \"PROJECT_ROOT=%cd%\"',
    'popd',
    '',
    'echo ================================================',
    'echo          MSearch 测试运行脚本',
    'echo ================================================',
    'echo.',
    'echo 选择测试类型:',
    'echo 1. 运行单元测试',
    'echo 2. 运行集成测试',
    'echo 3. 运行所有测试',
    'echo 4. 运行简单集成测试',
    'echo 5. 运行离线集成测试',
    'echo 0. 退出',
    'echo.',
    '',
    'set /p choice=请输入选择 (0-5): ',
    '',
    'if \"%choice%\" equ \"1\" (',
    '    echo 运行单元测试...',
    '    pushd %PROJECT_ROOT%',
    '    python -m pytest tests/unit -v',
    '    popd',
    ')',
    'if \"%choice%\" equ \"2\" (',
    '    echo 运行集成测试...',
    '    pushd %PROJECT_ROOT%',
    '    python -m pytest tests/integration -v',
    '    popd',
    ')',
    'if \"%choice%\" equ \"3\" (',
    '    echo 运行所有测试...',
    '    pushd %PROJECT_ROOT%',
    '    python -m pytest -v',
    '    popd',
    ')',
    'if \"%choice%\" equ \"4\" (',
    '    echo 运行简单集成测试...',
    '    pushd %PROJECT_ROOT%',
    '    python test_integration_simple.py',
    '    popd',
    ')',
    'if \"%choice%\" equ \"5\" (',
    '    echo 运行离线集成测试...',
    '    pushd %PROJECT_ROOT%',
    '    python test_offline_integration.py',
    '    popd',
    ')',
    'if \"%choice%\" equ \"0\" (',
    '    echo 退出脚本...',
    '    exit /b 0',
    ')',
    '',
    'echo.',
    'echo 测试完成！',
    'echo.',
    'pause'
]
with open(r'%PROJECT_ROOT%\\scripts\\run_tests.bat', 'w', encoding='utf-8') as f:',
    f.write('\n'.join(lines))
"

echo.
call :ColorEcho %GREEN% "[成功] 生成了辅助脚本："
call :ColorEcho %WHITE% "    scripts\check_environment.bat  - 环境检查脚本"
call :ColorEcho %WHITE% "    scripts\run_tests.bat         - 测试运行脚本"
echo.

call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "依赖安装脚本执行完成！"
echo.
call :ColorEcho %YELLOW% "建议后续操作："
echo 1. 运行环境检查脚本验证安装：
call :ColorEcho %WHITE% "    scripts\check_environment.bat"
echo.
echo 2. 如需运行测试：
call :ColorEcho %WHITE% "    scripts\run_tests.bat"
echo.
echo 3. 如需下载完整模型资源：
call :ColorEcho %WHITE% "    scripts\download_model_resources.bat"
echo.
call :ColorEcho %BLUE% "==============================================="

pause