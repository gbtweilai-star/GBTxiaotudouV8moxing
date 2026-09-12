@echo off
chcp 65001 >nul
title GBT小土豆 桌面数字人
cd /d "%~dp0"
python main.py
if errorlevel 1 (
  echo.
  echo 启动失败，请检查是否已安装依赖：pip install PySide6 live2d-py
  pause
)
