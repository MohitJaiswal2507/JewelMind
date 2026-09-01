"""
Centralized Application Logging Configuration
"""

import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """
    Configures standard structured application logging based on environment settings.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Custom format including timestamp, level, logger name, and message
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Reset existing handlers to prevent duplication
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
    handler.setFormatter(formatter)
    
    # Avoid duplicate handlers on reloads
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers = [handler]
        
    logger = logging.getLogger("jewelmind")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
