@echo off
chcp 65001 >nul

:: msearch 离线资源下载脚本 - 简化版
:: 一键下载所有依赖和模型到本地offline目录
:: Windows批处理版本

:: 获取脚本所在目录和项目根目录
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

:: 创建项目目录结构
echo [INFO] 创建项目目录结构...
mkdir "%PROJECT_ROOT%\offline\packages" 2>nul
mkdir "%PROJECT_ROOT%\offline\packages" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\clip-vit-base-patch32" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\clap-htsat-fused" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\whisper-base" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\insightface\models\buffalo_l" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\insightface\models\buffalo_sc" 2>nul
mkdir "%PROJECT_ROOT%\offline\models\huggingface" 2>nul
mkdir "%PROJECT_ROOT%\offline\packages" 2>nul

:: 1. 安装huggingface_hub
echo [INFO] 1. 安装huggingface_hub...
python -m pip install huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade

:: 2. 创建Python工具脚本
echo import os > "%PROJECT_ROOT%\scripts\download_utils.py"
echo import sys >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo import argparse >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo from huggingface_hub import snapshot_download >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo def download_model(model_id, local_dir): >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo     print(f"开始下载模型: {model_id}") >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo     try: >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         os.makedirs(local_dir, exist_ok=True) >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         snapshot_download(model_id, local_dir=local_dir, local_dir_use_symlinks=False, resume_download=True) >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         print(f"模型下载完成: {model_id}") >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         return True >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo     except Exception as e: >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         print(f"模型下载失败 {model_id}: {e}") >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         return False >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo def generate_batch_script(file_path, content): >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo     try: >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         os.makedirs(os.path.dirname(file_path), exist_ok=True) >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         with open(file_path, 'w', encoding='utf-8') as f: >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo             f.write(content) >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         print(f"生成文件: {file_path}") >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         return True >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo     except Exception as e: >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         print(f"生成文件失败 {file_path}: {e}") >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         return False >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo if __name__ == "__main__": >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo     parser = argparse.ArgumentParser() >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo     parser.add_argument('--action', required=True, choices=['download_model', 'generate_script']) >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo     parser.add_argument('--model_id', required=False) >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo     parser.add_argument('--local_dir', required=False) >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo     parser.add_argument('--file_path', required=False) >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo     parser.add_argument('--content', required=False) >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo     args = parser.parse_args() >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo     >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo     if args.action == 'download_model': >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         success = download_model(args.model_id, args.local_dir) >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         sys.exit(0 if success else 1) >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo     elif args.action == 'generate_script': >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         success = generate_batch_script(args.file_path, args.content) >> "%PROJECT_ROOT%\scripts\download_utils.py"
echo         sys.exit(0 if success else 1) >> "%PROJECT_ROOT%\scripts\download_utils.py"

:: 3. 下载Python依赖包
echo [INFO] 3. 下载Python依赖包...
python -m pip download -r "%PROJECT_ROOT%\requirements.txt" --dest "%PROJECT_ROOT%\offline\packages" --disable-pip-version-check -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 60 --retries 3

:: 4. 下载额外依赖
echo [INFO] 4. 下载额外依赖...
python -m pip download python-magic python-magic-bin inaspeechsegmenter --dest "%PROJECT_ROOT%\offline\packages" --disable-pip-version-check -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 60 --retries 3

:: 5. 下载PySide6
echo [INFO] 5. 下载PySide6...
python -m pip download PySide6 --dest "%PROJECT_ROOT%\offline\packages" --no-deps --disable-pip-version-check -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 60 --retries 3

:: 6. 设置HuggingFace镜像
echo [INFO] 6. 设置HuggingFace镜像...
set "HF_ENDPOINT=https://hf-mirror.com"

:: 7. 下载模型
echo [INFO] 7. 下载模型...
echo [INFO] 下载CLIP模型...
python "%PROJECT_ROOT%\scripts\download_utils.py" --action download_model --model_id "openai/clip-vit-base-patch32" --local_dir "%PROJECT_ROOT%\offline\models\clip-vit-base-patch32"

