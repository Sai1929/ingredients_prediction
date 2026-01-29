@echo off
REM ============================================
REM Recipe Ingredient Calculator - Start All
REM ============================================

echo.
echo ============================================
echo   Recipe Ingredient Calculator
echo   Starting Backend and Frontend...
echo ============================================
echo.

REM Check if Python exists
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements if needed
echo Checking dependencies...
pip install -r requirements.txt -q

REM Start backend in background
echo.
echo Starting backend server on port 8000...
start "Recipe API Backend" cmd /c "venv\Scripts\activate.bat && python run.py"

REM Wait for backend to start
echo Waiting for backend to initialize...
timeout /t 3 /nobreak >nul

REM Start frontend
echo Starting frontend server on port 3000...
start "Recipe Frontend" cmd /c "venv\Scripts\activate.bat && python serve_frontend.py"

echo.
echo ============================================
echo   Both servers are starting!
echo.
echo   Backend API: http://localhost:8000
echo   Frontend UI: http://localhost:3000
echo.
echo   Close the terminal windows to stop.
echo ============================================
echo.

pause
