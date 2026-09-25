@echo off
setlocal
chcp 65001 >nul
set "TARGET=%USERPROFILE%\Desktop\GBT小土豆V8-星云APP.cmd"
if exist "%TARGET%" del /q "%TARGET%"
echo 本机启动入口已移除。项目数据和凭据未删除。
pause
