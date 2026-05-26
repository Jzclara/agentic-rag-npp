@echo off
chcp 65001 >nul
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

:: Wait for backend to initialize (model loading takes a few seconds)
echo      Waiting for backend to load models...
timeout /t 8 /nobreak >nul

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
