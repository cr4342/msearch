@echo off
setlocal enabledelayedexpansion

:: msearch Windows部署脚本
:: 支持离线部署和在线部署两种模式

:: 获取脚本所在目录
set SCRIPT_DIR=%~dp0
for %%i in ("%SCRIPT_DIR:~0,-1%") do set PROJECT_ROOT=%%~dpi
set PROJECT_ROOT=%PROJECT_ROOT:~0,-1%

:: 颜色定义
set GREEN=[0;32m
set RED=[0;31m
set YELLOW=[1;33m
set BLUE=[0;34m
set NC=[0m

:: 日志函数
:log_info
echo %GREEN%[INFO]%NC% %~1
goto :eof

:log_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:log_error
echo %RED%[ERROR]%NC% %~1
goto :eof

:log_debug
echo %BLUE%[DEBUG]%NC% %~1
goto :eof

:: 显示帮助信息
:show_help
echo msearch Windows部署脚本
echo.
echo 用法: %0 [选项]
echo.
echo 选项:
echo   -h, --help     显示此帮助信息
echo   -o, --offline  离线部署模式
echo   -f, --force    强制重新部署（删除现有资源）
echo.
echo 示例:
echo   %0              >> 在线部署
echo   %0 -o           >> 离线部署
echo   %0 -f           >> 强制重新部署
goto :eof

:: 解析命令行参数
set OFFLINE_MODE=false
set FORCE_MODE=false

:parse_args
if "%~1"=="" goto :args_parsed
if "%~1"=="-h" goto :show_help
if "%~1"=="--help" goto :show_help
if "%~1"=="-o" (
    set OFFLINE_MODE=true
    shift
    goto :parse_args
)
if "%~1"=="--offline" (
    set OFFLINE_MODE=true
    shift
    goto :parse_args
)
if "%~1"=="-f" (
    set FORCE_MODE=true
    shift
    goto :parse_args
)
if "%~1"=="--force" (
    set FORCE_MODE=true
    shift
    goto :parse_args
)
call :log_error "未知选项: %~1"
call :show_help
exit /b 1

:args_parsed

call :log_info "开始部署 msearch 项目..."
call :log_info "部署模式: %OFFLINE_MODE%"
call :log_info "强制模式: %FORCE_MODE%"

:: 检查是否需要强制重新部署
if "%FORCE_MODE%"=="true" (
    call :log_info "强制重新部署模式已启用"
    set /p CONFIRM="这将删除现有的离线资源，是否继续？(y/N): "
    if /i not "!CONFIRM!"=="y" (
        call :log_info "取消强制重新部署"
        exit /b 0
    )
    call :log_info "删除现有离线资源..."
    if exist "%PROJECT_ROOT%\offline\" (
        rmdir /s /q "%PROJECT_ROOT%\offline\"
    )
    call :log_info "现有离线资源已删除"
)

:: 创建必要的目录
if not exist "%PROJECT_ROOT%\offline\models\" mkdir "%PROJECT_ROOT%\offline\models\"
if not exist "%PROJECT_ROOT%\offline\packages\" mkdir "%PROJECT_ROOT%\offline\packages\"
if not exist "%PROJECT_ROOT%\logs\" mkdir "%PROJECT_ROOT%\logs\"

call :log_info "检查系统环境..."

:: 检查系统环境
call :check_environment

:: 检查离线资源
call :check_offline_resources

:: 设置国内镜像源
call :setup_china_mirrors

:: 安装Python依赖
call :install_python_dependencies

:: 下载模型文件（在线模式）
if "%OFFLINE_MODE%"=="false" (
    call :download_models
)

:: 启动服务
call :start_services

:: 验证安装
call :verify_installation

call :log_info "部署完成！"
call :log_info ""
call :log_info "下一步操作:"
call :log_info "1. 启动服务: scripts\start_infinity_services.bat"
call :log_info "2. 启动API服务: python src\api\main.py"
call :log_info ""
call :log_info "离线部署说明:"
call :log_info "如需进行离线部署，请将整个项目目录（包括offline文件夹）复制到目标机器，然后运行:"
call :log_info "  scripts\deploy_msearch_windows.bat --offline"

goto :eof

:: 检查系统环境
:check_environment
call :log_info "检查系统环境..."

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    call :log_error "未检测到 Python，请先安装 Python"
    exit /b 1
) else (
    for /f "tokens=*" %%a in ('python --version 2^>nul') do set PYTHON_VERSION=%%a
    call :log_info "检测到 Python: !PYTHON_VERSION!"
)

:: 检查pip
pip --version >nul 2>&1
if errorlevel 1 (
    call :log_warning "未检测到 pip，将尝试使用 python -m pip"
    python -m pip --version >nul 2>&1
    if errorlevel 1 (
        call :log_error "未检测到 pip，请先安装 pip"
        exit /b 1
    )
) else (
    call :log_info "检测到 pip"
)

:: 检查Git
git --version >nul 2>&1
if errorlevel 1 (
    call :log_error "未检测到 Git，请先安装 Git"
    exit /b 1
) else (
    call :log_info "检测到 Git"
)

:: 检查FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    call :log_warning "未检测到 FFmpeg，某些功能可能无法正常工作"
) else (
    call :log_info "检测到 FFmpeg"
)

call :log_info "系统环境检查完成"
goto :eof

:: 检查离线资源
:check_offline_resources
call :log_info "检查离线资源..."

if exist "%PROJECT_ROOT%\offline\" (
    if exist "%PROJECT_ROOT%\offline\models\" if exist "%PROJECT_ROOT%\offline\packages\" (
        set models_count=0
        set packages_count=0
        for /f %%a in ('dir "%PROJECT_ROOT%\offline\models\" /s /b ^| find /c /v ""') do set models_count=%%a
        for /f %%a in ('dir "%PROJECT_ROOT%\offline\packages\" /s /b ^| find /c /v ""') do set packages_count=%%a
        
        if !models_count! gtr 0 if !packages_count! gtr 0 (
            call :log_info "检测到离线资源:"
            call :log_info "  - 模型文件: !models_count! 个"
            call :log_info "  - 依赖包: !packages_count! 个"
            exit /b 0
        )
    )
)

