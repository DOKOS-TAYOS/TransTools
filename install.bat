@echo off
REM TransTools - Installation Script (Windows)
REM Checks Git and Python, clones repo, runs setup

echo.
echo ====================================
echo TransTools Installation
echo ====================================
echo.

git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH
    echo Install from https://git-scm.com/download/win
    pause
    exit /b 1
)
echo [1/3] Git found: 
git --version

set "REPO_URL=https://github.com/DOKOS-TAYOS/TransTools.git"
set "REPO_NAME=TransTools"

if exist "%REPO_NAME%" (
    echo.
    echo WARNING: Directory %REPO_NAME% already exists
    echo Using existing directory. Run setup.bat to update.
    cd "%REPO_NAME%"
    goto :run_setup
)

echo.
echo [2/3] Cloning repository...
git clone "%REPO_URL%"
if errorlevel 1 (
    echo ERROR: Failed to clone
    pause
    exit /b 1
)

cd "%REPO_NAME%"
if errorlevel 1 (
    echo ERROR: Failed to change directory
    pause
    exit /b 1
)

:run_setup
echo.
echo [3/3] Running setup...
call setup.bat
if errorlevel 1 (
    echo ERROR: Setup failed
    pause
    exit /b 1
)

echo.
echo Installation Complete!
echo Run from: %CD%
echo.
pause
