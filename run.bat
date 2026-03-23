@echo off
title Voice Assistant Launcher
echo ========================================
echo Voice Assistant - Auto Setup & Launch
echo ========================================
echo [1/3] Installing Python dependencies...
pip install -r requirements.txt > nul 2>&1
if %errorlevel% neq 0 (
    echo [1.1] PyAudio failed - Installing via pipwin...
    pip install pipwin > nul 2>&1
    pipwin install pyaudio > nul 2>&1
    pip install SpeechRecognition pyttsx3 pywhatkit wikipedia eel > nul 2>&1
)
echo [2/3] Dependencies ready!
echo [3/3] Launching Django Server with Marry UI (http://127.0.0.1:8000)...
start "" "http://127.0.0.1:8000"
python manage.py runserver 0.0.0.0:8000
echo.
echo ========================================
echo App closed. Press any key to exit.
pause > nul
