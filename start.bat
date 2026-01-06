@echo off
REM Voice PDF Assistant - Windows Startup Script

echo.
echo ========================================
echo   Voice PDF Assistant - Starting...
echo ========================================
echo.

REM Start backend in new window
echo Starting backend server...
start "Voice PDF Backend" cmd /k "cd backend && venv\Scripts\activate && python run.py server"

REM Wait a moment
timeout /t 3 /nobreak > nul

REM Start frontend in new window
echo Starting frontend server...
start "Voice PDF Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo   Services are starting...
echo ========================================
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
echo   Close the command windows to stop services
echo ========================================
echo.

pause
