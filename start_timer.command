#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if command -v python3 >/dev/null 2>&1; then
    nohup python3 "$DIR/timer_app.py" >/dev/null 2>&1 &
elif command -v python >/dev/null 2>&1; then
    nohup python "$DIR/timer_app.py" >/dev/null 2>&1 &
else
    echo "Python 3 is required to run Countdown Timer."
    read -p "Press Enter to exit..."
fi
