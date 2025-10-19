@echo off
chcp 65001 >nul

:: msearch 一键停止所有服务脚本 (Windows版本)
:: 功能: 自动停止所有Msearch相关服务

:: 设置颜色输出
for /f "tokens=1,2 delims=#" %%a in ('"prompt #$E[32m#$E[0m" ^& echo on ^& for %%b in (1) do rem') do (
    set "ESC=%%a"
)

:: 颜色定义
set "RED=%ESC%[31m"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "NC=%ESC%[0m"  :: No Color

:: 输出标题
echo.  
echo %RED%==================================================%NC%
echo %RED%            MSEARCH 多模态检索系统            %NC%
echo %RED%             一键停止所有服务                  %NC%
echo %RED%==================================================%NC%
echo.

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"

:: 步骤1: 停止Qdrant服务
echo %YELLOW%[步骤1] 停止Qdrant向量数据库服务...%NC%
call "%SCRIPT_DIR%\stop_qdrant.bat"
echo.

:: 步骤2: 停止主API服务
echo %YELLOW%[步骤2] 停止MSearch API服务...%NC%

:: 查找并杀死uvicorn进程（API服务）
taskkill /fi "imagename eq uvicorn.exe" /f >nul 2>&1
if %errorlevel% equ 0 (
    echo %GREEN%[成功] MSearch API服务已成功停止%NC%
) else (
    echo %YELLOW%[提示] 未找到uvicorn进程，可能已经停止%NC%
)

:: 查找并杀死python进程中包含src.api.main的进程
for /f "tokens=2" %%p in ('tasklist /fi "imagename eq python.exe" /fo list /v ^| findstr /i "src.api.main"') do (
    taskkill /pid %%p /f >nul 2>&1
    if %errorlevel% equ 0 (
        echo %GREEN%[成功] MSearch API Python进程已成功停止%NC%
    )
)

echo.

:: 步骤3: 停止其他相关进程
echo %YELLOW%[步骤3] 清理其他相关进程...%NC%

:: 停止可能的其他相关进程
taskkill /fi "windowtitle eq MSearch API" /f >nul 2>&1
taskkill /fi "windowtitle eq Qdrant" /f >nul 2>&1

echo %GREEN%[成功] 进程清理完成%NC%
echo.

:: 输出完成信息
echo %GREEN%==================================================%NC%
echo %GREEN%                所有服务已停止！                %NC%
echo %GREEN%==================================================%NC%
echo.
echo %YELLOW%[提示] 如需重新启动服务，请运行：%NC%
echo %YELLOW%scripts\deploy_msearch.bat%NC%
echo.
pause