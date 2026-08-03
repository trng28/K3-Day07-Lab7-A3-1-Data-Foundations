@echo off
setlocal
cd /d "%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\install_requirements.ps1" %*
exit /b %errorlevel%
