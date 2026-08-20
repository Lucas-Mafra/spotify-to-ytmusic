"""Application configuration loaded from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

SPOTIFY_SCOPE = "playlist-read-private"
DEFAULT_AUTH_PATH = Path("browser.json")
ENV_FILE = Path(".env")


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable settings container populated from environment variables."""

    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str
    ytmusic_auth_path: Path

    @classmethod
    def from_env(cls, env_file: Path = ENV_FILE) -> Settings:
        """Build settings from a ``.env`` file plus the process environment."""
        load_dotenv(env_file)

        return cls(
            spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID", ""),
            spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET", ""),
            spotify_redirect_uri=os.getenv(
                "SPOTIFY_REDIRECT_URI",
                "http://localhost:8888/callback",
            ),
            ytmusic_auth_path=Path(os.getenv("HEADERS_AUTH_PATH", str(DEFAULT_AUTH_PATH))),
        )
