@echo off
REM GridTrading Pro Startup Script for Windows
REM This script helps you start GridTrading Pro with proper environment setup

setlocal enabledelayedexpansion

echo ==================================================
echo          GridTrading Pro v2.0.0 Startup
echo ==================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [INFO] Python detected
python --version

REM Check if virtual environment exists
if not exist ".venv" (
    echo [WARNING] Virtual environment not found. Creating...
    python -m venv .venv
    echo [SUCCESS] Virtual environment created
)

REM Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [SUCCESS] Virtual environment activated
) else (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)

echo [INFO] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [SUCCESS] Dependencies installed

REM Check configuration files
if not exist "config.yaml" (
    echo [WARNING] config.yaml not found
    echo Please copy and configure it:
    echo   copy config.yaml.example config.yaml
    echo   Edit config.yaml with your settings
    pause
    exit /b 1
)

if not exist ".env" (
    echo [WARNING] .env file not found
    echo Please copy and configure it:
    echo   copy .env.example .env
    echo   Edit .env with your API credentials
    pause
    exit /b 1
)

echo [SUCCESS] Configuration files found

REM Create necessary directories
if not exist "data" mkdir data
if not exist "data\backups" mkdir data\backups
if not exist "logs" mkdir logs
echo [SUCCESS] Directories created

echo.
echo [SUCCESS] Setup complete! Starting GridTrading Pro...
echo.

REM Parse command line arguments and start
set ARGS=
:parse_args
if "%1"=="" goto start_app
if "%1"=="--testnet" (
    set ARGS=!ARGS! --testnet
    echo [INFO] Testnet mode enabled
)
if "%1"=="--config" (
    set ARGS=!ARGS! --config %2
    echo [INFO] Using config file: %2
    shift
)
if "%1"=="--dry-run" (
    set ARGS=!ARGS! --dry-run
    echo [INFO] Dry run mode enabled
)
shift
goto parse_args

:start_app
REM Start the application
python main.py !ARGS!

if errorlevel 1 (
    echo.
    echo [ERROR] GridTrading Pro exited with error
    pause
)

echo.
echo GridTrading Pro stopped
pause
