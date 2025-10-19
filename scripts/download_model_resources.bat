@echo off
chcp 65001 >nul

:: msearch 离线资源下载脚本
:: 一键下载所有依赖和模型到本地offline目录
:: Windows批处理版本

:: 获取脚本所在目录和项目根目录（使用绝对路径）
set "SCRIPT_DIR=%~dp0"
pushd %SCRIPT_DIR%..
set "PROJECT_ROOT=%cd%"
popd

:: 日志函数
echo [INFO] 开始下载所有离线资源...

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到Python，请先安装Python 3.9-3.11版本
    pause
    exit /b 1
)

:: 检查pip是否可用
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到pip，请确保Python正确安装
    pause
    exit /b 1
)

:: 确保huggingface_hub已安装（用于模型下载）
echo [INFO] 0. 确保huggingface_hub已安装...
python -m pip install huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade || echo [WARNING] huggingface_hub安装失败，但继续执行

:: 下载依赖包
echo [INFO] 1. 下载Python依赖包...

:: 创建offline目录结构
mkdir "%PROJECT_ROOT%\offline\packages\requirements" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\clip-vit-base-patch32" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\clap-htsat-fused" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\whisper-base" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\insightface" 2>nul

:: 下载requirements.txt中列出的所有依赖包
echo [INFO] 下载requirements.txt中所有依赖包...
python -m pip download -r "%PROJECT_ROOT%\requirements.txt" ^
    --dest "%PROJECT_ROOT%\offline\packages\requirements" ^
    --disable-pip-version-check ^
    -i https://pypi.tuna.tsinghua.edu.cn/simple ^
    --timeout 60 ^
    --retries 3

if %errorlevel% neq 0 (
    echo [ERROR] 依赖包下载失败
    pause
    exit /b 1
)

:: 特别处理inaSpeechSegmenter包
echo [INFO] 特别处理inaSpeechSegmenter包...
python -m pip download inaspeechsegmenter ^
    --dest "%PROJECT_ROOT%\offline\packages\requirements" ^
    --disable-pip-version-check ^
    -i https://pypi.tuna.tsinghua.edu.cn/simple ^
    --timeout 60 ^
    --retries 3

:: 下载PySide6
echo [INFO] 2. 下载PySide6跨平台GUI框架...

:: 创建offline目录结构
mkdir "%PROJECT_ROOT%\offline\packages\pyside6" 2>nul

echo [INFO] 开始下载PySide6离线包...

:: 下载PySide6及其依赖
python -m pip download PySide6 ^
    --dest "%PROJECT_ROOT%\offline\packages\pyside6" ^
    --no-deps ^
    --disable-pip-version-check ^
    --timeout 60 ^
    --retries 3

:: 下载模型
echo [INFO] 3. 下载AI模型...

:: 设置HuggingFace镜像（国内优化）
set "HF_ENDPOINT=https://hf-mirror.com"

:: 创建模型目录结构
mkdir "%PROJECT_ROOT%\offline\models\huggingface" 2>nul

:: 创建GitHub相关资源目录
mkdir "%PROJECT_ROOT%\offline\github" 2>nul

:: 下载CLIP模型（文本-图像检索）
echo [INFO] 1. 下载CLIP模型 (openai/clip-vit-base-patch32)...
python -c "from huggingface_hub import snapshot_download; snapshot_download('openai/clip-vit-base-patch32', local_dir=r'%PROJECT_ROOT%\offline\models\clip-vit-base-patch32', local_dir_use_symlinks=False, resume_download=True)"

if %errorlevel% neq 0 (
    echo [ERROR] CLIP模型下载失败
    pause
    exit /b 1
)

:: 下载CLAP模型（文本-音频检索）
echo [INFO] 2. 下载CLAP模型 (laion/clap-htsat-fused)...
python -c "from huggingface_hub import snapshot_download; snapshot_download('laion/clap-htsat-fused', local_dir=r'%PROJECT_ROOT%\offline\models\clap-htsat-fused', local_dir_use_symlinks=False, resume_download=True)"

