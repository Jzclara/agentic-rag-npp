@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Agentic RAG NPP - Demo

echo ============================================
echo   Agentic RAG - NPP Fault Diagnosis Demo
echo ============================================
echo.

:: Check venv exists
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] .venv not found. Run: python -m venv .venv
    pause
    exit /b 1
)

:: Check node_modules exists
if not exist "web\node_modules" (
    echo [ERROR] web/node_modules not found. Run: cd web ^&^& npm install
    pause
    exit /b 1
)

echo [1/2] Starting backend (FastAPI + LangGraph) ...
start "RAG-Backend" cmd /k ".venv\Scripts\activate.bat && echo Backend starting on http://localhost:8000 && .venv\Scripts\uvicorn.exe src.server:app --port 8000"

:: Wait until backend health endpoint is ready.
echo      Waiting for backend to become ready...
for /l %%i in (1,1,60) do (
    powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/health -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } } catch { exit 1 }"
    if not errorlevel 1 goto backend_ready
    timeout /t 2 /nobreak >nul
)

echo [ERROR] Backend did not become ready after 120 seconds.
echo Check the RAG-Backend window for the real error message.
pause
exit /b 1

:backend_ready
echo      Backend is ready.

echo [2/2] Starting frontend (Vite + React) ...
start "RAG-Frontend" cmd /k "cd web && echo Frontend starting... && npx vite --port 5173 --open"

echo.
echo ============================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo ============================================
echo.
echo Both services are running in separate windows.
echo Close this window or press any key to exit.
echo (Closing this window will NOT stop the services.)
echo.
pause
