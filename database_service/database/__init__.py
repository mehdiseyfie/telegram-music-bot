#__init__.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os
import redis
from redis import ConnectionPool
from cachetools import TTLCache

# بارگذاری مقادیر از فایل .env
load_dotenv()

# دریافت مقادیر از متغیرهای محیطی
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# ساختن رشته اتصال به دیتابیس
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}/{MYSQL_DATABASE}"

# تنظیمات SQLAlchemy با استفاده از QueuePool
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# تنظیمات Redis با استفاده از ConnectionPool
redis_pool = ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
    max_connections=100
)
redis_client = redis.Redis(connection_pool=redis_pool)

# تنظیمات TTLCache
user_cache = TTLCache(maxsize=100000, ttl=3600)  # Cache for 1 hour
language_cache = TTLCache(maxsize=100000, ttl=3600)  # Cache for 1 hour

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# اطمینان از در دسترس بودن توابع و کلاس‌های مورد نیاز

from .crud import (
    get_user, create_user, create_playlist_tracks_bulk,
    update_user_language, create_playlist_for_database,
    update_playlist_track_count
)