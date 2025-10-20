@echo off
chcp 65001 >nul

:: MSearch 环境配置与部署管理工具 v2.0
:: 整合了环境检查、依赖安装、PyTorch DLL修复、服务部署等功能

:: 获取脚本所在目录和项目根目录
set "SCRIPT_DIR=%~dp0"
pushd %SCRIPT_DIR%..
set "PROJECT_ROOT=%cd%"
popd

:: 日志配置
set "LOG_DIR=%PROJECT_ROOT%\logs"
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%"
set "MM=%dt:~4,2%"
set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%"
set "Min=%dt:~10,2%"
set "Sec=%dt:~12,2%"
set "TIMESTAMP=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"
set "LOG_FILE=%LOG_DIR%\install_configure_%TIMESTAMP%.log"
set "LOG_LEVEL=INFO" :: 可选: DEBUG, INFO, WARNING, ERROR, CRITICAL

:: 创建日志目录
mkdir "%LOG_DIR%" 2>nul

:: 日志级别映射
set "DEBUG_LEVEL=0"
set "INFO_LEVEL=1"
set "WARNING_LEVEL=2"
set "ERROR_LEVEL=3"
set "CRITICAL_LEVEL=4"

:: 获取当前日志级别数值
if /i "%LOG_LEVEL%" == "DEBUG" set "CURRENT_LEVEL=%DEBUG_LEVEL%"
if /i "%LOG_LEVEL%" == "INFO" set "CURRENT_LEVEL=%INFO_LEVEL%"
if /i "%LOG_LEVEL%" == "WARNING" set "CURRENT_LEVEL=%WARNING_LEVEL%"
if /i "%LOG_LEVEL%" == "ERROR" set "CURRENT_LEVEL=%ERROR_LEVEL%"
if /i "%LOG_LEVEL%" == "CRITICAL" set "CURRENT_LEVEL=%CRITICAL_LEVEL%"
if not defined CURRENT_LEVEL set "CURRENT_LEVEL=%INFO_LEVEL%"

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

:: 日志颜色定义
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "WHITE=[97m"

:: 格式化日志时间戳
:GetTimestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%"
set "MM=%dt:~4,2%"
set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%"
set "Min=%dt:~10,2%"
set "Sec=%dt:~12,2%"
set "LOG_TIMESTAMP=%YYYY%-%MM%-%DD% %HH%:%Min%:%Sec%"
goto :eof

:: 通用日志函数
:Log
set "level=%1"
set "message=%2"
set "level_num="

:: 设置日志级别数值
if /i "%level%" == "DEBUG" set "level_num=%DEBUG_LEVEL%"
if /i "%level%" == "INFO" set "level_num=%INFO_LEVEL%"
if /i "%level%" == "WARNING" set "level_num=%WARNING_LEVEL%"
if /i "%level%" == "ERROR" set "level_num=%ERROR_LEVEL%"
if /i "%level%" == "CRITICAL" set "level_num=%CRITICAL_LEVEL%"

:: 检查是否应该记录该级别日志
if %level_num% lss %CURRENT_LEVEL% goto :eof

:: 获取时间戳
call :GetTimestamp

:: 格式化日志信息
set "formatted_log=[%LOG_TIMESTAMP%] [%level%] %message%"

:: 输出到文件
>> "%LOG_FILE%" echo %formatted_log%

:: 输出到控制台（根据级别使用不同颜色）
if /i "%level%" == "DEBUG" (call :ColorEcho %BLUE% "%formatted_log%")
if /i "%level%" == "INFO" (call :ColorEcho %GREEN% "%formatted_log%")
if /i "%level%" == "WARNING" (call :ColorEcho %YELLOW% "%formatted_log%")
if /i "%level%" == "ERROR" (call :ColorEcho %RED% "%formatted_log%")
if /i "%level%" == "CRITICAL" (call :ColorEcho %RED% "%formatted_log%")
goto :eof

:: 便捷日志函数
:LogDebug
call :Log "DEBUG" "%1"
goto :eof

:LogInfo
call :Log "INFO" "%1"
goto :eof

:LogWarning
call :Log "WARNING" "%1"
goto :eof

:LogError
call :Log "ERROR" "%1"
goto :eof

:LogCritical
call :Log "CRITICAL" "%1"
goto :eof

:: 初始化日志
call :LogInfo "==========================================="
call :LogInfo "MSearch环境配置与部署管理工具启动"
call :LogInfo "日志文件: %LOG_FILE%"
call :LogInfo "==========================================="

