#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR/app"
LOG_DIR="$APP_DIR/logs"
UV="/home/user_1/.local/bin/uv"
mkdir -p "$LOG_DIR"

cd "$APP_DIR"

if [ -x "$UV" ]; then
    "$UV" run python main.py "$@" 2>>"$LOG_DIR/erro.log"
else
    python3 main.py "$@" 2>>"$LOG_DIR/erro.log"
fi
