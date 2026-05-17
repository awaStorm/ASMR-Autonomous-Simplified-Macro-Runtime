
@echo off
chcp 65001 >nul
title ASMR 项目启动器

cd /d "%~dp0"
echo ========================================
echo 正在启动 ASMR 项目...
echo ========================================

REM 检查 Node.js 是否安装
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Node.js，请先安装 Node.js！
    pause
    exit /b 1
)

REM 检查 Python 是否安装
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python！
    pause
    exit /b 1
)

echo [1/3] 正在启动后端服务...
start "后端服务" powershell -NoExit -Command "cd '%~dp0backend'; python -m uvicorn app.main:app --reload --port 8137"

timeout /t 2 /nobreak >nul

echo [2/3] 正在启动前端服务...
start "前端服务" powershell -NoExit -Command "cd '%~dp0frontend'; npm run dev"

timeout /t 3 /nobreak >nul

echo [3/3] 尝试启动浏览器...
where msedge >nul 2>nul
if %errorlevel% equ 0 (
    start msedge "http://localhost:5173"
) else (
    where chrome >nul 2>nul
    if %errorlevel% equ 0 (
        start chrome "http://localhost:5173"
    ) else (
        echo [提示] 未检测到 Edge 或 Chrome 浏览器，请手动访问:
        echo           http://localhost:5173
        echo.
    )
)

echo ========================================
echo 启动完成！
echo - 前端地址: http://localhost:5173
echo - 后端地址: http://localhost:8137
echo ========================================
echo.
echo 如需关闭服务，请关闭对应的窗口。
echo.
pause
