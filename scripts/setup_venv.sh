#!/bin/sh
# Creates .venv with Python 3.14 and installs requirements.txt, unless it's already there.
# Used by run.sh and make_app.sh.
set -e
cd "$(dirname "$0")/.."

[ -x .venv/bin/python ] && exit 0

if ! command -v python3.14 >/dev/null 2>&1; then
    echo "Python 3.14 is needed (PySide6 doesn't support 3.15 yet): brew install python@3.14" >&2
    exit 1
fi
echo "Creating .venv and installing PySide6 (about 1 minute)…"
python3.14 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
