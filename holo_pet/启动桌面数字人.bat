@echo off
setlocal
title GBT Xiao Tu Dou V8 - Desktop Digital Human
cd /d "%~dp0.."

set "PY="
if exist "C:\Python310\python.exe" set "PY=C:\Python310\python.exe"
if not defined PY if exist "C:\Python312\python.exe" set "PY=C:\Python312\python.exe"
if not defined PY where python >nul 2>nul && set "PY=python"

if not defined PY (
  echo [ERROR] Python was not found.
  pause
  exit /b 1
)

echo [1/2] Ensuring the local panel is running on 127.0.0.1:8765 ...
start "GBT Holo Panel" /min "%PY%" "holo_pet\launch_panel.py" --host 127.0.0.1 --port 8765
timeout /t 3 /nobreak >nul

echo [2/2] Opening the transparent always-on-top desktop shell ...
pushd "%~dp0"
call npx --no-install electron "desktop\main.cjs"
popd

if errorlevel 1 (
  echo.
  echo [HINT] Electron runtime missing. Run:  cd holo_pet ^&^& npm install --no-audit --no-fund electron@43.0.0
  pause
)
