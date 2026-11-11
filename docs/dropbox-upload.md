# Dropbox uploads

PhotoBooth uploads each completed output photo to Dropbox when an access token
is configured. The local output is still saved as usual.

Create a Dropbox API app in the Dropbox App Console with the
`files.content.write` and `sharing.write` permissions, and generate an access
token. To use the default Dropbox path, give the app **Full Dropbox** access;
with **App Folder** access, the configured path is relative to that app's
folder. Keep the token secret. For automatic access-token refresh, authorize
the app using Dropbox's OAuth flow with offline access enabled
(`token_access_type=offline`) and keep the returned refresh token, app key,
and app secret. Copy `.env.example` to `.env` in the project root and fill in
all four credentials. `start.sh` sources `.env` automatically; `.env` is
ignored by Git:

```sh
cp .env.example .env
# Edit .env and enter the Dropbox credentials
./start.sh
```

When Dropbox rejects an expired access token, PhotoBooth exchanges the refresh
token for a new access token and retries the API request once. The replacement
access token is kept in memory; the refresh token remains the long-lived
credential. If the refresh token or app credentials are not configured, the
upload reports that automatic refresh is unavailable.

Dropbox requests that fail with a connection reset (`Errno 104`) are retried
twice with short delays. Retries target the same timestamped filename to avoid
creating duplicate files if Dropbox received an upload before the connection
was interrupted.

By default, uploads go to `/PhotoBooth/output` in the Dropbox account. Change
`DROPBOX_UPLOAD_PATH` in `src/photo_booth/config.py` to use another Dropbox
folder. Create the destination folder in Dropbox before the first upload.
Existing names are preserved by Dropbox autorename behavior.

After upload, PhotoBooth creates a shared link and displays the saved photo
beside a QR code for that link. The display lasts 5 seconds by default; change
`DROPBOX_QR_DISPLAY_SECONDS` in `src/photo_booth/config.py` to adjust the
duration. Anyone who scans the QR can access the shared link according to its
Dropbox sharing settings.

If no access token is set, Dropbox uploads are skipped. A Dropbox upload error
is reported as a photo output error; the output file remains saved locally.
