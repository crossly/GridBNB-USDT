@echo off
REM GridTrading Pro Testnet Startup Script for Windows
REM Pre-configured for BTC/USDT Futures Trading with 50x Leverage

setlocal enabledelayedexpansion

echo ==================================================================
echo          GridTrading Pro v2.0.0 - TESTNET MODE
echo ==================================================================
echo [WARNING] This is configured for HIGH LEVERAGE trading!
echo [WARNING] Trading Pair: BTC/USDT Futures
echo [WARNING] Leverage: 50x
echo [WARNING] Environment: Binance Testnet
echo ==================================================================
echo.

REM Confirmation prompt
set /p "confirm=Do you want to continue with testnet trading? (y/N): "
if /i not "%confirm%"=="y" (
    echo [INFO] Testnet startup cancelled
    pause
    exit /b 0
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [SUCCESS] Python detected
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
echo [INFO] Installing/updating dependencies...
pip install -r requirements.txt >nul 2>&1
echo [SUCCESS] Dependencies ready

REM Setup testnet environment
echo [TESTNET] Setting up testnet environment...

REM Copy testnet environment file
if exist ".env.testnet" (
    copy .env.testnet .env >nul
    echo [TESTNET] Testnet environment variables loaded
) else (
    echo [ERROR] Testnet environment file not found!
    pause
    exit /b 1
)

REM Check if testnet config exists
if not exist "config.testnet.yaml" (
    echo [ERROR] Testnet configuration file not found!
    pause
    exit /b 1
)

REM Create necessary directories
if not exist "data" mkdir data
if not exist "data\backups" mkdir data\backups
if not exist "logs" mkdir logs
echo [SUCCESS] Directories created

REM Display configuration summary
echo.
echo [TESTNET] === TESTNET CONFIGURATION SUMMARY ===
echo [TESTNET] Trading Mode: USDT-M Futures
echo [TESTNET] Symbol: BTC/USDT
echo [TESTNET] Leverage: 50x
echo [TESTNET] Grid Size: 0.5%% (dynamic)
echo [TESTNET] Max Drawdown: -10%%
echo [TESTNET] Daily Loss Limit: -5%%
echo [TESTNET] Web Dashboard: http://localhost:58181
echo.

REM Final confirmation
echo [WARNING] FINAL WARNING: 50x leverage is extremely risky!
echo [WARNING] Only use testnet funds for testing!
set /p "final_confirm=Are you sure you want to start? (y/N): "
if /i not "%final_confirm%"=="y" (
    echo [INFO] Testnet startup cancelled
    pause
    exit /b 0
)

REM Start the application with testnet config
echo [TESTNET] Starting GridTrading Pro in testnet mode...
echo.
python main.py --config config.testnet.yaml --testnet

REM Cleanup message
echo.
echo [TESTNET] GridTrading Pro testnet session ended
echo [INFO] Remember to review logs and performance before live trading!
pause
