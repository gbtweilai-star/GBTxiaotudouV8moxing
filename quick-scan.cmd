@echo off
rem ==================================================================
rem  GBT xiaotudou V8 -- full-dimension fault quick-scan -- launcher
rem  Author: zi you de feng  (Chinese doc lives in skills/gbt-quickscan/SKILL.md)
rem
rem  WHY THIS FILE IS 7-BIT ASCII ONLY:
rem  cmd.exe parses this file under the console codepage (GBK/936 here).
rem  Any non-ASCII byte inside a "rem" line gets mis-decoded, the line is
rem  split, and cmd.exe then tries to EXECUTE the tail as a command.
rem  Observed twice on 2026-09-23: exit code 3 + "'<mojibake>' is not
rem  recognized as an internal or external command". Keep it pure ASCII.
rem
rem  USAGE (works from ANY directory):
rem    quick-scan.cmd                quick scan
rem    quick-scan.cmd --with-gates   also run the framework read-only gates
rem    quick-scan.cmd --accept       set this round as the new baseline
rem    quick-scan.cmd --quiet        exit code only (heartbeat / CI)
rem
rem  EXIT CODE: 0 no P0/P1 - 1 has P0 - 2 has P1 - 3 scanner itself failed
rem ==================================================================
setlocal
chcp 65001 >nul 2>&1

set "GBT_ROOT=%~dp0"
set "GBT_TOOL=%GBT_ROOT%tools\codex-scripts\quick_scan.py"

if not exist "%GBT_TOOL%" (
  echo [ERROR] scanner not found: %GBT_TOOL%
  echo         keep this launcher at the repo root.
  exit /b 3
)

set PYTHONUTF8=1
set PYTHONDONTWRITEBYTECODE=1

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3.14 "%GBT_TOOL%" %*
) else (
  python "%GBT_TOOL%" %*
)
exit /b %ERRORLEVEL%