:show_menu
call :LogInfo "=================================================="
call :LogInfo "           MSearch 环境配置与部署管理工具         "
call :LogInfo "=================================================="
echo.
call :LogInfo "请选择操作："
call :LogInfo "1. 检查运行环境"
call :LogInfo "2. 安装所有依赖包"
call :LogInfo "3. 修复PyTorch DLL问题"
call :LogInfo "4. 运行依赖检查（详细）"
call :LogInfo "5. 一键配置（检查+安装+修复）"
call :LogInfo "6. 下载模型资源"
call :LogInfo "7. 创建虚拟环境"
call :LogInfo "8. 一键部署并启动服务"
call :LogInfo "9. 停止所有服务"
call :LogInfo "0. 退出"
echo.

set /p choice=请输入选择 (0-9): 
echo.

if "%choice%" equ "1" (
    call :check_environment
    goto :menu_after_action
)

if "%choice%" equ "2" (
    call :install_dependencies
    goto :menu_after_action
)

if "%choice%" equ "3" (
    call :fix_pytorch_dll
    goto :menu_after_action
)

if "%choice%" equ "4" (
    call :detailed_dependency_check
    goto :menu_after_action
)

if "%choice%" equ "5" (
    call :one_click_setup
    goto :menu_after_action
)

if "%choice%" equ "6" (
    call :download_model_resources
    goto :menu_after_action
)

if "%choice%" equ "7" (
    call :create_virtual_environment
    goto :menu_after_action
)

if "%choice%" equ "8" (
    call :deploy_and_start_services
    goto :menu_after_action
)

if "%choice%" equ "9" (
    call :stop_all_services
    goto :menu_after_action
)

if "%choice%" equ "0" (
    call :ColorEcho %GREEN% "退出程序..."
    exit /b 0
)

call :ColorEcho %RED% "无效的选择，请重新输入"
goto :show_menu

:menu_after_action
echo.
set /p continue=按回车键返回主菜单...
goto :show_menu

:: 1. 检查运行环境
:check_environment
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "            检查MSearch运行环境                "
call :ColorEcho %BLUE% "==============================================="
echo.

:: 检查Python版本
call :ColorEcho %BLUE% "[检查] Python版本..."
for /f "tokens=2 delims= " %%v in ('python --version') do (
    call :ColorEcho %WHITE% "Python %%v"
)

:: 检查关键库是否安装
echo.
call :ColorEcho %BLUE% "[检查] 核心依赖库..."
python -c "import sys; print(f'Python路径: {sys.path}')"
echo.
python -c "
import importlib
import sys

def check_import(module_name):
    try:
        importlib.import_module(module_name)
        print(f'[✓] {module_name}')
        return True
    except ImportError as e:
        print(f'[✗] {module_name} - {e}')
        return False

modules = [
    # 核心框架
    'fastapi', 'uvicorn', 'pydantic',
    # 图像处理
    'PIL', 'cv2',
    # 机器学习
    'numpy', 'scipy',
    # NLP相关
    'transformers',
    # GUI相关
    'PySide6',
    # 测试框架
    'pytest',
    # 可选组件
    'infinity_emb',
]

success_count = 0
for module in modules:
    if check_import(module):
        success_count += 1

print(f'\n成功加载: {success_count}/{len(modules)} 个模块')

if success_count == len(modules):
    print('\n[✓] 所有依赖库检查通过!')
else:
    print('\n[!] 有依赖库缺失，建议重新运行安装脚本')
"
echo.
call :ColorEcho %BLUE% "[检查] 项目配置文件..."
if exist "%PROJECT_ROOT%\config\config.yml" (
    call :ColorEcho %GREEN% "[✓] config.yml 文件存在"
) else (
    call :ColorEcho %YELLOW% "[!] config.yml 文件不存在，请创建配置文件"
)
echo.
call :ColorEcho %GREEN% "环境检查完成！"
goto :eof

:: 2. 安装所有依赖包
:install_dependencies
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "          安装MSearch依赖包                    "
call :ColorEcho %BLUE% "==============================================="
echo.

:: 检查Python是否安装
call :ColorEcho %BLUE% "[步骤 1] 检查Python环境..."
python --version >nul 2>&1
if %errorlevel% neq 0 (
    call :ColorEcho %RED% "[错误] 未找到Python，请先安装Python 3.9-3.11版本"
    goto :eof
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
    goto :eof
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
    goto :eof
)

