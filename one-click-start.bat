@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"
TITLE SAU 一键启动

echo ==================================================
echo   SAU 视频一键发布 - 一键启动
echo ==================================================
echo.

if not exist "conf.py" (
    if exist "conf.example.py" (
        copy /y "conf.example.py" "conf.py" >nul
        echo [OK] 已自动生成 conf.py
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/4] 正在创建 Python 虚拟环境 .venv ...
    where uv >nul 2>nul
    if !errorlevel! equ 0 (
        uv venv .venv --python 3.12
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 (
        echo [ERROR] 创建虚拟环境失败，请检查 Python 或 uv 是否可用。
        pause
        exit /b 1
    )
)

".venv\Scripts\python.exe" -c "import flask, flask_cors, playwright, patchright, xhs" >nul 2>nul
if errorlevel 1 (
    echo [2/4] 正在安装后端依赖 ...
    where uv >nul 2>nul
    if !errorlevel! equ 0 (
        uv pip install --python ".venv\Scripts\python.exe" -e ".[web]" playwright xhs
    ) else (
        ".venv\Scripts\python.exe" -m pip install -e ".[web]" playwright xhs
    )
    if errorlevel 1 (
        echo [ERROR] 后端依赖安装失败。
        pause
        exit /b 1
    )
) else (
    echo [OK] 后端依赖已就绪
)

dir /b "%LOCALAPPDATA%\ms-playwright\chromium-*" >nul 2>nul
if errorlevel 1 (
    echo [2.5/4] 未检测到 Chromium 浏览器缓存，正在自动安装...
    set "PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright"
    ".venv\Scripts\python.exe" -m playwright install chromium
    ".venv\Scripts\python.exe" -m patchright install chromium
)

if not exist "sau_frontend\node_modules" (
    echo [3/4] 正在安装前端依赖 ...
    pushd sau_frontend
    call npm install --no-audit --no-fund
    if errorlevel 1 (
        popd
        echo [ERROR] 前端依赖安装失败。
        pause
        exit /b 1
    )
    popd
) else (
    echo [OK] 前端依赖已就绪
)

echo [4/4] 正在启动后端(5409) 与 前端(5173) ...
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 5409 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if errorlevel 1 (
    start "SAU Backend (5409)" cmd /k "cd /d ""%~dp0"" && "".venv\Scripts\python.exe"" sau_backend.py"
) else (
    echo [WARN] 5409 端口已在运行，跳过重复启动后端
)

powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if errorlevel 1 (
    start "SAU Frontend (5173)" cmd /k "cd /d ""%~dp0sau_frontend"" && npm run dev -- --host 0.0.0.0"
) else (
    echo [WARN] 5173 端口已在运行，跳过重复启动前端
)

echo.
echo ==================================================
echo   启动指令已发出：
echo   前端地址: http://localhost:5173
echo   后端地址: http://localhost:5409
echo ==================================================
powershell -NoProfile -Command "Start-Sleep -Seconds 4"
exit /b 0
