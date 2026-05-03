@echo off
setlocal
REM TransTools - Installation Script (Windows)
REM Checks Git, clones safely, and delegates setup

echo.
echo ====================================
echo TransTools Installation
echo ====================================
echo.

git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH.
    echo Install it from https://git-scm.com/download/win and then run this script again.
    pause
    exit /b 1
)
echo [1/4] Git found:
git --version

if not defined REPO_URL set "REPO_URL=https://github.com/DOKOS-TAYOS/TransTools.git"
if not defined REPO_NAME set "REPO_NAME=TransTools"

echo.
echo [2/4] Preparing target folder...
if exist "%REPO_NAME%" (
    if exist "%REPO_NAME%\setup.bat" if exist "%REPO_NAME%\pyproject.toml" (
        echo Existing TransTools checkout detected in "%REPO_NAME%".
        cd /d "%REPO_NAME%"
        goto :run_setup
    )
    echo ERROR: "%REPO_NAME%" already exists but does not look like a TransTools checkout.
    echo Choose another folder name with REPO_NAME or rename the existing path and try again.
    pause
    exit /b 1
)

echo.
echo [3/4] Cloning repository...
git clone "%REPO_URL%" "%REPO_NAME%"
if errorlevel 1 (
    echo ERROR: Failed to clone "%REPO_URL%".
    echo Check your internet connection or repository access and try again.
    pause
    exit /b 1
)

cd /d "%REPO_NAME%"
if errorlevel 1 (
    echo ERROR: The repository was cloned but the folder could not be opened.
    pause
    exit /b 1
)

:run_setup
if not exist setup.bat (
    echo ERROR: setup.bat was not found in "%CD%".
    pause
    exit /b 1
)

echo.
echo [4/4] Running setup...
call setup.bat %*
if errorlevel 1 (
    echo ERROR: Setup did not complete successfully.
    pause
    exit /b 1
)

echo.
echo Installation complete.
echo Folder: %CD%
echo Next run command: bin\run.bat
echo.
pause
