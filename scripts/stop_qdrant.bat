@echo off 
:: Qdrant向量数据库服务停止脚本 

echo [INFO] 停止Qdrant向量数据库服务... 

:: 查找并杀死Qdrant进程
taskkill /im qdrant.exe /f >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Qdrant服务已成功停止
) else (
    echo [INFO] 未找到Qdrant进程，可能已经停止
)

:: 等待进程确认停止
ping -n 2 127.0.0.1 >nul

echo [INFO] Qdrant服务停止操作完成
