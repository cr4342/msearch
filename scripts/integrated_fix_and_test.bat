@echo off
chcp 65001 >nul

:: 整合版依赖解决和集成测试运行批处理文件
:: 直接调用Python实现的整合脚本，确保在Windows环境下正常运行

set "SCRIPT_DIR=%~dp0"
pushd %SCRIPT_DIR%..
set "PROJECT_ROOT=%cd%"
popd

echo [INFO] 整合版依赖解决和集成测试脚本
set "PYTHON_SCRIPT=%SCRIPT_DIR%integrated_fix_and_test.py"

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到Python，请先安装Python 3.9-3.11版本
    pause
    exit /b 1
)

:: 确保脚本有执行权限（Windows上主要是确保文件存在）
if not exist "%PYTHON_SCRIPT%" (
    echo [ERROR] Python脚本不存在: %PYTHON_SCRIPT%
    echo [INFO] 请确保已正确创建integrated_fix_and_test.py文件
    pause
    exit /b 1
)

:: 设置环境变量以抑制警告
set "PYTHONWARNINGS=ignore"
set "KMP_DUPLICATE_LIB_OK=True"

:: 直接运行Python整合脚本
echo [INFO] 开始执行整合版Python脚本...
echo ===================================================
python "%PYTHON_SCRIPT%"
set "SCRIPT_RESULT=%errorlevel%"
echo ===================================================

:: 输出执行结果
if %SCRIPT_RESULT% equ 0 (
    echo [SUCCESS] 整合脚本执行成功！
) else (
    echo [FAILURE] 整合脚本执行失败，退出代码: %SCRIPT_RESULT%
)

echo [INFO] 如需重新运行，请再次执行此批处理文件
pause
