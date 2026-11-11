"""Timestamped application log output."""

from datetime import datetime
from pathlib import Path
from threading import Lock

_LOG_DIRECTORY = Path(__file__).resolve().parents[2] / "logs"
_LOG_LOCK = Lock()


def log(message: str):
    """Write each timestamped line to the daily log file and console."""

    now = datetime.now().astimezone()
    timestamp = now.isoformat(timespec="milliseconds")
    entries = [
        f"[{timestamp}] {line}"
        for line in str(message).splitlines() or [""]
    ]
    log_path = _LOG_DIRECTORY / f"photobooth_{now:%Y-%m-%d}.log"

    with _LOG_LOCK:
        _LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write("\n".join(entries) + "\n")
            log_file.flush()
        for entry in entries:
            print(entry)
