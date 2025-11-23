#local spotify.py
from logging_config import setup_logging
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOauthError
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, SPOTIFY_USERNAME
import random
from collections import defaultdict
import asyncio
from functools import lru_cache
from spotify_service.spotify.redis_client import get_redis_client
import json


logger = setup_logging(logstash_host='localhost', logstash_port=5000)
auth_manager = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
)

sp = spotipy.Spotify(auth_manager=auth_manager)
# Update the authentication setup
# در spotify.py، یک تابع برای بازسازی توکن اضافه کنید
async def refresh_spotify_auth():
    global sp, auth_manager
    try:
        # حذف کش فعلی
        import os
        cache_path = f".cache-{SPOTIFY_USERNAME}"
        if os.path.exists(cache_path):
            os.remove(cache_path)
        
        # بازسازی مدیر احراز هویت
        auth_manager = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET)

        sp = spotipy.Spotify(auth_manager=auth_manager)
        return True
    except Exception as e:
        logger.error(f"Failed to refresh Spotify auth: {str(e)}")
        return False

@lru_cache(maxsize=1000)
def get_audio_features(track_id):
    features = sp.audio_features([track_id])[0]
    return features if features else {}

async def get_audio_features_batch(track_ids):
    redis = await get_redis_client()
    features = {}
    missing_ids = []

    # Try to get features from cache
    for track_id in track_ids:
        cached_feature = await redis.get(f"audio_feature:{track_id}")
        if cached_feature:
            features[track_id] = json.loads(cached_feature)
        else:
            missing_ids.append(track_id)

    # Fetch missing features from Spotify API
    if missing_ids:
        batch_features = await asyncio.to_thread(sp.audio_features, missing_ids)
        for track_id, feature in zip(missing_ids, batch_features):
            if feature:
                features[track_id] = feature
                await redis.setex(f"audio_feature:{track_id}", 86400, json.dumps(feature))  # Cache for 24 hours

    return features

def calculate_similarity(seed_features, track_features):
    similarity = 0
    for key in ['danceability', 'energy', 'valence', 'acousticness', 'instrumentalness']:
        similarity += abs(seed_features.get(key, 0) - track_features.get(key, 0))
    return 1 - (similarity / 5)  # Normalized to a scale of 0 to 1

async def get_recommendations(seed_tracks=None, seed_artists=None, seed_genres=None, limit=20, retry_auth=True, **kwargs):
    try:
        essential_params = {
            'limit': min(limit * 2, 100)  # Request more tracks for further filtering
        }
        if seed_tracks:
            essential_params['seed_tracks'] = seed_tracks[:2]
        if seed_artists:
            essential_params['seed_artists'] = seed_artists[:1]
        if seed_genres:
            essential_params['seed_genres'] = seed_genres[:2]
        for key, value in kwargs.items():
            if key.startswith('target_') and 0 <= value <= 1:
                essential_params[key] = value
            elif key in ['min_popularity', 'max_popularity', 'target_popularity'] and 0 <= value <= 100:
                essential_params[key] = value

        recommendations = await asyncio.to_thread(sp.recommendations, **essential_params)
        return [rec['id'] for rec in recommendations['tracks']]
    except SpotifyOauthError as se:
        if retry_auth:
            logger.warning("Spotify auth error, attempting to refresh credentials...")
            if await refresh_spotify_auth():
                return await get_recommendations(seed_tracks, seed_artists, seed_genres, limit, retry_auth=False, **kwargs)
        logger.error(f"Spotify OAuth error: {str(se)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_recommendations: {str(e)}")
        raise

async def filter_and_rank_tracks(seed_track_id, recommended_track_ids, target_count):
    seed_features = await asyncio.to_thread(get_audio_features, seed_track_id)
    recommended_features = await get_audio_features_batch(recommended_track_ids)
    
    similarities = [(track_id, calculate_similarity(seed_features, features))
                    for track_id, features in recommended_features.items()]
    
    # Sort by similarity and select the best matches
    sorted_tracks = sorted(similarities, key=lambda x: x[1], reverse=True)
    return [track_id for track_id, _ in sorted_tracks[:target_count]]

