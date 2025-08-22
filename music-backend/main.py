from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

# CORS – allow frontend (local + deployed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment vars (you can also set these in Render)
MUSIXMATCH_API_KEY = os.getenv("MUSIXMATCH_API_KEY", "demo_key")  # replace later with your real key
DEEZER_API = "https://api.deezer.com"

# Root
@app.get("/")
def root():
    return {"message": "Music Backend is running 🎶"}


# Search songs (Deezer API)
@app.get("/search")
def search_songs(q: str = Query(..., min_length=2)):
    try:
        res = requests.get(f"{DEEZER_API}/search", params={"q": q})
        data = res.json()
        tracks = []
        for item in data.get("data", []):
            tracks.append({
                "id": item["id"],
                "title": item["title"],
                "artist": item["artist"]["name"],
                "preview": item.get("preview"),
                "albumCover": item["album"]["cover_medium"]
            })
        return tracks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get lyrics (Musixmatch API)
@app.get("/lyrics")
def get_lyrics(artist: str, track: str):
    try:
        url = "https://api.musixmatch.com/ws/1.1/matcher.lyrics.get"
        params = {
            "q_artist": artist,
            "q_track": track,
            "apikey": MUSIXMATCH_API_KEY
        }
        res = requests.get(url, params=params)
        data = res.json()

        message = data.get("message", {}).get("body", {}).get("lyrics")
        if not message:
            return {"lyrics": "Lyrics not found."}

        return {"lyrics": message["lyrics_body"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
