import argparse
import os
import sys
from pathlib import Path

import yaml

from mediascan.mediascan import MediaScan
from mediascan.config import Config


def load_config(config_path):
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return None


def save_config(config_path, config):
    with open(config_path, "w") as f:
        yaml.dump(config, f)


def generate_default_config():
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
    }


def main():
    parser = argparse.ArgumentParser(
        description="MediaScan - Organize your media files"
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
    args = parser.parse_args()

    config_path = os.path.expanduser(args.config)

    if args.generate_config:
        if os.path.exists(config_path):
            print(f"Config file already exists at {config_path}")
            sys.exit(1)
        config = generate_default_config()
        save_config(config_path, config)
        print(f"Default config file generated at {config_path}")
        sys.exit(0)

    config = load_config(config_path)
    if config is None:
        print(
            f"Config file not found at {config_path}."
            "Run with --generate-config to create one."
        )
        sys.exit(1)

    # Override config with command-line arguments
    if args.input_dir:
        config["input_dir"] = args.input_dir
    if args.output_dir:
        config["output_dir"] = args.output_dir
    if args.action:
        config["action"] = args.action

    # Create MediaScan instance
    media_scan = MediaScan(
        input_dir=config["input_dir"],
        output_dir=config["output_dir"],
        action=config["action"],
        extensions=config["extensions"],
        movie_path=config["movie_path"],
        movie_path_no_year=config["movie_path_no_year"],
        episode_path=config["episode_path"],
        episode_path_no_year=config["episode_path_no_year"],
        dated_episode_path=config["dated_episode_path"],
        min_video_size=config["min_video_size"],
        min_audio_size=config["min_audio_size"],
        delete_non_media=config["delete_non_media"],
    )

    # Run the scan
    media_scan.scan()


if __name__ == "__main__":
    main()
