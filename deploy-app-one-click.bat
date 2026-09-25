@echo off
REM One-click: APP payload -> one-key deploy (universal plug / run_task).
REM Grants are issued ONLY by the human typing YES in this window.
chcp 65001 >nul
cd /d "%~dp0"
py -3.10 deploy_app_oneclick.py %*
echo.
pause
