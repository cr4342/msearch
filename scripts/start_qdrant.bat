@echo off 
:: Qdrant向量数据库服务启动脚本 
 
echo [INFO] 启动Qdrant向量数据库服务... 
 
:: 设置Qdrant数据目录 
set "QDRANT_DATA_DIR=%~dp0..\offline\qdrant_data" 
mkdir "%QDRANT_DATA_DIR%" 2>nul 
 
:: 使用离线下载的Qdrant二进制文件 
if exist "%~dp0..\offline\bin\qdrant.exe" ( 
    echo 使用离线Qdrant二进制文件启动服务... 
    start "Qdrant" "%~dp0..\offline\bin\qdrant.exe" --config-path "%~dp0..\config\qdrant.yml" 
) else ( 
    echo 离线Qdrant二进制文件不存在，请先下载 
    pause 
    exit /b 1 
) 
 
echo [INFO] Qdrant服务启动完成！ 
echo 服务地址: http://localhost:6333 
echo Web UI: http://localhost:6333 
echo. 
echo 服务健康检查: 
echo curl http://localhost:6333/health 
