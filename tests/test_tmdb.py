import unittest
import os
import time
from datetime import datetime

from src.mediascan.tmdb import TMDbAPI


class TestTMDbAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load API key from environment variable
        cls.api_key = os.environ.get("TMDB_API_KEY")
        if not cls.api_key:
            raise ValueError("TMDB_API_KEY environment variable is not set")

        # Initialize TMDbAPI
        cls.tmdb = TMDbAPI(cls.api_key)

        # Ensure the index is built
        cls.tmdb.rebuild_index()

    def test_movie_search(self):
        results = self.tmdb.movie_search("Inception")
        self.assertTrue(len(results) > 0)
        self.assertIn("Inception", [movie["title"] for movie in results])

    def test_tv_search(self):
        results = self.tmdb.tv_search("Breaking Bad")
        self.assertTrue(len(results) > 0)
        self.assertIn("Breaking Bad", [show["name"] for show in results])

    def test_match_movie(self):
        self.assertTrue(self.tmdb.match_movie("Inception", 2010))
        self.assertFalse(self.tmdb.match_movie("Nonexistent Movie", 2020))

    def test_match_tv(self):
        self.assertTrue(self.tmdb.match_tv("Breaking Bad", 2008))
        self.assertFalse(self.tmdb.match_tv("Nonexistent TV Show", 2020))

    def test_list_popular_movies(self):
        movies = list(self.tmdb.list_popular_movies(limit=10))
        self.assertEqual(len(movies), 10)
        self.assertTrue(all("title" in movie for movie in movies))

    def test_list_popular_tv(self):
        tv_shows = list(self.tmdb.list_popular_tv(limit=10))
        self.assertEqual(len(tv_shows), 10)
        self.assertTrue(all("name" in show for show in tv_shows))

    def test_search(self):
        results = self.tmdb.search("Inception")
        self.assertTrue(len(results) > 0)
        self.assertIn("inception", [title.lower() for title in results])

    def test_match(self):
        self.assertTrue(self.tmdb.match("Inception", 2010))
        self.assertFalse(self.tmdb.match("Nonexistent Movie", 2020))

    def test_get_db_dump(self):
        movie_dump = self.tmdb.get_db_dump("movie")
        self.assertIsNotNone(movie_dump)
        self.assertTrue(os.path.exists(movie_dump))

    def test_list_all(self):
        movies = list(self.tmdb.list_all("movie", min_popularity=15))
        self.assertTrue(len(movies) > 0)
        self.assertTrue(all("title" in movie for movie in movies))

    def test_cache(self):
        # Make an initial request
        self.tmdb.movie_search("Inception")

        # Make the same request again and measure time
        start_time = time.time()
        self.tmdb.movie_search("Inception")
        end_time = time.time()

        # The cached request should be very fast
        self.assertLess(end_time - start_time, 0.1)


if __name__ == "__main__":
    unittest.main()
