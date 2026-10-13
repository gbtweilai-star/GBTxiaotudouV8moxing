@echo off
chcp 65001 >nul
title GBT小土豆V8 · 接管 V9 换脑启动
cd /d "%~dp0"
echo ============================================================
echo   GBT小土豆V8 - 接管外部件 V9（换脑 + 联能力）
echo   口径：**她的树一行不改** —— 只在她进程的环境里把
echo         她唯一的 LLM 出口(core/brain.py)指到我们的大模型
echo ============================================================
echo.
echo [1/3] 接管自检（穿透 + 换脑实测 + 联能力）
py -3.14 -X utf8 tools\codex-scripts\takeover-v9.py --check
if errorlevel 1 (
  echo.
  echo [停] 接管自检没过 —— 按上面的读数修，不硬闯。
  pause
  exit /b 1
)
echo.
echo [2/3] 把她的脑指到我们的口（**只在本进程的环境变量里**）
set "OPENAI_BASE_URL=http://127.0.0.1:11434/v1"
set "OPENAI_API_KEY=ollama"
set "BRAIN_MODELS=qwen3:0.6b"
set "OMNIVOICE_PORT=3900"
echo     OPENAI_BASE_URL=%OPENAI_BASE_URL%
echo     BRAIN_MODELS=%BRAIN_MODELS%
echo.
echo [3/3] 原样调她的入口（原入口不动）
call "C:\Users\ADMIN\Desktop\GBT小土豆V9\GBT小土豆V9-总控台.cmd"
