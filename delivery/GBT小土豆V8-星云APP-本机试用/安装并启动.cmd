@echo off
setlocal
chcp 65001 >nul
set "TARGET=%USERPROFILE%\Desktop\GBT小土豆V8-星云APP.cmd"
(
  echo @echo off
  echo powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0启动星云APP.ps1"
) > "%TARGET%"
echo 已安装本机启动入口：%TARGET%
start "" "%TARGET%"
