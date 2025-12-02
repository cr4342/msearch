#!/usr/bin/env pwsh
# TargetOS: Windows
# MSearch - Multimodal Search System Windows Simple Run Script
# This script skips problematic dependencies and runs the core functionality

# Set script and project paths
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Join-Path $SCRIPT_DIR ".."

Write-Host "=== MSearch Windows Simple Run Script ===" -ForegroundColor Green
Write-Host "Project Root: $PROJECT_ROOT"
Write-Host "This script skips problematic dependencies and runs core functionality"
Write-Host ""

# 1. Check Python installation
Write-Host "1. Checking Python installation..." -ForegroundColor Cyan
try {
    $python_version = python --version 2>&1
    Write-Host "   Python version: $python_version"
    
    # Validate Python version (3.8+ required)
    if ($python_version -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
            Write-Host "   ERROR: Python 3.8+ is required, found $major.$minor" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "   ERROR: Python not found. Please install Python 3.8+ and add to PATH." -ForegroundColor Red
    exit 1
}

# 2. Check pip installation
try {
    $pip_version = pip --version 2>&1
    Write-Host "   pip version: $pip_version"
} catch {
    Write-Host "   ERROR: pip not found. Please ensure pip is installed." -ForegroundColor Red
    exit 1
}

# 3. Install minimal dependencies (skip problematic ones)
Write-Host "" -ForegroundColor Cyan
Write-Host "2. Installing minimal dependencies..." -ForegroundColor Cyan
Write-Host "   Skipping problematic dependencies: insightface, stringzilla"
Write-Host "   Installing core dependencies only..."

# Create a temporary requirements file with problematic dependencies removed
$temp_requirements = Join-Path $PROJECT_ROOT "temp_requirements.txt"
$original_requirements = Join-Path $PROJECT_ROOT "requirements.txt"

if (Test-Path $original_requirements) {
    # Read original requirements and filter out problematic packages
    $requirements = Get-Content $original_requirements
    $filtered_requirements = $requirements | Where-Object {
        $_ -notmatch "insightface" -and $_ -notmatch "stringzilla"
    }
    
    # Write filtered requirements to temp file
    $filtered_requirements | Out-File -FilePath $temp_requirements -Encoding UTF8
    
    Write-Host "   Installing from filtered requirements..."
    pip install -r $temp_requirements --no-deps
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   WARNING: Some dependencies failed to install, but continuing..." -ForegroundColor Yellow
    }
    
    # Clean up temp file
    Remove-Item $temp_requirements -Force
} else {
    Write-Host "   ERROR: requirements.txt not found at $original_requirements" -ForegroundColor Red
    exit 1
}

# 4. Download models
Write-Host "" -ForegroundColor Cyan
Write-Host "3. Downloading models..." -ForegroundColor Cyan
Write-Host "   Setting HF_ENDPOINT to https://hf-mirror.com..."
$env:HF_ENDPOINT = "https://hf-mirror.com"

# Check if huggingface_hub is installed
Write-Host "   Installing huggingface_hub for model downloads..."
pip install huggingface_hub

$model_script = Join-Path $PROJECT_ROOT "scripts" "download_models.py"
if (Test-Path $model_script) {
    Write-Host "   Running model download script..."
    python $model_script
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   WARNING: Some models failed to download, but continuing..." -ForegroundColor Yellow
    }
} else {
    Write-Host "   WARNING: Model download script not found, skipping model download..." -ForegroundColor Yellow
}

# 4. Create Qdrant data directories
Write-Host "" -ForegroundColor Cyan
Write-Host "3. Setting up Qdrant data directories..." -ForegroundColor Cyan
$QDRANT_DATA_DIR = Join-Path $PROJECT_ROOT "data\qdrant"
$QDRANT_STORAGE_DIR = Join-Path $QDRANT_DATA_DIR "storage"
$QDRANT_LOG_DIR = Join-Path $QDRANT_DATA_DIR "logs"

New-Item -ItemType Directory -Path $QDRANT_DATA_DIR -Force | Out-Null
New-Item -ItemType Directory -Path $QDRANT_STORAGE_DIR -Force | Out-Null
New-Item -ItemType Directory -Path $QDRANT_LOG_DIR -Force | Out-Null

Write-Host "   Qdrant data directory: $QDRANT_DATA_DIR"
Write-Host "   Qdrant storage directory: $QDRANT_STORAGE_DIR"

# 5. Check if Qdrant is running
Write-Host "" -ForegroundColor Cyan
Write-Host "4. Checking Qdrant service..." -ForegroundColor Cyan

$qdrant_running = $false
try {
    $response = Invoke-RestMethod -Uri "http://localhost:6333/health" -Method Get -TimeoutSec 3
    if ($response.status -eq "ok") {
        $qdrant_running = $true
        Write-Host "   Qdrant service is running at http://localhost:6333" -ForegroundColor Green
    }
} catch {
    Write-Host "   WARNING: Qdrant service is not running at http://localhost:6333" -ForegroundColor Yellow
    Write-Host "   Please start Qdrant manually before running this script." -ForegroundColor Yellow
    Write-Host "   You can download Qdrant from: https://qdrant.tech/download/" -ForegroundColor Yellow
    Write-Host "   Or use Docker: docker run -d -p 6333:6333 qdrant/qdrant:latest" -ForegroundColor Yellow
    Write-Host "   "
    
    # Ask user if they want to continue without Qdrant
    $continue = Read-Host -Prompt "   Do you want to continue without Qdrant? (y/N)"
    if ($continue -notmatch "^[Yy]$" -and $continue -notmatch "^$|^[Nn]$" -and $continue -notmatch "^No$") {
        Write-Host "   Continuing without Qdrant..." -ForegroundColor Yellow
    } else {
        exit 1
    }
}

# 6. Start MSearch API server (with limited functionality)
Write-Host "" -ForegroundColor Cyan
Write-Host "5. Starting MSearch API server..." -ForegroundColor Cyan

$api_script = Join-Path $PROJECT_ROOT "src" "api_server.py"
if (Test-Path $api_script) {
    Write-Host "   API server script: $api_script" -ForegroundColor Green
    Write-Host "   Starting API server with limited functionality..." -ForegroundColor Green
    Write-Host "   API server URL: http://localhost:8000" -ForegroundColor Green
    Write-Host "   API documentation: http://localhost:8000/docs" -ForegroundColor Green
    Write-Host "   Press Ctrl+C to stop the server." -ForegroundColor Green
    Write-Host "   " -ForegroundColor Green
    
    try {
        # Start the API server
        python $api_script
    } catch {
        Write-Host "   ERROR: Failed to start API server: $_.Exception.Message" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ERROR: API server script not found at $api_script" -ForegroundColor Red
    exit 1
}
