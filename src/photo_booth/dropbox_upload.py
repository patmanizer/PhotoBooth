"""Upload completed output photos to Dropbox using a persistent refresh token."""

import base64
import errno
import json
import ssl
import time
from pathlib import Path
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPSHandler, Request, build_opener

import certifi

from .config import (
    DROPBOX_APP_KEY,
    DROPBOX_APP_SECRET,
    DROPBOX_REFRESH_TOKEN,
    DROPBOX_UPLOAD_PATH,
)
from .logging_utils import log

_DROPBOX_UPLOAD_URL = "https://content.dropboxapi.com/2/files/upload"
_DROPBOX_SHARE_URL = (
    "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings"
)
_DROPBOX_LIST_LINKS_URL = "https://api.dropboxapi.com/2/sharing/list_shared_links"
_DROPBOX_TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"

_REQUEST_TIMEOUT_SECONDS = 120
_CONNECTION_RESET_RETRY_DELAYS_SECONDS = (1, 2)

# The refresh token is long-lived and is read from config.py.
# The short-lived access token is kept in memory and refreshed as needed.
_access_token = ""
_TOKEN_REFRESH_LOCK = Lock()


class _DropboxAPIError(RuntimeError):
    """Dropbox returned an HTTP error response."""

    def __init__(self, status, reason, error, raw_body):
        self.status = status
        self.error = error
        self.raw_body = raw_body

        if isinstance(error, dict):
            detail = error.get("error_summary")
            if not detail and "error" in error:
                detail = json.dumps(error["error"], sort_keys=True)
        else:
            detail = None

        detail = detail or raw_body.strip() or reason
        super().__init__(f"HTTP {status}: {detail}")


def _build_opener():
    """Build an HTTPS opener using the certifi CA bundle."""
    tls_context = ssl.create_default_context()
    tls_context.load_verify_locations(cafile=certifi.where())
    return build_opener(HTTPSHandler(context=tls_context))


def _read_api_response(opener, request, operation):
    """Send a request and decode Dropbox's JSON response."""
    try:
        with opener.open(
                request,
                timeout=_REQUEST_TIMEOUT_SECONDS,
        ) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        try:
            error = json.loads(raw_body)
        except json.JSONDecodeError:
            error = None

        raise _DropboxAPIError(
            exc.code,
            exc.reason,
            error,
            raw_body,
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(
            f"Dropbox {operation} request failed: {exc}"
        ) from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Dropbox returned an invalid {operation} response"
        ) from exc

    if not isinstance(result, dict):
        raise RuntimeError(
            f"Dropbox returned an unexpected {operation} response"
        )
    return result


def _caused_by_connection_reset(error):
    """Return True when an exception chain contains ECONNRESET."""
    seen = set()

    while isinstance(error, BaseException) and id(error) not in seen:
        seen.add(id(error))

        if isinstance(error, HTTPError):
            return False

        if isinstance(error, URLError):
            error = error.reason
            continue

        if isinstance(error, OSError) and error.errno in {
            errno.ECONNRESET,
            104,
        }:
            return True

        error = error.__cause__

    return False



    # Another thread may already have refreshed the token while this request
    # was in flight. Only refresh if the token we used is still current.
    with _TOKEN_REFRESH_LOCK:
        if _access_token == token_used:
            _access_token = _refresh_access_token(opener)
        refreshed_token = _access_token

    request.add_header("Authorization", f"Bearer {refreshed_token}")
    return _read_api_response_with_retry(opener, request, operation)


def _get_existing_shared_link(opener, dropbox_path):
    request = Request(
        _DROPBOX_LIST_LINKS_URL,
        data=json.dumps(
            {"path": dropbox_path, "direct_only": True}
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    result = _read_authenticated_api_response(
        opener,
        request,
        "existing shared-link lookup",
    )

    for link in result.get("links", []):
        link_path = link.get("path_lower", "")
        url = link.get("url")

        if link_path.casefold() == dropbox_path.casefold():
            if isinstance(url, str) and url.startswith("https://"):
                return url

    raise RuntimeError(
        "Dropbox reported an existing shared link but returned no link for "
        f"{dropbox_path}"
    )


def upload_output_photo(photo_path: Path) -> str | None:
    """Upload a photo and return its Dropbox shared URL.

    Returns None when Dropbox credentials have not been configured.
    """
    if not all((DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN)):
        log("Dropbox upload skipped: refresh-token credentials are not configured.")
        return None

    if not DROPBOX_UPLOAD_PATH.startswith("/"):
        raise ValueError(
            "DROPBOX_UPLOAD_PATH in config.py must start with '/'"
        )

    photo_path = Path(photo_path)
    if not photo_path.is_file():
        raise FileNotFoundError(f"Photo to upload does not exist: {photo_path}")

    dropbox_path = (
        f"{DROPBOX_UPLOAD_PATH.rstrip('/')}/{photo_path.name}"
    )

    upload_request = Request(
        _DROPBOX_UPLOAD_URL,
        data=photo_path.read_bytes(),
        headers={
            "Content-Type": "application/octet-stream",
            "Dropbox-API-Arg": json.dumps(
                {
                    "path": dropbox_path,
                    "mode": "overwrite",
                    "autorename": False,
                    "mute": True,
                }
            ),
        },
        method="POST",
    )

    opener = _build_opener()
    result = _read_authenticated_api_response(
        opener,
        upload_request,
        "photo upload",
    )

    if not isinstance(result, dict) or result.get("name") != photo_path.name:
        raise RuntimeError("Dropbox returned an unexpected upload response")

    uploaded_path = result.get("path_lower", dropbox_path)
    log(f"Photo uploaded to Dropbox: {dropbox_path}")

    share_request = Request(
        _DROPBOX_SHARE_URL,
        data=json.dumps({"path": uploaded_path}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        share_result = _read_authenticated_api_response(
            opener,
            share_request,
            "shared-link creation",
        )
    except _DropboxAPIError as exc:
        error_text = (
            json.dumps(exc.error).casefold()
            if exc.error is not None
            else ""
        )

        if "shared_link_already_exists" in error_text:
            return _get_existing_shared_link(opener, uploaded_path)

        raise RuntimeError(
            f"Dropbox shared-link creation failed: {exc}"
        ) from exc

    shared_url = share_result.get("url")
    if not isinstance(shared_url, str) or not shared_url.startswith("https://"):
        raise RuntimeError("Dropbox returned an invalid shared photo URL")

    return shared_url
