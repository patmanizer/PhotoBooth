"""Upload completed photos to Synology DSM File Station."""

import json
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener

from .config import (
    NAS_PASSWORD,
    NAS_UPLOAD_ENABLED,
    NAS_UPLOAD_PATH,
    NAS_URL,
    NAS_USERNAME,
)
from .logging_utils import log

_REQUEST_TIMEOUT_SECONDS = 120


def _read_api_response(opener, request):
    try:
        with opener.open(request, timeout=_REQUEST_TIMEOUT_SECONDS) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Synology API request failed: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Synology API returned an invalid JSON response") from exc

    if not result.get("success"):
        error = result.get("error", {})
        code = error.get("code", "unknown")
        raise RuntimeError(f"Synology API request failed with error code {code}")
    return result.get("data", {})


def _multipart_upload_body(sid, upload_path, photo_path):
    boundary = "----PhotoBoothSynologyUploadBoundary"
    fields = {
        "api": "SYNO.FileStation.Upload",
        "version": "2",
        "method": "upload",
        "path": upload_path,
        "create_parents": "true",
        "overwrite": "false",
        "_sid": sid,
    }
    body = bytearray()
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("ascii"))
        body.extend(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(
                "ascii"
            )
        )
        body.extend(value.encode("utf-8"))
        body.extend(b"\r\n")

    filename = photo_path.name
    if "\r" in filename or "\n" in filename:
        raise ValueError("Photo filename cannot contain newline characters")
    escaped_filename = filename.replace("\\", "\\\\").replace('"', '\\"')
    body.extend(f"--{boundary}\r\n".encode("ascii"))
    body.extend(
        (
            'Content-Disposition: form-data; name="file"; '
            f'filename="{escaped_filename}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8")
    )
    body.extend(photo_path.read_bytes())
    body.extend(f"\r\n--{boundary}--\r\n".encode("ascii"))
    return boundary, bytes(body)


def upload_output_photo(photo_path: Path):
    """Upload one completed output photo when NAS uploads are enabled."""

    if not NAS_UPLOAD_ENABLED:
        return
    if not all((NAS_URL, NAS_USERNAME, NAS_PASSWORD, NAS_UPLOAD_PATH)):
        raise RuntimeError(
            "NAS uploads are enabled but NAS_URL, NAS_USERNAME, "
            "NAS_PASSWORD, and NAS_UPLOAD_PATH in config.py must all be set"
        )

    parsed_url = urlsplit(NAS_URL)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("NAS_URL in config.py must be an HTTP(S) URL")
    if parsed_url.query or parsed_url.fragment:
        raise ValueError("NAS_URL in config.py cannot include a query or fragment")
    if not NAS_UPLOAD_PATH.startswith("/"):
        raise ValueError("NAS_UPLOAD_PATH in config.py must start with '/'")

    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    auth_endpoint = f"{NAS_URL}/webapi/auth.cgi"
    entry_endpoint = f"{NAS_URL}/webapi/entry.cgi"
    sid = None

    try:
        login_request = Request(
            auth_endpoint,
            data=urlencode(
                {
                    "api": "SYNO.API.Auth",
                    "version": "6",
                    "method": "login",
                    "account": NAS_USERNAME,
                    "passwd": NAS_PASSWORD,
                    "session": "FileStation",
                    "format": "sid",
                }
            ).encode("utf-8"),
        )
        login_data = _read_api_response(opener, login_request)
        sid = login_data.get("sid")
        if not sid:
            raise RuntimeError("Synology login succeeded without returning a SID")

        boundary, body = _multipart_upload_body(
            sid,
            NAS_UPLOAD_PATH,
            Path(photo_path),
        )
        upload_request = Request(
            entry_endpoint,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        _read_api_response(opener, upload_request)
        log(f"Photo uploaded to Synology: {Path(photo_path).name}")
    finally:
        if sid:
            try:
                logout_request = Request(
                    auth_endpoint,
                    data=urlencode(
                        {
                            "api": "SYNO.API.Auth",
                            "version": "6",
                            "method": "logout",
                            "session": "FileStation",
                            "_sid": sid,
                        }
                    ).encode("utf-8"),
                )
                _read_api_response(opener, logout_request)
            except Exception as exc:
                log(f"Synology logout warning: {exc}")
