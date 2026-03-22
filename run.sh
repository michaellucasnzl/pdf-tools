#!/usr/bin/env bash
# Run PDF Toolkit — pass any arguments straight through to the app.
# With no arguments, opens a file picker dialog (requires python3-tk).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    echo "Virtual environment not found — running setup..."
    bash "$SCRIPT_DIR/setup.sh"
fi

"$SCRIPT_DIR/.venv/bin/python" -m pdf_toolkit "$@"
