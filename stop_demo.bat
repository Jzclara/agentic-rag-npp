@echo off
chcp 65001 >nul
echo Stopping demo services...

:: Kill uvicorn (backend)
taskkill /f /im uvicorn.exe 2>nul
if %errorlevel%==0 (echo   Backend stopped.) else (echo   Backend was not running.)

:: Kill node/vite (frontend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a 2>nul
)
echo   Frontend stopped.

echo.
echo All demo services stopped.
timeout /t 3 >nul
