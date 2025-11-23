from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, BigInteger, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(50))
    language = Column(String(2), default='en')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    playlists = relationship("Playlist", back_populates="user")

    __table_args__ = (
        Index('idx_telegram_id', 'telegram_id', 'language'),
        Index('idx_username', 'username'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'language': self.language,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

    def get_playlists(self):
        return [playlist.to_dict() for playlist in self.playlists]

class Playlist(Base):
    __tablename__ = 'playlists'
    spotify_playlist_id = Column(String(100), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(300))
    mood = Column(String(50))
    genre = Column(String(50))
    track_count = Column(Integer, default=0)
    created_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="playlists")
    tracks = relationship("PlaylistTrack", back_populates="playlist")

    __table_args__ = (
        Index('idx_user_id', user_id),
        Index('idx_created_at', created_at),
        Index('idx_mood_genre', mood, genre),
    )

    def to_dict(self):
        return {
            'spotify_playlist_id': self.spotify_playlist_id,
            'name': self.name,
            'description': self.description,
            'mood': self.mood,
            'genre': self.genre,
            'track_count': self.track_count,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

    def get_tracks(self):
        return [track.to_dict() for track in self.tracks]

class PlaylistTrack(Base):
    __tablename__ = 'playlist_tracks'
    id = Column(Integer, primary_key=True)
    playlist_id = Column(String(100), ForeignKey('playlists.spotify_playlist_id'), nullable=False)
    spotify_track_id = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    artist = Column(String(200), nullable=False)
    album = Column(String(200))
    duration_ms = Column(Integer)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    playlist = relationship("Playlist", back_populates="tracks")

    __table_args__ = (
        Index('idx_playlist_id', playlist_id),
        Index('idx_spotify_track_id', spotify_track_id),
        Index('idx_artist', artist),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'spotify_track_id': self.spotify_track_id,
            'name': self.name,
            'artist': self.artist,
            'album': self.album,
            'duration_ms': self.duration_ms,
            'added_at': self.added_at.isoformat() if isinstance(self.added_at, datetime) else self.added_at
        }