call :log_info "未检测到完整的离线资源"
exit /b 1

:: 设置国内镜像源
:setup_china_mirrors
call :log_info "设置国内镜像源..."

:: 设置HuggingFace镜像
set HF_ENDPOINT=https://hf-mirror.com
call :log_info "已设置 HF_ENDPOINT=https://hf-mirror.com"

:: 设置PyPI镜像 (清华源)
set PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
call :log_info "已设置 PyPI 镜像源"
goto :eof

:: 安装Python依赖
:install_python_dependencies
call :log_info "安装Python依赖..."

:: 检查requirements.txt是否存在
if not exist "%PROJECT_ROOT%\requirements.txt" (
    call :log_error "未找到 requirements.txt 文件"
    exit /b 1
)

:: 根据部署模式选择安装方式
call :check_offline_resources
if errorlevel 1 (
    if "%OFFLINE_MODE%"=="true" (
        call :log_error "离线模式下未找到离线依赖包"
        exit /b 1
    )
    call :log_info "使用在线模式安装依赖..."
    pip install -r "%PROJECT_ROOT%\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    call :log_info "使用离线模式安装依赖..."
    if not exist "%PROJECT_ROOT%\offline\packages\" (
        call :log_error "离线依赖包目录不存在: %PROJECT_ROOT%\offline\packages\"
        exit /b 1
    )
    pip install --no-index --find-links="%PROJECT_ROOT%\offline\packages\" -r "%PROJECT_ROOT%\requirements.txt"
)

call :log_info "Python依赖安装完成"
goto :eof

:: 下载模型文件
:download_models
call :log_info "下载模型文件..."

:: 检查是否已经存在模型文件
call :check_offline_resources
if errorlevel 0 if "%FORCE_MODE%"=="false" (
    call :log_info "模型文件已存在，跳过下载"
    exit /b 0
)

:: 创建模型目录
if not exist "%PROJECT_ROOT%\offline\models\" mkdir "%PROJECT_ROOT%\offline\models\"

:: 下载模型文件
call :log_info "开始下载模型文件..."

:: 确保huggingface_hub已安装
call :log_info "确保huggingface_hub已安装..."
pip install huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade

:: 下载CLIP模型
call :log_info "下载CLIP模型: openai/clip-vit-base-patch32"
huggingface-cli download --resume-download --local-dir-use-symlinks False "openai/clip-vit-base-patch32" --local-dir "%PROJECT_ROOT%\offline\models\clip-vit-base-patch32"

:: 下载CLAP模型
call :log_info "下载CLAP模型: laion/clap-htsat-fused"
huggingface-cli download --resume-download --local-dir-use-symlinks False "laion/clap-htsat-fused" --local-dir "%PROJECT_ROOT%\offline\models\clap-htsat-fused"

