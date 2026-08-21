"""Core domain models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Track:
    """A single song identified by artist and title.

    The extra metadata (full artist credits, album, duration) is optional and
    used by the fuzzy matcher to score YouTube Music candidates.
    """

    artist: str
    title: str
    artists: tuple[str, ...] = ()
    album: str = ""
    duration_ms: int | None = None

    @property
    def query(self) -> str:
        """Search query combining artist and title."""
        return f"{self.artist} {self.title}"

    @property
    def credits(self) -> tuple[str, ...]:
        """All known artists, falling back to the primary artist alone."""
        if self.artists:
            return self.artists
        return (self.artist,) if self.artist else ()

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Track:
        """Rebuild a track from its cached dictionary representation."""
        artists = data.get("artists", [])
        duration = data.get("duration_ms")
        return cls(
            artist=str(data.get("artist", "")),
            title=str(data.get("title", "")),
            artists=tuple(str(a) for a in artists) if isinstance(artists, list) else (),
            album=str(data.get("album", "")),
            duration_ms=int(duration) if isinstance(duration, (int, float)) else None,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation for the cache."""
        return {
            "artist": self.artist,
            "title": self.title,
            "artists": list(self.artists),
            "album": self.album,
            "duration_ms": self.duration_ms,
        }


@dataclass(frozen=True, slots=True)
class Playlist:
    """A playlist that can be addressed by name and URL/ID."""

    name: str
    link: str = ""
    playlist_id: str = ""
