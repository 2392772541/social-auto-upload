@echo off
chcp 65001 >nul
cd /d "%~dp0"
TITLE SAU 一键停止

echo ==================================================
echo   正在停止 SAU 后端(5409) 和 前端(5173) ...
echo ==================================================

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-win.ps1"

echo.
echo 已完成清理。
powershell -NoProfile -Command "Start-Sleep -Seconds 2"
exit /b 0
