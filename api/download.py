from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
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
    }
    if cookies_file and os.path.isfile(cookies_file):
        opts['cookiefile'] = cookies_file
    return opts

# Optional: Get filesize from headers if not available
import requests
def get_filesize_from_url(url):
    try:
        r = requests.head(url, allow_redirects=True, timeout=5)
        size = r.headers.get("Content-Length")
        return int(size) if size else None
    except:
        return None

@app.get("/api/download")
def download(
    url: str,
    request: Request,
    cookies_file: str = Query(default=None, description="Optional path to cookies.txt for authenticated downloads")
):
    if not url or not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    try:
        ydl_opts = get_ydl_opts(cookies_file)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        videos = []

        entries = info.get("entries") or [info]

        for entry in entries:
            video_obj = {}
            audio_obj = {}

            for f in entry.get("formats", []):
                height = f.get("height")
                key = f"{height}p" if height else "audio_only"
                abs_url = str(request.base_url) + f"d/{create_short_link(f.get('url'))}"

                # Get filesize: yt_dlp filesize or approximate or HTTP HEAD fallback
                filesize = f.get("filesize") or f.get("filesize_approx") or None
                # Optional: uncomment next line for live HEAD check (slower)
                # if filesize is None: filesize = get_filesize_from_url(f.get("url"))

                if f.get("vcodec") != "none" and f.get("acodec") != "none":
                    video_obj[key] = {
                        "url": abs_url,
                        "extension": f.get("ext"),
                        "filesize": filesize
                    }
                elif f.get("vcodec") == "none" and f.get("acodec") != "none":
                    audio_obj[key] = {
                        "url": abs_url,
                        "extension": f.get("ext"),
                        "filesize": filesize
                    }

            # Thumbnail short link
            thumbnail_url = entry.get("thumbnail")
            if thumbnail_url:
                thumb_short = str(request.base_url) + f"d/{create_short_link(thumbnail_url)}"
                thumbnail_info = {"url": thumb_short}
            else:
                thumbnail_info = {"url": None}

            # Width/height
            if entry.get("thumbnails"):
                thumb = entry.get("thumbnails")[-1]
                thumbnail_info["width"] = thumb.get("width")
                thumbnail_info["height"] = thumb.get("height")

            # Sort video qualities descending (highest p first)
            video_sorted = dict(sorted(
                video_obj.items(),
                key=lambda x: int(x[0].replace('p','')) if x[0]!='audio_only' else 0,
                reverse=True
            ))

            videos.append({
                "platform": entry.get("extractor_key"),
                "title": entry.get("title"),
                "uploader": entry.get("uploader"),
                "thumbnail": thumbnail_info,
                "duration": entry.get("duration"),
                "description": entry.get("description"),
                "video": video_sorted,
                "audio": audio_obj
            })

        return JSONResponse({
            "status": "success",
            "Credit": "@xdshivay",
            "videos": videos
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
