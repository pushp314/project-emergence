#!/bin/bash
# A2A Sandbox Native Desktop Launcher
# Change to correct directory (force absolute path for launchd)
DIR="/Users/pushp/Desktop/A2A/ai-sandbox"
cd "$DIR" || exit 1

# Check if venv exists, create it if it doesn't
if [ ! -d "venv" ]; then
    echo "[System] Virtual environment not found. Creating 'venv'..."
    python3 -m venv venv
    echo "[System] Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate || true
fi

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "[System] Loading .env file..."
    set -a
    source .env
    set +a
fi

export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "==================================="
echo " Jarvis Voice Agent Starting... "
echo "==================================="

# Run the app directly in the foreground so macOS allows the window to appear
venv/bin/python3 -m app.desktop.app
