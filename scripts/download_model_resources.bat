@echo off
chcp 65001 >nul

:: 简化版下载脚本
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%.."
set "PROJECT_ROOT=%cd%"
popd

echo 开始设置...

:: 创建基本目录结构
mkdir "%PROJECT_ROOT%\offline\packages" 2>nul
mkdir "%PROJECT_ROOT%\offline\models" 2>nul

:: 安装huggingface_hub
echo 安装huggingface_hub...
python -m pip install huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade

:: 下载依赖包
echo 下载依赖包...
python -m pip download -r "%PROJECT_ROOT%\requirements.txt" --dest "%PROJECT_ROOT%\offline\packages" -i https://pypi.tuna.tsinghua.edu.cn/simple

:: 生成简单的工具脚本
echo 创建简单下载工具...
echo import os > "%PROJECT_ROOT%\scripts\simple_download.py"
echo from huggingface_hub import snapshot_download >> "%PROJECT_ROOT%\scripts\simple_download.py"
echo def download_model(model_id, local_dir): >> "%PROJECT_ROOT%\scripts\simple_download.py"
echo     os.makedirs(local_dir, exist_ok=True) >> "%PROJECT_ROOT%\scripts\simple_download.py"
echo     snapshot_download(model_id, local_dir=local_dir, local_dir_use_symlinks=False) >> "%PROJECT_ROOT%\scripts\simple_download.py"
echo if __name__ == "__main__": >> "%PROJECT_ROOT%\scripts\simple_download.py"
echo     import sys >> "%PROJECT_ROOT%\scripts\simple_download.py"
echo     if len(sys.argv) > 2: >> "%PROJECT_ROOT%\scripts\simple_download.py"
echo         download_model(sys.argv[1], sys.argv[2]) >> "%PROJECT_ROOT%\scripts\simple_download.py"

:: 下载基本模型
echo 下载CLIP模型...
mkdir "%PROJECT_ROOT%\offline\models\clip-vit-base-patch32" 2>nul
set HF_ENDPOINT=https://hf-mirror.com
python "%PROJECT_ROOT%\scripts\simple_download.py" "openai/clip-vit-base-patch32" "%PROJECT_ROOT%\offline\models\clip-vit-base-patch32"

echo 下载完成！
echo.