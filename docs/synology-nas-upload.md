# Synology NAS uploads

PhotoBooth can upload each completed output photo to a Synology NAS using the
DSM File Station REST API. Uploads are disabled by default.

Set these values in `src/photo_booth/config.py`:

```python
NAS_UPLOAD_ENABLED = True
NAS_URL = "https://nas.example.com:5001"
NAS_USERNAME = "photobooth"
NAS_PASSWORD = "your-account-password"
NAS_UPLOAD_PATH = "/photo/PhotoBooth"
```

`NAS_URL` is the DSM base URL, without a trailing `/webapi` path.
`NAS_UPLOAD_PATH` is the destination directory as it appears in File Station,
beginning with `/`. The API creates missing destination directories and does
not overwrite existing files. Use an account with access only to the required
destination folder. Keep real credentials out of tracked files and logs;
HTTPS is recommended.

When enabled, PhotoBooth logs in to DSM, uploads each completed output photo,
and logs out. The original output remains saved locally. An upload/API error is
reported as a photo output error.
