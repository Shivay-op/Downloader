# Multi-Platform Video Downloader API

A serverless API to get **combined video + audio download links**, **thumbnails**, and **metadata** for multiple platforms including Instagram, YouTube, TikTok, Facebook, and Twitter/X.

This API is built using **FastAPI** and **yt-dlp** and can be deployed on **Vercel** as a serverless function.

---

## Features

- Multi-platform support: Instagram (post, reel, story), YouTube, TikTok, Facebook, Twitter/X
- Returns **video + audio combined** links (no muted videos)
- Returns **thumbnail URL**, title, uploader, and post type
- Supports **multiple quality download links** (1080p, 720p, 480p, etc.)
- Generates **short links** for easy sharing
- Supports **batch processing** via POST requests
- Can run serverless (Vercel) or on a VPS/Docker

---

## API Endpoints

### 1. GET Single URL
# Multi-Platform Video Downloader API

A serverless API to get **combined video + audio download links**, **thumbnails**, and **metadata** for multiple platforms including Instagram, YouTube, TikTok, Facebook, and Twitter/X.

This API is built using **FastAPI** and **yt-dlp** and can be deployed on **Vercel** as a serverless function.

---

## Features

- Multi-platform support: Instagram (post, reel, story), YouTube, TikTok, Facebook, Twitter/X
- Returns **video + audio combined** links (no muted videos)
- Returns **thumbnail URL**, title, uploader, and post type
- Supports **multiple quality download links** (1080p, 720p, 480p, etc.)
- Generates **short links** for easy sharing
- Supports **batch processing** via POST requests
- Can run serverless (Vercel) or on a VPS/Docker

---

## API Endpoints

### 1. GET Single URL
GET /api/download?url=<VIDEO_URL>

**Example:**
GET /api/download?url=<VIDEO_URL>

**Example:**
https://your-project.vercel.app/api/download?url=https://www.instagram.com/reel/ABC123/


**Response:**

```json
{
  "status": "success",
  "title": "Amazing Reel",
  "uploader": "cool_user",
  "thumbnail": "https://instagramcdn.com/path/to/thumbnail.jpg",
  "qualities": {
    "1080p": "/d/AbC123",
    "720p": "/d/XyZ789",
    "480p": "/d/QwE456"
  }
}

Installation (Local / VPS)
Clone the repo:
git clone https://github.com/<your-username>/multi-platform-downloader.git
cd multi-platform-downloader
Install dependencies:
pip install -r requirements.txt
Run locally:
uvicorn api.download:app --host 0.0.0.0 --port 8000 --reload
