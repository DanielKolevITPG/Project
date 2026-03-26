import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_FILE = os.path.join(BASE_DIR, "commands.log")


def setup_logger(name: str = "football_manager") -> logging.Logger:
    """Setup and return a logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        logger.addHandler(handler)
    return logger


def log_command(
    raw_input: str,
    intent: Optional[str],
    params: Optional[Dict[str, Any]],
    result: str
) -> None:
    """
    Log a command to commands.log with timestamp, input, intent, params, and result.

    Args:
        raw_input: Raw user input
        intent: Detected intent name
        params: Extracted parameters (will be truncated for brevity)
        result: Result message (OK or ERROR + message)
    """
    logger = setup_logger()
    
    # Truncate params for brevity
    params_str = ""
    if params:
        short_params = {k: str(v)[:30] for k, v in params.items()}
        params_str = f" | PARAMS: {short_params}"
    
    # Determine result status
    if result.startswith("Успех") or "успешно" in result.lower():
        status = "OK"
    elif "грешка" in result.lower() or "error" in result.lower():
        status = "ERROR"
    else:
        status = "OK"
    
    log_entry = f"INPUT: {raw_input} | INTENT: {intent or 'none'}{params_str} | RESULT: {status} | MESSAGE: {result}"
    logger.info(log_entry)


def log_error(raw_input: str, error_message: str) -> None:
    """Log an error with the raw input."""
    logger = setup_logger()
    logger.error(f"INPUT: {raw_input} | ERROR: {error_message}")
