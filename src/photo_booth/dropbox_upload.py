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
_DROPBOX_SHARE_URL = (
    "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings"
)
_REQUEST_TIMEOUT_SECONDS = 120


def _build_opener():
    tls_context = ssl.create_default_context()
    tls_context.load_verify_locations(cafile=certifi.where())
    return build_opener(HTTPSHandler(context=tls_context))


def _read_api_response(opener, request, operation):
    try:
        with opener.open(
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
            f"Dropbox {operation} failed with HTTP {exc.code}: {detail}"
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Dropbox {operation} request failed: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Dropbox returned an invalid {operation} response"
        ) from exc

    if not isinstance(result, dict):
        raise RuntimeError(f"Dropbox returned an unexpected {operation} response")
    return result


def upload_output_photo(photo_path: Path) -> str | None:
    """Upload a photo and return its Dropbox shared URL, if configured."""

    if not DROPBOX_ACCESS_TOKEN:
        return
    if not DROPBOX_UPLOAD_PATH.startswith("/"):
        raise ValueError("DROPBOX_UPLOAD_PATH in config.py must start with '/'")

    photo_path = Path(photo_path)
    dropbox_path = f"{DROPBOX_UPLOAD_PATH.rstrip('/')}/{photo_path.name}"
    upload_request = Request(
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
    opener = _build_opener()
    result = _read_api_response(opener, upload_request, "photo upload")

    if not isinstance(result, dict) or result.get("name") != photo_path.name:
        raise RuntimeError("Dropbox returned an unexpected upload response")
    log(f"Photo uploaded to Dropbox: {dropbox_path}")

    share_request = Request(
        _DROPBOX_SHARE_URL,
        data=json.dumps({"path": result.get("path_lower", dropbox_path)}).encode(
            "utf-8"
        ),
        headers={
            "Authorization": f"Bearer {DROPBOX_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    share_result = _read_api_response(opener, share_request, "shared-link creation")
    shared_url = share_result.get("url")
    if not isinstance(shared_url, str) or not shared_url.startswith("https://"):
        raise RuntimeError("Dropbox returned an invalid shared photo URL")
    return shared_url
