@echo off
setlocal
REM ============================================================================
REM TransTools - Quick Launch Script for Windows
REM ============================================================================

REM Change to project root directory (parent of bin)
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found.
    echo Run setup.bat to finish the installation.
    pause
    exit /b 1
)

if /I "%~1"=="--check" goto :console_mode
if /I "%~1"=="--console" goto :console_mode

.venv\Scripts\python.exe src\bootstrap_cli.py run --check >nul 2>&1
if errorlevel 1 goto :console_mode

if exist ".venv\Scripts\pythonw.exe" (
    .venv\Scripts\pythonw.exe src\main.py %*
    if not errorlevel 1 exit /b 0
    echo ERROR: Windowed launch failed.
    echo Retrying in console mode...
)

:console_mode
.venv\Scripts\python.exe src\bootstrap_cli.py run --console %*
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    pause
)
exit /b %EXIT_CODE%
