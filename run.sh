#!/bin/sh
# Starts Video File Organizer. The first run creates .venv and installs PySide6.
set -e
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
    if ! command -v python3.14 >/dev/null 2>&1; then
        echo "Python 3.14 is needed (PySide6 doesn't support 3.15 yet): brew install python@3.14" >&2
        exit 1
    fi
    echo "First run: creating .venv and installing PySide6…"
    python3.14 -m venv .venv
    .venv/bin/pip install --quiet --upgrade pip
    .venv/bin/pip install --quiet -r requirements.txt
fi

exec .venv/bin/python -m fileorganizer "$@"
