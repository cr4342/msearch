# TargetOS: Windows
# Simple PowerShell download script

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Join-Path -Path $ScriptDir -ChildPath ".." -Resolve

Write-Host "Starting setup..."

# Create basic directory structure
$PackagesDir = Join-Path -Path $ProjectRoot -ChildPath "offline\packages"
$ModelsDir = Join-Path -Path $ProjectRoot -ChildPath "offline\models"
New-Item -Path $PackagesDir -ItemType Directory -Force | Out-Null
New-Item -Path $ModelsDir -ItemType Directory -Force | Out-Null

# Install huggingface_hub
Write-Host "Installing huggingface_hub..."
python -m pip install huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade

# Download dependencies
Write-Host "Downloading dependencies..."
$RequirementsFile = Join-Path -Path $ProjectRoot -ChildPath "requirements.txt"
python -m pip download -r $RequirementsFile --dest $PackagesDir -i https://pypi.tuna.tsinghua.edu.cn/simple

# Generate simple download tool
Write-Host "Creating download tool..."
$DownloadTool = Join-Path -Path $ScriptDir -ChildPath "simple_download.py"
$PythonScript = @"
import os
from huggingface_hub import snapshot_download
def download_model(model_id, local_dir):
    os.makedirs(local_dir, exist_ok=True)
    snapshot_download(model_id, local_dir=local_dir, local_dir_use_symlinks=False)
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        download_model(sys.argv[1], sys.argv[2])
"@
Set-Content -Path $DownloadTool -Value $PythonScript -Encoding utf8

# Download CLIP model
Write-Host "Downloading CLIP model..."
$ClipModelDir = Join-Path -Path $ModelsDir -ChildPath "clip-vit-base-patch32"
New-Item -Path $ClipModelDir -ItemType Directory -Force | Out-Null
$env:HF_ENDPOINT = "https://hf-mirror.com"
python $DownloadTool "openai/clip-vit-base-patch32" $ClipModelDir

Write-Host "Download completed!"