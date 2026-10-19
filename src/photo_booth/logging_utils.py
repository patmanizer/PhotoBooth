"""Timestamped application log output."""

from datetime import datetime


def log(message: str):
    """Print each log line with a local timestamp."""

    timestamp = datetime.now().astimezone().isoformat(timespec="milliseconds")
    for line in str(message).splitlines() or [""]:
        print(f"[{timestamp}] {line}")
