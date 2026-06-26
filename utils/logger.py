# ============================================================
# utils/logger.py
# Centralized logging for the AI List Cleanup Assistant
# ============================================================
# All modules import this logger instead of using print().
# This means every message is timestamped, labeled by severity,
# and written to both the terminal AND a log file automatically.
# ============================================================

import logging
import os
from datetime import datetime

def get_logger(name: str) -> logging.Logger:
    """
    Creates and returns a logger for the given module name.

    Usage in any other file:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Processing started")
        logger.warning("Missing email found")
        logger.error("File could not be read")
    """

    # Create a logs/ directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Name the log file by today's date — one log file per day
    log_filename = f"logs/cleanup_{datetime.now().strftime('%Y-%m-%d')}.log"

    # Get or create a logger with the given name
    logger = logging.getLogger(name)

    # Only add handlers if this logger hasn't been set up yet
    # (prevents duplicate log entries if the function is called multiple times)
    if not logger.handlers:

        logger.setLevel(logging.DEBUG)

        # --- File Handler ---
        # Writes ALL messages (DEBUG and above) to the log file
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)

        # --- Console Handler ---
        # Writes INFO and above to the terminal (less noisy)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # --- Format ---
        # Example output:
        # 2024-01-15 10:23:45 | INFO     | email_cleaner | Processing 500 records
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
