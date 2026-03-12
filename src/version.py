#! /usr/bin/env python3

from functools import lru_cache
from pathlib import Path


VERSION_FILE = Path(__file__).resolve().parents[1] / 'VERSION'


@lru_cache(maxsize=1)
def get_version() -> str:
    return VERSION_FILE.read_text(encoding='utf-8').strip()


def get_display_version() -> str:
    version = get_version()
    return version if version.startswith('v') else f'v{version}'


VERSION = get_version()
DISPLAY_VERSION = get_display_version()