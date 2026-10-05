@echo off
title CYBER AI
cd /d "%~dp0"

REM --- first-run API key setup: ask once, save forever ---
if "%GEMINI_API_KEY%"=="" (
  echo ============================================
  echo  CYBER AI - first time setup
  echo ============================================
  echo.
  echo  Get a FREE Gemini API key (no card):
  echo  https://aistudio.google.com/apikey
  echo.
  set /p GEMINI_KEY="  Paste your key here (or Enter for offline mode): "
  if not "%GEMINI_KEY%"=="" (
    set GEMINI_API_KEY=%GEMINI_KEY%
    setx GEMINI_API_KEY "%GEMINI_KEY%" >nul 2>&1
    echo.
    echo  Key saved! You won't be asked again.
  ) else (
    echo.
    echo  Starting in OFFLINE mode (built-in answers only)...
  )
  echo.
)

echo Starting CYBER AI...
python -u jarvis.py
pause
