import logging
from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
from bot_service.bot import create_application
from config import SERVER_PORT
from telegram import Update
import asyncio
from starlette.responses import JSONResponse
from redis import asyncio as aioredis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a connection pool
redis_pool = aioredis.ConnectionPool.from_url(
    "redis://localhost", 
    max_connections=10,
    encoding="utf-8", 
    decode_responses=True
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = aioredis.Redis(connection_pool=redis_pool)
    await app.state.redis.ping()
    yield
    # Shutdown
    await app.state.redis.close()
    await redis_pool.disconnect()

app = FastAPI(lifespan=lifespan)
bot_app = create_application()

@app.get('/')
async def index():
    return {"status": "Bot is running"}

@app.post('/bot')
async def bot_webhook(request: Request):
    data = await request.json()
    update_id = data.get('update_id')
    
    try:
        if await app.state.redis.exists(f"processed:{update_id}"):
            return JSONResponse(content={"status": "already processed"}, status_code=200)
        
        logger.info(f"Received update ID: {update_id}")
        update = Update.de_json(data, bot_app.bot)
        
        # Process update in the background
        asyncio.create_task(process_update(update, update_id, app.state.redis))
        
        return JSONResponse(content={"status": "accepted"}, status_code=202)
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        raise HTTPException(status_code=400, detail=str(e))

async def process_update(update: Update, update_id: int, redis):
    try:
        await bot_app.process_update(update)
        logger.info(f"Successfully processed update ID: {update_id}")
        await redis.setex(f"processed:{update_id}", 3600, "1")
    except Exception as e:
        logger.error(f"Error in async processing of update {update_id}: {e}")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "webserver:app",  # اینجا باید نام ماژول (فایل) و شیء اپلیکیشن را به صورت رشته‌ای پاس دهی
        host="0.0.0.0", 
        port=SERVER_PORT,
        workers=4,  # استفاده از workers حالا درست کار می‌کند
        limit_concurrency=1000,  
    )
