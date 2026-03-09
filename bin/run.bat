@echo off
REM ============================================================================
REM TransTools - Quick Launch Script for Windows
REM ============================================================================

REM Change to project root directory (parent of bin)
cd /d "%~dp0.."

REM Check if virtual environment exists
if not exist .venv (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment and run the program
call .venv\Scripts\activate.bat
pythonw src\main.py
if errorlevel 1 (
    echo ERROR: TransTools failed to start with pythonw.
    echo Showing detailed error output...
    python src\main.py
    pause
    exit /b 1
)