:: 更新pip到最新版本
call :ColorEcho %BLUE% "[步骤 3] 更新pip..."
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
if %errorlevel% equ 0 (
    call :ColorEcho %GREEN% "[成功] pip更新完成"
) else (
    call :ColorEcho %YELLOW% "[警告] pip更新失败，但将继续执行"
)

:: 定义集成测试中常用的额外依赖
set "TEST_DEPS=^\
    pytest pytest-cov pytest-html pytest-mock pytest-xdist coverage^\
    httpx pytest-httpx pytest-timeout pytest-docker^\
    ipython jupyter matplotlib numpy scipy pandas^\
    opencv-python-headless pillow scikit-learn scikit-image^\
    transformers datasets torch torchvision torchaudio^\
    librosa moviepy ffmpeg-python^\
    python-multipart uvicorn gunicorn python-magic python-magic-bin"

:: 首先安装requirements.txt中的依赖
call :ColorEcho %BLUE% "[步骤 4] 安装requirements.txt中的依赖..."
python -m pip install -r "%PROJECT_ROOT%\requirements.txt" ^
    -i https://pypi.tuna.tsinghua.edu.cn/simple ^
    --timeout 60 ^
    --retries 3

if %errorlevel% neq 0 (
    call :ColorEcho %RED% "[错误] requirements.txt依赖安装失败"
    call :ColorEcho %YELLOW% "[尝试] 尝试单独安装可能缺失的关键依赖..."
    
    :: 尝试安装常见缺失的关键包
    python -m pip install fastapi uvicorn pydantic pillow opencv-python python-magic python-magic-bin ^
        -i https://pypi.tuna.tsinghua.edu.cn/simple
)

:: 安装测试所需的额外依赖
echo.
call :ColorEcho %BLUE% "[步骤 5] 安装测试环境所需的额外依赖..."
python -m pip install %TEST_DEPS% ^
    -i https://pypi.tuna.tsinghua.edu.cn/simple ^
    --timeout 60 ^
    --retries 3

:: 安装PySide6 GUI框架
echo.
call :ColorEcho %BLUE% "[步骤 6] 安装PySide6 GUI框架..."
python -m pip install PySide6 ^
    -i https://pypi.tuna.tsinghua.edu.cn/simple ^
    --timeout 120 ^
    --retries 3

:: 设置HuggingFace镜像（国内优化）
echo.
call :ColorEcho %BLUE% "[步骤 7] 配置HuggingFace下载环境..."
set "HF_ENDPOINT=https://hf-mirror.com"
set "HF_HOME=%PROJECT_ROOT%\offline\models\huggingface"
set "TRANSFORMERS_CACHE=%HF_HOME%"

:: 检查并安装infinity_emb（用于模型服务）
echo.
call :ColorEcho %BLUE% "[步骤 8] 检查并安装infinity_emb..."
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

call :ColorEcho %GREEN% "依赖安装完成！"
goto :eof

:: 3. 修复PyTorch DLL问题
:fix_pytorch_dll
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "          修复PyTorch DLL问题                  "
call :ColorEcho %BLUE% "==============================================="
echo.

call :ColorEcho %BLUE% "正在检查Python环境..."
python --version

if errorlevel 1 (
    call :ColorEcho %RED% "错误: 未找到Python环境，请确保已正确安装Python并添加到系统PATH"
    goto :eof
)

echo.
call :ColorEcho %BLUE% "正在尝试修复PyTorch DLL问题..."

:: 安装特定版本的PyTorch
call :ColorEcho %BLUE% "尝试安装稳定版本的PyTorch..."
pip install torch==2.0.0+cpu torchvision==0.15.1+cpu -f https://download.pytorch.org/whl/torch_stable.html --force-reinstall

if errorlevel 1 (
    call :ColorEcho %YELLOW% "警告: PyTorch安装失败，尝试降级版本..."
    pip install torch==1.13.1+cpu torchvision==0.14.1+cpu -f https://download.pytorch.org/whl/torch_stable.html --force-reinstall
)

echo.
call :ColorEcho %BLUE% "正在重新安装依赖包..."
pip install -r "%PROJECT_ROOT%\requirements.txt" --force-reinstall

echo.
call :ColorEcho %GREEN% "修复完成！建议重启系统以确保所有更改生效"
echo.
goto :eof

:: 4. 详细的依赖检查
:detailed_dependency_check
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "          详细依赖检查                          "
call :ColorEcho %BLUE% "==============================================="
echo.

