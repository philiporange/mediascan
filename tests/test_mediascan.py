import unittest
import os
import shutil
import tempfile
from pathlib import Path

from src.mediascan.mediascan import MediaScan
from src.mediascan.config import Config


class TestMediaScan(unittest.TestCase):
    def setUp(self):
        # Create temporary directories for input and output
        self.temp_dir = tempfile.mkdtemp()
        self.input_path = os.path.join(self.temp_dir, "input")
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.movies_path = os.path.join(self.output_dir, Config.MOVIES_DIR)
        self.tv_shows_path = os.path.join(self.output_dir, Config.TV_SHOWS_DIR)

        os.makedirs(self.input_path)
        os.makedirs(self.output_dir)

        # Create an existing TV show folder
        existing_show_folder = os.path.join(
            self.tv_shows_path, "Existing Show (2020)"
        )
        os.makedirs(existing_show_folder)

        # Create a MediaScan instance with temporary directories and zero min sizes
        self.media_scan = MediaScan(
            input_path=self.input_path,
            output_dir=self.output_dir,
            min_video_size=0,
            min_audio_size=0,
            prefer_existing_folders=True,
        )

    def tearDown(self):
        # Remove temporary directory and all its contents
        shutil.rmtree(self.temp_dir)

    def create_empty_file(self, file_path):
        Path(file_path).touch()

    def test_scan_with_media_files(self):
        # Create test media files
        self.create_empty_file(os.path.join(self.input_path, "movie.mp4"))
        self.create_empty_file(os.path.join(self.input_path, "document.txt"))

        # Run the scan
        self.media_scan.scan()

        # Check if media files were processed
        expected_movie_path = os.path.join(
            self.movies_path, "Movie/Movie [Unknown].mp4"
        )
        self.assertTrue(
            os.path.exists(expected_movie_path),
            f"Movie file not found: {expected_movie_path}",
        )

        unexpected_doc_path = os.path.join(self.output_dir, "document.txt")
        self.assertFalse(
            os.path.exists(unexpected_doc_path),
            f"Unexpected document file found: {unexpected_doc_path}",
        )

    def test_scan_with_tv_show(self):
        # Create a test TV show file
        self.create_empty_file(
            os.path.join(self.input_path, "Show.Name.S01E05.mp4")
        )

        # Run the scan
        self.media_scan.scan()

        # Check if the TV show file was processed correctly
        expected_path = os.path.join(
            self.tv_shows_path,
            "Show Name",
            "Season 01",
            "Show Name - S01E05 [Unknown].mp4",
        )
        self.assertTrue(
            os.path.exists(expected_path),
            f"TV show file not found: {expected_path}",
        )

    def test_scan_with_movie_and_year(self):
        # Create a test movie file with year
        self.create_empty_file(
            os.path.join(self.input_path, "Movie.Name.2021.mp4")
        )

        # Run the scan
        self.media_scan.scan()

        # Check if the movie file was processed correctly
        expected_path = os.path.join(
            self.movies_path,
            "Movie Name (2021)",
            "Movie Name (2021) [Unknown].mp4",
        )
        self.assertTrue(
            os.path.exists(expected_path),
            f"Movie file not found: {expected_path}",
        )

    def test_scan_with_different_actions(self):
        # Create a test media file
        source_file = os.path.join(self.input_path, "test movie.mp4")
        self.create_empty_file(source_file)

        # Test 'link' action
        self.media_scan.action = "link"
        self.media_scan.scan()
        linked_file = os.path.join(
            self.movies_path, "Test Movie/Test Movie [Unknown].mp4"
        )
        self.assertTrue(
            os.path.exists(linked_file),
            f"Linked file not found: {linked_file}",
        )
        if os.path.exists(linked_file):
            self.assertEqual(
                os.stat(source_file).st_ino,
                os.stat(linked_file).st_ino,
                "Inodes don't match for linked file",
            )

        # Clear output directory
        shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)

        # Test 'copy' action
        self.media_scan.action = "copy"
        self.media_scan.scan()
        copied_file = os.path.join(
            self.movies_path, "Test Movie/Test Movie [Unknown].mp4"
        )
        self.assertTrue(
            os.path.exists(copied_file),
            f"Copied file not found: {copied_file}",
        )
        if os.path.exists(copied_file):
            self.assertNotEqual(
                os.stat(source_file).st_ino,
                os.stat(copied_file).st_ino,
                "Inodes match for copied file",
            )

        # Clear output directory
        shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)

        # Test 'move' action
        self.media_scan.action = "move"
        self.media_scan.scan()
        moved_file = os.path.join(
            self.movies_path, "Test Movie/Test Movie [Unknown].mp4"
        )
        self.assertTrue(
            os.path.exists(moved_file), f"Moved file not found: {moved_file}"
        )
        self.assertFalse(
            os.path.exists(source_file),
            f"Source file still exists after move: {source_file}",
        )

    def test_scan_with_delete_non_media(self):
        # Create test files
        self.create_empty_file(os.path.join(self.input_path, "movie.mp4"))
        self.create_empty_file(os.path.join(self.input_path, "document.txt"))

        # Set delete_non_media to True and action to 'move'
        self.media_scan.delete_non_media = True
        self.media_scan.action = "move"

        # Run the scan
        self.media_scan.scan()

        # Check if media file was moved and non-media file was deleted
        expected_movie_path = os.path.join(
            self.movies_path, "Movie/Movie [Unknown].mp4"
        )
        self.assertTrue(
            os.path.exists(expected_movie_path),
            f"Moved movie file not found: {expected_movie_path}",
        )

        original_movie_path = os.path.join(self.input_path, "movie.mp4")
        self.assertFalse(
            os.path.exists(original_movie_path),
            f"Original movie file still exists: {original_movie_path}",
        )

        document_path = os.path.join(self.input_path, "document.txt")
        self.assertFalse(
            os.path.exists(document_path),
            f"Document file was not deleted: {document_path}",
        )

    def test_scan_with_existing_tv_show_year(self):
        # Create a test TV show file without a year
        self.create_empty_file(
            os.path.join(self.input_path, "Existing Show S01E01.mp4")
        )

        # Run the scan
        self.media_scan.scan()

        # Check if the TV show file was placed in the existing folder with year
        existing_show_folder = os.path.join(
            self.tv_shows_path, "Existing Show (2020)"
        )
        expected_path = os.path.join(
            existing_show_folder,
            "Season 01",
            "Existing Show (2020) - S01E01 [Unknown].mp4",
        )
        self.assertTrue(
            os.path.exists(expected_path),
            f"TV show file not found in existing folder: {expected_path}",
        )

    def test_scan_without_existing_tv_show_year(self):
        # Setup: No existing TV show folders

        # Create a test TV show file without a year
        self.create_empty_file(
            os.path.join(self.input_path, "New Show S01E01.mp4")
        )

        # Run the scan
        self.media_scan.scan()

        # Check if the TV show file was placed without a year
        expected_path = os.path.join(
            self.tv_shows_path,
            "New Show",
            "Season 01",
            "New Show - S01E01 [Unknown].mp4",
        )
        self.assertTrue(
            os.path.exists(expected_path),
            f"TV show file not found without year: {expected_path}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
