@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

python gui.py

if errorlevel 1 (
    echo.
    echo GUI exited with an error.
    pause
)
