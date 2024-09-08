import os
import re
import gzip
import requests
import json
import time
from typing import Dict, Optional, List, Generator
from datetime import timedelta, datetime
from urllib.request import urlretrieve

from redislite import Redis, StrictRedis

from .config import Config


BASE_URL = Config.TMDB_BASE_URL
DUMP_URL_TEMPLATE = Config.TMDB_DUMP_URL_TEMPLATE
IMAGE_URL_PREFIX = Config.TMDB_IMAGE_URL_PREFIX
INDEX_PATH = Config.TMDB_INDEX_PATH
CACHE_EXPIRATION = timedelta(seconds=Config.TMDB_CACHE_EXPIRATION)
RATE_LIMIT = Config.TMDB_RATE_LIMIT
RATE_LIMIT_WINDOW = Config.TMDB_RATE_LIMIT_WINDOW
MAX_RETRIES = Config.TMDB_MAX_RETRIES
RETRY_DELAY = Config.TMDB_RETRY_DELAY
TMP_DIR = Config.TMDB_TMP_DIR


class TMDbAPI:
    FORGOTTEN_ENGLISH_WORDS = [
        "the",
        "a",
        "an",
    ]
    NATIONALITIES = [
        "US",
        "USA",
        "UK",
        "GB",
        "CA",
        "AU",
        "NZ",
        "IE",
        "ZA",
        "IN",
        "FR",
        "DE",
        "IT",
        "ES",
        "JP",
        "KR",
        "CN",
        "RU",
        "Canada",
        "Australia",
        "New Zealand",
        "Ireland",
        "South Africa",
        "India",
        "France",
        "Germany",
        "Italy",
        "Spain",
        "Japan",
        "South Korea",
        "China",
        "Russia",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        redis_path: str = "tmdb_cache.db",
        index_path: str = "title_index.db",
    ):
        self.api_key = api_key or os.environ.get("TMDB_API_KEY")
        self.redis = Redis(redis_path)
        self.title_index = StrictRedis(index_path)

        # Create the temporary directory if it doesn't exist
        if not os.path.exists(TMP_DIR):
            os.makedir(TMP_DIR)

        self.nationality_re = re.compile(
            r"\b(" + "|".join(self.NATIONALITIES) + r")\b", re.IGNORECASE
        )

    def _get_cache_key(self, endpoint: str, params: Dict[str, str]) -> str:
        return f"cache:{endpoint}:{json.dumps(params, sort_keys=True)}"

    def _get_rate_limit_key(self) -> str:
        return f"rate_limit:{int(time.time())}"

    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        cached_data = self.redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None

    def _set_cached_response(self, cache_key: str, data: Dict):
        self.redis.setex(
            cache_key, int(CACHE_EXPIRATION.total_seconds()), json.dumps(data)
        )

    def _check_rate_limit(self):
        rate_limit_key = self._get_rate_limit_key()

        pipe = self.redis.pipeline()
        pipe.incr(rate_limit_key)
        pipe.expire(rate_limit_key, RATE_LIMIT_WINDOW)
        request_count, _ = pipe.execute()

        if request_count > RATE_LIMIT:
            time.sleep(RATE_LIMIT_WINDOW)

    def _make_request(self, endpoint: str, params: Dict[str, str]) -> Dict:
        cache_key = self._get_cache_key(endpoint, params)
        cached_response = self._get_cached_response(cache_key)

        if cached_response:
            return cached_response

        # Check api key is set
        if not self.api_key:
            raise ValueError("API key is not set")

        params["api_key"] = self.api_key

        url = f"{BASE_URL}{endpoint}"

        for attempt in range(MAX_RETRIES):
            self._check_rate_limit()

            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                self._set_cached_response(cache_key, data)
                return data
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    if attempt < MAX_RETRIES - 1:
                        print(
                            "Rate limit exceeded. "
                            f"Waiting for {RETRY_DELAY} seconds..."
                        )
                        time.sleep(RETRY_DELAY)
                    else:
                        raise
                else:
                    raise

        raise Exception("Max retries exceeded")

    def _normalize_title(self, title: str) -> str:
        # Join accronyms
        title = re.sub(r"(?<=[a-zA-Z])\.(?=[a-zA-Z])", "", title)

        # Remove special characters
        title = "".join(e for e in title if e.isalnum() or e == " ")
        title = title.strip()
        title = title.lower()

        return title

    def get_db_dump(self, subject: str) -> Optional[str]:
        now = datetime.utcnow()
        if now.hour < 8:
            now -= timedelta(days=1)
        day_str = now.strftime("%m_%d_%Y")

        list_name = "tv_series" if subject == "tv" else subject
        subject_url = DUMP_URL_TEMPLATE.format(list_name, day_str)
        subject_filename = f"{subject}_ids.json.gz"
        subject_path = os.path.join(TMP_DIR, subject_filename)

        if not os.path.exists(subject_path) and not os.path.exists(
            subject_path[:-3]
        ):
            print(f"Downloading {subject} dump file...", end=" ", flush=True)
            try:
                urlretrieve(subject_url, subject_path)
                print("Done")
            except Exception as e:
                print(f"Error downloading {subject} dump: {e}")
                return None

        return subject_path

    def list_all(
        self, subject: str = "movie", min_popularity: float = 5.0
    ) -> Generator[Dict, None, None]:
        subject_path = self.get_db_dump(subject)
        if not subject_path:
            return

        with gzip.open(subject_path, "rt") as f:
            for line in f:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if item.get("adult", False) or item.get("video", False):
                    continue

                title_key = (
                    "original_title"
                    if "original_title" in item
                    else "original_name"
                )
                if title_key in item:
                    item["title" if subject == "movie" else "name"] = item[
                        title_key
                    ]

                for key in [
                    "adult",
                    "video",
                    "original_title",
                    "original_name",
                ]:
                    item.pop(key, None)

                if item.get("popularity", 0) < min_popularity:
                    continue

                yield item

    def movie_search(
        self, query: str, year: Optional[int] = None
    ) -> List[Dict]:
        params = {"query": query}
        if year:
            params["year"] = str(year)
        return self._make_request("/search/movie", params)["results"]

    def tv_search(
        self, query: str, first_air_date_year: Optional[int] = None
    ) -> List[Dict]:
        params = {"query": query}
        if first_air_date_year:
            params["first_air_date_year"] = str(first_air_date_year)
        return self._make_request("/search/tv", params)["results"]

    def match_movie(self, title: str, year: Optional[int] = None) -> bool:
        results = self.movie_search(title, year)
        if not results:
            return False

        title_alpha = "".join(filter(str.isalpha, title.lower()))
        for result in results:
            result_title_alpha = "".join(
                filter(str.isalpha, result["title"].lower())
            )
            if title_alpha == result_title_alpha:
                if year:
                    # Check if the release date is within the specified year
                    release_date = result.get("release_date", "")
                    if (
                        release_date.startswith(str(year))
                        or release_date.startswith(str(year - 1))
                        or release_date.startswith(str(year + 1))
                    ):
                        return True
                else:
                    return True
        return False

    def match_tv(self, title: str, year: Optional[int] = None) -> bool:
        results = self.tv_search(title, year)
        if not results:
            return False

        title_alpha = "".join(filter(str.isalpha, title.lower()))
        for result in results:
            result_title_alpha = "".join(
                filter(str.isalpha, result["name"].lower())
            )
            if title_alpha == result_title_alpha:
                if year:
                    # Check if the first air date is within the specified year
                    first_air_date = result.get("first_air_date", "")
                    if (
                        first_air_date.startswith(str(year))
                        or first_air_date.startswith(str(year - 1))
                        or first_air_date.startswith(str(year + 1))
                    ):
                        return True
                else:
                    return True
        return False

    def list_popular_movies(
        self, language: str = "en-US", limit: int = 10000
    ) -> Generator[Dict, None, None]:
        return self._paginated_request("/movie/popular", language, limit)

    def list_popular_tv(
        self, language: str = "en-US", limit: int = 10000
    ) -> Generator[Dict, None, None]:
        return self._paginated_request("/tv/popular", language, limit)

    def _paginated_request(
        self, endpoint: str, language: str, limit: int
    ) -> Generator[Dict, None, None]:
        params = {"language": language, "page": 1}
        total_yielded = 0

        while total_yielded < limit:
            response = self._make_request(endpoint, params)
            results = response.get("results", [])

            for item in results:
                if total_yielded >= limit:
                    return
                yield item
                total_yielded += 1

            if response["page"] >= response["total_pages"]:
                return

            params["page"] += 1

    def index_all(self):
        count = 0
        for _type in ["movie", "tv"]:
            for result in self.list_all(_type):
                _id = f"{_type[:1]}:{result['id']}"
                title = result.get("title", result.get("name", ""))
                title = self._normalize_title(title)

                # Add title to the index
                self.title_index.set(f"t:{_id}", title)

                # Add words to the index
                for word in title.split():
                    if word not in self.FORGOTTEN_ENGLISH_WORDS:
                        self.title_index.sadd(f"w:{word}", _id)

                count += 1

        print(f"Indexed {count} titles")

    def search(self, query: str, sort: bool = True) -> List[str]:
        query = self._normalize_title(query)
        words = query.split()
        results = set()

        for word in words:
            if word not in self.FORGOTTEN_ENGLISH_WORDS:
                results.update(self.title_index.smembers(f"w:{word}"))

        titles = []
        for index in results:
            title = self.title_index.get(f"t:{index.decode()}")
            if title:
                titles.append(title.decode())

        # Return unsorted results if sort is disabled
        if not sort:
            return titles

        # Calculate a score for each title
        scored_titles = []
        for title in titles:
            score = 0
            title_lower = title.lower()
            for word in words:
                if word.lower() in title_lower:
                    score += 1
                    # Bonus points for exact word matches
                    if f" {word.lower()} " in f" {title_lower} ":
                        score += 0.5
            # Bonus points for titles that start with the query
            if title_lower.startswith(query):
                score += 2
            # Penalty for much longer titles
            score -= max(0, (len(title) - len(query)) / 100)
            scored_titles.append((title, score))

        # Sort by score
        scored_titles.sort(key=lambda x: x[1], reverse=True)

        return [title for title, _ in scored_titles]

    def match(self, query: str, year: Optional[int] = None) -> bool:
        # Clean up query
        query = query.lower().strip()
        query = self.nationality_re.sub("", query)
        query = "".join(e for e in query if e.isalnum() or e == " ")

        # Check if the query is in the index
        search_results = self.search(query, sort=False)
        if not search_results:
            return False

        # Check if the query is a subset of the search results
        query_words = set(query.lower().split()) - set(
            self.FORGOTTEN_ENGLISH_WORDS
        )
        for result in search_results:
            result_words = set(result.lower().split()) - set(
                self.FORGOTTEN_ENGLISH_WORDS
            )
            if query_words.issubset(result_words):
                if year:
                    # Check if the result matches the year
                    if self.match_movie(result, year) or self.match_tv(
                        result, year
                    ):
                        return True
                else:
                    return True

        return False

    def rebuild_index(self):
        # Clear existing index
        self.title_index.flushdb()
        # Rebuild index
        self.index_all()


# Usage example
if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()
    api_key = os.environ.get("TMDB_API_KEY")

    tmdb = TMDbAPI(api_key)

    # Rebuild the index
    tmdb.rebuild_index()

    # Example search
    search_results = tmdb.search("Oceans Eleven")
    print("Search results for 'star wars':")
    for result in search_results[:10]:  # Print first 10 results
        print(result)
