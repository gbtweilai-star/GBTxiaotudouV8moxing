@echo off
title GBT Potato - Desktop Digital Human
cd /d "%~dp0"
set "PY="
call :probe python
call :probe py -3
call :probe "C:\Python310\python.exe"
call :probe "C:\Python311\python.exe"
call :probe "C:\Python312\python.exe"
call :probe "C:\Python313\python.exe"
if not defined PY (
  echo [ERROR] No Python with PySide6 found.
  echo         Run first:  pip install PySide6 live2d-py
  echo.
  pause
  exit /b 1
)
echo Interpreter: %PY%
echo Starting GBT Potato desktop digital human...
%PY% main.py
if errorlevel 1 (
  echo.
  echo Start failed. Check dependencies:  pip install PySide6 live2d-py
  pause
)
exit /b 0

:probe
if defined PY goto :eof
"%~1" %~2 -c "import PySide6" >nul 2>nul
if errorlevel 1 goto :eof
set "PY="%~1" %~2"
goto :eof
