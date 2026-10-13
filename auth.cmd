@echo off
rem GBT V8 - authorization grant launcher (Owner-only; AI can never grant)
rem Usage:
rem   auth.cmd                 -> grant the 5 daily scopes (each asks you to type YES)
rem   auth.cmd browser_control -> grant one scope (default ttl 3600)
rem   auth.cmd browser_control 600 -> grant one scope with ttl seconds
rem ASCII-only comments on purpose: cmd.exe reads this file in the OEM codepage (936/GBK),
rem so UTF-8 Chinese comments get byte-split and leak into commands (same class as "ps1 needs BOM").
setlocal
cd /d "%~dp0"

set "SCOPES=%*"
if "%SCOPES%"=="" set "SCOPES=browser_control desktop_control external_llm process_execute filesystem_write"

echo.
echo == GBT V8 auth grant ==
echo    scopes: %SCOPES%
echo    Each grant will ask you to type YES (input hidden). Ctrl+C cancels.
echo.

for %%S in (%SCOPES%) do (
  echo ---------------- scope: %%S ----------------
  py -3.14 -m gbt_allinone auth grant --scope %%S --ttl 3600
)

echo.
echo == done. Current status: ==
py -3.14 -m gbt_allinone auth status
echo.
echo ---- press any key to close ----
pause >nul