echo [INFO] 下载CLAP模型...
python "%PROJECT_ROOT%\scripts\download_utils.py" --action download_model --model_id "laion/clap-htsat-fused" --local_dir "%PROJECT_ROOT%\offline\models\clap-htsat-fused"

echo [INFO] 下载Whisper模型...
python "%PROJECT_ROOT%\scripts\download_utils.py" --action download_model --model_id "openai/whisper-base" --local_dir "%PROJECT_ROOT%\offline\models\whisper-base"

:: 8. 生成启动脚本
echo [INFO] 8. 生成启动脚本...

:: 生成Qdrant启动脚本
python "%PROJECT_ROOT%\scripts\download_utils.py" --action generate_script --file_path "%PROJECT_ROOT%\scripts\start_qdrant.bat" --content "@echo off\necho 启动Qdrant服务...\nset \"QDRANT_DATA_DIR=%%~dp0..\\offline\\qdrant_data\"\nmkdir \"%%QDRANT_DATA_DIR%%\" 2^>nul\nstart \"Qdrant\" \"%%~dp0..\\offline\\bin\\qdrant.exe\" --config-path \"%%~dp0..\\config\\qdrant.yml\"\necho Qdrant服务启动完成！"

:: 生成Qdrant停止脚本
python "%PROJECT_ROOT%\scripts\download_utils.py" --action generate_script --file_path "%PROJECT_ROOT%\scripts\stop_qdrant.bat" --content "@echo off\necho 停止Qdrant服务...\ntaskkill /F /IM qdrant.exe >nul 2^>nul\necho Qdrant服务已停止"

:: 生成Infinity启动脚本
python "%PROJECT_ROOT%\scripts\download_utils.py" --action generate_script --file_path "%PROJECT_ROOT%\scripts\start_infinity_services.bat" --content "@echo off\necho 启动Infinity服务...\nset \"HF_HOME=%%~dp0..\\offline\\models\\huggingface\"\nmkdir \"%%HF_HOME%%\" 2^>nul\nstart \"Infinity CLIP\" infinity_emb v2 --model-id \"%%~dp0..\\offline\\models\\clip-vit-base-patch32\" --port 7997 --device cpu\nstart \"Infinity CLAP\" infinity_emb v2 --model-id \"%%~dp0..\\offline\\models\\clap-htsat-fused\" --port 7998 --device cpu\nstart \"Infinity Whisper\" infinity_emb v2 --model-id \"%%~dp0..\\offline\\models\\whisper-base\" --port 7999 --device cpu\necho Infinity服务启动完成！"

:: 生成Infinity停止脚本
python "%PROJECT_ROOT%\scripts\download_utils.py" --action generate_script --file_path "%PROJECT_ROOT%\scripts\stop_infinity_services.bat" --content "@echo off\necho 停止Infinity服务...\ntaskkill /F /IM python.exe /FI \"WINDOWTITLE eq Infinity CLIP*\" >nul 2^>nul\ntaskkill /F /IM python.exe /FI \"WINDOWTITLE eq Infinity CLAP*\" >nul 2^>nul\ntaskkill /F /IM python.exe /FI \"WINDOWTITLE eq Infinity Whisper*\" >nul 2^>nul\necho 所有Infinity服务已停止"

:: 9. 显示完成信息
echo [INFO] 所有资源下载完成！
echo. 
echo 后续操作步骤：
echo 1. 安装依赖包：
echo    python -m pip install --no-index --find-links=offline\packages -r requirements.txt
echo 2. 启动服务：
echo    scripts\start_qdrant.bat
echo    scripts\start_infinity_services.bat
echo 3. 停止服务：
echo    scripts\stop_qdrant.bat
echo    scripts\stop_infinity_services.bat

echo.
echo 按任意键退出...
pause