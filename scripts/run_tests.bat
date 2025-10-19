@echo off
chcp 65001 >nul

:: MSearch 测试运行脚本
:: 提供便捷的测试运行选项

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

:: 测试运行函数
:RunTest
set "test_type=%1"
set "test_command=%~2"
set "test_description=%~3"

echo.
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "开始运行：%test_description%"
call :ColorEcho %BLUE% "==============================================="

pushd %PROJECT_ROOT%
call :ColorEcho %WHITE% "运行命令: %test_command%"
echo.

:: 执行测试命令
%test_command%

:: 检查测试结果
if %errorlevel% equ 0 (
    echo.
    call :ColorEcho %GREEN% "[✓] 测试成功完成！"
) else (
    echo.
    call :ColorEcho %RED% "[✗] 测试失败！"
    call :ColorEcho %YELLOW% "提示：如果是因为依赖缺失，请先运行 scripts\install_dependencies.bat"
)

popd
goto :eof

:: 主菜单
:MainMenu
cls
call :ColorEcho %BLUE% "==============================================="
call :ColorEcho %GREEN% "         MSearch 测试运行工具 v1.0             "
call :ColorEcho %BLUE% "==============================================="
echo.
call :ColorEcho %WHITE% "选择测试类型："
echo.
call :ColorEcho %WHITE% "1. 运行单元测试"
echo "2. 运行集成测试"
echo "3. 运行所有测试"
echo "4. 运行简单集成测试 (test_integration_simple.py)"
echo "5. 运行离线集成测试 (test_offline_integration.py)"
echo "6. 运行测试覆盖率检查"
echo "7. 运行特定测试文件"
echo "8. 运行特定测试函数"
echo "9. 检查测试环境"
echo "0. 退出"
echo.

set /p choice=请输入选择 (0-9): 
echo.

:: 根据选择执行相应测试
if "%choice%" equ "1" (
    call :RunTest "unit" "python -m pytest tests/unit -v" "单元测试"
) else if "%choice%" equ "2" (
    call :RunTest "integration" "python -m pytest tests/integration -v" "集成测试"
) else if "%choice%" equ "3" (
    call :RunTest "all" "python -m pytest -v" "所有测试"
) else if "%choice%" equ "4" (
    if exist "%PROJECT_ROOT%\test_integration_simple.py" (
        call :RunTest "simple_integration" "python test_integration_simple.py" "简单集成测试"
    ) else (
        call :ColorEcho %RED% "错误：test_integration_simple.py 文件不存在！"
    )
) else if "%choice%" equ "5" (
    if exist "%PROJECT_ROOT%\test_offline_integration.py" (
        call :RunTest "offline_integration" "python test_offline_integration.py" "离线集成测试"
    ) else (
        call :ColorEcho %RED% "错误：test_offline_integration.py 文件不存在！"
    )
) else if "%choice%" equ "6" (
    call :RunTest "coverage" "python -m pytest --cov=src --cov-report=term --cov-report=html:coverage_report" "测试覆盖率检查"
) else if "%choice%" equ "7" (
    set /p test_file=请输入测试文件路径 (例如: tests/unit/test_core_components.py): 
    if exist "%PROJECT_ROOT%\%test_file%" (
        call :RunTest "specific_file" "python -m pytest %test_file% -v" "特定测试文件: %test_file%"
    ) else (
        call :ColorEcho %RED% "错误：测试文件不存在！"
    )
) else if "%choice%" equ "8" (
    set /p test_function=请输入测试函数路径 (例如: tests/unit/test_core_components.py::test_config_manager): 
    call :RunTest "specific_function" "python -m pytest %test_function% -v" "特定测试函数: %test_function%"
) else if "%choice%" equ "9" (
    echo 运行环境检查...
    if exist "%SCRIPT_DIR%\check_environment.bat" (
        call "%SCRIPT_DIR%\check_environment.bat"
    ) else (
        call :ColorEcho %RED% "错误：check_environment.bat 文件不存在！"
    )
    goto :MainMenu
) else if "%choice%" equ "0" (
    call :ColorEcho %BLUE% "退出脚本..."
    exit /b 0
) else (
    call :ColorEcho %YELLOW% "无效选择，请重新输入！"
    timeout /t 2 >nul
    goto :MainMenu
)

echo.
set /p continue=按 Enter 键返回主菜单，或输入 'q' 退出: 
if /i "%continue%" equ "q" (
    call :ColorEcho %BLUE% "退出脚本..."
    exit /b 0
) else (
    goto :MainMenu
)