import logging
from logstash_async.handler import AsynchronousLogstashHandler
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import os

_logger = None

def setup_logging(log_dir='logs', logstash_host='localhost', logstash_port=5000):
    global _logger
    if _logger is not None:
        return _logger

    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Create a custom formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove all existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler for general logs
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'bot.log'),
        maxBytes=50*1024*1024,  # 50MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # File handler for error logs
    error_file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        when='midnight',
        interval=1,
        backupCount=30
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    root_logger.addHandler(error_file_handler)

    # Logstash handler
    try:
        logstash_handler = AsynchronousLogstashHandler(
            host=logstash_host,
            port=logstash_port,
            database_path=os.path.join(log_dir, 'logstash_queue.db')
        )
        logstash_handler.setFormatter(formatter)
        root_logger.addHandler(logstash_handler)
    except Exception as e:
        root_logger.error(f"Failed to initialize Logstash handler: {e}")

    _logger = root_logger
    return _logger

def get_logger():
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger