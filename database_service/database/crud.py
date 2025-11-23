#crud.py
from sqlalchemy.orm import Session, joinedload
from . import models, redis_client, user_cache, language_cache
from typing import Optional, List, Dict
import json
from logging_config import setup_logging
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from cachetools import cached
import uuid

logger = setup_logging(logstash_host='localhost', logstash_port=5000)

CACHE_EXPIRATION = 3600  # 1 hour in seconds
BULK_INSERT_BATCH_SIZE = 1000  # Adjust based on your database limits

@cached(cache=user_cache)
def get_user(db: Session, telegram_id: int) -> Optional[models.User]:
    # Try to get user from Redis cache
    user_cache_key = f"user:{telegram_id}"
    cached_user = redis_client.get(user_cache_key)
    if cached_user:
        return models.User(**json.loads(cached_user))

    # If not in cache, query the database
    user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()
    if user:
        # Cache the user in Redis
        redis_client.setex(user_cache_key, CACHE_EXPIRATION, json.dumps(user.to_dict()))
    return user

def get_user_with_playlists(db: Session, telegram_id: int):
    return db.query(models.User).options(joinedload(models.User.playlists)).filter(models.User.telegram_id == telegram_id).first()
def create_user(db: Session, telegram_id: int, username: Optional[str] = None) -> models.User:
    try:
        db_user = models.User(id=str(uuid.uuid4()), telegram_id=telegram_id, username=username)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        # Cache the new user
        user_cache_key = f"user:{telegram_id}"
        redis_client.setex(user_cache_key, CACHE_EXPIRATION, json.dumps(db_user.to_dict()))
        return db_user
    except SQLAlchemyError as e:
        logger.error(f"Error creating user: {str(e)}")
        db.rollback()
        raise

def create_playlist_for_database(db: Session, user_id: str, spotify_playlist_id: str, name: str, description: str, created_by: str, mood: Optional[str] = None, genre: Optional[str] = None) -> models.Playlist:
    try:
        db_playlist = models.Playlist(
            spotify_playlist_id=spotify_playlist_id,
            user_id=user_id,
            name=name,
            description=description,
            mood=mood,
            genre=genre,
            created_by=created_by
        )
        db.add(db_playlist)
        db.commit()
        db.refresh(db_playlist)
        return db_playlist
    except SQLAlchemyError as e:
        logger.error(f"Error creating playlist: {str(e)}")
        db.rollback()
        raise

def get_user_playlists(db: Session, user_id: str) -> List[models.Playlist]:
    return db.query(models.Playlist).filter(models.Playlist.user_id == user_id).all()
def get_playlist_tracks(db: Session, spotify_playlist_id: str) -> List[models.PlaylistTrack]:
    return db.query(models.PlaylistTrack).filter(models.PlaylistTrack.playlist_id == spotify_playlist_id).all()

def create_playlist_tracks_bulk(db: Session, tracks_data: List[Dict]):
    try:
        for i in range(0, len(tracks_data), BULK_INSERT_BATCH_SIZE):
            batch = tracks_data[i:i+BULK_INSERT_BATCH_SIZE]
            db_tracks = [models.PlaylistTrack(**track) for track in batch]
            db.bulk_save_objects(db_tracks)
            db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Error saving tracks: {str(e)}")
        db.rollback()
        raise
def update_user_language(db: Session, telegram_id: int, language: str) -> Optional[models.User]:
    try:
        db_user = get_user(db, telegram_id)
        if db_user:
            db_user.language = language
            db.commit()

            # Clear user and language caches
            user_cache.pop(telegram_id, None)
            language_cache.pop(telegram_id, None)

            # Notify connected clients (implementation depends on your bot architecture)
            notify_language_update(telegram_id, language)

            return db_user
    except SQLAlchemyError as e:
        logger.error(f"Error updating user language: {str(e)}")
        db.rollback()
        raise
def update_playlist_track_count(db: Session, spotify_playlist_id: str, track_count: int) -> None:
    try:
        db_playlist = db.query(models.Playlist).filter(models.Playlist.spotify_playlist_id == spotify_playlist_id).first()
        if db_playlist:
            db_playlist.track_count = track_count
            db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Error updating playlist track count: {str(e)}")
        db.rollback()
        raise

# Other functions remain the same...

# Placeholder function for notifying clients about language updates
def notify_language_update(telegram_id: int, new_language: str):
    # Implement the logic to notify connected clients about the language update
    # This could involve sending a message to the Telegram bot or updating a shared state
    logger.info(f"Language updated for user {telegram_id} to {new_language}")
    # Add your implementation here