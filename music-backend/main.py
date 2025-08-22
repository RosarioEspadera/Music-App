from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Allow CORS (so frontend can fetch)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

YOUTUBE_API_KEY = "AIzaSyATYkPNJbUpy6UbflmaFjXLyG6LQ_aqaw4"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

@app.get("/")
def root():
    return {"message": "Music Backend with YouTube Search is running 🎶"}

@app.get("/search")
def search_tracks(q: str = Query(..., description="Search query")):
    try:
        params = {
            "part": "snippet",
            "q": q,
            "type": "video",
            "videoCategoryId": "10",  # Music category
            "maxResults": 10,
            "key": YOUTUBE_API_KEY,
        }
        r = requests.get(YOUTUBE_SEARCH_URL, params=params)
        r.raise_for_status()
        data = r.json()

        results = []
        for item in data.get("items", []):
            results.append({
                "videoId": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
            })

        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