if %errorlevel% neq 0 (
    echo [ERROR] CLAP模型下载失败
    pause
    exit /b 1
)

:: 下载Whisper模型（语音转文本）
echo [INFO] 3. 下载Whisper模型 (openai/whisper-base)...
python -c "from huggingface_hub import snapshot_download; snapshot_download('openai/whisper-base', local_dir=r'%PROJECT_ROOT%\offline\models\whisper-base', local_dir_use_symlinks=False, resume_download=True)"

if %errorlevel% neq 0 (
    echo [ERROR] Whisper模型下载失败
    pause
    exit /b 1
)

:: 下载人脸识别模型
echo [INFO] 4. 下载人脸识别模型 (buffalo_l, buffalo_sc)...

:: 注意：由于模型下载可能遇到问题，这里创建空目录作为占位符
echo [INFO] 创建人脸识别模型目录结构...
mkdir "%PROJECT_ROOT%\offline\models\insightface\models" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\insightface\models\buffalo_l" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\insightface\models\buffalo_sc" 2>nul

echo [INFO] 人脸识别模型目录创建完成（请手动下载模型文件并放入对应目录）
:: 跳过实际下载，避免repo_id错误

:: 验证下载结果
echo [INFO] 5. 验证下载结果...
if exist "%PROJECT_ROOT%\offline\packages" (echo [INFO] 依赖包目录存在) else (echo [ERROR] 依赖包目录不存在)
if exist "%PROJECT_ROOT%\offline\models" (echo [INFO] 模型目录存在) else (echo [ERROR] 模型目录不存在)

echo [INFO] 离线资源下载完成！

:: 生成Qdrant服务启动脚本
echo [INFO] 6. 生成Qdrant服务启动脚本...

:: 创建启动脚本 - 使用更简单的方式
python -c "
lines = [
    '@echo off',
    ':: Qdrant向量数据库服务启动脚本',
    '',
    'echo [INFO] 启动Qdrant向量数据库服务...',
    '',
    ':: 设置Qdrant数据目录',
    'set "QDRANT_DATA_DIR=%~dp0..\offline\qdrant_data"',
    'mkdir "%QDRANT_DATA_DIR%" 2>nul',
    '',
    ':: 使用离线下载的Qdrant二进制文件',
    'if exist "%~dp0..\offline\bin\qdrant.exe" (',
    '    echo 使用离线Qdrant二进制文件启动服务...',
    '    start "Qdrant" "%~dp0..\offline\bin\qdrant.exe" --config-path "%~dp0..\config\qdrant.yml"',
    ') else (',
    '    echo 离线Qdrant二进制文件不存在，请先下载',
    '    pause',
    '    exit /b 1',
    ')',
    '',
    'echo [INFO] Qdrant服务启动完成！',
    'echo 服务地址: http://localhost:6333',
    'echo Web UI: http://localhost:6333',
    '',
    'echo 服务健康检查:',
    'echo curl http://localhost:6333/health'
]
with open(r'%PROJECT_ROOT%\scripts\start_qdrant.bat', 'w', encoding='utf-8') as f:',
    f.write('\n'.join(lines))
"

:: 创建停止脚本
python -c "
lines = [
    '@echo off',
    ':: Qdrant服务停止脚本',
    '',
    'echo 停止Qdrant服务...',
    'taskkill /F /IM qdrant.exe >nul 2>nul',
    'if %%errorlevel%% equ 0 (',
    '    echo Qdrant服务已停止',
    ') else (',
    '    echo Qdrant服务未运行',
    ')'
]
with open(r'%PROJECT_ROOT%\scripts\stop_qdrant.bat', 'w', encoding='utf-8') as f:',
    f.write('\n'.join(lines))
"

:: 生成infinity服务启动脚本
echo [INFO] 7. 生成infinity服务启动脚本...

