#main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import logging
import asyncio
from logging_config import setup_logging
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
from functools import wraps
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import SQLALCHEMY_DATABASE_URL

# Constants
REQUEST_TIMEOUT = 10.0  # seconds
CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60  # seconds

class CircuitBreaker:
    def __init__(self, threshold=CIRCUIT_BREAKER_THRESHOLD, timeout=CIRCUIT_BREAKER_TIMEOUT):
        self.threshold = threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = 0
        self.is_open = False

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.threshold:
            self.is_open = True

    def record_success(self):
        self.failures = 0
        self.is_open = False

    def can_execute(self):
        if not self.is_open:
            return True
        if time.time() - self.last_failure_time >= self.timeout:
            self.is_open = False
            self.failures = 0
            return True
        return False

circuit_breakers = {
    "spotify": CircuitBreaker(),
    "database": CircuitBreaker()
}

app = FastAPI(title="Spotify Bot API Gateway", version="1.0.0")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = setup_logging(logstash_host='localhost', logstash_port=5000)

# Add database connection pooling and retry logic
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)

# Pydantic models for request validation
class TrackSearch(BaseModel):
    query: str

class PlaylistCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tracks: List[str]
    user_id: int

class UserCreate(BaseModel):
    telegram_id: int
    username: Optional[str] = None

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def make_request(url: str, method: str = "GET", data: dict = None) -> dict:
    service = "spotify" if "spotify_service" in url else "database"
    circuit_breaker = circuit_breakers[service]

    if not circuit_breaker.can_execute():
        raise HTTPException(
            status_code=503,
            detail=f"Service {service} is temporarily unavailable"
        )

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            headers = {"Content-Type": "application/json"}
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            circuit_breaker.record_success()
            return response.json()

        except httpx.TimeoutException:
            logger.error(f"Request timeout for {url}")
            circuit_breaker.record_failure()
            raise HTTPException(status_code=504, detail="Request timeout")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            circuit_breaker.record_failure()
            
            if e.response.status_code == 401:
                if "spotify" in url:
                    raise HTTPException(
                        status_code=401,
                        detail="Spotify authentication failed. Please check your credentials."
                    )
                raise HTTPException(status_code=401, detail="Authentication failed")
                
            raise HTTPException(
                status_code=e.response.status_code,
                detail=str(e)
            )

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            circuit_breaker.record_failure()
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )

def handle_spotify_error(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException as e:
            if e.status_code == 401 and "spotify" in str(e.detail).lower():
                logger.error("Spotify authentication error. Refreshing credentials...")
                # Add logic here to refresh Spotify credentials if needed
            raise
    return wrapper

@app.post("/search_track")
@handle_spotify_error
async def search_track(track_search: TrackSearch):
    """
    Search for tracks using the Spotify service.
    """
    return await make_request(
        "http://spotify_service:8000/search_track",
        method="POST",
        data=track_search.dict()
    )

@app.post("/create_playlist")
async def create_playlist(playlist_create: PlaylistCreate):
    """
    Create a new playlist using the Database service.
    """
    return await make_request("http://database_service:8000/create_playlist", method="POST", data=playlist_create.dict())

@app.post("/create_user")
async def create_user(user_create: UserCreate):
    """
    Create a new user using the Database service.
    """
    return await make_request("http://database_service:8000/create_user", method="POST", data=user_create.dict())

@app.get("/get_user/{telegram_id}")
async def get_user(telegram_id: int):
    """
    Get user information by Telegram ID using the Database service.
    """
    return await make_request(f"http://database_service:8000/get_user/{telegram_id}")

@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "healthy"}

@app.get("/auth/status")
async def check_auth_status():
    """
    Check authentication status for all services
    """
    try:
        spotify_status = await make_request("http://spotify_service:8000/health", method="GET")
        db_status = await make_request("http://database_service:8000/health", method="GET")
        return {
            "spotify_service": spotify_status.get("status", "error"),
            "database_service": db_status.get("status", "error")
        }
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        return {
            "status": "error",
            "detail": str(e)
        }

@app.get("/service_health")
async def service_health():
    """
    Get detailed health status of all services including circuit breaker status
    """
    return {
        "spotify_service": {
            "status": "open" if circuit_breakers["spotify"].is_open else "closed",
            "failures": circuit_breakers["spotify"].failures
        },
        "database_service": {
            "status": "open" if circuit_breakers["database"].is_open else "closed",
            "failures": circuit_breakers["database"].failures
        }
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Global exception handler for HTTPExceptions.
    """
    logger.error(f"HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RetryError)
async def retry_exception_handler(request, exc):
    """
    Handler for retry exhaustion
    """
    logger.error(f"Retry limit exceeded: {exc}")
    return JSONResponse(
        status_code=503,
        content={"detail": "Service temporarily unavailable after multiple retries"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)