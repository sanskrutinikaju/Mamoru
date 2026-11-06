"""Set test environment before the app is imported."""

import os

os.environ["MAMORU_API_TOKEN"] = "test-token-ci"
os.environ["MAMORU_MAX_CONTENT_CHARS"] = "50000"
os.environ["GEMINI_API_KEY"] = ""
os.environ["MAMORU_EXTENSION_ORIGIN"] = (
    "chrome-extension://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
)
