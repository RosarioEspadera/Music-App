from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx, os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"

@app.get("/")
async def root():
    return {"message": "Music Backend with DB is running 🎶"}

@app.get("/search")
async def search(q: str):
    if not YOUTUBE_API_KEY:
        raise HTTPException(status_code=500, detail="API key not set")

    params = {
        "part": "snippet",
        "q": q,
        "type": "video",
        "videoCategoryId": "10",
        "maxResults": 5,
        "key": YOUTUBE_API_KEY,
    }

    async with httpx.AsyncClient() as client:
        r = await client.get(YOUTUBE_API_URL, params=params)

    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    items = r.json().get("items", [])
    results = [
        {
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
            "videoId": item["id"]["videoId"],
        }
        for item in items
    ]
    return {"results": results}
