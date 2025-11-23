#local redis_client.py
import os
from redis.asyncio import Redis, ConnectionPool
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Ensure that the Redis configuration is valid
if REDIS_HOST is None or REDIS_PORT is None or REDIS_DB is None:
    raise ValueError("Redis configuration is missing in environment variables.")

redis_pool = ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
    max_connections=100,
    socket_timeout=5,  # Add a socket timeout
    socket_connect_timeout=5  # Add a connection timeout
)

async def get_redis_pool():
    return Redis(connection_pool=redis_pool)

# Alias for get_redis_pool
get_redis_client = get_redis_pool

# Make sure to export the functions
__all__ = ['get_redis_pool', 'get_redis_client']