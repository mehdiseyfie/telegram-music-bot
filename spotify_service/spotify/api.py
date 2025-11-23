#api.py
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import asyncio
from logging_config import setup_logging
from asyncio_throttle import Throttler
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

client_credentials_manager = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
)

sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

logger = setup_logging(logstash_host='localhost', logstash_port=5000)

throttler = Throttler(rate_limit=1000, period=3600)  # 1000 requests per hour

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def retry_with_backoff(coroutine):
    return await coroutine

async def throttled_spotify_request(func, *args, **kwargs):
    async with throttler:
        return await retry_with_backoff(asyncio.to_thread(func, *args, **kwargs))

async def search_track(query):
    return await throttled_spotify_request(sp.search, q=query, type='track', limit=10)

async def get_artist(artist_id):
    return await throttled_spotify_request(sp.artist, artist_id)

async def get_recommendations(seed_tracks, limit=100):
    return await throttled_spotify_request(sp.recommendations, seed_tracks=seed_tracks, limit=limit)

async def spotify_search(query: str, search_type: str, limit: int):
    return await throttled_spotify_request(sp.search, q=query, type=search_type, limit=limit)

# اضافه کردن cached_spotify_search
CACHE_EXPIRATION = 86400  # 24 hours

async def cached_spotify_search(query: str, search_type: str, limit: int) -> Dict[str, Any]:
    from .cache import cached_operation
    return await cached_operation(spotify_search, f"spotify_search:{query}:{search_type}:{limit}", query, search_type, limit, expiration=CACHE_EXPIRATION)
