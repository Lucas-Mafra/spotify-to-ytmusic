"""YouTube Music client built on :mod:`ytmusicapi`."""

from __future__ import annotations

import logging
from typing import Any

from rich.progress import Progress
from ytmusicapi import YTMusic

from .config import Settings
from .models import Playlist, Track

logger = logging.getLogger(__name__)


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

    def search_video_ids(self, queries: list[str]) -> list[str]:
        """Resolve a YouTube Music video ID for every search query.

        Queries that cannot be matched are skipped and reported as warnings.
        """
        found: list[str] = []
        with Progress() as progress:
            task = progress.add_task("Searching songs on YouTube Music", total=len(queries))
            for query in queries:
                video_id = self._search_video_id(query)
                if video_id is not None:
                    found.append(video_id)
                progress.advance(task)

        logger.info(
            "Completed search for %d queries (%d found).",
            len(queries),
            len(found),
        )
        return found

    def _search_video_id(self, query: str) -> str | None:
        """Return the first matching video ID for a single track query."""
        for item in self.client.search(query):
            video_id = item.get("videoId")
            if video_id:
                return str(video_id)

        logger.warning("No video ID found for song: %s", query)
        return None

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
