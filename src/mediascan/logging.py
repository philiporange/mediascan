from loguru import logger
import sys

from .config import Config


def configure_logging(log_level=None):
    # Remove any existing handlers
    logger.remove()

    # Default logger
    logger.add(
        Config.LOG_PATH,
        level=log_level or Config.LOG_LEVEL,
        rotation=Config.LOG_ROTATION,
        retention=Config.LOG_RETENTION,
    )

    # Console output
    logger.add(
        sys.stderr,
        level=log_level or Config.LOG_LEVEL,
        format="<level>{level}: {message}</level>",
    )


configure_logging()
