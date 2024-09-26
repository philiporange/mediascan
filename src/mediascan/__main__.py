import argparse
import os
import sys
from pathlib import Path

import yaml

from mediascan.mediascan import MediaScan
from mediascan.config import Config
from mediascan.logging import configure_logging


def load_config(config_path):
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return None


def save_config(config_path, config):
    with open(config_path, "w") as f:
        yaml.dump(config, f)


def get_default_config():
    return {
        "input_dir": str(Path.home() / "Downloads"),
        "output_dir": str(Path.home() / "MediaLibrary"),
        "action": Config.ACTION,
        "extensions": Config.EXTENSIONS,
        "movie_path": Config.MOVIE_PATH,
        "movie_path_no_year": Config.MOVIE_PATH_NO_YEAR,
        "episode_path": Config.EPISODE_PATH,
        "episode_path_no_year": Config.EPISODE_PATH_NO_YEAR,
        "dated_episode_path": Config.DATED_EPISODE_PATH,
        "min_video_size": Config.MIN_VIDEO_SIZE,
        "min_audio_size": Config.MIN_AUDIO_SIZE,
        "delete_non_media": Config.DELETE_NON_MEDIA,
        "prefer_existing_folders": Config.PREFER_EXISTING_FOLDERS,
        "clean": Config.CLEAN,
    }


def get_config(args, config_path):
    config = get_default_config()  # Start with default settings
    config_file = load_config(config_path)
    if config_file:
        config.update(config_file)  # Override defaults with config file
    # Override config with command-line arguments
    for key, value in vars(args).items():
        if value is not None:
            config[key] = value
    return config


def main():
    parser = argparse.ArgumentParser(
        description="MediaScan - Organize your media files"
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        help="Input directory to scan (overrides config and --input-dir)",
    )
    parser.add_argument(
        "--config", default="~/.mediascan.yaml", help="Path to config file"
    )
    parser.add_argument("--input-dir", help="Input directory to scan")
    parser.add_argument(
        "--output-dir", help="Output directory for organized files"
    )
    parser.add_argument(
        "--action",
        choices=["link", "copy", "move"],
        help="Action to perform on files",
    )
    parser.add_argument(
        "--generate-config",
        action="store_true",
        help="Generate default config file",
    )
    parser.add_argument("--movie-path", help="Path template for movies")
    parser.add_argument(
        "--movie-path-no-year", help="Path template for movies without year"
    )
    parser.add_argument("--episode-path", help="Path template for TV episodes")
    parser.add_argument(
        "--episode-path-no-year",
        help="Path template for TV episodes without year",
    )
    parser.add_argument(
        "--dated-episode-path", help="Path template for dated TV episodes"
    )
    parser.add_argument(
        "--min-video-size", type=int, help="Minimum video file size in bytes"
    )
    parser.add_argument(
        "--min-audio-size", type=int, help="Minimum audio file size in bytes"
    )
    parser.add_argument(
        "--delete-non-media",
        action="store_true",
        help="Delete non-media files",
    )
    parser.add_argument(
        "--no-delete-non-media",
        action="store_false",
        dest="delete_non_media",
        help="Don't delete non-media files",
    )
    parser.add_argument(
        "--prefer-existing-folders",
        action="store_true",
        help="Use existing output folders when possible",
    )
    parser.add_argument(
        "--clean", action="store_true", help="Clean up empty directories"
    )

    # Add quiet and verbose options
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Quiet mode (only show errors)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose mode (show debug messages)",
    )

    args = parser.parse_args()

    config_path = os.path.expanduser(args.config)

    if args.generate_config:
        if os.path.exists(config_path):
            print(f"Config file already exists at {config_path}")
            sys.exit(1)
        config = get_default_config()
        save_config(config_path, config)
        print(f"Default config file generated at {config_path}")
        sys.exit(0)

    config = get_config(args, config_path)

    # Override input_dir if provided as a positional argument
    if args.input_dir:
        config["input_dir"] = args.input_dir

    # Configure logging based on quiet and verbose flags
    if args.quiet:
        log_level = Config.QUIET_LOG_LEVEL
    elif args.verbose:
        log_level = Config.VERBOSE_LOG_LEVEL
    else:
        log_level = Config.LOG_LEVEL

    configure_logging(log_level)

    # Create MediaScan instance
    media_scan = MediaScan(**config)

    # Run the scan
    media_scan.scan()


if __name__ == "__main__":
    main()
