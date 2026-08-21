"""YouTube Music client built on :mod:`ytmusicapi`."""

from __future__ import annotations

import logging
from typing import Any, Literal

from rich.progress import Progress
from ytmusicapi import YTMusic

from .config import Settings
from .matching import SONG_MATCH_THRESHOLD, VIDEO_MATCH_THRESHOLD, score_match
from .models import Playlist, Track

logger = logging.getLogger(__name__)

# Search stages: official songs are preferred; videos are a fallback for
# tracks that only exist as uploads (but demand a stricter score).
_SearchFilter = Literal["songs", "videos"]
_SEARCH_STAGES: tuple[tuple[_SearchFilter, float], ...] = (
    ("songs", SONG_MATCH_THRESHOLD),
    ("videos", VIDEO_MATCH_THRESHOLD),
)

_CANDIDATES_PER_SEARCH = 5


class YouTubeMusicClient:
    """Thin, lazy wrapper around the YouTube Music API.

    The underlying :class:`ytmusicapi.YTMusic` client is created on first use
    so importing this module never touches the filesystem or the network.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: YTMusic | None = None

    @property
    def client(self) -> YTMusic:
        """Return the lazily-initialized YTMusic client."""
        if self._client is None:
            self._client = YTMusic(str(self._settings.ytmusic_auth_path))
        return self._client

    def get_playlists(self) -> list[Playlist]:
        """Return all playlists from the user's YouTube Music library."""
        playlists = [
            Playlist(
                name=item.get("title", "Unknown"),
                playlist_id=item.get("playlistId", ""),
            )
            for item in self.client.get_library_playlists()
            if item.get("playlistId")
        ]

        logger.info("Retrieved %d playlists from library.", len(playlists))
        return playlists

    def get_playlist_tracks(self, playlist_id: str) -> list[Track]:
        """Fetch every track from a YouTube Music playlist."""
        items = self.client.get_playlist(playlist_id).get("tracks", [])

        tracks: list[Track] = []
        for item in items:
            artists = item.get("artists", [])
            tracks.append(
                Track(
                    artist=artists[0]["name"] if artists else "Unknown Artist",
                    title=item.get("title", "Unknown Title"),
                )
            )

        logger.info("Retrieved %d tracks from playlist %s.", len(tracks), playlist_id)
        return tracks

    def get_playlist_name(self, playlist_id: str) -> str:
        """Resolve the name of a playlist from its YouTube Music ID."""
        playlist: dict[str, Any] = self.client.get_playlist(playlist_id)
        return str(playlist.get("title", "Unknown Playlist"))

    def search_video_ids(self, tracks: list[Track]) -> list[str]:
        """Resolve a YouTube Music video ID for every Spotify track.

        Tracks that cannot be matched are skipped and reported as warnings.
        """
        found: list[str] = []
        with Progress() as progress:
            task = progress.add_task("Searching songs on YouTube Music", total=len(tracks))
            for track in tracks:
                video_id = self._match_track(track)
                if video_id is not None:
                    found.append(video_id)
                progress.advance(task)

        logger.info(
            "Completed search for %d tracks (%d found).",
            len(tracks),
            len(found),
        )
        return found

    def _match_track(self, track: Track) -> str | None:
        """Search YouTube Music for a track and return the best matching video ID.

        Each stage searches a result category and only accepts a candidate
        whose score clears that stage's threshold. Songs are tried first;
        videos act as a stricter fallback so covers and live takes are avoided.
        """
        fallback: tuple[str, float] | None = None

        for search_filter, threshold in _SEARCH_STAGES:
            try:
                results = self.client.search(
                    track.query, filter=search_filter, limit=_CANDIDATES_PER_SEARCH
                )
            except Exception:
                logger.warning("Search failed for '%s'.", track.query, exc_info=True)
                continue

            video_id, score = self._best_candidate(track, results)
            if video_id is None:
                continue

            if score >= threshold:
                logger.debug("Matched '%s' -> %s (score %.2f).", track.title, video_id, score)
                return video_id

            if fallback is None or score > fallback[1]:
                fallback = (video_id, score)

        if fallback is not None:
            logger.warning(
                "Low-confidence match (%.2f) for '%s' by %s.",
                fallback[1],
                track.title,
                ", ".join(track.credits),
            )
        else:
            logger.warning(
                "No match found for '%s' by %s.",
                track.title,
                ", ".join(track.credits),
            )
        return None

    @staticmethod
    def _best_candidate(track: Track, results: list[dict[str, Any]]) -> tuple[str | None, float]:
        """Return the highest scoring video ID and its score for a list of results."""
        best_id: str | None = None
        best_score = 0.0

        for item in results:
            video_id = item.get("videoId")
            if not video_id:
                continue

            title = item.get("title", "")
            artists = [
                artist["name"]
                for artist in item.get("artists") or []
                if isinstance(artist, dict) and artist.get("name")
            ]
            duration = item.get("duration_seconds")
            score = score_match(
                track,
                title,
                artists,
                float(duration) if duration is not None else None,
            )
            if score > best_score:
                best_id, best_score = str(video_id), score

        return best_id, best_score

    def create_playlist(
        self,
        name: str,
        video_ids: list[str],
        privacy: str = "PRIVATE",
    ) -> str:
        """Create a playlist and return a human-readable result message."""
        if not video_ids:
            return "No songs provided to create playlist."

        self.client.create_playlist(
            title=name,
            description="",
            privacy_status=privacy,
            video_ids=video_ids,
        )

        message = f"Playlist '{name}' was created!"
        logger.info("%s", message)
        return message

    def delete_playlist(self, playlist_id: str) -> bool:
        """Delete a playlist, returning ``True`` on success."""
        self.client.delete_playlist(playlist_id)
        logger.info("Playlist %s deleted successfully.", playlist_id)
        return True

    def account_info(self) -> dict[str, Any]:
        """Return the authenticated account info."""
        return self.client.get_account_info()
