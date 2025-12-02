#!/usr/bin/env pwsh
# TargetOS: Windows
# MSearch - Multimodal Search System Windows Run Script

# Check PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Host "WARNING: PowerShell 7+ is recommended, current version: $($PSVersionTable.PSVersion)" -ForegroundColor Yellow
}

# Set script and project paths
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Join-Path $SCRIPT_DIR ".."

Write-Host "=== MSearch Windows Run Script ===" -ForegroundColor Green
Write-Host "Project Root: $PROJECT_ROOT"
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

# 3. Install dependencies
Write-Host "" -ForegroundColor Cyan
Write-Host "2. Installing project dependencies..." -ForegroundColor Cyan
$requirements_file = Join-Path $PROJECT_ROOT "requirements.txt"
if (Test-Path $requirements_file) {
    Write-Host "   Installing from $requirements_file..."
    pip install -r $requirements_file
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   WARNING: Some dependencies failed to install, but continuing..." -ForegroundColor Yellow
    }
} else {
    Write-Host "   ERROR: requirements.txt not found at $requirements_file" -ForegroundColor Red
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

# 5. Start Qdrant service
Write-Host "" -ForegroundColor Cyan
Write-Host "4. Starting Qdrant service..." -ForegroundColor Cyan

# Check if Qdrant is already running
$qdrant_running = $false
try {
    $response = Invoke-RestMethod -Uri "http://localhost:6333/health" -Method Get -TimeoutSec 3
    if ($response.status -eq "ok") {
        $qdrant_running = $true
        Write-Host "   Qdrant service is already running at http://localhost:6333" -ForegroundColor Green
    }
} catch {
    # Qdrant is not running, try to start it
    $qdrant_running = $false
}

if (-not $qdrant_running) {
    # Try to start Qdrant in different ways
    $qdrant_started = $false
    
    # Check if Qdrant CLI is available
    try {
        $qdrant_version = qdrant --version 2>&1
        Write-Host "   Found Qdrant CLI: $qdrant_version"
        Write-Host "   Starting Qdrant service..."
        
        # Start Qdrant in background
        Start-Process -FilePath "qdrant" -WorkingDirectory $QDRANT_DATA_DIR -WindowStyle Minimized
        Start-Sleep -Seconds 5
        
        # Check if Qdrant started successfully
        $response = Invoke-RestMethod -Uri "http://localhost:6333/health" -Method Get -TimeoutSec 3
        if ($response.status -eq "ok") {
            $qdrant_started = $true
            Write-Host "   Qdrant service started successfully at http://localhost:6333" -ForegroundColor Green
        }
    } catch {
        # Qdrant CLI not found, try Docker
        Write-Host "   Qdrant CLI not found, trying Docker..." -ForegroundColor Yellow
        
        # Check if Docker is available
        try {
            $docker_version = docker --version 2>&1
            Write-Host "   Found Docker: $docker_version"
            
            # Check if Qdrant container already exists
            $existing_container = docker ps -a -f name=qdrant-msearch --format "{{.Names}}"
            
            if ($existing_container -eq "qdrant-msearch") {
                Write-Host "   Starting existing Qdrant container..."
                docker start qdrant-msearch
            } else {
                Write-Host "   Creating new Qdrant container..."
                docker run -d --name qdrant-msearch -p 6333:6333 -p 6334:6334 -v "${QDRANT_STORAGE_DIR}:/qdrant/storage" qdrant/qdrant:latest
            }
            
            Start-Sleep -Seconds 5
            
            # Check if Qdrant started successfully
            $response = Invoke-RestMethod -Uri "http://localhost:6333/health" -Method Get -TimeoutSec 3
            if ($response.status -eq "ok") {
                $qdrant_started = $true
                Write-Host "   Qdrant Docker container started successfully at http://localhost:6333" -ForegroundColor Green
            }
        } catch {
            # Both Qdrant CLI and Docker failed
            Write-Host "   ERROR: Failed to start Qdrant service." -ForegroundColor Red
            Write-Host "   Please install Qdrant or Docker manually and start it." -ForegroundColor Yellow
            Write-Host "   Qdrant service URL: http://localhost:6333" -ForegroundColor Yellow
            exit 1
        }
    }
    
    if (-not $qdrant_started) {
        Write-Host "   ERROR: Failed to start Qdrant service." -ForegroundColor Red
        exit 1
    }
}

# 6. Start MSearch API server
Write-Host "" -ForegroundColor Cyan
Write-Host "5. Starting MSearch API server..." -ForegroundColor Cyan

$api_script = Join-Path $PROJECT_ROOT "src" "api_server.py"
if (Test-Path $api_script) {
    Write-Host "   API server script: $api_script"
    Write-Host "   Starting API server..." -ForegroundColor Green
    Write-Host "   API server URL: http://localhost:8000" -ForegroundColor Green
    Write-Host "   API documentation: http://localhost:8000/docs" -ForegroundColor Green
    Write-Host "   Press Ctrl+C to stop the server." -ForegroundColor Green
    Write-Host "" -ForegroundColor Green
    
    # Start the API server
    python $api_script
} else {
    Write-Host "   ERROR: API server script not found at $api_script" -ForegroundColor Red
    exit 1
}
