@echo off
setlocal

echo ≡ƒöì Checking if pyngrok is already installed...

:: Use python -m pip to avoid PATH issues
python -m pip show pyngrok >nul 2>&1

if %errorlevel%==0 (
    echo ✅ pyngrok is already installed.
) else (
    echo ⬇️ pyngrok not found. Installing...
    python -m pip install pyngrok
    if %errorlevel%==0 (
        echo ✅ pyngrok installed successfully!
    ) else (
        echo ❌ Failed to install pyngrok. Make sure pip and internet are working.
    )
)

echo.
pause
