"""Core domain models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Track:
    """A single song identified by artist and title."""

    artist: str
    title: str

    @property
    def query(self) -> str:
        """Search query combining artist and title."""
        return f"{self.artist} {self.title}"


@dataclass(frozen=True, slots=True)
class Playlist:
    """A playlist that can be addressed by name and URL/ID."""

    name: str
    link: str = ""
    playlist_id: str = ""
