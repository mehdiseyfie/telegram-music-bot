import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User, Message, CallbackQuery
from telegram.ext import Application, ContextTypes,MessageHandler
import asyncio
import sys
import os

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the actual implementation
from bot_service.bot.middlewares.rate_limiter import RateLimiter, RateLimitMiddleware, setup_rate_limiter

class TestRateLimiter(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.limiter = RateLimiter(max_calls=2, time_frame=5)
        self.middleware = RateLimitMiddleware(limit=2, window=5)

    async def test_is_allowed(self):
        user_id = 123
        self.assertTrue(await self.limiter.is_allowed(user_id))
        self.assertTrue(await self.limiter.is_allowed(user_id))
        self.assertFalse(await self.limiter.is_allowed(user_id))

        # Wait for the time frame to pass
        await asyncio.sleep(5)
        self.assertTrue(await self.limiter.is_allowed(user_id))

    async def test_middleware_message(self):
        update = MagicMock(spec=Update)
        update.= MagicMock(spec=User)
        update.effective_user.id = 456
        update.message = AsyncMock(spec=Message)
        update.callback_query = None
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        # First two requests should be allowed
        self.assertTrue(await self.middleware.middleware(update, context))
        self.assertTrue(await self.middleware.middleware(update, context))

        # Third request should be blocked
        self.assertFalse(await self.middleware.middleware(update, context))
        update.message.reply_text.assert_called_once_with("You're sending requests too quickly. Please slow down.")

    async def test_middleware_callback_query(self):
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 789
        update.message = None
        update.callback_query = AsyncMock(spec=CallbackQuery)
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        # First two requests should be allowed
        self.assertTrue(await self.middleware.middleware(update, context))
        self.assertTrue(await self.middleware.middleware(update, context))

        # Third request should be blocked
        self.assertFalse(await self.middleware.middleware(update, context))
        update.callback_query.answer.assert_called_once_with("You're sending requests too quickly. Please slow down.")

    @patch('bot_service.bot.middlewares.rate_limiter.RateLimitMiddleware')
    def test_setup_rate_limiter(self, MockRateLimitMiddleware):
        app = Application.builder().token("TEST_TOKEN").build()
        setup_rate_limiter(app, limit=5, window=60)
        
        # Check if RateLimitMiddleware was created with correct parameters
        MockRateLimitMiddleware.assert_called_once_with(limit=5, window=60)
        
        # Check if the rate limiter was added to the application handlers
        self.assertTrue(any(isinstance(handler, MessageHandler) for handler in app.handlers[-1]))

        rate_limit_handler = next(handler for handler in app.handlers[-1] if isinstance(handler, MessageHandler))
        self.assertTrue(callable(rate_limit_handler.callback))
        self.assertTrue(asyncio.iscoroutinefunction(rate_limit_handler.callback))
    async def test_different_users(self):
        user1_id = 111
        user2_id = 222

        self.assertTrue(await self.limiter.is_allowed(user1_id))
        self.assertTrue(await self.limiter.is_allowed(user1_id))
        self.assertFalse(await self.limiter.is_allowed(user1_id))

        # Different user should not be affected
        self.assertTrue(await self.limiter.is_allowed(user2_id))
        self.assertTrue(await self.limiter.is_allowed(user2_id))

if __name__ == '__main__':
    unittest.main()