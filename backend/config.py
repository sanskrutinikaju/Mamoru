"""Read and validate settings from environment variables."""

import os
import re

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MAX_CONTENT_CHARS = 50000
MAX_LLM_CONTENT_CHARS = 12000
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
EXTENSION_ORIGIN_PATTERN = re.compile(r"^chrome-extension://[a-p]{32}$")


def get_api_token() -> str:
    """Shared secret expected in the X-Mamoru-Token header."""
    return os.getenv("MAMORU_API_TOKEN", "")


def get_openai_api_key() -> str:
    """OpenAI key used only by the local backend."""
    return os.getenv("OPENAI_API_KEY", "").strip()


def get_openai_model() -> str:
    """Single configured OpenAI model name."""
    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip()
    if not model or len(model) > 100:
        raise ValueError("OPENAI_MODEL must be a non-empty name of at most 100 characters.")
    return model


def get_extension_origin() -> str | None:
    """Return the one allowed extension origin, or None when not configured."""
    origin = os.getenv("MAMORU_EXTENSION_ORIGIN", "").strip()
    if not origin:
        return None
    if not EXTENSION_ORIGIN_PATTERN.fullmatch(origin):
        raise ValueError(
            "MAMORU_EXTENSION_ORIGIN must be chrome-extension:// followed by "
            "the 32-character extension ID."
        )
    return origin


def get_max_content_chars() -> int:
    raw = os.getenv("MAMORU_MAX_CONTENT_CHARS", str(DEFAULT_MAX_CONTENT_CHARS))
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(
            "MAMORU_MAX_CONTENT_CHARS must be a positive integer."
        ) from None
    if value < 1:
        raise ValueError("MAMORU_MAX_CONTENT_CHARS must be a positive integer.")
    return value
