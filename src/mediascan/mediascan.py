import os
import re
import shutil
from typing import List, Dict, Tuple
from pathlib import Path

from .config import Config
from .interpreter import Interpreter
from .logging import logger


class MediaScan:
    def __init__(
        self,
        input_dir: str,
        output_dir: str,
        action: str = "link",
        movies_dir: str = Config.MOVIES_DIR,
        tv_shows_dir: str = Config.TV_SHOWS_DIR,
        extensions: dict = Config.EXTENSIONS,
        movie_path: str = Config.MOVIE_PATH,
        movie_path_no_year: str = Config.MOVIE_PATH_NO_YEAR,
        episode_path: str = Config.EPISODE_PATH,
        episode_path_no_year: str = Config.EPISODE_PATH_NO_YEAR,
        dated_episode_path: str = Config.DATED_EPISODE_PATH,
        min_video_size: int = Config.MIN_VIDEO_SIZE,
        min_audio_size: int = Config.MIN_AUDIO_SIZE,
        delete_non_media: bool = Config.DELETE_NON_MEDIA,
        prefer_existing_folders: bool = False,
        clean: bool = Config.CLEAN,
    ):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.movies_path = self.output_dir / movies_dir
        self.tv_shows_path = self.output_dir / tv_shows_dir

        self.action = action

        self.extensions = extensions
        self.movie_path = movie_path
        self.movie_path_no_year = movie_path_no_year
        self.episode_path = episode_path
        self.episode_path_no_year = episode_path_no_year
        self.dated_episode_path = dated_episode_path
        self.min_video_size = min_video_size
        self.min_audio_size = min_audio_size
        self.delete_non_media = delete_non_media
        self.prefer_existing_folders = prefer_existing_folders
        self.clean = clean

        self.interpreter = Interpreter()

        if not self.input_dir.exists():
            raise FileNotFoundError(
                f"Input directory '{input_dir}' does not exist."
            )
        if not self.output_dir.exists():
            os.makedirs(self.output_dir, exist_ok=True)

        # Load existing years
        self.existing_tv_shows = {}
        if self.prefer_existing_folders:
            self.existing_tv_shows = self._get_existing_tv_show_folders()

    def scan(self):
        logger.info(f"Scanning directory: {self.input_dir}")

        for file_path in self._walk_directory(self.input_dir):
            if self._is_media_file(file_path):
                self._process_file(file_path)
            elif self.action == "move" and self.delete_non_media:
                logger.info(f"Deleting non-media file: {file_path}")
                os.remove(file_path)

        if self.clean:
            self._clean_empty_folders(self.input_dir)

    def process(self, file_path: Path) -> None:
        logger.info(f"Processing file: {file_path}")

        if self._is_media_file(file_path):
            self._process_file(file_path)
        elif self.action == "move" and self.delete_non_media:
            logger.info(f"Deleting non-media file: {file_path}")
            os.remove(file_path)

    def _walk_directory(self, directory: Path) -> List[Path]:
        for root, _, files in os.walk(directory):
            for file in files:
                yield Path(root) / file

    def _is_media_file(self, file_path: Path) -> bool:
        if not file_path.is_file():
            return False

        # Skip files with "sample" in the filename
        if "sample" in file_path.stem.lower():
            return False

        # Skip files smaller than the minimum size
        extension = file_path.suffix.lower()[1:]  # Remove the leading dot
        size = file_path.stat().st_size

        if (
            extension in self.extensions["video"]
            and size < self.min_video_size
        ):
            return False

        if (
            extension in self.extensions["audio"]
            and size < self.min_audio_size
        ):
            return False

        # Check if the file extension is known
        return (
            extension in self.extensions["video"]
            or extension in self.extensions["audio"]
        )

    def _process_file(self, file_path: Path):
        relative_path = file_path.relative_to(self.input_dir).as_posix()
        file_info = self.interpreter.interpret(relative_path)

        # Use existing folder?
        if self.prefer_existing_folders and not file_info["year"]:
            title_norm = file_info["title"].strip().lower()
            if title_norm in self.existing_tv_shows:
                title, year = self.existing_tv_shows[title_norm]
                if year > 1920:
                    file_info["title"] = title
                    file_info["year"] = year
                    print(f"Using existing year for {title}: {year}")
                    logger.debug(f"Using existing year for {title}: {year}")

        new_path = self._get_new_path(file_path, file_info)
        if new_path:
            self._perform_action(file_path, new_path)

    def _get_new_path(self, file_path: Path, file_info: dict) -> Path:
        new_path = None
        if file_info["date"] is not None:
            new_path = self._get_dated_media_path(file_path, file_info)
        elif file_info["episode"] is not None:
            new_path = self._get_tv_path(file_path, file_info)
        else:
            new_path = self._get_movie_path(file_path, file_info)

        logger.debug(f"New path for {file_path}: {new_path}")
        return new_path

    def _get_tv_path(self, file_path: Path, file_info: dict) -> Path:
        path = (
            self.episode_path
            if file_info["year"]
            else self.episode_path_no_year
        )
        return self.tv_shows_path / path.format(
            title=file_info["title"],
            year=file_info["year"] or "Unknown Year",
            season=f"{file_info['season']:02d}",
            episode=f"{file_info['episode']:02d}",
            quality=file_info["resolution"] or "Unknown",
            ext=file_path.suffix[1:],
        )

    def _get_dated_media_path(self, file_path: Path, file_info: dict) -> Path:
        date = file_info["date"]
        season = date[:4]  # Year
        return self.tv_shows_path / self.dated_episode_path.format(
            title=file_info["title"],
            year=file_info["year"] or "Unknown Year",
            season=season,
            date=date,
            quality=file_info["resolution"] or "Unknown",
            ext=file_path.suffix[1:],
        )

    def _get_movie_path(self, file_path: Path, file_info: dict) -> Path:
        path = (
            self.movie_path if file_info["year"] else self.movie_path_no_year
        )
        return self.movies_path / path.format(
            title=file_info["title"],
            year=file_info["year"] or "Unknown Year",
            quality=file_info["resolution"] or "Unknown",
            ext=file_path.suffix[1:],
        )

    def _get_existing_tv_show_folders(self) -> Dict[str, Tuple[str, int]]:
        """
        Scans the TV Shows directory and returns a dictionary mapping
        normalized show titles to their actual title and year.
        Assumes TV show folders are named in the format "Show Name (Year)".
        """
        existing_shows = {}
        tv_shows_dir = self.tv_shows_path

        if not tv_shows_dir.exists():
            logger.debug(f"TV Shows directory does not exist: {tv_shows_dir}")
            return existing_shows

        year_pattern = re.compile(r"^(?P<title>.+?)\s*\((?P<year>\d{4})\)$")

        for folder in tv_shows_dir.iterdir():
            if folder.is_dir():
                match = year_pattern.match(folder.name)
                if match:
                    title = match.group("title")
                    title_norm = title.strip().lower()
                    year = int(match.group("year"))
                    existing_shows[title_norm] = title, year
                    logger.debug(
                        f"Found existing TV show: '{title}' with year {year}"
                    )

        return existing_shows

    def _perform_action(self, source: Path, destination: Path, force=False):
        if destination.exists():
            if force and destination.is_file():
                logger.info(
                    f"Forcing overwrite of existing file {destination}"
                )
                os.remove(destination)
            else:
                logger.info(
                    f"Destination already exists: {destination}. Skipping."
                )
                return

        destination.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"{self.action}: {source} -> {destination}")

        if self.action == "symlink":
            self._create_symlink(source, destination)
        elif self.action == "link":
            self._create_hard_link(source, destination)
        elif self.action == "copy":
            shutil.copy2(source, destination)
        elif self.action == "move":
            shutil.move(source, destination)

    def _create_hard_link(self, source: Path, destination: Path):
        try:
            os.link(source, destination)
        except OSError:
            # If hard linking fails, fall back to copying
            shutil.copy2(source, destination)

    def _create_symlink(self, source: Path, destination: Path):
        try:
            os.symlink(source, destination)
        except OSError:
            # If linking fails, fall back to copying
            shutil.copy2(source, destination)

    def _clean_empty_folders(self, input_dir: Path):
        for root, dirs, files in os.walk(input_dir, topdown=False):
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                if not os.listdir(dir_path):
                    logger.info(f"Removing empty folder: {dir_path}")
                    os.rmdir(dir_path)
