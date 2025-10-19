@echo off
chcp 65001 >nul

:: MSearch 简化测试运行脚本

set "PROJECT_ROOT=%~dp0..\..\"
set "PYTHONPATH=%PROJECT_ROOT%"

echo [INFO] 开始MSearch简化测试...
echo [INFO] 项目根目录: %PROJECT_ROOT%
echo [INFO] Python路径: %PYTHONPATH%

cd /d "%PROJECT_ROOT%"

echo [INFO] 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python环境检查失败
    pause
    exit /b 1
)

echo [INFO] 检查项目结构...
if not exist "src\api\main.py" (
    echo [ERROR] API主文件不存在
    pause
    exit /b 1
)

echo [INFO] 运行简化测试...
python tests\deployment_test\simple_test.py

if %errorlevel% equ 0 (
    echo [SUCCESS] 测试通过
) else (
    echo [ERROR] 测试失败
)

pause