@echo off
title GBT Potato - Codex channel self-check
cd /d "%~dp0.."
set "PY="
call :probe python
call :probe py -3
call :probe "C:\Python310\python.exe"
call :probe "C:\Python311\python.exe"
call :probe "C:\Python312\python.exe"
call :probe "C:\Python313\python.exe"
if not defined PY (
  echo [ERROR] No usable Python found. Install Python 3.10+ and add it to PATH.
  echo.
  pause
  exit /b 1
)
echo Interpreter: %PY%
echo.
echo Running Codex channel self-check. A real turn consumes a little quota.
echo.
%PY% -m gbt_allinone.codex_bridge --live
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo [ALL GREEN] locate, handshake, session, real reply - all four steps passed.
) else (
  echo [NOT ALL GREEN] If the first three steps passed and only turn_stream failed,
  echo                 it is usually not-logged-in or no network.
  echo                 Run  codex login  in a terminal, then retry.
  echo                 If locate already failed, Codex is not installed on this machine.
)
echo.
pause
exit /b %RC%

:probe
if defined PY goto :eof
"%~1" %~2 -c "import encodings, sys" >nul 2>nul
if errorlevel 1 goto :eof
set "PY="%~1" %~2"
goto :eof
