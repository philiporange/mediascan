"""
Enhanced media filename interpreter using multiple parsing libraries.

This module provides comprehensive media filename parsing by combining:
- guessit: Advanced pattern matching with extensive rule sets
- PTN (parse-torrent-title): Specialized torrent filename parsing
- regex: Custom fallback patterns for edge cases

The interpreter intelligently merges results from multiple parsers,
preferring more confident and specific matches.
"""

import re
from typing import Dict, Optional, Tuple, List, Union
from datetime import datetime

import guessit
import PTN


class Interpreter:
    def __init__(self):
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
            "MPEG-2",
            "MPEG-4",
            "DivX",
            "VP8",
            "VP9",
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
        self.extensions = [
            "mp4",
            "mkv",
            "avi",
        ]

        self.audio_codec_pattern = re.compile(
            r"\b(" + "|".join(self.audio_codecs) + r")\b", re.IGNORECASE
        )
        # Escape special regex characters in codec names
        escaped_video_codecs = [
            re.escape(codec) for codec in self.video_codecs
        ]
        self.video_codec_pattern = re.compile(
            r"\b(" + "|".join(escaped_video_codecs) + r")\b", re.IGNORECASE
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

    def remove_square_brackets(self, name: str) -> str:
        return self.square_brackets_pattern.sub("", name)

    def determine_delimiter(
        self, name: str, delimiters: List[str] = [" ", ".", "_"]
    ) -> str:
        counts = {delimiter: name.count(delimiter) for delimiter in delimiters}
        return max(counts, key=counts.get)

    def find_year(self, name: str) -> Dict[str, Optional[Union[int, str]]]:
        current_year = datetime.now().year
        # Years in parentheses are unambiguous
        year_matches = list(self.year_in_parentheses_pattern.finditer(name))
        if year_matches:
            match = year_matches[-1]  # Get the last match
            year = int(match.group(1))
            if 1895 <= year <= current_year + 1:
                return {
                    "value": year,
                    "raw": match.group(0),
                    "index": match.start(),
                }

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
                year = int(match.group(1))
                if 1895 <= year <= current_year + 1:
                    year_match = match
                    break

        # Return the year, raw token, and index, if found
        return {
            "value": int(year_match.group(1)) if year_match else None,
            "raw": year_match.group(0) if year_match else None,
            "index": year_match.start() if year_match else None,
        }

    def find_episode(
        self, name: str
    ) -> Dict[str, Optional[Union[Tuple[int, int], str, int]]]:
        episode_match = self.episode_pattern.search(name)
        if episode_match:
            groups = episode_match.groups()
            if groups[0] and groups[1]:  # SxxExx format
                return {
                    "value": (int(groups[0]), int(groups[1])),
                    "raw": episode_match.group(),
                    "index": episode_match.start(),
                }
            elif groups[2] and groups[3]:  # xxxyy format
                return {
                    "value": (int(groups[2]), int(groups[3])),
                    "raw": episode_match.group(),
                    "index": episode_match.start(),
                }
        return {"value": None, "raw": None, "index": None}

    def find_season(self, name: str) -> Dict[str, Optional[Union[int, str]]]:
        season_match = self.season_pattern.search(name)
        if season_match:
            return {
                "value": int(
                    next(group for group in season_match.groups() if group)
                ),
                "raw": season_match.group(),
                "index": season_match.start(),
            }
        return {"value": None, "raw": None, "index": None}

    def find_date(self, name: str) -> Dict[str, Optional[Union[str, int]]]:
        date_match = self.date_pattern.search(name)
        if date_match:
            year, month, day = date_match.groups()
            try:
                date_obj = datetime(int(year), int(month), int(day))
                return {
                    "value": date_obj.strftime("%Y-%m-%d"),
                    "raw": date_match.group(),
                    "index": date_match.start(),
                }
            except ValueError:
                return {"value": None, "raw": None, "index": None}
        return {"value": None, "raw": None, "index": None}

    def find_audio_codec(
        self, name: str
    ) -> Dict[str, Optional[Union[str, int]]]:
        audio_match = self.audio_codec_pattern.search(name)
        if audio_match:
            return {
                "value": audio_match.group(),
                "raw": audio_match.group(),
                "index": audio_match.start(),
            }
        return {"value": None, "raw": None, "index": None}

    def find_video_codec(
        self, name: str
    ) -> Dict[str, Optional[Union[str, int]]]:
        video_match = self.video_codec_pattern.search(name)
        if video_match:
            return {
                "value": video_match.group(),
                "raw": video_match.group(),
                "index": video_match.start(),
            }
        return {"value": None, "raw": None, "index": None}

    def find_resolution(
        self, name: str
    ) -> Dict[str, Optional[Union[str, int]]]:
        resolution_match = self.resolution_pattern.search(name)
        if resolution_match:
            return {
                "value": resolution_match.group(),
                "raw": resolution_match.group(),
                "index": resolution_match.start(),
            }
        return {"value": None, "raw": None, "index": None}

    def find_source(self, name: str) -> Dict[str, Optional[Union[str, int]]]:
        source_match = self.source_pattern.search(name)
        if source_match:
            source = source_match.group().lower()
            if any(x.lower() in source for x in self.bluray_sources):
                value = "bluray"
            elif any(x.lower() in source for x in self.dvd_sources):
                value = "dvd"
            elif any(x.lower() in source for x in self.web_sources):
                value = "web"
            elif any(x.lower() in source for x in self.tv_sources):
                value = "tv"
            elif any(x.lower() in source for x in self.cam_sources):
                value = "cam"
            else:
                value = source
            return {
                "value": value,
                "raw": source_match.group(),
                "index": source_match.start(),
            }
        return {"value": None, "raw": None, "index": None}

    def find_language(self, name: str) -> Dict[str, Optional[Union[str, int]]]:
        language_match = self.language_pattern.search(name)
        if language_match:
            return {
                "value": language_match.group(),
                "raw": language_match.group(),
                "index": language_match.start(),
            }
        return {"value": None, "raw": None, "index": None}

    def is_proper_or_repack(
        self, name: str
    ) -> Dict[str, Optional[Union[bool, str, int]]]:
        proper_repack_match = self.proper_repack_pattern.search(name)
        if proper_repack_match:
            return {
                "value": True,
                "raw": proper_repack_match.group(),
                "index": proper_repack_match.start(),
            }
        return {"value": False, "raw": None, "index": None}

    def split_extension(self, name: str) -> Tuple[str, str]:
        parts = name.rsplit(".", 1)
        if len(parts) == 1 or parts[1] not in self.extensions:
            return parts[0], ""

        return parts[0], parts[1]

    def clean_title(self, title: str) -> str:
        # Remove everything after the last letter, number, ! or ?
        cleaned_title = re.sub(r"[^a-zA-Z0-9!?]+$", "", title)
        return cleaned_title.strip()

    def _parse_with_guessit(self, name: str) -> Dict:
        """Parse filename using guessit library."""
        try:
            result = guessit.guessit(name)

            # Convert guessit result to our format
            parsed = {
                "title": str(result.get("title", "")),
                "year": result.get("year"),
                "season": result.get("season"),
                "episode": result.get("episode"),
                "episode_title": result.get("episode_title"),
                "date": None,
                "resolution": None,
                "source": None,
                "video_codec": None,
                "audio_codec": None,
                "language": None,
                "type": "tv" if result.get("type") == "episode" else "movie",
                "is_proper": result.get("other") in (["Proper"], ["Repack"]) if result.get("other") else False,
            }

            # Handle date
            if result.get("date"):
                parsed["date"] = result.get("date").strftime("%Y-%m-%d")

            # Handle resolution
            if result.get("screen_size"):
                parsed["resolution"] = str(result.get("screen_size"))

            # Handle source
            if result.get("source"):
                source = str(result.get("source")).lower()
                if "blu-ray" in source or "bluray" in source:
                    parsed["source"] = "bluray"
                elif "dvd" in source:
                    parsed["source"] = "dvd"
                elif "web" in source:
                    parsed["source"] = "web"
                elif "hdtv" in source or "tv" in source:
                    parsed["source"] = "tv"
                else:
                    parsed["source"] = source

            # Handle video codec
            if result.get("video_codec"):
                parsed["video_codec"] = str(result.get("video_codec"))

            # Handle audio codec
            if result.get("audio_codec"):
                parsed["audio_codec"] = str(result.get("audio_codec"))

            # Handle language
            if result.get("language"):
                lang = result.get("language")
                if hasattr(lang, "alpha3"):
                    parsed["language"] = lang.alpha3
                else:
                    parsed["language"] = str(lang)

            return parsed
        except Exception:
            return {}

    def _parse_with_ptn(self, name: str) -> Dict:
        """Parse filename using PTN (parse-torrent-title) library."""
        try:
            result = PTN.parse(name)

            # Convert PTN result to our format
            parsed = {
                "title": result.get("title", ""),
                "year": result.get("year"),
                "season": result.get("season"),
                "episode": result.get("episode"),
                "date": None,
                "resolution": result.get("resolution"),
                "source": None,
                "video_codec": result.get("codec"),
                "audio_codec": result.get("audio"),
                "language": result.get("language"),
                "type": "tv" if result.get("season") or result.get("episode") else "movie",
                "is_proper": result.get("proper", False) or result.get("repack", False),
            }

            # Handle quality/source
            if result.get("quality"):
                quality = result.get("quality").lower()
                if "blu-ray" in quality or "bluray" in quality or "bdrip" in quality or "brrip" in quality:
                    parsed["source"] = "bluray"
                elif "dvd" in quality:
                    parsed["source"] = "dvd"
                elif "web" in quality:
                    parsed["source"] = "web"
                elif "hdtv" in quality or "pdtv" in quality:
                    parsed["source"] = "tv"
                else:
                    parsed["source"] = quality

            return parsed
        except Exception:
            return {}

    def _parse_with_regex(self, name: str) -> Dict:
        """Parse filename using custom regex patterns (original implementation)."""
        # Handle filenames
        name, extension = self.split_extension(name)

        # Cleaning
        name = self.remove_square_brackets(name)

        # Find the delimiter
        delimiter = self.determine_delimiter(name)

        # Match the metadata tokens. These all appear at the end of the name
        source_match = self.find_source(name)
        language_match = self.find_language(name)
        resolution_match = self.find_resolution(name)
        audio_codec_match = self.find_audio_codec(name)
        video_codec_match = self.find_video_codec(name)
        proper_repack_match = self.is_proper_or_repack(name)
        metadata_matches = [
            source_match,
            language_match,
            resolution_match,
            audio_codec_match,
            video_codec_match,
            proper_repack_match,
        ]

        # Strip the metadata tokens from the name
        earliest_match = None
        for match in metadata_matches:
            if match["value"]:
                if (
                    earliest_match is None
                    or match["index"] < earliest_match["index"]
                ):
                    earliest_match = match

        if earliest_match:
            start_token = earliest_match["index"]
            name = name[:start_token].strip()

        # Find the season, episode and/or date
        episode_match = self.find_episode(name)
        season_match = self.find_season(name)
        date_match = self.find_date(name)

        # Is it a movie or a TV show?
        media_type = "tv"
        season_no = None
        episode_no = None
        title_before = len(name)

        if episode_match["value"] is not None:
            season_no, episode_no = episode_match["value"]
            title_before = episode_match["index"]
        elif season_match["value"] is not None:
            season_no = season_match["value"]
            title_before = season_match["index"]
        elif date_match["value"] is not None:
            title_before = date_match["index"]
        else:
            media_type = "movie"

        # Remove any episode/season/date tokens from the title
        name = name[:title_before].strip()

        # Find the year
        year_match = self.find_year(name)
        if year_match:
            name = name[: year_match["index"]].strip()

        # Title is everything before the year
        title = name

        # Clean up the title
        title = re.sub(r"\s*\([^)]*\)\s*$", "", title)
        title = re.sub(r"^\s*\(|\)\s*$", "", title)

        # Remove the delimiters
        if delimiter != " ":
            title = title.replace(delimiter, " ")

        # Clean up the end of the title
        title = self.clean_title(title)

        return {
            "type": media_type,
            "title": title,
            "year": year_match["value"],
            "episode": episode_no,
            "season": season_no,
            "date": date_match["value"],
            "delimiter": delimiter,
            "audio_codec": audio_codec_match["value"],
            "video_codec": video_codec_match["value"],
            "resolution": resolution_match["value"],
            "source": source_match["value"],
            "language": language_match["value"],
            "is_proper": proper_repack_match["value"],
        }

    def _merge_results(self, guessit_result: Dict, ptn_result: Dict, regex_result: Dict) -> Dict:
        """
        Intelligently merge results from multiple parsers.

        Priority:
        1. guessit (most comprehensive and accurate)
        2. PTN (good for torrent-style filenames)
        3. regex (custom fallback patterns)

        For each field, prefer non-None values from higher priority parsers.
        """
        merged = {}

        # Define field priority: which parser is best for each field
        field_priority = {
            "title": ["regex", "guessit", "ptn"],  # Prefer regex (more conservative, keeps country codes)
            "year": ["regex", "guessit", "ptn"],  # Prefer regex for year (better date handling)
            "season": ["regex", "guessit", "ptn"],  # Prefer regex (fewer false positives)
            "episode": ["regex", "guessit", "ptn"],  # Prefer regex (fewer false positives)
            "date": ["regex", "guessit", "ptn"],  # Prefer regex for date parsing
            "resolution": ["guessit", "ptn", "regex"],
            "source": ["guessit", "ptn", "regex"],
            "video_codec": ["regex", "ptn", "guessit"],  # Prefer regex (preserves original notation)
            "audio_codec": ["regex", "ptn", "guessit"],  # Prefer regex (preserves original notation)
            "language": ["ptn", "guessit", "regex"],
            "type": ["regex", "guessit", "ptn"],  # Prefer regex (more conservative)
            "is_proper": ["ptn", "regex", "guessit"],
        }

        parsers = {
            "guessit": guessit_result,
            "ptn": ptn_result,
            "regex": regex_result,
        }

        # Merge each field based on priority
        for field, priority in field_priority.items():
            for parser_name in priority:
                value = parsers[parser_name].get(field)
                if value is not None and value != "" and value is not False:
                    merged[field] = value
                    break
            else:
                # If no parser found a value, use None
                merged[field] = None

        # Special case: If there's a date, don't use year from guessit (it's part of the date)
        if merged.get("date") and merged.get("year"):
            # Check if year is from the date
            date_year = int(merged["date"][:4])
            if merged["year"] == date_year:
                merged["year"] = None

        # Keep delimiter from regex (only regex extracts this)
        merged["delimiter"] = regex_result.get("delimiter", " ")

        return merged

    def interpret(
        self,
        name: str,
        match_title: bool = False,
    ) -> Dict:
        """
        Parse media filename using multiple parsers and merge results.

        Uses guessit, PTN, and custom regex patterns to extract metadata,
        intelligently merging results for maximum accuracy.
        """
        # Parse with all three methods
        guessit_result = self._parse_with_guessit(name)
        ptn_result = self._parse_with_ptn(name)
        regex_result = self._parse_with_regex(name)

        # Merge results intelligently
        return self._merge_results(guessit_result, ptn_result, regex_result)
