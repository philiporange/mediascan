import os

import dotenv
import appdirs


dotenv.load_dotenv()


# Default values
APP_NAME = "MediaScan"
MEDIA_PATH = os.path.expanduser("~/" + APP_NAME)
MOVIES_DIR = "Movies"
TV_SHOWS_DIR = "TV Shows"
MUSIC_DIR = "Music"

CONFIG_DIR = appdirs.user_config_dir(APP_NAME)
CACHE_DIR = appdirs.user_cache_dir(APP_NAME)
LOG_DIR = appdirs.user_log_dir(APP_NAME)

DB_PATH = os.path.join(CACHE_DIR, "MediaScan.db")
KV_PATH = os.path.join(CACHE_DIR, "MediaScan.kv")

LOG_PATH = os.path.join(LOG_DIR, "MediaScan.log")
LOG_LEVEL = "INFO"
LOG_ROTATION = "1 week"
LOG_RETENTION = "1 month"

ACTION = "link"  # link, copy, move
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
SONG_PATH = "{artist}/{album}/{track} - {title}.{ext}"
DELETE_NON_MEDIA = False

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
    MUSIC_DIR = MUSIC_DIR
    EXTENSIONS = EXTENSIONS
    ACTION = ACTION
    MIN_AUDIO_SIZE = MIN_AUDIO_SIZE
    MIN_VIDEO_SIZE = MIN_VIDEO_SIZE
    MOVIE_PATH = MOVIE_PATH
    MOVIE_PATH_NO_YEAR = MOVIE_PATH_NO_YEAR
    EPISODE_PATH = EPISODE_PATH
    EPISODE_PATH_NO_YEAR = EPISODE_PATH_NO_YEAR
    DATED_EPISODE_PATH = DATED_EPISODE_PATH
    SONG_PATH = SONG_PATH
    DELETE_NON_MEDIA = DELETE_NON_MEDIA

    # Database
    DB_PATH = DB_PATH
    KV_PATH = KV_PATH

    # Logging
    LOG_PATH = LOG_PATH
    LOG_LEVEL = LOG_LEVEL
    LOG_ROTATION = LOG_ROTATION
    LOG_RETENTION = LOG_RETENTION

    # TMDb
    TMDB_API_KEY = os.getenv("TMDB_API_KEY")
    TMDB_BASE_URL = "https://api.themoviedb.org/3"
    TMDB_DUMP_URL_TEMPLATE = (
        "http://files.tmdb.org/p/exports/{}_ids_{}.json.gz"
    )
    TMDB_IMAGE_URL_PREFIX = "https://image.tmdb.org/t/p/w500"
    TMDB_INDEX_PATH = "index.db"
    TMDB_CACHE_EXPIRATION = 24 * 3600  # 1 day
    TMDB_RATE_LIMIT = 20  # requests per second
    TMDB_RATE_LIMIT_WINDOW = 1  # second
    TMDB_MAX_RETRIES = 3
    TMDB_RETRY_DELAY = 10  # seconds
    TMDB_TMP_DIR = "/tmp/tmdb"
