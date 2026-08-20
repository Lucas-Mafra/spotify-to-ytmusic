"""Persistent cache for fetched tracks and resolved YouTube Music IDs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

CACHE_FILE = Path("cache.json")

_SECTION_SPOTIFY = "spotify_tracks_cache"
_SECTION_YT_TRACKS = "ytmusic_tracks_cache"
_SECTION_YT_IDS = "ytmusic_songsid_cache"


@dataclass(slots=True)
class Cache:
    """File-backed storage for the current import/transfer session."""

    path: Path = CACHE_FILE
    spotify_tracks: list[str] = field(default_factory=list)
    ytmusic_tracks: list[str] = field(default_factory=list)
    ytmusic_songsid: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.load()

    def load(self) -> None:
        """Populate fields from disk, keeping defaults when no cache exists."""
        if not self.path.exists():
            return

        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.spotify_tracks = list(data.get(_SECTION_SPOTIFY, []))
        self.ytmusic_tracks = list(data.get(_SECTION_YT_TRACKS, []))
        self.ytmusic_songsid = list(data.get(_SECTION_YT_IDS, []))

    def save(self) -> None:
        """Persist the current state to disk."""
        data = {
            _SECTION_SPOTIFY: self.spotify_tracks,
            _SECTION_YT_TRACKS: self.ytmusic_tracks,
            _SECTION_YT_IDS: self.ytmusic_songsid,
        }
        self.path.write_text(
            json.dumps(data, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )

    def clear(self) -> None:
        """Reset every field and write an empty cache to disk."""
        self.spotify_tracks = []
        self.ytmusic_tracks = []
        self.ytmusic_songsid = []
        self.save()
