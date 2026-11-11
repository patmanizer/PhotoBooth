# Dropbox uploads

PhotoBooth uploads each completed output photo to Dropbox when a fresh
authorization code is configured. The local output is still saved as usual.

Create a Dropbox API app in the Dropbox App Console with the
`files.content.write` and `sharing.write` permissions. To use the default
Dropbox path, give the app **Full Dropbox** access; with **App Folder** access,
the configured path is relative to that app's folder.

Copy `.env.example` to `.env` in the project root and set the app key and app
secret. `start.sh` sources `.env` automatically; `.env` is ignored by Git.
Before each PhotoBooth start, authorize the app in a browser with offline
access (`token_access_type=offline`) and copy the returned authorization code
into `PHOTOBOOTH_DROPBOX_AUTHORIZATION_CODE`. The code is single-use and
short-lived, so replace it with a new code before each restart. If the
authorization used a redirect URI, set the exact same URI in
`PHOTOBOOTH_DROPBOX_REDIRECT_URI`; otherwise leave that variable blank.

An authorization URL can be constructed with the app key:

```sh
cp .env.example .env
```

```text
https://www.dropbox.com/oauth2/authorize?client_id=YOUR_APP_KEY&response_type=code&token_access_type=offline&scope=files.content.write%20sharing.write
```

If Dropbox redirects to a registered URI, copy the `code` query parameter
from the resulting URL. Do not share or commit the authorization code.

PhotoBooth exchanges the authorization code for an access token and refresh
token in memory. It never writes either token to disk. When an access token
expires during the current run, PhotoBooth uses the in-memory refresh token to
get another one. Dropbox does not rotate refresh tokens on refresh. Because
tokens are not persisted, a fresh authorization code is required after each
application restart.

Dropbox requests that fail with a connection reset (`Errno 104`) are retried
twice with short delays. Retries target the same timestamped filename to avoid
creating duplicate files if Dropbox received an upload before the connection
was interrupted.

By default, uploads go to `/PhotoBooth/output` in the Dropbox account. Change
`DROPBOX_UPLOAD_PATH` in `src/photo_booth/config.py` to use another Dropbox
folder. Create the destination folder in Dropbox before the first upload.
Existing names are preserved by Dropbox autorename behavior.

After upload, PhotoBooth creates a shared link and displays the saved photo
beside a QR code for that link. The display lasts 12 seconds by default; change
`DROPBOX_QR_DISPLAY_SECONDS` in `src/photo_booth/config.py` to adjust the
duration. Anyone who scans the QR can access the shared link according to its
Dropbox sharing settings.

If no authorization code is set, Dropbox uploads are skipped. A Dropbox
upload error is reported as a photo output error; the output file remains
saved locally.
