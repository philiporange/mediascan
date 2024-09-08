from loguru import logger

from .config import Config


PATH = Config.LOG_PATH
LEVEL = Config.LOG_LEVEL
ROTATION = Config.LOG_ROTATION
RETENTION = Config.LOG_RETENTION


logger.add(
    PATH,
    level=LEVEL,
    rotation=ROTATION,
    retention=RETENTION,
)