:: 设置项目根目录环境变量
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

:: 使用Python脚本来执行详细的依赖检查
python -c "
import os
import sys
import importlib

# 设置项目根目录
project_root = os.environ.get('PROJECT_ROOT', '.')

# 检查模块导入并获取版本
def check_import(module_name, required=True):
    try:
        module = importlib.import_module(module_name)
        # 获取版本信息
        version = 'unknown'
        try:
            if hasattr(module, '__version__'):
                version = module.__version__
            elif module_name == 'PIL':
                from PIL import Image
                version = Image.__version__
        except:
            pass
        
        status = '✓' if required else '✓ (Optional)'
        print(f'[{status}] {module_name} (v{version})')
        return True
    except ImportError as e:
        if required:
            print(f'[✗] {module_name} - {str(e)}')
        else:
            print(f'[!] {module_name} (Optional) - Not installed')
        return False

# 检查配置文件
def check_config_files():
    print('\n=== 配置文件检查 ===')
    config_path = os.path.join(project_root, 'config', 'config.yml')
    if os.path.exists(config_path):
        print(f'[✓] 配置文件存在: {config_path}')
    else:
        print(f'[✗] 配置文件不存在: {config_path}')

# 检查目录结构
def check_directory_structure():
    print('\n=== 目录结构检查 ===')
    dirs_to_check = [
        ('src', True),
        ('tests', True),
        ('config', True),
        ('scripts', True),
        ('offline', False),
        ('offline/models', False),
        ('offline/packages', False),
    ]

    for dir_name, required in dirs_to_check:
        dir_path = os.path.join(project_root, dir_name)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f'[✓] 目录存在: {dir_path}')
        else:
            status = '[✗]' if required else '[!] (Optional)'
            print(f'{status} 目录不存在: {dir_path}')

# 核心模块列表
core_modules = [
    # FastAPI框架
    'fastapi', 'uvicorn', 'pydantic', 'pydantic_settings',
    'python-multipart', 
    
    # 数据处理
    'numpy', 'pandas', 'scipy',
    
    # 图像处理
    'PIL', 
    
    # ML和NLP
    'sklearn', 
    
    # 测试框架
    'pytest', 
    
    # 文件类型检测
    'magic',
]

# 可选模块列表
optional_modules = [
    # GUI相关
    'PySide6',
    
    # ML和NLP
    'torch', 'transformers',
    
    # 图像处理
    'cv2', 'scikit-image',
    
    # 音频处理
    'librosa', 
    
    # 视频处理
    'moviepy', 
]

# 运行检查
print('=== 核心依赖检查 ===')
success_count = 0
for module in core_modules:
    if check_import(module, required=True):
        success_count += 1

print('\n=== 可选依赖检查 ===')
optional_success = 0
for module in optional_modules:
    if check_import(module, required=False):
        optional_success += 1

# 检查配置文件和目录结构
check_config_files()
check_directory_structure()

# 打印整体状态
print('\n=== 环境检查结果 ===')
print(f'核心依赖: {success_count}/{len(core_modules)} 通过')
print(f'可选依赖: {optional_success}/{len(optional_modules)} 通过')

if success_count == len(core_modules):
    print('\n[✓] 所有核心依赖已安装！')
else:
    missing = len(core_modules) - success_count
    print(f'\n[✗] 缺少 {missing} 个核心依赖，请运行安装脚本')
"

goto :eof

:: 5. 一键配置
:one_click_setup
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "              一键配置MSearch环境               "
call :ColorEcho %BLUE% "==============================================="
echo.

call :ColorEcho %GREEN% "[步骤 1] 创建必要的目录结构..."
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

call :ColorEcho %GREEN% "[步骤 2] 安装所有依赖..."
echo.
call :install_dependencies

call :ColorEcho %GREEN% "[步骤 3] 修复PyTorch DLL问题..."
echo.
call :fix_pytorch_dll

call :ColorEcho %GREEN% "[步骤 4] 最终环境检查..."
echo.
call :check_environment

echo.
call :ColorEcho %GREEN% "一键配置完成！MSearch环境已准备就绪。"
goto :eof

:: 6. 下载模型资源
:download_model_resources
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "          下载模型资源                         "
call :ColorEcho %BLUE% "==============================================="
echo.

call :ColorEcho %YELLOW% "提示: 模型资源下载脚本已集成，如需下载完整模型资源，请运行："
call :ColorEcho %WHITE% "    scripts\download_model_resources.bat"
echo.
call :ColorEcho %BLUE% "是否需要运行模型资源下载脚本？"
set /p download_choice=[Y/N]: 

