@echo off
chcp 65001 >nul

:: msearch 一键部署脚本 (Windows版本)
:: 功能: 自动安装依赖、配置环境、启动所有服务

:: 设置颜色输出
for /f "tokens=1,2 delims=#" %%a in ('"prompt #$E[32m#$E[0m" ^& echo on ^& for %%b in (1) do rem') do (
    set "ESC=%%a"
)

:: 颜色定义
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "RED=%ESC%[31m"
set "BLUE=%ESC%[34m"
set "NC=%ESC%[0m"  :: No Color

:: 输出标题
echo.  
echo %GREEN%==================================================%NC%
echo %GREEN%            MSEARCH 多模态检索系统            %NC%
echo %GREEN%             一键部署脚本 (Windows版)           %NC%
echo %GREEN%==================================================%NC%
echo.

:: 获取脚本所在目录和项目根目录
set "SCRIPT_DIR=%~dp0"
pushd %SCRIPT_DIR%..
set "PROJECT_ROOT=%cd%"
popd

:: 步骤1: 检查Python环境
echo %BLUE%[步骤1] 检查Python环境...%NC%
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%[错误] 未找到Python，请先安装Python 3.9-3.11版本%NC%
    pause
    exit /b 1
)

:: 获取Python版本
for /f "tokens=2 delims= " %%v in ('python --version') do (
    set "PYTHON_VERSION=%%v"
)
echo %GREEN%[成功] Python版本: %PYTHON_VERSION%%NC%
echo.

:: 步骤2: 创建虚拟环境
echo %BLUE%[步骤2] 创建虚拟环境...%NC%
set "VENV_DIR=%PROJECT_ROOT%\venv"

if exist "%VENV_DIR%" (
    echo %YELLOW%[提示] 虚拟环境已存在，正在更新...%NC%
    rmdir /s /q "%VENV_DIR%" 2>nul
)

python -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo %RED%[错误] 创建虚拟环境失败%NC%
    pause
    exit /b 1
)

echo %GREEN%[成功] 虚拟环境创建成功%NC%

:: 激活虚拟环境
call "%VENV_DIR%\Scripts\activate"
echo %GREEN%[成功] 虚拟环境已激活%NC%
echo.

:: 步骤3: 安装依赖包
echo %BLUE%[步骤3] 安装项目依赖...%NC%

:: 先升级pip
echo %BLUE%[子步骤] 升级pip...%NC%
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1

:: 尝试从离线包安装
set "OFFLINE_PACKAGES=%PROJECT_ROOT%\offline\packages\requirements"
if exist "%OFFLINE_PACKAGES%" (
    echo %BLUE%[子步骤] 从离线包安装依赖...%NC%
    pip install --no-index --find-links="%OFFLINE_PACKAGES%" -r "%PROJECT_ROOT%\requirements.txt" >nul 2>&1
    if %errorlevel% neq 0 (
        echo %YELLOW%[警告] 离线安装失败，尝试在线安装...%NC%
        goto online_install
    )
    echo %GREEN%[成功] 依赖包离线安装完成%NC%
) else (
    echo %YELLOW%[提示] 未找到离线包，尝试在线安装...%NC%
    goto online_install
)

goto install_complete

:online_install
:: 在线安装依赖
echo %BLUE%[子步骤] 在线安装依赖...%NC%
pip install -r "%PROJECT_ROOT%\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo %RED%[错误] 依赖包安装失败%NC%
    pause
    exit /b 1
)
echo %GREEN%[成功] 依赖包在线安装完成%NC%

:install_complete

:: 步骤4: 确保必要的目录结构
echo %BLUE%[步骤4] 创建必要的目录结构...%NC%
mkdir "%PROJECT_ROOT%\data" 2>nul
mkdir "%PROJECT_ROOT%\data\database" 2>nul
mkdir "%PROJECT_ROOT%\data\temp" 2>nul
mkdir "%PROJECT_ROOT%\.infinity_cache" 2>nul
mkdir "%PROJECT_ROOT%\offline\models" 2>nul
mkdir "%PROJECT_ROOT%\offline\qdrant_data" 2>nul
echo %GREEN%[成功] 目录结构创建完成%NC%
echo.

:: 步骤5: 启动Qdrant服务
echo %BLUE%[步骤5] 启动Qdrant向量数据库服务...%NC%
start "Qdrant" cmd /c "%SCRIPT_DIR%\start_qdrant.bat"

:: 等待Qdrant启动
echo %YELLOW%[等待] 正在等待Qdrant服务启动...%NC%
ping -n 5 127.0.0.1 >nul
echo %GREEN%[成功] Qdrant服务已启动%NC%
echo.

:: 步骤6: 启动主API服务
echo %BLUE%[步骤6] 启动msearch主服务...%NC%
start "MSearch API" cmd /c "cd %PROJECT_ROOT% && call %VENV_DIR%\Scripts\activate && python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"

:: 等待服务初始化
echo %YELLOW%[等待] 正在等待服务初始化...%NC%
ping -n 10 127.0.0.1 >nul

:: 输出部署完成信息
echo.  
echo %GREEN%==================================================%NC%
echo %GREEN%                部署完成！                        %NC%
echo %GREEN%==================================================%NC%
echo.
echo %GREEN%[服务信息]%NC%
echo %YELLOW%- API服务地址: http://localhost:8000%NC%
echo %YELLOW%- API文档地址: http://localhost:8000/docs%NC%
echo %YELLOW%- Qdrant地址: http://localhost:6333%NC%
echo.
echo %GREEN%[使用说明]%NC%
echo %BLUE%1. 在浏览器中访问API文档：http://localhost:8000/docs%NC%
echo %BLUE%2. 或运行桌面应用：python %PROJECT_ROOT%\src\gui\gui_main.py%NC%
echo.
echo %GREEN%[停止服务]%NC%
echo %BLUE%执行以下命令停止所有服务：%NC%
echo %BLUE%scripts\stop_qdrant.bat && 关闭MSearch API窗口%NC%
echo.
echo %YELLOW%[提示] 首次启动可能需要下载模型文件，这将需要一些时间...%NC%
echo.
pause