async def create_playlist_from_song(track_id, target_count=100, max_iterations=10):
    try:
        seed_track = await asyncio.to_thread(sp.track, track_id)
        seed_artists = [artist['id'] for artist in seed_track['artists']]
        seed_track_features = await asyncio.to_thread(get_audio_features, track_id)
        
        logger.info(f"Seed track: {seed_track['name']} by {seed_track['artists'][0]['name']}")
        
        artist_genres = (await asyncio.to_thread(sp.artist, seed_artists[0]))['genres']
        seed_genres = artist_genres[:2] if artist_genres else []
        
        logger.info(f"Seed genres: {seed_genres}")
        
        base_params = {
            'target_danceability': seed_track_features['danceability'],
            'target_energy': seed_track_features['energy'],
            'target_valence': seed_track_features['valence'],
            'target_acousticness': seed_track_features['acousticness'],
            'target_instrumentalness': seed_track_features['instrumentalness'],
            'min_popularity': max(0, seed_track['popularity'] - 20),
            'max_popularity': min(100, seed_track['popularity'] + 20),
        }
        
        all_recommended_tracks = set()
        iteration = 0
        
        while len(all_recommended_tracks) < target_count and iteration < max_iterations:
            remaining = target_count - len(all_recommended_tracks)
            
            similar_tracks = (await asyncio.to_thread(sp.search, q=f"track:{seed_track['name']} artist:{seed_track['artists'][0]['name']}", type='track', limit=2))['tracks']['items']
            seed_tracks = [track_id] + [track['id'] for track in similar_tracks[:1]]
            
            try:
                new_tracks = await get_recommendations(seed_tracks, seed_artists[:1], seed_genres, remaining, **base_params)
                all_recommended_tracks.update(new_tracks)
            except SpotifyException:
                simplified_params = {'seed_tracks': seed_tracks, 'seed_artists': seed_artists[:1], 'seed_genres': seed_genres}
                new_tracks = await get_recommendations(**simplified_params, limit=remaining)
                all_recommended_tracks.update(new_tracks)
            
            if len(all_recommended_tracks) < target_count:
                base_params['min_popularity'] = max(0, base_params['min_popularity'] - 5)
                base_params['max_popularity'] = min(100, base_params['max_popularity'] + 5)
                
                for param in ['target_danceability', 'target_energy', 'target_valence']:
                    base_params[param] = max(0, min(1, base_params[param] + (random.random() - 0.5) * 0.2))
            
            iteration += 1
        
        logger.info(f"{len(all_recommended_tracks)} recommendations generated after {iteration} iterations")
        
        # Filter and rank the recommended tracks
        filtered_tracks = await filter_and_rank_tracks(track_id, list(all_recommended_tracks), target_count)
        
        return filtered_tracks
    except Exception as e:
        logger.error(f"Unexpected error in create_playlist_from_song: {str(e)}")
        raise

async def create_playlist_from_genre(genre, target_count=100, max_iterations=10):
    try:
        all_recommended_tracks = set()
        iteration = 0
        
        while len(all_recommended_tracks) < target_count and iteration < max_iterations:
            remaining = target_count - len(all_recommended_tracks)
            
            try:
                new_tracks = await get_recommendations(seed_genres=[genre], limit=remaining)
                all_recommended_tracks.update(new_tracks)
            except SpotifyException:
                logger.error(f"Error getting recommendations for genre {genre}")
                break
            
            iteration += 1
        
        logger.info(f"{len(all_recommended_tracks)} recommendations generated after {iteration} iterations")
        
        # Additional filtering or ranking could be added here if needed
        return list(all_recommended_tracks)[:target_count]
    except Exception as e:
        logger.error(f"Unexpected error in create_playlist_from_genre: {str(e)}")
        raise

async def create_playlist(name, tracks):
    try:
        playlist = await asyncio.to_thread(sp.user_playlist_create, SPOTIFY_USERNAME, name, public=True, description="Created by @AR_MUSICLAND_BOT")
        await asyncio.to_thread(sp.playlist_add_items, playlist['id'], tracks)
        logger.info(f"Playlist successfully created: {playlist['external_urls']['spotify']}")
        return playlist['external_urls']['spotify']
    except Exception as e:
        logger.error(f"Error in create_playlist: {str(e)}")
        raise

async def analyze_playlist_diversity(tracks):
    features = await get_audio_features_batch(tracks)
    diversity_scores = defaultdict(list)
    
    for feature in features.values():
        for key in ['danceability', 'energy', 'valence', 'acousticness', 'instrumentalness']:
            diversity_scores[key].append(feature.get(key, 0))
    
    diversity_report = {}
    for key, values in diversity_scores.items():
        diversity_report[key] = {
            'mean': sum(values) / len(values),
            'range': max(values) - min(values)
        }
    
    return diversity_report

# Use the diversity analysis function
async def create_and_analyze_playlist(name, seed_track_id, target_count=100):
    tracks = await create_playlist_from_song(seed_track_id, target_count)
    playlist_url = await create_playlist(name, tracks)
    diversity_report = await analyze_playlist_diversity(tracks)
    
    logger.info(f"Playlist diversity analysis:\n{diversity_report}")
    return playlist_url, diversity_report