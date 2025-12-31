"""
MediaScan - Advanced media file organizer with intelligent filename parsing.

This package uses multiple parsing libraries (guessit, PTN, custom regex) to
accurately detect and extract metadata from media filenames, then organizes
them into a structured library.
"""

from .interpreter import Interpreter
from .mediascan import MediaScan

__all__ = ["Interpreter", "MediaScan"]
__name__ = "mediascan"
__version__ = "0.1.7"
__author__ = "Philip Orange"
__author_email__ = "git" + "@" + "philiporange.com"
__description__ = "A Python package for scanning and organizing media files."
__url__ = "http://github.com/philiporange/mediascan"
