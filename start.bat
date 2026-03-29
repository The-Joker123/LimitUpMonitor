@echo off
setlocal enabledelayedexpansion

set "projectRoot=%~dp0"
set "backendDir=%projectRoot%backend"
set "frontendDir=%projectRoot%frontend"

for /f "tokens=4" %%a in ('powershell -Command "(Get-Content '%projectRoot%config.json' | ConvertFrom-Json).backend.port"') do set BACKEND_PORT=%%a
for /f "tokens=4" %%a in ('powershell -Command "(Get-Content '%projectRoot%config.json' | ConvertFrom-Json).frontend.port"') do set FRONTEND_PORT=%%a

echo Checking ports...
netstat -ano | findstr "LISTENING" | findstr ":%BACKEND_PORT%" >nul
if %errorlevel% equ 0 (
    echo Backend port %BACKEND_PORT% is in use, killing...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT%" ^| findstr "LISTENING"') do taskkill /F /PID %%a
)
netstat -ano | findstr "LISTENING" | findstr ":%FRONTEND_PORT%" >nul
if %errorlevel% equ 0 (
    echo Frontend port %FRONTEND_PORT% is in use, killing...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%FRONTEND_PORT%" ^| findstr "LISTENING"') do taskkill /F /PID %%a
)

echo Starting backend on port %BACKEND_PORT%...
start "" cmd /c "cd /d "%backendDir% && python -m uvicorn main:app --reload --host 0.0.0.0 --port %BACKEND_PORT%"

echo Starting frontend on port %FRONTEND_PORT%...
cd /d "%frontendDir%"
start "" cmd /c "npm run dev"

echo.
echo LimitUp Monitor started.
echo   Frontend: http://localhost:%FRONTEND_PORT%
echo   Backend:  http://localhost:%BACKEND_PORT%
