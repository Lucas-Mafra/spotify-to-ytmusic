"""Spotify API client built on :mod:`spotipy`."""

from __future__ import annotations

import logging
from typing import Any

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from .config import SPOTIFY_SCOPE, Settings
from .models import Playlist, Track

logger = logging.getLogger(__name__)

_PAGE_SIZE = 100


class SpotifyClient:
    """Thin, lazy wrapper around the Spotify Web API.

    The underlying :class:`spotipy.Spotify` client is created on first use so
    importing this module never triggers an OAuth flow or a network request.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: spotipy.Spotify | None = None

    @property
    def client(self) -> spotipy.Spotify:
        """Return the lazily-initialized Spotipy client."""
        if self._client is None:
            self._client = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    client_id=self._settings.spotify_client_id,
                    client_secret=self._settings.spotify_client_secret,
                    redirect_uri=self._settings.spotify_redirect_uri,
                    scope=SPOTIFY_SCOPE,
                )
            )
        return self._client

    def get_playlists(self) -> list[Playlist]:
        """Return all playlists owned by the authenticated user."""
        user_id = self.client.current_user()["id"]
        page: dict[str, Any] | None = self.client.user_playlists(user_id)

        playlists: list[Playlist] = []
        while page:
            for item in page.get("items", []):
                playlists.append(
                    Playlist(
                        name=item.get("name", "No name"),
                        link=item.get("external_urls", {}).get("spotify", ""),
                    )
                )
            page = self.client.next(page) if page.get("next") else None

        logger.info("Retrieved %d playlists.", len(playlists))
        return playlists

    def get_tracks(self, playlist_url: str) -> list[Track]:
        """Fetch every track from a Spotify playlist as :class:`Track` objects."""
        results = self.client.playlist_items(playlist_url, limit=_PAGE_SIZE, offset=0)
        items = list(results["items"])
        total = results["total"]

        offset = _PAGE_SIZE
        while offset < total:
            page = self.client.playlist_items(playlist_url, limit=_PAGE_SIZE, offset=offset)
            items.extend(page["items"])
            offset += _PAGE_SIZE

        tracks: list[Track] = []
        for item in items:
            track = item.get("track")
            if not track or not track.get("name"):
                continue

            artists = tuple(
                artist["name"] for artist in track.get("artists", []) if artist.get("name")
            )
            if not artists:
                continue

            tracks.append(
                Track(
                    artist=artists[0],
                    title=track["name"],
                    artists=artists,
                    album=(track.get("album") or {}).get("name", ""),
                    duration_ms=track.get("duration_ms"),
                )
            )

        logger.info("Retrieved %d tracks from playlist.", len(tracks))
        return tracks

    def get_playlist_name(self, playlist_url: str) -> str:
        """Resolve the name of a Spotify playlist from its URL."""
        playlist: dict[str, Any] = self.client.playlist(playlist_url)
        return str(playlist["name"])
