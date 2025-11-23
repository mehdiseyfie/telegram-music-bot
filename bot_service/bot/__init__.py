#__init__.py
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, InlineQueryHandler, ChosenInlineResultHandler, filters
from .handlers import start, search, playlist
from .middlewares.rate_limiter import setup_rate_limiter
from config import TELEGRAM_BOT_TOKEN
import logging
import asyncio

logger = logging.getLogger(__name__)

def create_application() -> Application:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Initialize the application
    asyncio.get_event_loop().run_until_complete(application.initialize())
    
    # Setup rate limiter
    setup_rate_limiter(application, limit=30, window=60, cooldown_time=120)  # 5 messages per 60 seconds
    
    # Add handlers
    application.add_handler(CommandHandler("start", start.start_command))
    application.add_handler(CommandHandler("menu", start.show_main_menu))
    application.add_handler(CommandHandler("genre", search.genre_command))
    application.add_handler(CommandHandler("mood", search.mood_command))
    application.add_handler(CommandHandler("artist", search.artist_command))
    application.add_handler(CommandHandler("song", search.song_command))
    application.add_handler(CommandHandler("language", start.language_command))
    application.add_handler(CallbackQueryHandler(start.button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start.handle_message))
    application.add_handler(InlineQueryHandler(search.inline_search))
    application.add_handler(ChosenInlineResultHandler(playlist.create_playlist_from_inline))
    application.add_handler(InlineQueryHandler(start.handle_genre_search))
    
    return application