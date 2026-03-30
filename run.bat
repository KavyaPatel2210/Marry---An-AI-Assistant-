@echo off
title Marry AI Assistant
echo ========================================
echo   Marry AI Assistant - Launcher
echo ========================================

:: Activate virtual environment
call .venv\Scripts\activate.bat

:: Train model if pkl files are missing
if not exist model.pkl (
    echo [INFO] No trained model found. Training now...
    python train_model.py
)

:: Open browser automatically
echo [INFO] Starting server at http://127.0.0.1:8000
start "" "http://127.0.0.1:8000"

:: Run Django server
python manage.py runserver

echo.
echo ========================================
echo App closed. Press any key to exit.
pause > nul
