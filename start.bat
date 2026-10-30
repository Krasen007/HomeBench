@echo off
setlocal enabledelayedexpansion

echo ================================================
echo HomeBench - starting up
echo ================================================

REM --- Check Python 3.8+ ---
echo.
echo [1/4] Checking Python (requires 3.8+)...

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python is not installed or not found on PATH.
    echo Please install Python 3.8 or later from https://www.python.org
    echo.
    pause
    exit /b 1
)

python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>nul
if errorlevel 1 (
    for /f "delims=" %%v in ('python --version 2^>^&1') do set PYVER=%%v
    echo ERROR: Python 3.8 or later is required.
    echo Detected: !PYVER!
    echo.
    pause
    exit /b 1
)

for /f "delims=" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo OK: !PYVER!

REM --- Check Node.js (optional, for game task) ---
echo.
echo [2/4] Checking Node.js ^(optional, needed for game task JS syntax check^)...

where node >nul 2>nul
if errorlevel 1 (
    echo WARNING: Node.js not found. The game task JavaScript syntax check
    echo will be skipped. Install from https://nodejs.org to enable this.
) else (
    for /f "delims=" %%v in ('node --version 2^>^&1') do set NODEVER=%%v
    echo OK: !NODEVER!
)

REM --- Check Chrome or Edge (optional, for game task) ---
echo.
echo [3/4] Checking Chrome or Edge ^(optional, needed for game task runtime check^)...

set "BROWSER_FOUND="
for %%p in (
    "C:\Program Files\Google\Chrome\Application\chrome.exe"
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
) do (
    if exist %%p (
        set "BROWSER_FOUND=%%p"
    )
)

if defined BROWSER_FOUND (
    echo OK: !BROWSER_FOUND!
) else (
    echo WARNING: Chrome or Edge not found in standard locations.
    echo The game task headless runtime check will be inconclusive.
    echo Set CHROME_BIN or BROWSER_BIN to a custom browser path to enable it.
)

REM --- Start the app ---
echo.
echo [4/4] Starting HomeBench...
echo.
python homebench.py
pause
