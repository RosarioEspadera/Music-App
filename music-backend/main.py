from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# --------------------------------------------------
# FastAPI App + CORS
# --------------------------------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Database Config (SQLite locally / PostgreSQL in Render)
# --------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./music.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --------------------------------------------------
# Database Models
# --------------------------------------------------
class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    tracks = relationship("Track", back_populates="playlist", cascade="all, delete")

class Track(Base):
    __tablename__ = "tracks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    artist = Column(String)
    preview = Column(String, nullable=True)
    albumCover = Column(String, nullable=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"))
    playlist = relationship("Playlist", back_populates="tracks")

Base.metadata.create_all(bind=engine)

# --------------------------------------------------
# Pydantic Models
# --------------------------------------------------
class PlaylistCreate(BaseModel):
    name: str

class PlaylistAddTrack(BaseModel):
    playlist_id: int
    title: str
    artist: str
    preview: str | None = None
    albumCover: str | None = None

# --------------------------------------------------
# External APIs
# --------------------------------------------------
MUSIXMATCH_API_KEY = os.getenv("MUSIXMATCH_API_KEY", "demo_key")
DEEZER_API = "https://api.deezer.com"

# --------------------------------------------------
# Routes
# --------------------------------------------------
@app.get("/")
def root():
    return {"message": "Music Backend with DB is running 🎶"}

# Search Deezer
@app.get("/search")
def search_songs(q: str = Query(..., min_length=2)):
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

# Lyrics via Musixmatch
@app.get("/lyrics")
def get_lyrics(artist: str, track: str):
    url = "https://api.musixmatch.com/ws/1.1/matcher.lyrics.get"
    params = {"q_artist": artist, "q_track": track, "apikey": MUSIXMATCH_API_KEY}
    res = requests.get(url, params=params)
    data = res.json()
    message = data.get("message", {}).get("body", {}).get("lyrics")
    if not message:
        return {"lyrics": "Lyrics not found."}
    return {"lyrics": message["lyrics_body"]}

# ----------------- Playlist Endpoints -----------------
@app.post("/playlists")
def create_playlist(pl: PlaylistCreate):
    db = SessionLocal()
    new_pl = Playlist(name=pl.name)
    db.add(new_pl)
    db.commit()
    db.refresh(new_pl)
    db.close()
    return {"id": new_pl.id, "name": new_pl.name}

@app.get("/playlists")
def list_playlists():
    db = SessionLocal()
    pls = db.query(Playlist).all()
    result = [{"id": p.id, "name": p.name, "tracks": [
        {"id": t.id, "title": t.title, "artist": t.artist, "preview": t.preview, "albumCover": t.albumCover}
        for t in p.tracks]} for p in pls]
    db.close()
    return result

@app.post("/playlists/add")
def add_to_playlist(item: PlaylistAddTrack):
    db = SessionLocal()
    pl = db.query(Playlist).filter(Playlist.id == item.playlist_id).first()
    if not pl:
        db.close()
        raise HTTPException(status_code=404, detail="Playlist not found")
    track = Track(title=item.title, artist=item.artist, preview=item.preview, albumCover=item.albumCover, playlist_id=item.playlist_id)
    db.add(track)
    db.commit()
    db.refresh(track)
    db.close()
    return {"message": "Track added", "track_id": track.id}
