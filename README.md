# Countdown Timer App

A sleek, lightweight, offline countdown timer desktop application built with Python's standard library (`tkinter`).

## Features
- **Zero external dependencies**: Built entirely using Python's standard library.
- **Modern dark UI**: Custom styled countdown display with presets and sound/visual notifications.
- **One-click background launcher**: Includes `Start Timer.bat` to launch windowless via `pythonw.exe` without leaving an open terminal.

## Requirements
- Python 3.8+ (with standard `tkinter` support included on Windows).

## Running the App

### Option 1: Double-click Launcher (Windows)
Double-click `Start Timer.bat`. This automatically detects your Python environment and runs the app in windowless mode (`pythonw`).

### Option 2: Command Line
```bash
python timer_app.py
```
or to run without terminal window:
```bash
pythonw timer_app.py
```
