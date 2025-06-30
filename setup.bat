@echo off
setlocal enabledelayedexpansion

:: === Configuration ===
set "PYVER=3.12.3"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYVER%/python-%PYVER%-amd64.exe"
set "BASE=%CD%"
set "ROOT=%BASE%\pythonserver"
set "LIVE=%ROOT%\LIVE"

:: 1. Create folders
echo 📁 Creating folder: %LIVE%
mkdir "%LIVE%" >nul 2>&1

:: 2. Check Python version
for /f "tokens=2 delims==" %%V in ('"python --version 2>&1 | findstr "Python""') do (
    set "VERSION=%%V"
)
set "VERSION=!VERSION:~1!"

:: 3. Compare version
if "!VERSION!"=="%PYVER%" (
    echo ✅ Python %PYVER% already installed. Skipping installation.
) else (
    echo 🐍 Installing Python %PYVER%...
    curl -o python-installer.exe %PYTHON_URL%
    start /wait python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    del python-installer.exe
)

:: 4. Verify Python is now usable
python --version >nul 2>&1 || (
    echo ❌ Python installation failed or not added to PATH.
    pause
    exit /b
)

:: 5. Download server.py into backend only (NOT in LIVE)
echo ⬇️ Downloading server.py to: %ROOT%
curl -o "%ROOT%\server.py" https://raw.githubusercontent.com/YOUR_USERNAME/pythonserver-autosetup/main/server.py

:: 6. Done
echo.
echo ✅ Setup complete.
echo ▶️ To start your server:
echo    cd /d "%ROOT%"
echo    python server.py
pause