:: 下载Whisper模型
call :log_info "下载Whisper模型: openai/whisper-base"
huggingface-cli download --resume-download --local-dir-use-symlinks False "openai/whisper-base" --local-dir "%PROJECT_ROOT%\offline\models\whisper-base"

call :log_info "模型文件下载完成"
goto :eof

:: 启动服务
:start_services
call :log_info "启动服务..."

:: 生成infinity服务启动脚本
call :log_info "生成infinity服务启动脚本..."
echo @echo off^

echo setlocal^

echo.^r

echo :: 设置模型缓存路径（指向离线下载的模型）^

echo set HF_HOME=%%cd%%\offline\models\huggingface^

echo set TRANSFORMERS_CACHE=%%HF_HOME%%^

echo.^r

echo :: 创建缓存目录^

echo if not exist "%%HF_HOME%%" mkdir "%%HF_HOME%%"^

echo.^r

echo :: 启动CLIP模型服务（端口7997）^

echo echo 启动CLIP模型服务 ^(端口7997^)...^

echo start /b infinity_emb v2 --model-id "%%cd%%\offline\models\clip-vit-base-patch32" --port 7997 --device cpu^

echo.^r

echo :: 启动CLAP模型服务（端口7998）^

echo echo 启动CLAP模型服务 ^(端口7998^)...^

echo start /b infinity_emb v2 --model-id "%%cd%%\offline\models\clap-htsat-fused" --port 7998 --device cpu^

echo.^r

echo :: 启动Whisper模型服务（端口7999）^

echo echo 启动Whisper模型服务 ^(端口7999^)...^

echo start /b infinity_emb v2 --model-id "%%cd%%\offline\models\whisper-base" --port 7999 --device cpu^

echo.^r

echo echo Infinity服务启动完成！^

echo echo 服务健康检查:^r

echo echo curl http://localhost:7997/health^

echo echo curl http://localhost:7998/health^

echo echo curl http://localhost:7999/health^
> "%PROJECT_ROOT%\scripts\start_infinity_services.bat"

:: 生成服务停止脚本
call :log_info "生成服务停止脚本..."
echo @echo off^

echo echo 停止Infinity服务...^

echo.^r

echo :: 查找并结束相关进程^

echo tasklist ^| findstr infinity_emb >nul^

echo if not errorlevel 1 (^

echo   for /f "tokens=2" %%i in ^('tasklist ^| findstr infinity_emb ^| findstr /v findstr'^) do (^

echo     echo 结束进程 %%i^

echo     taskkill /f /pid %%i^

echo   ^)^

echo ^)^

echo.^r

echo echo 所有Infinity服务已停止^
> "%PROJECT_ROOT%\scripts\stop_infinity_services.bat"

call :log_info "服务脚本生成完成"
call :log_info "启动服务: scripts\start_infinity_services.bat"
call :log_info "停止服务: scripts\stop_infinity_services.bat"
goto :eof

:: 验证安装
:verify_installation
call :log_info "验证安装..."

:: 验证Python依赖
call :log_info "验证Python依赖..."
python -c "import torch; import torchvision; import transformers; import numpy; import pandas; print('核心依赖验证通过')" >nul 2>&1
if errorlevel 1 (
    call :log_warning "核心Python依赖验证失败，请检查安装"
) else (
    call :log_info "核心Python依赖验证通过"
)

:: 验证关键依赖
call :log_info "验证关键依赖..."
set key_modules=torch torchvision transformers numpy pandas opencv_python librosa scipy scikit_learn whisper infinity_emb inaspeechsegmenter
for %%m in (!key_modules!) do (
    set module=%%m
    set module=!module: =!
    python -c "import !module:~0,-1!; print('!module:~0,-1! 导入成功')" >nul 2>&1
    if errorlevel 1 (
        call :log_warning "!module:~0,-1! 验证失败，请检查安装"
    ) else (
        call :log_info "!module:~0,-1! 验证通过"
    )
)

:: 验证模型文件
call :log_info "验证模型文件..."
set required_models=clip-vit-base-patch32 clap-htsat-fused whisper-base
for %%m in (!required_models!) do (
    if exist "%PROJECT_ROOT%\offline\models\%%m\" (
        dir "%PROJECT_ROOT%\offline\models\%%m\" /a /b | findstr . >nul
        if errorlevel 1 (
            call :log_warning "模型 %%m 验证失败，目录为空"
        ) else (
            call :log_info "模型 %%m 验证通过"
        )
    ) else (
        call :log_warning "模型 %%m 验证失败，目录不存在"
    )
)

call :log_info "安装验证完成"
goto :eof