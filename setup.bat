@echo off
setlocal
REM TransTools - Setup Script (Windows)
cd /d "%~dp0"

call :resolve_python
if errorlevel 1 (
    pause
    exit /b 1
)

%PYTHON_EXE% %PYTHON_ARGS% src\bootstrap_cli.py setup %*
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    pause
)
exit /b %EXIT_CODE%

:resolve_python
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PYTHON_ARGS=-3.12"
    exit /b 0
)

py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PYTHON_ARGS=-3"
    exit /b 0
)

python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python"
    set "PYTHON_ARGS="
    exit /b 0
)

echo ERROR: Python 3.12 or newer is required.
echo Install Python from https://www.python.org/ and then run setup.bat again.
exit /b 1
