@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON=venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

echo.
echo [autosetup] Using Python: %PYTHON%

if exist "build" (
    echo [autosetup] Removing old build folder...
    rmdir /s /q "build"
)

echo [autosetup] Clearing old extension outputs...
del /q "pieces.pyd" "invert.pyd" "pieces*.pyd" "invert*.pyd" 2>nul

echo [autosetup] Checking pybind11...
"%PYTHON%" -c "import pybind11" >nul 2>nul
if errorlevel 1 (
    echo [autosetup] pybind11 is missing. Installing it...
    "%PYTHON%" -m pip install pybind11
    if errorlevel 1 goto :fail
)

echo [autosetup] Building extensions...
"%PYTHON%" setup.py build_ext --force
if errorlevel 1 goto :fail

call :normalize_output pieces
if errorlevel 1 goto :fail

call :normalize_output invert
if errorlevel 1 goto :fail

echo.
echo [autosetup] Done.
echo [autosetup] Created pieces.pyd and invert.pyd in:
echo [autosetup] %cd%
echo.
pause
exit /b 0

:normalize_output
set "MODULE=%~1"
set "FOUND="
for /r "build" %%F in ("%MODULE%*.pyd") do (
    if exist "%%~fF" (
        copy /y "%%~fF" "%MODULE%.pyd" >nul
        set "FOUND=1"
    )
)

if not defined FOUND (
    echo [autosetup] ERROR: Could not find a built %MODULE% .pyd file.
    exit /b 1
)

echo [autosetup] Wrote %MODULE%.pyd
exit /b 0

:fail
echo.
echo [autosetup] Build failed.
echo.
pause
exit /b 1
