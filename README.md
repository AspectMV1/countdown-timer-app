# Countdown Timer App

A sleek, lightweight, offline countdown timer desktop application built with Python's standard library (`tkinter`).

Cross-platform: Works on **Windows**, **macOS**, and **Linux**.

## Features
- **Zero external dependencies**: Built entirely using Python's standard library.
- **Cross-Platform**: Full support for Windows, macOS, and Linux with native optimizations (DPI awareness, custom window management).
- **Modern dark UI**: Custom styled countdown display with presets, controls auto-fade, and alert sounds.
- **One-click launch scripts**:
  - **Windows**: Double-click `Start Timer.bat` (runs in background without keeping terminal open).
  - **macOS**: Double-click `start_timer.command` (launches in background via `nohup`).

## Requirements
- Python 3.8+ (standard `tkinter` included).

## Running the App

### Windows
- Double-click **`Start Timer.bat`**, or run:
  ```cmd
  python timer_app.py
  ```

### macOS
- Double-click **`start_timer.command`**, or run:
  ```bash
  python3 timer_app.py
  ```
  *(Note: If opening `.command` for the first time, macOS may ask for permission; you can also run `chmod +x start_timer.command` in terminal).*

### Linux
```bash
python3 timer_app.py
```
