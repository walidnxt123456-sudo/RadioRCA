import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Centralized Constants
LOG_FILE = "radiorca.log"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3  # Keep 3 old logs (radiorca.log.1, .2, .3)
DEFAULT_LEVEL = logging.DEBUG

def get_logger(name="RadioRCA"):
    """
    Configures and returns a singleton logger instance.
    Ensures handlers are only added once to prevent duplicate output in Streamlit.
    """
    logger = logging.getLogger(name)
    
    # Only configure if handlers don't already exist
    if not logger.handlers:
        logger.setLevel(DEFAULT_LEVEL)
        
        # Formatter: Timestamp | Level | Source Module | Message
        # The %(module)s flag helps identify if logs come from app.py or geospatial.py
        formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(module)s | %(message)s')
        
        # 1. Rotating File Handler: Manages disk space automatically
        try:
            file_handler = RotatingFileHandler(
                LOG_FILE, 
                maxBytes=MAX_LOG_SIZE, 
                backupCount=BACKUP_COUNT
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Fallback to standard print if file system is read-only or inaccessible
            print(f"Critical Error: Could not initialize FileHandler: {e}")

        # 2. Console Handler: Directs logs to the terminal (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Initial heartbeat to confirm logger is active
        logger.info("--- RadioRCA Logger Initialized ---")
    
    return logger
    
# Create the singleton instance to be imported by all other modules
log = get_logger()