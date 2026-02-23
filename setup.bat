@echo off
REM TransTools - Setup Script (Windows)
cd /d "%~dp0"

echo.
echo ====================================
echo TransTools Setup (Windows)
echo ====================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.12+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/6] Checking Python version...
python --version
python -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.12 or higher is required
    pause
    exit /b 1
)
echo Python version OK

echo.
echo [2/6] Creating virtual environment...
if exist .venv (
    echo Virtual environment already exists
) else (
    python -m venv .venv
    echo Virtual environment created
)

echo.
echo [3/6] Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo [4/6] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [5/6] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [6/6] Setting up environment file...
if exist .env (
    echo .env already exists, skipping
) else (
    if exist .env.example (
        copy .env.example .env >nul
        echo .env created from .env.example
    ) else (
        echo Warning: .env.example not found
    )
)

echo.
echo [7/7] Creating desktop shortcut...
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT_NAME=TransTools.lnk"
set "TARGET_PATH=%~dp0bin\run.bat"
set "WORKING_DIR=%~dp0"
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\%SHORTCUT_NAME%'); $Shortcut.TargetPath = '%TARGET_PATH%'; $Shortcut.WorkingDirectory = '%WORKING_DIR%'; $Shortcut.Description = 'TransTools'; $Shortcut.Save()" >nul 2>&1
if errorlevel 1 (
    echo Warning: Could not create desktop shortcut
) else (
    echo Desktop shortcut created
)

echo.
echo ====================================
echo Setup Complete!
echo ====================================
echo Run: bin\run.bat
echo Or double-click TransTools.lnk on Desktop
echo.
pause
