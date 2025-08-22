from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
import os, requests

# -------------------
# Database Setup
# -------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# -------------------
# Database Models
# -------------------
class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    tracks = relationship("Track", back_populates="playlist", cascade="all, delete")


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(String, nullable=False)  # Deezer track ID
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    preview = Column(String)   # 30s preview from Deezer
    album_cover = Column(String)
    playlist_id = Column(Integer, ForeignKey("playlists.id"))

    playlist = relationship("Playlist", back_populates="tracks")


# -------------------
# Schemas
# -------------------
class TrackCreate(BaseModel):
    playlist_id: int
    track_id: str
    title: str
    artist: str
    preview: str
    album_cover: str


class TrackOut(BaseModel):
    id: int
    track_id: str
    title: str
    artist: str
    preview: str
    album_cover: str

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
# FastAPI App
# -------------------
app = FastAPI()

# Allow frontend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Ensure DB tables exist at startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# Dependency for DB session
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
    return {"message": "Music Backend with DB is running 🎶"}


# ---- Playlist Endpoints ----
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
        track_id=track.track_id,
        title=track.title,
        artist=track.artist,
        preview=track.preview,
        album_cover=track.album_cover,
        playlist_id=track.playlist_id,
    )

    db.add(new_track)
    db.commit()
    db.refresh(new_track)
    return new_track


# ---- Deezer Integration ----
@app.get("/search_deezer")
def search_deezer(query: str):
    url = f"https://api.deezer.com/search?q={query}"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch from Deezer")

    data = response.json()
    results = []
    for item in data.get("data", []):
        results.append({
            "track_id": str(item["id"]),
            "title": item["title"],
            "artist": item["artist"]["name"],
            "preview": item["preview"],
            "album_cover": item["album"]["cover_medium"]
        })

    return results
