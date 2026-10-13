@echo off
chcp 65001 >nul
"C:\WINDOWS\system32\netsh.EXE" wlan set ? 2>&1
