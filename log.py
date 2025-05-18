import logging
from functools import wraps
from typing import Callable

import colorlog


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # Configure the logger with its own handler to prevent duplication
    if not logger.handlers:
        handler = colorlog.StreamHandler()
        formatter = colorlog.ColoredFormatter(
            f"%(log_color)s%(asctime)s %(levelname)-8s%(reset)s %(thin_white)s%(name)s%(reset)s - %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors={},
            style="%",
        )
        handler.setFormatter(formatter)
        logger.handlers = [handler]
    logger.propagate = False
    return logger


def add_logger(base_logger: logging.Logger) -> Callable:
    def decorator(func: Callable) -> Callable:
        logger_name = f"{base_logger.name}.{func.__name__}"
        new_logger = logging.getLogger(logger_name)

        # Copy configuration from base_logger
        new_logger.setLevel(base_logger.level)
        for handler in base_logger.handlers:
            new_logger.addHandler(handler)
        new_logger.propagate = base_logger.propagate

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Attach the logger to the function
        wrapper.logger = new_logger
        return wrapper

    return decorator
