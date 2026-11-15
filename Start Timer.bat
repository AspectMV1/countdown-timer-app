@echo off
setlocal
set "TIMER_SCRIPT=%~dp0timer_app.py"

if exist "%~dp0pythonw.exe" (
    start "" "%~dp0pythonw.exe" "%TIMER_SCRIPT%"
    exit /b
)

where pythonw.exe >nul 2>nul
if not errorlevel 1 (
    start "" pythonw.exe "%TIMER_SCRIPT%"
    exit /b
)

where pyw.exe >nul 2>nul
if not errorlevel 1 (
    start "" pyw.exe "%TIMER_SCRIPT%"
    exit /b
)

python "%TIMER_SCRIPT%"
