from fastapi import FastAPI, HTTPException, Request
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

# yt_dlp options
ydl_opts = {
    'quiet': True,
    'skip_download': True,
    'noplaylist': False,
    'format': 'bestvideo+bestaudio/best'
}

@app.get("/api/download")
def download(url: str, request: Request):
    if not url or not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        videos = []

        # Handle playlists or single videos
        entries = info.get("entries") or [info]

        for entry in entries:
            video_obj = {}
            audio_obj = {}

            for f in entry.get("formats", []):
                height = f.get("height")
                key = f"{height}p" if height else "audio_only"
                abs_url = str(request.base_url) + f"d/{create_short_link(f.get('url'))}"

                if f.get("vcodec") != "none" and f.get("acodec") != "none":
                    video_obj[key] = {
                        "url": abs_url,
                        "extension": f.get("ext"),
                        "filesize": f.get("filesize")
                    }
                elif f.get("vcodec") == "none" and f.get("acodec") != "none":
                    audio_obj[key] = {
                        "url": abs_url,
                        "extension": f.get("ext"),
                        "filesize": f.get("filesize")
                    }

            # Thumbnail width/height (if available)
            thumbnail_info = {
                "url": entry.get("thumbnail")
            }
            # yt_dlp sometimes has "thumbnails" list with width/height
            if entry.get("thumbnails"):
                thumb = entry.get("thumbnails")[-1]  # highest quality thumbnail
                thumbnail_info["width"] = thumb.get("width")
                thumbnail_info["height"] = thumb.get("height")

            videos.append({
                "platform": entry.get("extractor_key"),
                "title": entry.get("title"),
                "uploader": entry.get("uploader"),
                "thumbnail": thumbnail_info,
                "duration": entry.get("duration"),
                "description": entry.get("description"),
                "video": dict(sorted(video_obj.items(), key=lambda x: int(x[0].replace('p','')) if x[0]!='audio_only' else 0, reverse=True)),
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
