from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (you can restrict to your frontend domain)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

YOUTUBE_API_KEY = os.getenv("AIzaSyCEqR37yESpaMPezhwGHL-7A6KKJKlN7mE", "AIzaSyATYkPNJbUpy6UbflmaFjXLyG6LQ_aqaw4")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

@app.get("/")
def root():
    return {"message": "Music Backend with DB is running 🎶"}

@app.get("/search")
async def search(q: str = Query(..., min_length=1)):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                YOUTUBE_SEARCH_URL,
                params={
                    "part": "snippet",
                    "q": q,
                    "type": "video",
                    "videoCategoryId": "10",  # Music
                    "maxResults": 10,
                    "key": YOUTUBE_API_KEY,
                },
            )
            res.raise_for_status()
            data = res.json()

        results = []
        for item in data.get("items", []):
            results.append({
                "videoId": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
            })

        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
