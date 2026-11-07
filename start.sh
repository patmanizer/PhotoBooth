#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
VENV_ACTIVATE="$PROJECT_DIR/.venv/bin/activate"

if [ ! -f "$VENV_ACTIVATE" ]; then
    printf 'Virtual environment not found: %s\n' "$VENV_ACTIVATE" >&2
    exit 1
fi

if ! command -v pkill >/dev/null 2>&1 || ! command -v pgrep >/dev/null 2>&1; then
    printf 'pkill and pgrep are required to release the camera before startup.\n' >&2
    exit 1
fi

USER_ID=$(id -u)
if pkill -TERM -u "$USER_ID" -x gvfsd-gphoto2; then
    printf 'Stopped gvfsd-gphoto2 to release the camera.\n'
    attempts=0
    while pgrep -u "$USER_ID" -x gvfsd-gphoto2 >/dev/null 2>&1; do
        if [ "$attempts" -ge 5 ]; then
            printf 'gvfsd-gphoto2 is still running; cannot safely start PhotoBooth.\n' >&2
            exit 1
        fi
        sleep 1
        attempts=$((attempts + 1))
    done
else
    status=$?
    if [ "$status" -ne 1 ]; then
        printf 'Could not stop gvfsd-gphoto2 (exit status %s).\n' "$status" >&2
        exit "$status"
    fi
fi

. "$VENV_ACTIVATE"
cd "$PROJECT_DIR/src"
exec python -m photo_booth.main
