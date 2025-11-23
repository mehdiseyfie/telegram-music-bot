import logging
from bot_service.bot import create_application
from logging_config import setup_logging
from bot_service.bot.middlewares.rate_limiter import setup_rate_limiter
from config import SERVER_PORT

def main():
    # Configure logging
    setup_logging()
    
    logger = setup_logging(logstash_host='localhost', logstash_port=5000)
    logger.info("Starting bot...")

    # Create the bot application
    application = create_application()

    # Setup rate limiter
    setup_rate_limiter(application, limit=30, window=60, cooldown_time=120)
    
    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()