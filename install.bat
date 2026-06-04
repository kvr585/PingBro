@echo off
title PingBro Installer
echo Launching Setup Wizard...
python setup.py
if %errorlevel% neq 0 (
    echo.
    echo Python was not found in your PATH. Trying to run via local virtualenv...
    .venv\Scripts\python.exe setup.py
)
if %errorlevel% neq 0 (
    echo.
    echo Failed to start Setup Wizard. Please double-click 'setup.py' directly.
    pause
)
