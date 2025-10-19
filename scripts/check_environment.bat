@echo off
chcp 65001 >nul

:: MSearch 环境检查脚本
:: 用于验证所有关键依赖是否正确安装

:: 获取脚本所在目录和项目根目录
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

:: 设置颜色常量
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "WHITE=[97m"
set "RESET=[0m"

call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "         MSearch 环境检查工具 v1.0             "
call :ColorEcho %BLUE% "==============================================="
echo.

:: 检查Python版本
call :ColorEcho %BLUE% "[检查] Python版本..."
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do (
    call :ColorEcho %GREEN% "[✓] Python %%v"
)

:: 检查pip版本
call :ColorEcho %BLUE% "[检查] pip版本..."
for /f "tokens=1,2 delims= " %%a in ('python -m pip --version') do (
    if "%%a" == "pip" (
        call :ColorEcho %GREEN% "[✓] pip %%b"
    )
)

:: 显示Python路径
echo.
call :ColorEcho %BLUE% "[信息] Python路径..."
python -c "import sys; print(f'Python路径: {sys.path}')"

:: 检查关键依赖库
echo.
call :ColorEcho %BLUE% "[检查] 核心依赖库..."

:: 创建Python脚本进行依赖检查
set "CHECK_SCRIPT=%TEMP%\_msearch_dep_check.py"

python -c "
with open(r'%CHECK_SCRIPT%', 'w', encoding='utf-8') as f:
    f.write('''
import importlib
import sys

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
        
        status = '✓' if required else '✓ (可选)'
        print(f'[{{status}}] {{module_name}} (v{{version}})'.format(status=status, module_name=module_name, version=version))
        return True
    except ImportError as e:
        if required:
            print(f'[✗] {{module_name}} - {{str(e)}}'.format(module_name=module_name, str=lambda x: x))
        else:
            print(f'[!] {{module_name}} (可选) - 未安装'.format(module_name=module_name))
        return False

# 定义核心模块列表
core_modules = [
    # FastAPI框架相关
    'fastapi', 'uvicorn', 'pydantic', 'pydantic_settings',
    'python-multipart', 'uvloop', 'httpx',
    
    # 数据处理
    'numpy', 'pandas', 'scipy',
    
    # 图像处理
    'PIL', 'cv2', 'scikit-image',
    
    # 音频处理
    'librosa', 'inaSpeechSegmenter',
    
    # 视频处理
    'moviepy', 'ffmpeg',
    
    # 机器学习
    'sklearn', 'scikit-learn',
    
    # NLP和模型
    'transformers', 'torch', 'torchvision', 'torchaudio',
    
    # 向量数据库
    'qdrant_client',
    
    # 测试框架
    'pytest', 'pytest-cov', 'coverage',
]

# 定义可选模块列表
optional_modules = [
    # GUI相关
    'PySide6',
    
    # 模型服务
    'infinity_emb',
    
    # 分布式计算
    'dask',
]

# 执行检查
success_count = 0
required_count = len(core_modules)
optional_success = 0
optional_count = len(optional_modules)

print('\n=== 核心依赖检查 ===')
for module in core_modules:
    if check_import(module, required=True):
        success_count += 1

print('\n=== 可选依赖检查 ===')
for module in optional_modules:
    if check_import(module, required=False):
        optional_success += 1

# 检查配置文件
print('\n=== 配置文件检查 ===')
import os
project_root = os.environ.get('PROJECT_ROOT', '.')
config_path = os.path.join(project_root, 'config', 'config.yml')
if os.path.exists(config_path):
    print(f'[✓] 配置文件存在: {config_path}')
else:
    print(f'[✗] 配置文件不存在: {config_path}')

# 检查目录结构
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
        status = '[✗]' if required else '[!] (可选)'
        print(f'{status} 目录不存在: {dir_path}')

# 输出总体状态
print('\n=== 环境检查结果 ===')
print(f'核心依赖: {success_count}/{required_count} 通过')
print(f'可选依赖: {optional_success}/{optional_count} 通过')

if success_count == required_count:
    print('\n[✓] 所有核心依赖已安装完成！')
else:
    missing = required_count - success_count
    print(f'\n[✗] 缺少 {missing} 个核心依赖，请运行安装脚本')
    print('    scripts\install_dependencies.bat')
''')

# 运行检查脚本
python "%CHECK_SCRIPT%"

:: 删除临时脚本
if exist "%CHECK_SCRIPT%" (
    del "%CHECK_SCRIPT%"
)

echo.
echo ===================================================
echo.  环境检查完成！
echo.
echo  提示：
echo  1. 如需重新安装依赖，请运行：
echo     scripts\install_dependencies.bat
echo  
echo  2. 如需下载完整模型资源，请运行：
echo     scripts\download_model_resources.bat
echo  
echo  3. 如需运行测试，请使用：
echo     scripts\run_tests.bat
echo.
echo ===================================================

pause