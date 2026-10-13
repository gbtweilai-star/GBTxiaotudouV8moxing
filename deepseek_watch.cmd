@echo off
title GBT XiaoTuDou V8 - DeepSeek Decision Bridge watch
cd /d "%~dp0"
py -3.14 tools\codex-scripts\deepseek_bridge.py watch --execute --interval 1.2
pause
