"""Read and validate settings from environment variables."""

import math
import os
import re

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MAX_CONTENT_CHARS = 50000
DEFAULT_GEMINI_MIN_SECONDS_BETWEEN_CALLS = 12.0
DEFAULT_GEMINI_MAX_CALLS_PER_RUN = 40
MAX_LLM_CONTENT_CHARS = 12000
EXTENSION_ORIGIN_PATTERN = re.compile(r"^chrome-extension://[a-p]{32}$")
GEMINI_MODEL_PATTERN = re.compile(r"^gemini-[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")


def get_api_token() -> str:
    """Shared secret expected in the X-Mamoru-Token header."""
    return os.getenv("MAMORU_API_TOKEN", "").strip()


def get_gemini_api_key() -> str:
    """Gemini API key used only by the synthetic evaluation harness."""
    return os.getenv("GEMINI_API_KEY", "").strip()


def get_gemini_model() -> str:
    """Return a required, syntactically valid Gemini model ID from .env."""
    model = os.getenv("GEMINI_MODEL", "").strip()
    if not model:
        raise ValueError(
            "GEMINI_MODEL is required. Set it in .env to a model ID currently "
            "listed by Google AI Studio."
        )
    if len(model) > 100 or not GEMINI_MODEL_PATTERN.fullmatch(model):
        raise ValueError(
            "GEMINI_MODEL must be a valid Gemini model ID beginning with 'gemini-' "
            "and containing only letters, numbers, '.', '_', or '-'."
        )
    return model


def get_gemini_min_seconds_between_calls() -> float:
    raw = os.getenv(
        "GEMINI_MIN_SECONDS_BETWEEN_CALLS",
        str(DEFAULT_GEMINI_MIN_SECONDS_BETWEEN_CALLS),
    ).strip()
    try:
        delay = float(raw)
    except ValueError:
        raise ValueError(
            "GEMINI_MIN_SECONDS_BETWEEN_CALLS must be a finite non-negative number."
        ) from None
    if not math.isfinite(delay) or delay < 0:
        raise ValueError(
            "GEMINI_MIN_SECONDS_BETWEEN_CALLS must be a finite non-negative number."
        )
    return delay


def get_gemini_max_calls_per_run() -> int:
    raw = os.getenv("GEMINI_MAX_CALLS_PER_RUN", str(DEFAULT_GEMINI_MAX_CALLS_PER_RUN)).strip()
    try:
        call_limit = int(raw)
    except ValueError:
        raise ValueError("GEMINI_MAX_CALLS_PER_RUN must be a positive integer.") from None
    if call_limit < 1:
        raise ValueError("GEMINI_MAX_CALLS_PER_RUN must be a positive integer.")
    return call_limit


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
