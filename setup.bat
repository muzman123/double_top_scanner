@echo off
REM Double Top Scanner - Windows Setup Script
REM This script sets up the Python environment and installs all dependencies

echo ================================================================================
echo DOUBLE TOP SCANNER - SETUP (Windows)
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Python detected: 
python --version
echo.

REM Create virtual environment
echo [2/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping creation
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)
echo.

REM Activate virtual environment and install dependencies
echo [3/5] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

REM Copy configuration template if settings.yaml doesn't exist
echo [4/5] Setting up configuration...
if exist config\settings.yaml (
    echo Configuration file already exists, skipping
) else (
    if exist config\settings.yaml.template (
        copy config\settings.yaml.template config\settings.yaml
        echo Configuration template copied to config\settings.yaml
        echo IMPORTANT: Edit config\settings.yaml with your settings before running
    ) else (
        echo WARNING: Configuration template not found
    )
)
echo.

REM Create output directories
echo [5/5] Creating output directories...
if not exist output mkdir output
if not exist output\logs mkdir output\logs
echo Output directories created
echo.

echo ================================================================================
echo SETUP COMPLETE!
echo ================================================================================
echo.
echo Next steps:
echo   1. Edit config\settings.yaml with your settings
echo   2. For Gmail notifications:
echo      - Enable 2-Step Verification
echo      - Generate App Password at: https://myaccount.google.com/apppasswords
echo      - Add credentials to config\settings.yaml
echo   3. Run the scanner:
echo      - Full scan:     python run_scanner.py
echo      - Test mode:     python run_scanner.py --test
echo      - Single symbol: python run_scanner.py --symbol AAPL
echo   4. Run tests:      python -m pytest tests/ -v
echo.
echo For help, see README.md
echo ================================================================================
pause
