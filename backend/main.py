"""Mamoru backend — FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Mamoru",
    description="Privacy-first, user-initiated browser safety assistant.",
    version="0.1.0",
)

# The popup runs as a chrome-extension:// page, so the browser may send CORS
# checks when it talks to this local API. This allows those local requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    """Simple confirmation that the application process is running."""
    return {
        "name": "Mamoru",
        "japanese_name": "マモル",
        "status": "running",
    }


@app.get("/health")
def health() -> dict[str, str]:
    """Confirm that Mamoru's backend is running."""
    return {
        "status": "ok",
        "service": "mamoru-backend",
        "message": "Mamoru backend is running.",
    }
