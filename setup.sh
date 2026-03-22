#!/usr/bin/env bash
set -e

echo "PDF Toolkit — First-time setup"
echo "================================"
echo

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 was not found."
    echo
    echo "Install it with your package manager, for example:"
    echo "  Ubuntu/Debian:  sudo apt install python3 python3-venv python3-tk"
    echo "  Fedora:         sudo dnf install python3 python3-tkinter"
    echo "  macOS:          brew install python-tk"
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv .venv

echo "Installing dependencies..."
.venv/bin/pip install --quiet -r requirements.txt

chmod +x run.sh

echo
echo "============================================"
echo " Setup complete!  Run:  ./run.sh"
echo "============================================"
echo
