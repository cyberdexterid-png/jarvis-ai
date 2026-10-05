@echo off
title Build JARVIS.exe
cd /d "%~dp0"
echo ============================================
echo  Building JARVIS.exe  (one-time, few minutes)
echo ============================================
echo.

echo [1/2] Installing PyInstaller...
python -m pip install --upgrade pyinstaller
if errorlevel 1 (
  echo FAILED to install PyInstaller. Check your internet / Python.
  pause
  exit /b 1
)

echo.
echo [2/2] Building exe (this takes a few minutes)...
set ICONARG=
if exist "jarvis.ico" set ICONARG=--icon jarvis.ico
python -m PyInstaller --noconfirm --clean ^
  --onefile ^
  --noconsole ^
  --name JARVIS ^
  %ICONARG% ^
  --add-data "web_hud.html;." ^
  --hidden-import pyttsx3.drivers.sapi5 ^
  jarvis.py

echo.
echo ============================================
if exist "dist\JARVIS.exe" (
  echo  DONE! Your file: dist\JARVIS.exe
  echo  Share that single file - no Python needed!
) else (
  echo  Build FAILED - see errors above.
)
echo ============================================
pause
