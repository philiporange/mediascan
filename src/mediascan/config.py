import os

import dotenv
import appdirs


dotenv.load_dotenv()


# Default values
APP_NAME = "MediaScan"
MEDIA_PATH = os.path.expanduser("~/" + APP_NAME)
MOVIES_DIR = "Movies"
TV_SHOWS_DIR = "TV Shows"

CONFIG_DIR = appdirs.user_config_dir(APP_NAME)
LOG_DIR = appdirs.user_log_dir(APP_NAME)

QUIET_LOG_LEVEL = "ERROR"
VERBOSE_LOG_LEVEL = "DEBUG"
LOG_PATH = os.path.join(LOG_DIR, "MediaScan.log")
LOG_LEVEL = "INFO"
LOG_ROTATION = "1 week"
LOG_RETENTION = "1 month"

ACTION = "symlink"  # symlink, link, copy, move
MIN_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB
MIN_AUDIO_SIZE = 3 * 1024 * 1024  # 3 MB
MOVIE_PATH = "{title} ({year})/{title} ({year}) [{quality}].{ext}"
MOVIE_PATH_NO_YEAR = "{title}/{title} [{quality}].{ext}"
EPISODE_PATH = (
    "{title} ({year})/Season {season}/"
    "{title} ({year}) - S{season}E{episode} [{quality}].{ext}"
)
EPISODE_PATH_NO_YEAR = (
    "{title}/Season {season}/{title} - S{season}E{episode} [{quality}].{ext}"
)
DATED_EPISODE_PATH = (
    "{title} ({year})/Season {season}/{title} - {date} [{quality}].{ext}"
)
DELETE_NON_MEDIA = False
PREFER_EXISTING_FOLDERS = True
CLEAN = False

EXTENSIONS = {
    "video": [
        "avi",
        "mkv",
        "mp4",
        "m4v",
        "mov",
        "wmv",
        "flv",
        "webm",
        "vob",
    ],
    "audio": [
        "mp3",
        "flac",
        "m4a",
        "aac",
        "ogg",
        "wma",
        "wav",
        "m4b",
    ],
}


class Config:
    APP_NAME = "MediaScan"

    # General
    MEDIA_PATH = MEDIA_PATH
    MOVIES_DIR = MOVIES_DIR
    TV_SHOWS_DIR = TV_SHOWS_DIR
    EXTENSIONS = EXTENSIONS
    ACTION = ACTION
    MIN_AUDIO_SIZE = MIN_AUDIO_SIZE
    MIN_VIDEO_SIZE = MIN_VIDEO_SIZE
    MOVIE_PATH = MOVIE_PATH
    MOVIE_PATH_NO_YEAR = MOVIE_PATH_NO_YEAR
    EPISODE_PATH = EPISODE_PATH
    EPISODE_PATH_NO_YEAR = EPISODE_PATH_NO_YEAR
    DATED_EPISODE_PATH = DATED_EPISODE_PATH
    DELETE_NON_MEDIA = DELETE_NON_MEDIA
    PREFER_EXISTING_FOLDERS = PREFER_EXISTING_FOLDERS
    CLEAN = CLEAN

    # Logging
    QUIET_LOG_LEVEL = QUIET_LOG_LEVEL
    VERBOSE_LOG_LEVEL = VERBOSE_LOG_LEVEL
    LOG_PATH = LOG_PATH
    LOG_LEVEL = LOG_LEVEL
    LOG_ROTATION = LOG_ROTATION
    LOG_RETENTION = LOG_RETENTION
