@echo off
chcp 65001 >nul 2>&1
rem run freebuff with the isolated HOME; ASCII-only on purpose
set "HOME=C:\Users\ADMIN\AppData\Local\gbt-freebuff\home"
set "USERPROFILE=C:\Users\ADMIN\AppData\Local\gbt-freebuff\home"
set "XDG_CONFIG_HOME=C:\Users\ADMIN\AppData\Local\gbt-freebuff\home\.config"
cd /d "%~dp0"
freebuff %*
