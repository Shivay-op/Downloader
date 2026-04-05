from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse, RedirectResponse
import yt_dlp
import string, random
from urllib.parse import urlparse
import os

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

# yt_dlp options
def get_ydl_opts(cookies_file=None):
    opts = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': False,
        'format': 'bestvideo+bestaudio/best',
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0 Safari/537.36'
    }
    if cookies_file and os.path.isfile(cookies_file):
        opts['cookiefile'] = cookies_file
    return opts

# MAIN DOWNLOAD API (metadata only)
@app.get("/api/download")
def download(
    url: str,
    request: Request,
    cookies_file: str = Query(default=None)
):
    if not url or not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    try:
        ydl_opts = get_ydl_opts(cookies_file)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            raise HTTPException(status_code=400, detail="Failed to extract info")

        videos = []
        entries = info.get("entries") or [info]

        for entry in entries:
            video_obj = {}
            audio_obj = {}

            for f in entry.get("formats", []):
                if not f.get("url"):
                    continue

                height = f.get("height")
                key = f"{height}p" if height else "audio"

                # Use short link (clients fetch video directly)
                short_id = create_short_link(f.get("url"))
                abs_url = str(request.base_url) + f"d/{short_id}"

                if f.get("vcodec") != "none" and f.get("acodec") != "none":
                    video_obj[key] = {
                        "url": abs_url,
                        "ext": f.get("ext"),
                        "filesize": f.get("filesize") or "unknown"
                    }
                elif f.get("vcodec") == "none" and f.get("acodec") != "none":
                    abr = f.get("abr") or "unknown"
                    audio_obj[f"{abr}kbps"] = {
                        "url": abs_url,
                        "ext": f.get("ext"),
                        "filesize": f.get("filesize") or "unknown"
                    }

            # Thumbnail
            thumbnail_url = entry.get("thumbnail")
            thumb_short = None
            if thumbnail_url:
                thumb_short = str(request.base_url) + f"d/{create_short_link(thumbnail_url)}"

            videos.append({
                "platform": entry.get("extractor_key"),
                "title": entry.get("title"),
                "uploader": entry.get("uploader"),
                "duration": entry.get("duration"),
                "description": entry.get("description"),
                "thumbnail": thumb_short,
                "video": dict(sorted(
                    video_obj.items(),
                    key=lambda x: int(x[0].replace('p','')) if 'p' in x[0] else 0,
                    reverse=True
                )),
                "audio": audio_obj
            })

        return JSONResponse({
            "status": True,
            "developer": "@xdshivay",
            "data": videos
        })

    except Exception as e:
        print("ERROR:", str(e))  # Debug
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch video. Instagram may require cookies or is blocking the request."
        )

# REDIRECT short link (client fetches video directly)
@app.get("/d/{short_id}")
def redirect_link(short_id: str):
    url = short_db.get(short_id)

    if not url:
        raise HTTPException(status_code=404, detail="Invalid link")

    if not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Unsafe URL")

    return RedirectResponse(url)
