@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"
TITLE SAU 控制中心

:menu
cls
echo ==================================================
echo   SAU 视频一键发布 - 控制中心
echo   项目目录: %~dp0
echo ==================================================
echo.
echo   [1] 启动服务 (自动检查依赖并启动前后端)
echo   [2] 仅安装依赖 (Python .venv + 前端 + 浏览器检查)
echo   [3] 强制重装依赖 (重建 .venv 和 node_modules)
echo   [4] 停止服务 (关闭 sau_backend / vite 并释放 5409/5173)
echo   [0] 退出
echo.
set /p choice=请输入选项编号并回车: 

if "%choice%"=="1" goto do_start
if "%choice%"=="2" goto do_install
if "%choice%"=="3" goto do_reinstall
if "%choice%"=="4" goto do_stop
if "%choice%"=="0" exit /b 0
echo 无效选项，请重新输入。
powershell -NoProfile -Command "Start-Sleep -Seconds 1"
goto menu

:do_start
call "%~dp0one-click-start.bat"
goto menu

:do_install
echo.
if not exist "conf.py" (
    if exist "conf.example.py" copy /y "conf.example.py" "conf.py" >nul
)
if not exist ".venv\Scripts\python.exe" (
    where uv >nul 2>nul
    if !errorlevel! equ 0 (
        uv venv .venv --python 3.12
    ) else (
        python -m venv .venv
    )
)
where uv >nul 2>nul
if !errorlevel! equ 0 (
    uv pip install --python ".venv\Scripts\python.exe" -e ".[web]" playwright xhs
) else (
    ".venv\Scripts\python.exe" -m pip install -e ".[web]" playwright xhs
)
dir /b "%LOCALAPPDATA%\ms-playwright\chromium-*" >nul 2>nul
if errorlevel 1 (
    set "PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright"
    ".venv\Scripts\python.exe" -m playwright install chromium
    ".venv\Scripts\python.exe" -m patchright install chromium
)
pushd sau_frontend
call npm install --no-audit --no-fund
popd
echo.
echo [OK] 依赖安装完成。
pause
goto menu

:do_reinstall
echo.
call "%~dp0stop-win.bat"
if exist ".venv" rmdir /s /q ".venv"
if exist "sau_frontend\node_modules" rmdir /s /q "sau_frontend\node_modules"
goto do_install

:do_stop
call "%~dp0stop-win.bat"
pause
goto menu
