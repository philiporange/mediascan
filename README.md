# MediaScan

MediaScan is a Python tool for organizing media files. It scans directories, interprets file names, and organizes movies and TV shows into a structured library.

## Features

- Automatically categorizes movies and TV shows
- Supports various naming conventions and file formats
- Configurable output directory structure
- Multiple actions: link, copy, or move files

## Installation

```bash
pip install mediascan
```

## Usage

### Command Line Interface

Generate a default config file:

```bash
mediascan --generate-config
```

Run MediaScan:

```bash
mediascan --input-dir ~/Downloads --output-dir ~/MediaLibrary --action link
```

### Python

```python
from mediascan import MediaScan

scanner = MediaScan(
    input_dir="~/Downloads",
    output_dir="~/MediaLibrary",
    action="symlink",
)

scanner.scan()
```

## License

CC0. Do whatever.
