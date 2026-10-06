# Cutout Studio — Streamlit

Upload a JPG, PNG or WebP, remove its background, preview the result, and download a transparent PNG at the original resolution. No API key is required.

## Run

Use Python 3.11 or 3.12. From this directory:

```sh
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The first removal downloads the U2NETP model into `.models/`. Internet access is needed for that download. Subsequent processing uses the cached model. Uploaded images and cutouts are held in session memory rather than written to disk. If hosted remotely, image processing happens on that server.

For Streamlit Community Cloud, point the deployment at `app.py` with this `requirements.txt` alongside it. Allow outbound access to GitHub for the first model download.
