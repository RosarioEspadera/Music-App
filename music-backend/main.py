from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# Models
class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    tracks = relationship("Track", back_populates="playlist")

class Track(Base):
    __tablename__ = "tracks"
    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    preview = Column(String)
    albumCover = Column(String)
    playlist_id = Column(Integer, ForeignKey("playlists.id"))
    playlist = relationship("Playlist", back_populates="tracks")

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Music Backend with DB is running 🎶"}

@app.get("/playlists")
def get_playlists():
    db = SessionLocal()
    playlists = db.query(Playlist).all()
    result = []
    for pl in playlists:
        result.append({
            "id": pl.id,
            "name": pl.name,
            "tracks": [
                {
                    "id": t.track_id,
                    "title": t.title,
                    "artist": t.artist,
                    "preview": t.preview,
                    "albumCover": t.albumCover
                } for t in pl.tracks
            ]
        })
    return result

class PlaylistCreate(BaseModel):
    name: str

@app.post("/playlists")
def create_playlist(data: PlaylistCreate):
    db = SessionLocal()
    playlist = Playlist(name=data.name)
    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    return {"id": playlist.id, "name": playlist.name, "tracks": []}

class TrackAdd(BaseModel):
    playlist_id: int
    track_id: str
    title: str
    artist: str
    preview: str | None = None
    albumCover: str | None = None

@app.post("/playlists/add")
def add_track(data: TrackAdd):
    db = SessionLocal()
    playlist = db.query(Playlist).filter(Playlist.id == data.playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    track = Track(
        track_id=data.track_id,
        title=data.title,
        artist=data.artist,
        preview=data.preview,
        albumCover=data.albumCover,
        playlist=playlist
    )
    db.add(track)
    db.commit()
    db.refresh(track)

    return {"message": "Track added", "playlist_id": playlist.id}
