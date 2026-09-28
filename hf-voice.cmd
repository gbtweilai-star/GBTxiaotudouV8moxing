@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
set PYTHONIOENCODING=utf-8
set PYEXE=py -3.14
%PYEXE% -c "import sys" >nul 2>&1 || set PYEXE=python
%PYEXE% -m gbt_allinone.tools.hf_voice %*