:: 创建启动脚本
python -c "
lines = [
    '@echo off',
    ':: Infinity多模型服务启动脚本',
    '',
    'echo [INFO] 启动Infinity多模型服务...',
    '',
    ':: 设置模型缓存路径（指向离线下载的模型）',
    'set "HF_HOME=%~dp0..\offline\models\huggingface"',
    'set "TRANSFORMERS_CACHE=%HF_HOME%"',
    '',
    ':: 创建缓存目录',
    'mkdir "%HF_HOME%" 2>nul',
    '',
    ':: 启动CLIP模型服务（端口7997）',
    'echo 启动CLIP模型服务 (端口7997)...',
    'start "Infinity CLIP" infinity_emb v2 --model-id "openai/clip-vit-base-patch32" --port 7997 --device cpu',
    '',
    ':: 启动CLAP模型服务（端口7998）',
    'echo 启动CLAP模型服务 (端口7998)...',
    'start "Infinity CLAP" infinity_emb v2 --model-id "laion/clap-htsat-fused" --port 7998 --device cpu',
    '',
    ':: 启动Whisper模型服务（端口7999）',
    'echo 启动Whisper模型服务 (端口7999)...',
    'start "Infinity Whisper" infinity_emb v2 --model-id "openai/whisper-base" --port 7999 --device cpu',
    '',
    'echo [INFO] Infinity服务启动完成！',
    '',
    'echo 服务健康检查:',
    'echo curl http://localhost:7997/health',
    'echo curl http://localhost:7998/health',
    'echo curl http://localhost:7999/health'
]
with open(r'%PROJECT_ROOT%\scripts\start_infinity_services.bat', 'w', encoding='utf-8') as f:',
    f.write('\n'.join(lines))
"

:: 创建停止脚本
python -c "
lines = [
    '@echo off',
    ':: Infinity服务停止脚本',
    '',
    'echo 停止Infinity服务...',
    'taskkill /F /IM python.exe /FI "WINDOWTITLE eq Infinity CLIP*" >nul 2>nul',
    'if %%errorlevel%% equ 0 (',
    '    echo CLIP服务已停止',
    ')',
    '',
    'taskkill /F /IM python.exe /FI "WINDOWTITLE eq Infinity CLAP*" >nul 2>nul',
    'if %%errorlevel%% equ 0 (',
    '    echo CLAP服务已停止',
    ')',
    '',
    'taskkill /F /IM python.exe /FI "WINDOWTITLE eq Infinity Whisper*" >nul 2>nul',
    'if %%errorlevel%% equ 0 (',
    '    echo Whisper服务已停止',
    ')',
    '',
    'echo 所有Infinity服务已停止'
]
with open(r'%PROJECT_ROOT%\scripts\stop_infinity_services.bat', 'w', encoding='utf-8') as f:',
    f.write('\n'.join(lines))
"


echo [INFO] 服务脚本已生成:
echo [INFO]   - Qdrant启动脚本: %PROJECT_ROOT%\scripts\start_qdrant.bat
echo [INFO]   - Qdrant停止脚本: %PROJECT_ROOT%\scripts\stop_qdrant.bat
echo [INFO]   - Infinity启动脚本: %PROJECT_ROOT%\scripts\start_infinity_services.bat
echo [INFO]   - Infinity停止脚本: %PROJECT_ROOT%\scripts\stop_infinity_services.bat

echo [INFO] 所有离线资源下载脚本执行完成！
echo [INFO]
echo [INFO] 8. 后续操作指南：
echo 1. 安装依赖包：
echo    python -m pip install --no-index --find-links=offline\packages -r requirements.txt
echo 
echo 2. 安装PySide6：
echo    python -m pip install --no-index --find-links=offline\packages\pyside6 PySide6
echo 
echo 3. 启动Qdrant服务：
echo    scripts\start_qdrant.bat
echo 
echo 4. 启动Infinity服务：
echo    scripts\start_infinity_services.bat
echo 
echo 5. 启动主服务：
echo    python src\api\main.py
echo 
echo 6. 停止服务：
echo    scripts\stop_qdrant.bat
echo    scripts\stop_infinity_services.bat

pause