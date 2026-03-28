from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
import yt_dlp
import string, random
from urllib.parse import urlparse

app = FastAPI()

# In-memory short link store
short_db = {}

# Generate unique short ID
def generate_short_id(length=6):
    while True:
        short_id = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        if short_id not in short_db:
            return short_id

# Create short link
def create_short_link(long_url):
    short_id = generate_short_id()
    short_db[short_id] = long_url
    return short_id

# URL validation
def is_valid_url(url: str):
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and parsed.netloc

# YT-DLP options
ydl_opts = {
    'quiet': True,
    'skip_download': True,
    'noplaylist': True,
    'format': 'bestvideo+bestaudio/best'
}

@app.get("/api/download")
def download(url: str):
    if not url or not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Video metadata
        video_data = {
            "platform": info.get("extractor_key"),
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "description": info.get("description"),
            "qualities": {}
        }

        # Build qualities dictionary
        for f in info.get("formats", []):
            # Only include streams with both video+audio or audio-only
            if (f.get("vcodec") != "none" and f.get("acodec") != "none") or (f.get("vcodec") == "none" and f.get("acodec") != "none"):
                height = f.get("height")
                if height:
                    key = f"{height}p"
                else:
                    key = "audio_only"
                video_data["qualities"][key] = {
                    "url": f"/d/{create_short_link(f.get('url'))}",
                    "extension": f.get("ext"),
                    "filesize": f.get("filesize")
                }

        return JSONResponse({
            "status": "success",
            "Credit":"@xdshivay",
            "videos": [video_data]
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/d/{short_id}")
def redirect_link(short_id: str):
    url = short_db.get(short_id)
    if not url:
        raise HTTPException(status_code=404, detail="Invalid link")
    if not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Unsafe URL")
    return RedirectResponse(url)
