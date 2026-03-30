# Marry AI Assistant — Quick Start
# Usage: .\runserver   (from the project folder in PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Marry AI Assistant - Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Activate virtual environment
& "$PSScriptRoot\.venv\Scripts\Activate.ps1"

# Train model if not already trained
if (-not (Test-Path "$PSScriptRoot\model.pkl")) {
    Write-Host "[INFO] No trained model found. Training now..." -ForegroundColor Yellow
    python train_model.py
}

# Open browser
Write-Host "[INFO] Opening http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process "http://127.0.0.1:8000"

# Start Django server
python manage.py runserver
