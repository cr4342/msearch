#!/usr/bin/env pwsh
# TargetOS: Windows
# MSearch - Multimodal Search System Windows Manual Run Script
# This script provides step-by-step instructions for manual setup

Write-Host "=== MSearch Windows Manual Setup Guide ===" -ForegroundColor Green
Write-Host ""

# 1. Check Python installation
Write-Host "1. Check Python Installation" -ForegroundColor Cyan
Write-Host "   Run: python --version"
Write-Host "   Requirement: Python 3.8+"
Write-Host ""

# 2. Install dependencies manually
Write-Host "2. Install Dependencies" -ForegroundColor Cyan
Write-Host "   Run: pip install -r requirements.txt --exclude insightface stringzilla"
Write-Host "   Or install specific packages:"
Write-Host "   pip install numpy asyncio fastapi uvicorn qdrant-client watchdog torch transformers huggingface_hub"
Write-Host ""

# 3. Download models
Write-Host "3. Download Models" -ForegroundColor Cyan
Write-Host "   Set HF mirror endpoint:"
Write-Host "   $env:HF_ENDPOINT = 'https://hf-mirror.com'"
Write-Host "   "
Write-Host "   Run the model download script:"
Write-Host "   python scripts/download_models.py"
Write-Host "   "
Write-Host "   For specific models:"
Write-Host "   python scripts/download_models.py --model text_embedding"
Write-Host "   "
Write-Host "   Models will be saved to: models/ directory"
Write-Host ""

# 3. Start Qdrant service
Write-Host "3. Start Qdrant Service" -ForegroundColor Cyan
Write-Host "   Option 1: Download Qdrant from https://qdrant.tech/download/ and run:"
Write-Host "             qdrant.exe"
Write-Host "   Option 2: Use Docker:"
Write-Host "             docker run -d -p 6333:6333 qdrant/qdrant:latest"
Write-Host "   Check Qdrant status: curl http://localhost:6333/health"
Write-Host ""

# 4. Start MSearch API server
Write-Host "4. Start MSearch API Server" -ForegroundColor Cyan
Write-Host "   Run: python src/api_server.py"
Write-Host "   API URL: http://localhost:8000"
Write-Host "   API Documentation: http://localhost:8000/docs"
Write-Host ""

# 5. Run examples
Write-Host "5. Run Examples" -ForegroundColor Cyan
Write-Host "   Example scripts are located in the examples/ directory:"
Write-Host "   python examples/qdrant_usage_example.py"
Write-Host "   python examples/time_accurate_retrieval_demo.py"
Write-Host "   python examples/media_preprocessing_example.py"
Write-Host ""

# 6. Run tests
Write-Host "6. Run Tests" -ForegroundColor Cyan
Write-Host "   Run: pytest tests/ -xvs"
Write-Host "   Or run specific test files:"
Write-Host "   pytest tests/test_msearch_core.py -xvs"
Write-Host ""

# 7. Stop services
Write-Host "7. Stop Services" -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to stop the API server"
Write-Host "   Stop Qdrant: kill the process or docker stop qdrant-msearch"
Write-Host ""

Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host "For more information, see the README.md file."
Write-Host ""
