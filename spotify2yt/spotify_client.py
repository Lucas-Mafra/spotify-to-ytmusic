"""Spotify API client."""

from __future__ import annotations

import logging
import os

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from .matching import Track

load_dotenv()

logger = logging.getLogger(__name__)

_client: spotipy.Spotify | None = None


def _get_client() -> spotipy.Spotify:
    """Build the Spotify client lazily so the CLI works without credentials."""
    global _client
    if _client is None:
        if not os.getenv("SPOTIFY_CLIENT_ID"):
            raise RuntimeError(
                "Spotify credentials are missing. Copy .env.example to .env and set "
                "SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET and SPOTIFY_REDIRECT_URI."
            )
        _client = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
                scope="playlist-read-private",
            )
        )
    return _client


def get_spotify_tracks(playlist_url: str) -> list[Track]:
    """Return structured tracks (title, artists, album, duration) of a playlist."""
    page = _get_client().playlist_items(playlist_url, limit=100, offset=0)
    items = list(page.get("items") or [])
    total = page.get("total", 0)

    offset = 100
    while offset < total:
        page = _get_client().playlist_items(playlist_url, limit=100, offset=offset)
        items.extend(page["items"])
        offset += 100

    tracks: list[Track] = []
    for item in items:
        track = item.get("track")
        if not track or not track.get("name"):
            continue
        artists = tuple(
            artist["name"] for artist in track.get("artists", []) if artist.get("name")
        )
        tracks.append(
            Track(
                title=track["name"],
                artists=artists,
                album=(track.get("album") or {}).get("name", ""),
                duration_ms=track.get("duration_ms"),
            )
        )

    logger.info("Retrieved %d tracks from playlist.", len(tracks))
    return tracks


def get_spotify_playlists() -> list[dict[str, str]]:
    """Return the user's playlists as ``{"name": ..., "link": ...}`` entries."""
    sp = _get_client()
    page = sp.user_playlists(sp.current_user()["id"])

    playlists: list[dict[str, str]] = []
    while page:
        for playlist in page.get("items", []):
            playlists.append(
                {
                    "name": playlist.get("name", "No name"),
                    "link": playlist.get("external_urls", {}).get("spotify", ""),
                }
            )
        page = sp.next(page) if page.get("next") else None

    logger.info("Retrieved %d playlists.", len(playlists))
    return playlists


def select_spotify_playlist(url: str) -> str:
    """Return the name of the Spotify playlist at ``url``."""
    playlist = _get_client().playlist(url)
    return playlist["name"]
