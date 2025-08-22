from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
MUSIXMATCH_API_KEY = os.getenv("MUSIXMATCH_API_KEY", "demo_key")  
DEEZER_API = "https://api.deezer.com"

# In-memory playlists (reset when server restarts)
playlists = {}

# Models
class PlaylistCreate(BaseModel):
    name: str

class PlaylistAddTrack(BaseModel):
    playlist_id: str
    track_id: str
    title: str
    artist: str
    preview: str | None = None
    albumCover: str | None = None


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


# ----------------- Playlist Endpoints -----------------

@app.get("/playlists")
def list_playlists():
    return playlists


@app.post("/playlists")
def create_playlist(pl: PlaylistCreate):
    playlist_id = str(len(playlists) + 1)
    playlists[playlist_id] = {"name": pl.name, "tracks": []}
    return {"id": playlist_id, "name": pl.name}


@app.post("/playlists/add")
def add_to_playlist(item: PlaylistAddTrack):
    if item.playlist_id not in playlists:
        raise HTTPException(status_code=404, detail="Playlist not found")
    track_info = {
        "id": item.track_id,
        "title": item.title,
        "artist": item.artist,
        "preview": item.preview,
        "albumCover": item.albumCover
    }
    playlists[item.playlist_id]["tracks"].append(track_info)
    return {"message": "Track added", "playlist": playlists[item.playlist_id]}
