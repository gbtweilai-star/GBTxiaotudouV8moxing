@echo off
rem GBT V8 - VoiceStudio local voice workbench launcher
rem Usage: double-click = status; or pass args: up / down / speak --text "..." / voices / models
rem Why: the owner often runs commands from C:\Users\ADMIN (home), where the repo-relative
rem path does not resolve. This file cd's into the repo root itself. ASCII-only on purpose:
rem cmd.exe reads .cmd files in the OEM codepage (936/GBK) - UTF-8 Chinese comments get
rem byte-split and leak into commands (same class as the "ps1 needs BOM" lesson in this repo).
cd /d "%~dp0"
set "ARGS=%*"
if "%ARGS%"=="" set "ARGS=status"
py -3.14 tools\codex-scripts\voicestudio.py %ARGS%
echo.
echo ---- done (press any key to close) ----
pause >nul
