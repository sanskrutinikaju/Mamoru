"""Read settings from environment variables. No secrets are hard-coded."""

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MAX_CONTENT_CHARS = 50000


def get_api_token() -> str:
    """Shared secret expected in the X-Mamoru-Token header."""
    return os.getenv("MAMORU_API_TOKEN", "")


def get_max_content_chars() -> int:
    raw = os.getenv("MAMORU_MAX_CONTENT_CHARS", str(DEFAULT_MAX_CONTENT_CHARS))
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_MAX_CONTENT_CHARS
    if value < 1:
        return DEFAULT_MAX_CONTENT_CHARS
    return value
