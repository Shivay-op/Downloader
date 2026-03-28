from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
import yt_dlp
import string, random

app = FastAPI()

# In‑memory short links store (resets on cold starts)
short_db = {}

def generate_short_id(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_short_link(long_url):
    short_id = generate_short_id()
    short_db[short_id] = long_url
    return short_id

# YT‑DLP options (best video+audio)
ydl_opts = {
    'quiet': True,
    'skip_download': True,
    'noplaylist': True,
    'format': 'bestvideo+bestaudio/best'
}

@app.get("/api/download")
def download(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        thumbnail = info.get("thumbnail")
        title = info.get("title")
        uploader = info.get("uploader")

        # Get combined formats (video+audio)
        qualities = {}
        for f in info.get("formats", []):
            if f.get("acodec") != "none" and f.get("vcodec") != "none":
                height = f.get("height") or 0
                key = f"{height}p" if height else "best"
                qualities[key] = f.get("url")

        # Create short links
        short_links = {q: f"/d/{create_short_link(link)}" for q, link in qualities.items()}

        return JSONResponse({
            "status": "success",
            "title": title,
            "uploader": uploader,
            "thumbnail": thumbnail,
            "qualities": short_links
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/d/{short_id}")
def redirect_link(short_id: str):
    url = short_db.get(short_id)
    if not url:
        raise HTTPException(status_code=404, detail="Invalid link")
    return RedirectResponse(url)
