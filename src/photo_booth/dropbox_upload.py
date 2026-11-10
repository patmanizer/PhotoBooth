"""Upload completed output photos to Dropbox when configured."""

import json
import ssl
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, Request, build_opener

import certifi

from .config import DROPBOX_ACCESS_TOKEN, DROPBOX_UPLOAD_PATH
from .logging_utils import log

_DROPBOX_UPLOAD_URL = "https://content.dropboxapi.com/2/files/upload"
_REQUEST_TIMEOUT_SECONDS = 120


def _build_opener():
    tls_context = ssl.create_default_context()
    tls_context.load_verify_locations(cafile=certifi.where())
    return build_opener(HTTPSHandler(context=tls_context))


def upload_output_photo(photo_path: Path):
    """Upload a completed photo if a Dropbox access token is configured."""

    if not DROPBOX_ACCESS_TOKEN:
        return
    if not DROPBOX_UPLOAD_PATH.startswith("/"):
        raise ValueError("DROPBOX_UPLOAD_PATH in config.py must start with '/'")

    photo_path = Path(photo_path)
    dropbox_path = f"{DROPBOX_UPLOAD_PATH.rstrip('/')}/{photo_path.name}"
    request = Request(
        _DROPBOX_UPLOAD_URL,
        data=photo_path.read_bytes(),
        headers={
            "Authorization": f"Bearer {DROPBOX_ACCESS_TOKEN}",
            "Content-Type": "application/octet-stream",
            "Dropbox-API-Arg": json.dumps(
                {
                    "path": dropbox_path,
                    "mode": "add",
                    "autorename": True,
                    "mute": True,
                }
            ),
        },
        method="POST",
    )

    try:
        with _build_opener().open(
            request,
            timeout=_REQUEST_TIMEOUT_SECONDS,
        ) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            error = json.loads(exc.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            error = {}
        detail = error.get("error_summary", exc.reason)
        raise RuntimeError(
            f"Dropbox photo upload failed with HTTP {exc.code}: {detail}"
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Dropbox photo upload request failed: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Dropbox returned an invalid upload response") from exc

    if not isinstance(result, dict) or result.get("name") != photo_path.name:
        raise RuntimeError("Dropbox returned an unexpected upload response")
    log(f"Photo uploaded to Dropbox: {dropbox_path}")
