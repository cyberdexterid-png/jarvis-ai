@echo off
title CYBER AI - ONLINE MODE
cd /d "%~dp0"

echo ============================================
echo  CYBER AI - ONLINE MODE
echo  Control your laptop from anywhere!
echo  (phone, tablet, another PC)
echo ============================================
echo.

if "%GEMINI_API_KEY%"=="" (
  echo  Get a FREE Gemini API key (no card):
  echo  https://aistudio.google.com/apikey
  echo.
  set /p GEMINI_KEY="  Paste your key here (or Enter for offline mode): "
  if not "%GEMINI_KEY%"=="" (
    set GEMINI_API_KEY=%GEMINI_KEY%
    setx GEMINI_API_KEY "%GEMINI_KEY%" >nul 2>&1
    echo  Key saved!
  )
  echo.
)

set CFD=%~dp0cloudflared.exe
if not exist "%CFD%" (
  where cloudflared >nul 2>&1
  if errorlevel 1 (
    echo  cloudflared not found.
    echo  Download it free from cloudflare.com and put
    echo  cloudflared.exe next to this file, then run again.
    pause
    exit /b 1
  ) else (
    set CFD=cloudflared
  )
)

echo  Starting CYBER AI server...
start "CYBER AI server" /min python -u jarvis.py
timeout /t 5 >nul

echo.
echo ============================================
echo  Creating your public link...
echo.
echo  *** DO NOT share this link ***
echo  Anyone with it can control your PC!
echo.
echo  Keep this window OPEN while using online mode.
echo ============================================
echo.
"%CFD%" tunnel --url http://127.0.0.1:8080
pause
