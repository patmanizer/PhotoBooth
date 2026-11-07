#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
VENV_ACTIVATE="$PROJECT_DIR/.venv/bin/activate"

if [ ! -f "$VENV_ACTIVATE" ]; then
    printf 'Virtual environment not found: %s\n' "$VENV_ACTIVATE" >&2
    exit 1
fi

. "$VENV_ACTIVATE"
cd "$PROJECT_DIR/src"
exec python -m photo_booth.main
