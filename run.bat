@echo off
echo Starting AI Code Editor Pro...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from https://python.org
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check for API key
if not exist .env (
    echo.
    echo Warning: .env file not found
    echo Please create a .env file with your Gemini API key:
    echo GEMINI_API_KEY=your_api_key_here
    echo.
    echo You can get an API key from: https://makersuite.google.com/app/apikey
    echo.
    pause
)

REM Start the application
echo Starting AI Code Editor Pro...
python enhanced_main.py

if errorlevel 1 (
    echo.
    echo Application exited with error
    pause
)

