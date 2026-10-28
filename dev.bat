@echo off
echo ========================================================
echo  Kortex - Autonomous Research Intelligence
echo ========================================================
echo Starting Backend and Frontend...

start "Kortex Backend" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"
timeout /t 2 /nobreak >nul
start "Kortex Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Backend running at:  http://127.0.0.1:8000
echo Frontend running at: http://127.0.0.1:5173
echo.
