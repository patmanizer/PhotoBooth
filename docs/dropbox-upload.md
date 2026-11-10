# Dropbox uploads

PhotoBooth uploads each completed output photo to Dropbox when an access token
is configured. The local output is still saved as usual.

Create a Dropbox API app in the Dropbox App Console with the `files.content.write`
permission, and generate an access token. To use the default Dropbox path, give
the app **Full Dropbox** access; with **App Folder** access, the configured
path is relative to that app's folder. Keep the token secret. Configure it in
the environment used to launch PhotoBooth:

```sh
export PHOTOBOOTH_DROPBOX_ACCESS_TOKEN="YOUR_DROPBOX_ACCESS_TOKEN"
./start.sh
```

By default, uploads go to `/PhotoBooth/output` in the Dropbox account. Change
`DROPBOX_UPLOAD_PATH` in `src/photo_booth/config.py` to use another Dropbox
folder. Create the destination folder in Dropbox before the first upload.
Existing names are preserved by Dropbox autorename behavior.

If no access token is set, Dropbox uploads are skipped. A Dropbox upload error
is reported as a photo output error; the output file remains saved locally.
