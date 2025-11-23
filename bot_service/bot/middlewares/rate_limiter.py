#rate_limiter.py
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from typing import Callable, Dict, Any
import time
from database_service.database import redis_client

class AdvancedRateLimiter:
    def __init__(self, max_calls: int, time_frame: int, cooldown_time: int):
        self.max_calls = max_calls
        self.time_frame = time_frame
        self.cooldown_time = cooldown_time

    def is_allowed(self, user_id: int) -> bool:
        current_time = int(time.time())
        key = f"rate_limit:{user_id}"

        pipe = redis_client.pipeline(transaction=True)
        pipe.zremrangebyscore(key, 0, current_time - self.time_frame)
        pipe.zcard(key)
        pipe.zadd(key, {current_time: current_time})
        pipe.expire(key, self.time_frame)
        _, call_count, _, _ = pipe.execute()

        return call_count <= self.max_calls

    def get_cooldown_time(self, user_id: int) -> int:
        current_time = int(time.time())
        key = f"rate_limit:{user_id}"

        pipe = redis_client.pipeline(transaction=True)
        pipe.zrange(key, 0, 0, withscores=True)
        result = pipe.execute()

        if result and result[0]:
            oldest_call = int(result[0][0][1])
            return max(0, self.cooldown_time - (current_time - oldest_call))
        return 0

class AdvancedRateLimitMiddleware:
    def __init__(self, limit: int, window: int, cooldown_time: int):
        self.limiter = AdvancedRateLimiter(max_calls=limit, time_frame=window, cooldown_time=cooldown_time)

    async def middleware(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        user_id = update.effective_user.id
        if self.limiter.is_allowed(user_id):
            return True

        cooldown_time = self.limiter.get_cooldown_time(user_id)
        message = f"You're sending requests too quickly. Please wait {cooldown_time} seconds before trying again."

        if update.message:
            await update.message.reply_text(message)
        elif update.callback_query:
            await update.callback_query.answer(message, show_alert=True)

        return False

def setup_rate_limiter(application: Application, limit: int, window: int, cooldown_time: int):
    middleware = AdvancedRateLimitMiddleware(limit=limit, window=window, cooldown_time=cooldown_time)
    application.add_handler(MessageHandler(filters.ALL, middleware.middleware), group=-1)

# Example usage in your main application
# setup_advanced_rate_limiter(application, limit=5, window=60, cooldown_time=120)