@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo Run setup.ps1 first. & pause & exit /b 3)
".venv\Scripts\python.exe" health_check.py
set "pixoo_health_exit=%ERRORLEVEL%"
pause
exit /b %pixoo_health_exit%
