@echo off
chcp 65001 >nul
REM MSearch Windows安装脚本

echo MSearch Windows安装脚本
echo ======================

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.9或更高版本
    pause
    exit /b 1
)

REM 检查pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到pip，请先安装pip
    pause
    exit /b 1
)

REM 安装依赖
echo 正在安装Python依赖...
pip install -r requirements.txt

REM 检查安装是否成功
echo 检查核心模块...
python -c "import src.api.main; print('核心模块导入成功')"

echo.
echo 安装完成！
echo.
echo 使用说明：
echo 1. 启动API服务: python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
echo 2. 启动桌面GUI: python src/gui/main.py
echo.
echo 请确保在项目根目录运行上述命令。
echo.
pause