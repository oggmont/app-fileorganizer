#!/bin/sh
# Starts Video File Organizer from Terminal. The first run creates .venv and installs PySide6.
# To start it with a double-click in Finder instead, build the app once with ./make_app.sh.
set -e
cd "$(dirname "$0")"
./scripts/setup_venv.sh
exec .venv/bin/python -m fileorganizer "$@"
