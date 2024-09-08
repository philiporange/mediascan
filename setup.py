from setuptools import setup, find_packages

from src.mediascan import (
    __name__,
    __version__,
    __author__,
    __author_email__,
    __description__,
    __url__,
)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name=__name__,
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    description=__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=__url__,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests",
        "pyyaml",
        "redislite",
        "appdirs",
        "loguru",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "mediascan=mediascan.__main__:main",
        ],
    },
)