if /i "%download_choice%" equ "Y" (
    if exist "%SCRIPT_DIR%download_model_resources.bat" (
        call "%SCRIPT_DIR%download_model_resources.bat"
    ) else (
        call :ColorEcho %RED% "错误: 模型资源下载脚本不存在"
    )
)

goto :eof

:: 7. 创建虚拟环境
:create_virtual_environment
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "          创建Python虚拟环境                   "
call :ColorEcho %BLUE% "==============================================="
echo.

set "VENV_DIR=%PROJECT_ROOT%\venv"

if exist "%VENV_DIR%" (
    call :ColorEcho %YELLOW% "[提示] 虚拟环境已存在，是否重新创建？"
    set /p recreate=[Y/N]: 
    
    if /i "%recreate%" equ "Y" (
        call :ColorEcho %BLUE% "[步骤] 删除旧虚拟环境..."
        rmdir /s /q "%VENV_DIR%" 2>nul
        
        call :ColorEcho %BLUE% "[步骤] 创建新虚拟环境..."
        python -m venv "%VENV_DIR%"
        
        if %errorlevel% equ 0 (
            call :ColorEcho %GREEN% "[成功] 虚拟环境重新创建成功"
        ) else (
            call :ColorEcho %RED% "[错误] 创建虚拟环境失败"
        )
    ) else (
        call :ColorEcho %GREEN% "[完成] 保留现有虚拟环境"
    )
) else (
    call :ColorEcho %BLUE% "[步骤] 创建新虚拟环境..."
    python -m venv "%VENV_DIR%"
    
    if %errorlevel% equ 0 (
        call :ColorEcho %GREEN% "[成功] 虚拟环境创建成功"
    ) else (
        call :ColorEcho %RED% "[错误] 创建虚拟环境失败"
    )
)

echo.
call :ColorEcho %BLUE% "虚拟环境路径: %VENV_DIR%"
call :ColorEcho %GREEN% "操作完成！"
goto :eof

:: 8. 一键部署并启动服务
:deploy_and_start_services
call :ColorEcho %BLUE% "=================================================="
call :ColorEcho %GREEN%             MSEARCH 一键部署脚本              
call :ColorEcho %BLUE% "=================================================="
echo.

:: 检查虚拟环境
set "VENV_DIR=%PROJECT_ROOT%\venv"
if not exist "%VENV_DIR%" (
    call :ColorEcho %YELLOW% "[提示] 未找到虚拟环境，正在创建..."
    python -m venv "%VENV_DIR%"
    
    if %errorlevel% neq 0 (
        call :ColorEcho %RED% "[错误] 创建虚拟环境失败"
        goto :eof
    )
)

:: 激活虚拟环境
call :ColorEcho %BLUE% "[步骤1] 激活虚拟环境..."
call "%VENV_DIR%\Scripts\activate"
call :ColorEcho %GREEN% "[成功] 虚拟环境已激活"
echo.

:: 安装依赖包
call :ColorEcho %BLUE% "[步骤2] 安装项目依赖..."

:: 升级pip
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1

:: 尝试离线安装
set "OFFLINE_PACKAGES=%PROJECT_ROOT%\offline\packages\requirements"
if exist "%OFFLINE_PACKAGES%" (
    call :ColorEcho %BLUE% "[子步骤] 尝试从离线包安装..."
    pip install --no-index --find-links="%OFFLINE_PACKAGES%" -r "%PROJECT_ROOT%\requirements.txt" >nul 2>&1
    
    if %errorlevel% neq 0 (
        call :ColorEcho %YELLOW% "[警告] 离线安装失败，尝试在线安装..."
        goto deploy_online_install
    )
    call :ColorEcho %GREEN% "[成功] 依赖包离线安装完成"
) else (
    call :ColorEcho %YELLOW% "[提示] 未找到离线包，尝试在线安装..."
    goto deploy_online_install
)

goto deploy_install_complete

deploy_online_install:
:: 在线安装依赖
pip install -r "%PROJECT_ROOT%\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple

if %errorlevel% neq 0 (
    call :ColorEcho %RED% "[错误] 依赖包安装失败"
    goto :eof
)
call :ColorEcho %GREEN% "[成功] 依赖包在线安装完成"

deploy_install_complete:

