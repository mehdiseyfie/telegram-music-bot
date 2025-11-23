#cache.py
import json
from typing import Dict, Any, List
from .api import search_track, get_artist, get_recommendations, spotify_search
from .redis_client import get_redis_pool
from logging_config import setup_logging

CACHE_EXPIRATION = 3600  # 1 hour in seconds

logger = setup_logging(logstash_host='localhost', logstash_port=5000)

async def cached_operation(operation, cache_key, *args, **kwargs):
    redis = await get_redis_pool()
    try:
        cached_result = await redis.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        result = await operation(*args, **kwargs)
        await redis.setex(cache_key, CACHE_EXPIRATION, json.dumps(result))
        return result
    except Exception as e:
        logger.error(f"Error in cached operation: {str(e)}")
        return await operation(*args, **kwargs)

async def cached_search_track(query: str) -> List[Dict[str, Any]]:
    return await cached_operation(search_track, f"search_track:{query}", query)

async def cached_get_artist(artist_id: str) -> Dict[str, Any]:
    return await cached_operation(get_artist, f"artist:{artist_id}", artist_id)

async def cached_get_recommendations(seed_tracks_key: str, limit: int = 100) -> List[Dict[str, Any]]:
    return await cached_operation(get_recommendations, f"recommendations:{seed_tracks_key}:{limit}", seed_tracks_key.split(','), limit)

async def cached_spotify_search(query: str, search_type: str, limit: int) -> Dict[str, Any]:
    return await cached_operation(spotify_search, f"spotify_search:{query}:{search_type}:{limit}", query, search_type, limit)

async def bulk_cache_operation(operations):
    redis = await get_redis_pool()
    pipe = redis.pipeline()
    results = []
    for op, cache_key, args, kwargs in operations:
        try:
            cached_result = await redis.get(cache_key)
            if cached_result:
                results.append(json.loads(cached_result))
            else:
                result = await op(*args, **kwargs)
                results.append(result)
                pipe.setex(cache_key, CACHE_EXPIRATION, json.dumps(result))
        except Exception as e:
            logger.error(f"Error in bulk cache operation: {str(e)}")
            results.append(await op(*args, **kwargs))
    
    await pipe.execute()
    return results