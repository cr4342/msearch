@echo off
chcp 65001 >nul
REM MSearch Windows安装脚本

echo MSearch Windows安装脚本
echo ======================
echo.

REM 创建日志文件
set LOG_FILE=install_log.txt
echo MSearch 安装日志 > %LOG_FILE%
echo 开始时间: %date% %time% >> %LOG_FILE%
echo ==================== >> %LOG_FILE%

echo 正在检查Python环境...
echo 检查Python环境... >> %LOG_FILE%
echo 正在检查Python环境... >> %LOG_FILE%

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Python已安装
    python --version
    python --version >> %LOG_FILE%
    set PYTHON_CMD=python
) else (
    echo 尝试使用python3...
    python3 --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo Python3已安装
        python3 --version
        python3 --version >> %LOG_FILE%
        set PYTHON_CMD=python3
    ) else (
        echo 错误: 未找到Python，请先安装Python 3.9或更高版本
        echo 错误: 未找到Python，请先安装Python 3.9或更高版本 >> %LOG_FILE%
        echo 请访问 https://www.python.org/downloads/ 下载并安装Python
        echo 请访问 https://www.python.org/downloads/ 下载并安装Python >> %LOG_FILE%
        echo.
        echo 按任意键退出...
        pause >nul
        exit /b 1
    )
)

echo.
echo 正在检查pip...
echo 检查pip... >> %LOG_FILE%

REM 检查pip
pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo pip已安装
    pip --version | findstr "pip"
    pip --version >> %LOG_FILE%
) else (
    echo 错误: 未找到pip，请先安装pip
    echo 错误: 未找到pip，请先安装pip >> %LOG_FILE%
    echo 请确保在安装Python时勾选"Add Python to PATH"选项
    echo 请确保在安装Python时勾选"Add Python to PATH"选项 >> %LOG_FILE%
    echo.
    echo 按任意键退出...
    pause >nul
    exit /b 1
)

echo.
echo 正在安装Python依赖...
echo 安装Python依赖... >> %LOG_FILE%
pip install -r requirements.txt >> %LOG_FILE% 2>&1
if %errorlevel% neq 0 (
    echo 警告: 依赖安装过程中出现错误，请查看日志文件 %LOG_FILE%
    echo 警告: 依赖安装过程中出现错误，请查看日志文件 %LOG_FILE% >> %LOG_FILE%
) else (
    echo Python依赖安装完成
    echo Python依赖安装完成 >> %LOG_FILE%
)

echo.
echo 正在检查核心模块...
echo 检查核心模块... >> %LOG_FILE%
%PYTHON_CMD% -c "import sys; print('Python路径:', sys.executable)" >> %LOG_FILE% 2>&1
%PYTHON_CMD% -c "import src.api.main; print('核心模块导入成功')" >> %LOG_FILE% 2>&1
if %errorlevel% equ 0 (
    echo 核心模块导入成功
    echo 核心模块导入成功 >> %LOG_FILE%
) else (
    echo 警告: 核心模块导入失败，请查看日志文件 %LOG_FILE%
    echo 警告: 核心模块导入失败，请查看日志文件 %LOG_FILE% >> %LOG_FILE%
)

echo.
echo 安装完成！
echo 安装完成！ >> %LOG_FILE%
echo 结束时间: %date% %time% >> %LOG_FILE%
echo.
echo 使用说明：
echo 1. 启动API服务: %PYTHON_CMD% -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
echo 2. 启动桌面GUI: %PYTHON_CMD% src/gui/main.py
echo.
echo 详细日志请查看: %LOG_FILE%
echo.
echo 按任意键退出...
pause >nul