:: 创建必要的目录结构
call :ColorEcho %BLUE% "[步骤3] 创建必要的目录结构..."
mkdir "%PROJECT_ROOT%\data" 2>nul
mkdir "%PROJECT_ROOT%\data\database" 2>nul
mkdir "%PROJECT_ROOT%\data\temp" 2>nul
mkdir "%PROJECT_ROOT%\.infinity_cache" 2>nul
mkdir "%PROJECT_ROOT%\offline\models" 2>nul
mkdir "%PROJECT_ROOT%\offline\qdrant_data" 2>nul
call :ColorEcho %GREEN% "[成功] 目录结构创建完成"
echo.

:: 启动Qdrant服务
call :ColorEcho %BLUE% "[步骤4] 启动Qdrant向量数据库服务..."
if exist "%SCRIPT_DIR%\start_qdrant.bat" (
    start "Qdrant" cmd /c "%SCRIPT_DIR%\start_qdrant.bat"
    
    :: 等待Qdrant启动
    call :ColorEcho %YELLOW% "[等待] 正在等待Qdrant服务启动..."
    ping -n 5 127.0.0.1 >nul
    call :ColorEcho %GREEN% "[成功] Qdrant服务已启动"
    echo.
    
    :: 启动主API服务
    call :ColorEcho %BLUE% "[步骤5] 启动msearch主服务..."
    start "MSearch API" cmd /c "cd %PROJECT_ROOT% && call %VENV_DIR%\Scripts\activate && python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"
    
    :: 等待服务初始化
    call :ColorEcho %YELLOW% "[等待] 正在等待服务初始化..."
    ping -n 10 127.0.0.1 >nul
    
    :: 输出部署完成信息
    echo.
    call :ColorEcho %GREEN% "=================================================="
    call :ColorEcho %GREEN% "                部署完成！                        "
    call :ColorEcho %GREEN% "=================================================="
    echo.
    call :ColorEcho %GREEN% "[服务信息]"
    call :ColorEcho %YELLOW% "- API服务地址: http://localhost:8000"
    call :ColorEcho %YELLOW% "- API文档地址: http://localhost:8000/docs"
    call :ColorEcho %YELLOW% "- Qdrant地址: http://localhost:6333"
    echo.
    call :ColorEcho %GREEN% "[使用说明]"
    call :ColorEcho %BLUE% "1. 在浏览器中访问API文档：http://localhost:8000/docs"
    call :ColorEcho %BLUE% "2. 或运行桌面应用：python %PROJECT_ROOT%\src\gui\gui_main.py"
    echo.
    call :ColorEcho %GREEN% "[停止服务]"
    call :ColorEcho %BLUE% "选择菜单中的'9. 停止所有服务'选项停止服务"
    echo.
    call :ColorEcho %YELLOW% "[提示] 首次启动可能需要下载模型文件，这将需要一些时间..."
) else (
    call :ColorEcho %RED% "[错误] Qdrant启动脚本不存在: %SCRIPT_DIR%\start_qdrant.bat"
)

goto :eof

:: 9. 停止所有服务
:stop_all_services
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "          停止所有MSearch服务                  "
call :ColorEcho %BLUE% "==============================================="
echo.

:: 停止Qdrant服务
if exist "%SCRIPT_DIR%\stop_qdrant.bat" (
    call :ColorEcho %BLUE% "[步骤1] 停止Qdrant服务..."
    call "%SCRIPT_DIR%\stop_qdrant.bat"
    call :ColorEcho %GREEN% "[成功] Qdrant服务已停止"
) else (
    call :ColorEcho %YELLOW% "[警告] Qdrant停止脚本不存在，尝试手动关闭"
)

:: 提示关闭API服务窗口
call :ColorEcho %BLUE% "[步骤2] 关闭MSearch API服务窗口..."
call :ColorEcho %YELLOW% "请手动关闭标题为'MSearch API'的命令窗口"

:: 可选：尝试通过taskkill关闭
call :ColorEcho %BLUE% "[可选] 尝试自动关闭API服务进程..."
taskkill /FI "WINDOWTITLE eq MSearch API" /F >nul 2>&1

if %errorlevel% equ 0 (
    call :ColorEcho %GREEN% "[成功] API服务进程已关闭"
) else (
    call :ColorEcho %YELLOW% "[提示] 请确保所有服务窗口都已关闭"
)

echo.
call :ColorEcho %GREEN% "所有服务已停止！"
goto :eof

:: 显示启动信息
echo 按任意键启动MSearch环境配置工具...
pause >nul
call :show_menu