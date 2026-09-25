@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

REM ---------------------------------------------------------------
REM Feishu credential self-check (read-only).
REM
REM WHY THIS FILE EXISTS:
REM   DPAPI blobs are bound to the Windows user session that created them.
REM   When the framework runs inside a sandbox identity, decryption fails and
REM   status() reports credential_source = "unreadable".
REM   "Cannot decrypt here" does NOT mean "not configured".
REM   Only the owner's own session can answer "is it configured?".
REM
REM   So: double-click THIS file. It runs in your session, prints one JSON
REM   blob, and writes nothing. Nothing is uploaded, nothing is changed.
REM
REM ASCII-only on purpose: cmd.exe reads .bat as ANSI/GBK, so a UTF-8
REM Chinese literal here would be garbled (pit list item #2).
REM ---------------------------------------------------------------

set "PY="
if exist "C:\Python310\python.exe" set "PY=C:\Python310\python.exe"
if not defined PY if exist "C:\Python312\python.exe" set "PY=C:\Python312\python.exe"
if not defined PY where python >nul 2>nul && set "PY=python"

if not defined PY (
  echo [ERROR] Python was not found.
  pause
  exit /b 1
)

echo [feishu] credential self-check (read-only) ...
echo.
"%PY%" -m gbt_allinone.feishu_bridge status
echo.
echo [how to read it]
echo   configured true   -^> credentials are usable in YOUR session
echo   configured false  -^> source says missing or unreadable; report the JSON as-is
echo.
pause
