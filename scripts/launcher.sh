# Body of the launcher inside "Video File Organizer.app" (Contents/MacOS/launcher).
# make_app.sh adds "#!/bin/sh" and the PROJECT=... line above this. Don't run this file directly.

LOG="$HOME/Library/Logs/Video File Organizer.log"
VENV_PY="$PROJECT/.venv/bin/python"
HERE="$(cd "$(dirname "$0")" && pwd)"
BUNDLED_PY="$HERE/Video File Organizer"

fail() {
    osascript -e "display alert \"Video File Organizer can't start\" message \"$1\" as critical" >/dev/null 2>&1
    exit 1
}

[ -d "$PROJECT/fileorganizer" ] ||
    fail "The project isn't at $PROJECT anymore. Open Terminal in its new folder and run ./make_app.sh again."
[ -x "$VENV_PY" ] ||
    fail "The Python environment is missing. Open Terminal in $PROJECT and run ./run.sh once."

cd "$PROJECT"
echo "=== $(date '+%Y-%m-%d %H:%M:%S') starting" >>"$LOG"

# Run Python's real interpreter from inside this bundle, so macOS shows this app's name and
# icon in the Dock and menu bar instead of "Python". The copy is refreshed whenever Homebrew
# updates Python. __PYVENV_LAUNCHER__ tells it to use the project's .venv.
BASE="$("$VENV_PY" -c 'import sys; print(sys.base_prefix)' 2>>"$LOG")"
REAL_PY="$BASE/Resources/Python.app/Contents/MacOS/Python"
if [ -x "$REAL_PY" ]; then
    cmp -s "$REAL_PY" "$BUNDLED_PY" || cp "$REAL_PY" "$BUNDLED_PY"
    export __PYVENV_LAUNCHER__="$VENV_PY"
    exec "$BUNDLED_PY" -m fileorganizer >>"$LOG" 2>&1
fi

# Python isn't a macOS framework build: the app still works, but the Dock shows "Python".
exec "$VENV_PY" -m fileorganizer >>"$LOG" 2>&1
