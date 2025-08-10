@echo off
setlocal enableextensions enabledelayedexpansion

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                                                                              ║
echo ║  🎮 Discord RPG Bot - Advanced Tactical Combat & Cooperative Gameplay      ║
echo ║                                                                              ║
echo ║  Starting with clean console output...                                      ║
echo ║                                                                              ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

REM Check if virtual environment exists
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    goto :start_bot
)

REM Try system Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :start_bot
)

REM Try py launcher
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    goto :start_bot
)

echo ❌ Python not found!
echo.
echo Please install Python 3.11+ from: https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:start_bot
echo ✅ Found Python: %PYTHON_CMD%
echo.

REM Check if .env exists and has proper token
if not exist ".env" (
    echo ⚠️  .env file not found. Creating template...
    echo DISCORD_TOKEN=your_discord_bot_token_here > .env
    echo BOT_PREFIX=! >> .env
    echo DEBUG_MODE=False >> .env
    echo.
    echo 📝 Please edit .env and add your Discord bot token!
    echo.
    pause
    exit /b 1
)

REM Check if token is placeholder
findstr /C:"your_discord_bot_token_here" .env >nul
if %errorlevel% equ 0 (
    echo ⚠️  Discord token not set in .env file
    echo 📝 Please edit .env and replace 'your_discord_bot_token_here' with your actual token
    echo.
    pause
    exit /b 1
)

echo 🚀 Starting Discord RPG Bot...
echo ============================================================
echo.

REM Start the bot with clean output
%PYTHON_CMD% start_bot.py

echo.
echo 👋 Bot stopped.
pause
