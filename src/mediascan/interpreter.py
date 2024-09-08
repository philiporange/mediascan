import re
from typing import Dict, Optional, Tuple, List
from datetime import datetime

from .tmdb import TMDbAPI


class Interpreter:
    def __init__(self, tmdb_api_key: str = None):
        self.year_pattern = re.compile(r"\b(19\d{2}|20\d{2})\b")
        self.year_in_parentheses_pattern = re.compile(
            r"\((" + self.year_pattern.pattern + r")\)"
        )
        self.episode_pattern = re.compile(
            r"S(\d{1,4})E(\d{1,3})|(\d{1,2})x(\d{1,3})", re.IGNORECASE
        )
        self.season_pattern = re.compile(
            r"\b(?:S(?:eason)?\s?(\d{1,2}))\b|\(Season\s?(\d{1,2})\)",
            re.IGNORECASE,
        )
        self.date_pattern = re.compile(r"(\d{4})[-\.\s](\d{2})[-\.\s](\d{2})")
        self.square_brackets_pattern = re.compile(r"\[.*?\]")
        self.proper_repack_pattern = re.compile(r"\b(PROPER|REPACK)\b")

        self.audio_codecs = [
            "MP3",
            "AAC",
            "AC3",
            "DTS",
            "FLAC",
            "OGG",
            "Vorbis",
            "WMA",
            "PCM",
            "LPCM",
            "DDP?5\\.1",
            "Atmos",
        ]
        self.video_codecs = [
            "XviD",
            "x264",
            "x265",
            "HEVC",
            "AVC",
            "MPEG-[24]",
            "DivX",
            "VP[89]",
            "AV1",
        ]
        self.resolutions = [
            "4320p",
            "2160p",
            "1080p",
            "720p",
            "480p",
            "360p",
            "240p",
            "8K",
            "4K",
            "1080i",
            "720i",
            "576p",
            "576i",
            "480i",
        ]

        self.bluray_sources = ["BluRay", "Blu-Ray", "BDRip", "BRRip"]
        self.dvd_sources = ["DVDRip", "HDDVD", "DVDScr"]
        self.web_sources = ["WebRip", "WEB-DL", "WEBCap", "HDRip"]
        self.tv_sources = ["HDTV", "PDTV", "SDTV"]
        self.cam_sources = [
            "CAM",
            "HDCam",
            "TS",
            "TC",
            "HDTS",
            "TELESYNC",
            "Screener",
            "VODRip",
        ]

        self.languages = [
            "English",
            "French",
            "German",
            "Spanish",
            "Portuguese",
            "Korean",
            "Japanese",
            "Polish",
            "Italian",
            "Hungarian",
            "Russian",
            "Chinese",
            "Mandarin",
            "Pashto",
            "Thai",
            "Indonesian",
            "Arabic",
            "Hindi",
            "Turkish",
            "Dutch",
            "Vietnamese",
            "Swedish",
        ]

        self.audio_codec_pattern = re.compile(
            r"\b(" + "|".join(self.audio_codecs) + r")\b", re.IGNORECASE
        )
        self.video_codec_pattern = re.compile(
            r"\b(" + "|".join(self.video_codecs) + r")\b", re.IGNORECASE
        )
        self.resolution_pattern = re.compile(
            r"\b(" + "|".join(self.resolutions) + r")\b", re.IGNORECASE
        )
        self.source_pattern = re.compile(
            r"\b("
            + "|".join(
                self.bluray_sources
                + self.dvd_sources
                + self.web_sources
                + self.tv_sources
                + self.cam_sources
            )
            + r")\b",
            re.IGNORECASE,
        )
        self.language_pattern = re.compile(
            r"\b(" + "|".join(self.languages) + r")\b", re.IGNORECASE
        )

        self.tmdb = TMDbAPI(api_key=tmdb_api_key) if tmdb_api_key else None

    def remove_square_brackets(self, name: str) -> str:
        return self.square_brackets_pattern.sub("", name)

    def determine_delimiter(
        self, name: str, delimiters: List[str] = [" ", ".", "_"]
    ) -> str:
        counts = {delimiter: name.count(delimiter) for delimiter in delimiters}
        return max(counts, key=counts.get)

    def find_longest_matching_title(self, name: str) -> Optional[str]:
        assert self.tmdb, "TMDb is required to find the longest matching title"

        name = self.remove_square_brackets(name)
        delimiter = self.determine_delimiter(name)
        name_parts = name.split(delimiter)

        longest_matching_title = None
        for i in range(len(name_parts), 0, -1):
            title = delimiter.join(name_parts[:i])
            if self.tmdb.search(title):
                longest_matching_title = title
                break

        return longest_matching_title

    def find_year(self, name: str) -> Optional[str]:
        # Years in parentheses are unambiguous
        year_matches = list(self.year_in_parentheses_pattern.finditer(name))
        if year_matches:
            return year_matches[-1].group(1)

        # Find all year matches, and check if they are part of a date match
        year_matches = list(self.year_pattern.finditer(name))
        date_matches = list(self.date_pattern.finditer(name))
        year_match = None
        # Iterate through year matches in reverse order
        for match in reversed(year_matches):
            # Check if the year match is not part of a date match
            if not any(
                date_match.start() <= match.start() <= date_match.end()
                for date_match in date_matches
            ):
                year_match = match
                break
        # Return the year if found, otherwise return None
        return year_match.group(1) if year_match else None

    def find_episode(self, name: str) -> Tuple[Optional[int], Optional[int]]:
        episode_match = self.episode_pattern.search(name)
        if episode_match:
            groups = episode_match.groups()
            if groups[0] and groups[1]:  # SxxExx format
                return int(groups[0]), int(groups[1])
            elif groups[2] and groups[3]:  # xxxyy format
                return int(groups[2]), int(groups[3])
        return None, None

    def find_season(self, name: str) -> Optional[int]:
        season_match = self.season_pattern.search(name)
        if season_match:
            return int(next(group for group in season_match.groups() if group))
        return None

    def find_date(self, name: str) -> Tuple[Optional[str], Optional[str]]:
        date_match = self.date_pattern.search(name)
        if date_match:
            year, month, day = date_match.groups()
            try:
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime("%Y-%m-%d"), date_match.group()
            except ValueError:
                return None, None
        return None, None

    def find_audio_codec(self, name: str) -> Optional[str]:
        audio_match = self.audio_codec_pattern.search(name)
        return audio_match.group() if audio_match else None

    def find_video_codec(self, name: str) -> Optional[str]:
        video_match = self.video_codec_pattern.search(name)
        return video_match.group() if video_match else None

    def find_resolution(self, name: str) -> Optional[str]:
        resolution_match = self.resolution_pattern.search(name)
        return resolution_match.group() if resolution_match else None

    def find_source(self, name: str) -> Optional[str]:
        source_match = self.source_pattern.search(name)
        if source_match:
            source = source_match.group().lower()
            if any(x.lower() in source for x in self.bluray_sources):
                return "bluray"
            elif any(x.lower() in source for x in self.dvd_sources):
                return "dvd"
            elif any(x.lower() in source for x in self.web_sources):
                return "web"
            elif any(x.lower() in source for x in self.tv_sources):
                return "tv"
            elif any(x.lower() in source for x in self.cam_sources):
                return "cam"
        return None

    def find_language(self, name: str) -> Optional[str]:
        language_match = self.language_pattern.search(name)
        return language_match.group() if language_match else None

    def is_proper_or_repack(self, name: str) -> bool:
        return bool(self.proper_repack_pattern.search(name))

    def clean_title(self, title: str) -> str:
        # Remove everything after the last letter, number, ! or ?
        cleaned_title = re.sub(r"[^a-zA-Z0-9!?]+$", "", title)
        return cleaned_title.strip()

    def interpret(
        self, name: str, match_title: bool = False
    ) -> Dict[str, Optional[str]]:
        clean_name = self.remove_square_brackets(name)
        delimiter = self.determine_delimiter(clean_name)

        year = self.find_year(clean_name)
        season, episode = self.find_episode(clean_name)
        if season is None:
            season = self.find_season(clean_name)
        standardized_date, original_date = self.find_date(clean_name)

        # Find all metadata tokens
        metadata_tokens = [
            (self.find_source(clean_name), self.source_pattern),
            (self.find_language(clean_name), self.language_pattern),
            (self.find_resolution(clean_name), self.resolution_pattern),
            (self.find_audio_codec(clean_name), self.audio_codec_pattern),
            (self.find_video_codec(clean_name), self.video_codec_pattern),
        ]

        # Find the earliest occurrence of any metadata token
        title_end = len(clean_name)
        for token, pattern in metadata_tokens:
            if token:
                match = pattern.search(clean_name)
                if match and match.start() < title_end:
                    title_end = match.start()

        # Consider year, season, episode, and date as well
        identifiers = [
            (
                year,
                (
                    clean_name.index(f"({year})")
                    if year and f"({year})" in clean_name
                    else clean_name.index(year) if year else float("inf")
                ),
            ),
            (
                episode,
                (
                    clean_name.index(f"S{season:02d}E{episode:02d}")
                    if season and episode
                    else float("inf")
                ),
            ),
            (
                (
                    season,
                    (
                        clean_name.index(f"S{season:02d}")
                        if season and f"S{season:02d}" in clean_name
                        else (
                            clean_name.index(f"Season {season}")
                            if season and f"Season {season}" in clean_name
                            else (
                                clean_name.index(f"(Season {season})")
                                if season
                                and f"(Season {season})" in clean_name
                                else float("inf")
                            )
                        )
                    ),
                )
                if season
                else (None, float("inf"))
            ),
            (
                standardized_date,
                (
                    clean_name.index(original_date)
                    if original_date
                    else float("inf")
                ),
            ),
        ]

        title_end = min(
            title_end,
            min(
                (idx for _, idx in identifiers if idx != float("inf")),
                default=len(clean_name),
            ),
        )
        title = clean_name[:title_end].strip()

        title = re.sub(r"\s*\([^)]*\)\s*$", "", title)
        title = re.sub(r"^\s*\(|\)\s*$", "", title)

        if delimiter != " ":
            title = title.replace(delimiter, " ")

        if year and title.endswith(year):
            title = title[: -len(year)].strip()
        elif standardized_date and title.endswith(original_date):
            title = title[: -len(original_date)].strip()

        # Clean up the end of the title
        title = self.clean_title(title)

        is_known = False
        if match_title:
            assert self.tmdb, "tmdb is required to match title"
            is_known = self.tmdb.match(title)

        return {
            "title": title,
            "known": is_known,
            "year": year,
            "episode": episode,
            "season": season,
            "date": standardized_date,
            "delimiter": delimiter,
            "audio_codec": self.find_audio_codec(clean_name),
            "video_codec": self.find_video_codec(clean_name),
            "resolution": self.find_resolution(clean_name),
            "source": self.find_source(clean_name),
            "language": self.find_language(clean_name),
            "is_proper": self.is_proper_or_repack(clean_name),
        }
