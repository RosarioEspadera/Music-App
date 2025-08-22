from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
import os
import requests

# -------------------
# Config
# -------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
YT_API_KEY = os.getenv("YT_API_KEY")  # <-- set this in Render (never expose in frontend)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------
# Models
# -------------------
class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    tracks = relationship("Track", back_populates="playlist", cascade="all, delete")

class Track(Base):
    __tablename__ = "tracks"
    id = Column(Integer, primary_key=True, index=True)
    # Reuse the existing column to store YouTube videoId
    track_id = Column(String, nullable=False)  # <- stores YouTube videoId
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)  # use YouTube channelTitle here
    preview = Column(String)                 # optional (unused for YT)
    album_cover = Column(String)             # use YouTube thumbnail URL
    playlist_id = Column(Integer, ForeignKey("playlists.id"))
    playlist = relationship("Playlist", back_populates="tracks")

# -------------------
# Schemas
# -------------------
class TrackCreate(BaseModel):
    playlist_id: int
    track_id: str      # YouTube videoId
    title: str
    artist: str        # YouTube channelTitle
    preview: str | None = None
    album_cover: str | None = None

class TrackOut(BaseModel):
    id: int
    track_id: str
    title: str
    artist: str
    preview: str | None = None
    album_cover: str | None = None
    class Config:
        orm_mode = True

class PlaylistCreate(BaseModel):
    name: str

class PlaylistOut(BaseModel):
    id: int
    name: str
    tracks: list[TrackOut] = []
    class Config:
        orm_mode = True

# -------------------
# App
# -------------------
app = FastAPI(title="Music Backend (YouTube)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # tighten to your frontend origin in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------
# Routes
# -------------------
@app.get("/")
def root():
    return {"message": "Music Backend (YouTube) is running 🎶"}

@app.get("/playlists", response_model=list[PlaylistOut])
def get_playlists(db: Session = Depends(get_db)):
    return db.query(Playlist).all()

@app.post("/playlists", response_model=PlaylistOut)
def create_playlist(playlist: PlaylistCreate, db: Session = Depends(get_db)):
    new_playlist = Playlist(name=playlist.name)
    db.add(new_playlist)
    db.commit()
    db.refresh(new_playlist)
    return new_playlist

@app.post("/playlists/add", response_model=TrackOut)
def add_track(track: TrackCreate, db: Session = Depends(get_db)):
    playlist = db.query(Playlist).filter(Playlist.id == track.playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    new_track = Track(
        track_id=track.track_id,       # YouTube videoId
        title=track.title,
        artist=track.artist,           # channelTitle
        preview=track.preview,
        album_cover=track.album_cover, # thumbnail
        playlist_id=track.playlist_id,
    )
    db.add(new_track)
    db.commit()
    db.refresh(new_track)
    return new_track

# ---- YouTube search proxy (keeps your key safe)
@app.get("/search")
def search_youtube(q: str = Query(..., min_length=1), max_results: int = 10):
    if not YT_API_KEY:
        raise HTTPException(status_code=500, detail="Server missing YT_API_KEY")
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "type": "video",
        "maxResults": max(1, min(max_results, 25)),
        "q": q,
        "key": YT_API_KEY,
        # Optional: filter to music category (10) – not perfect but helps:
        # "videoCategoryId": "10",
    }
    r = requests.get(url, params=params, timeout=15)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    data = r.json()
    # Map to simplified objects
    items = []
    for it in data.get("items", []):
        vid = it["id"]["videoId"]
        sn = it["snippet"]
        items.append({
            "videoId": vid,
            "title": sn["title"],
            "channelTitle": sn["channelTitle"],
            "thumbnail": (sn.get("thumbnails", {}).get("medium") or sn.get("thumbnails", {}).get("default") or {}).get("url", "")
        })
    return {"items": items}
